from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse, Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import subprocess
import os
import sys
import io
import json
import tempfile
from datetime import datetime
import traceback
import time
import pandas as pd
import getpass

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'DataValidation'))

app = FastAPI(title="WinETL DataRecon - ETL Validation and Data Reconciliation Framework API", version="1.0.0")

# Allow React/Frontend UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.join(BASE_DIR, "..", "etl_project_two_tables")
REPORT_PATH = os.path.join(PROJECT_PATH, "reports")
FRONTEND_PATH = os.path.join(BASE_DIR, "..", "frontend")
LOGS_PATH = os.path.join(PROJECT_PATH, "logs")
UPLOAD_PATH = os.path.join(PROJECT_PATH, "uploads")
PIPELINE_LOGS_FILE = os.path.join(LOGS_PATH, "pipeline_execution_logs.json")
PROJECTS_FILE = os.path.join(BASE_DIR, "..", "projects.json")

# Create necessary directories if they don't exist
os.makedirs(UPLOAD_PATH, exist_ok=True)
os.makedirs(LOGS_PATH, exist_ok=True)
os.makedirs(REPORT_PATH, exist_ok=True)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")

# Mount assets directory for authentication module
ASSETS_PATH = os.path.join(FRONTEND_PATH, "assets")
if os.path.exists(ASSETS_PATH):
    app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")


class ValidationRequest(BaseModel):
    source_table: str = ""
    target_table: str = ""
    source_query: str
    target_query: str
    source_database: str = "default"
    target_database: str = "default"
    source_db_config: Optional[dict] = None
    target_db_config: Optional[dict] = None
    validations: dict
    sample_size: int = 0  # 0 means all records, otherwise TOP N
    project_id: Optional[str] = None  # Project context for filtering


class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    full_name: str


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    type: str = "project"  # project, account, or product
    created_at: str
    updated_at: str
    created_by: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    type: str = "project"
    creator_email: Optional[str] = None
    creator_role: Optional[str] = None


# Store execution results
execution_results = {}
validation_outputs = {}
execution_metadata = {}  # Store table names and timestamps for each execution
pipeline_execution_logs = []  # Detailed pipeline execution logs
projects_data = {"projects": [], "accounts": [], "products": [], "last_updated": None}


def load_projects():
    """Load projects from JSON file"""
    global projects_data
    try:
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
                projects_data = json.load(f)
                print(f"[INFO] Loaded projects data from file")
        else:
            projects_data = {"projects": [], "accounts": [], "products": [], "last_updated": None}
            save_projects()
            print("[INFO] No existing projects file found, created new one")
    except Exception as e:
        print(f"[ERROR] Failed to load projects: {e}")
        projects_data = {"projects": [], "accounts": [], "products": [], "last_updated": None}


def save_projects():
    """Save projects to JSON file"""
    try:
        projects_data["last_updated"] = datetime.now().isoformat()
        with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Failed to save projects: {e}")


# Load existing projects on startup
load_projects()


def ensure_unnamed_project():
    """Ensure an 'Unnamed Project' exists and migrate untagged data to it"""
    global projects_data, pipeline_execution_logs
    
    # Check if Unnamed Project already exists
    unnamed_project = None
    for project in projects_data.get('projects', []):
        if project.get('name') == 'Unnamed Project':
            unnamed_project = project
            break
    
    # Create Unnamed Project if it doesn't exist
    if not unnamed_project:
        unnamed_project = {
            "id": "project_unnamed_default",
            "name": "Unnamed Project",
            "description": "Default project for legacy data without project assignment",
            "type": "project",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": "System"
        }
        if 'projects' not in projects_data:
            projects_data['projects'] = []
        projects_data['projects'].insert(0, unnamed_project)  # Add at beginning
        save_projects()
        print(f"[INFO] Created 'Unnamed Project' for legacy data")
    
    unnamed_project_id = unnamed_project['id']
    
    # Migrate untagged pipeline logs
    migrated_logs = 0
    for log in pipeline_execution_logs:
        if not log.get('project_id'):
            log['project_id'] = unnamed_project_id
            migrated_logs += 1
    
    if migrated_logs > 0:
        save_pipeline_logs()
        print(f"[INFO] Migrated {migrated_logs} pipeline logs to 'Unnamed Project'")
    
    return unnamed_project_id


def load_pipeline_logs():
    """Load pipeline logs from JSON file"""
    global pipeline_execution_logs
    try:
        if os.path.exists(PIPELINE_LOGS_FILE):
            with open(PIPELINE_LOGS_FILE, 'r', encoding='utf-8') as f:
                pipeline_execution_logs = json.load(f)
                print(f"[INFO] Loaded {len(pipeline_execution_logs)} pipeline execution logs from file")
        else:
            pipeline_execution_logs = []
            print("[INFO] No existing pipeline logs file found, starting fresh")
    except Exception as e:
        print(f"[ERROR] Failed to load pipeline logs: {e}")
        pipeline_execution_logs = []


def save_pipeline_logs():
    """Save pipeline logs to JSON file"""
    try:
        with open(PIPELINE_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pipeline_execution_logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Failed to save pipeline logs: {e}")


# Load existing logs on startup
load_pipeline_logs()

# Ensure Unnamed Project exists and migrate legacy data
try:
    ensure_unnamed_project()
except Exception as e:
    print(f"[ERROR] Failed to ensure unnamed project: {e}")


def get_current_user():
    """Get current username"""
    try:
        return getpass.getuser()
    except:
        return "Unknown"


def log_pipeline_execution(pipeline_name, table_name, status, start_date, end_date, 
                          execution_time, error_name=None, log_content=None, project_id=None):
    """Log pipeline execution details"""
    log_entry = {
        "id": len(pipeline_execution_logs) + 1,
        "pipeline_name": pipeline_name,
        "table_name": table_name,
        "status": status,
        "error_name": error_name if error_name else "N/A",
        "log_content": log_content if log_content else "N/A",
        "start_date": start_date,
        "end_date": end_date,
        "execution_time": execution_time,
        "user_name": get_current_user(),
        "timestamp": datetime.now().isoformat(),
        "project_id": project_id if project_id else None
    }
    pipeline_execution_logs.append(log_entry)
    save_pipeline_logs()  # Persist to file
    return log_entry


def get_db_connection():
    """Get database connection with error handling"""
    try:
        from config.db_config import create_connection
        conn = create_connection()
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


@app.get("/")
def root():
    """Serve the main frontend page"""
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))


@app.get("/login.html")
def login_page():
    """Serve the login page"""
    return FileResponse(os.path.join(FRONTEND_PATH, "login.html"))


@app.get("/signup.html")
def signup_page():
    """Serve the signup page"""
    return FileResponse(os.path.join(FRONTEND_PATH, "signup.html"))


@app.get("/admin.html")
def admin_page():
    """Serve the admin dashboard page"""
    return FileResponse(os.path.join(FRONTEND_PATH, "admin.html"))


@app.get("/api/health")
def health():
    """Health check endpoint"""
    return {"status": "running", "message": "ETL Validation API is active", "version": "2.0", "ui_updated": True}


# ============================================
# AUTHENTICATION & AUTHORIZATION ENDPOINTS
# ============================================

from auth import auth_service

class SignupRequest(BaseModel):
    email: str
    user_id: str
    username: str
    password: str
    mobile_number: Optional[str] = ''
    otp: Optional[str] = ''

class LoginRequest(BaseModel):
    email_or_userid: str
    password: str

class OTPRequest(BaseModel):
    mobile_number: str

class OTPVerifyRequest(BaseModel):
    mobile_number: str
    otp: str

class UpdateRoleRequest(BaseModel):
    target_email: str
    role: str
    group: str

class ToggleStatusRequest(BaseModel):
    target_email: str
    is_active: str

class DeleteUserRequest(BaseModel):
    target_email: str

@app.post("/api/auth/request-otp")
def request_otp(request: OTPRequest):
    """Generate and send OTP to mobile number"""
    try:
        if not request.mobile_number:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Mobile number is required"}
            )
        
        otp = auth_service.generate_otp(request.mobile_number)
        
        # In production, send OTP via SMS service (Twilio, AWS SNS, etc.)
        # For demo/development, return OTP in response
        return {
            "success": True,
            "message": "OTP sent successfully",
            "otp": otp,  # Remove this in production!
            "note": "In production, OTP will be sent via SMS. For demo, OTP is displayed here."
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to send OTP: {str(e)}"}
        )

@app.post("/api/auth/verify-otp")
def verify_otp(request: OTPVerifyRequest):
    """Verify OTP"""
    try:
        success, message = auth_service.verify_otp(request.mobile_number, request.otp)
        return {
            "success": success,
            "message": message
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"OTP verification failed: {str(e)}"}
        )

@app.post("/api/auth/signup")
def signup(request: SignupRequest):
    """Register new user"""
    try:
        # OTP verification disabled for demo purposes
        # otp_valid, otp_msg = auth_service.verify_otp(request.mobile_number, request.otp)
        # 
        # if not otp_valid:
        #     return JSONResponse(
        #         status_code=400,
        #         content={"success": False, "message": otp_msg}
        #     )
        
        # Proceed with signup (OTP verification bypassed)
        success, message = auth_service.signup(
            email=request.email,
            user_id=request.user_id,
            username=request.username,
            password=request.password,
            mobile_number=request.mobile_number or '',  # Make mobile optional
            otp_verified=True  # Bypass OTP check
        )
        
        if success:
            return {"success": True, "message": message}
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": message}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Signup failed: {str(e)}"}
        )

@app.post("/api/auth/login")
def login(request: LoginRequest):
    """Authenticate user and create session"""
    try:
        success, user_data, message = auth_service.login(
            email_or_userid=request.email_or_userid,
            password=request.password
        )
        
        if success:
            return {
                "success": True,
                "message": message,
                "user": user_data
            }
        else:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": message}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Login failed: {str(e)}"}
        )

@app.post("/api/auth/logout")
def logout(request: Request):
    """Logout user and destroy session"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "No session token provided"}
            )
        
        session_token = auth_header.replace('Bearer ', '')
        auth_service.logout(session_token)
        
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Logout failed: {str(e)}"}
        )

@app.get("/api/auth/validate")
def validate_session(request: Request):
    """Validate current session"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "No session token"}
            )
        
        session_token = auth_header.replace('Bearer ', '')
        session_data = auth_service.validate_session(session_token)
        
        if session_data:
            return {
                "success": True,
                "user": {
                    "email": session_data['email'],
                    "user_id": session_data['user_id'],
                    "username": session_data['username'],
                    "role": session_data['role'],
                    "group": session_data['group']
                }
            }
        else:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Invalid or expired session"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Validation failed: {str(e)}"}
        )

@app.get("/api/admin/users")
def get_all_users(request: Request):
    """Admin: Get all users"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Unauthorized"}
            )
        
        session_token = auth_header.replace('Bearer ', '')
        session_data = auth_service.validate_session(session_token)
        
        if not session_data or session_data.get('role') != 'Admin':
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "Admin access required"}
            )
        
        users = auth_service.get_all_users()
        return {"success": True, "users": users}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to get users: {str(e)}"}
        )

@app.post("/api/admin/update-role")
def update_user_role(request: UpdateRoleRequest, req: Request):
    """Admin: Update user role and group"""
    try:
        auth_header = req.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Unauthorized"}
            )
        
        session_token = auth_header.replace('Bearer ', '')
        success, message = auth_service.update_user_role(
            admin_session_token=session_token,
            target_email=request.target_email,
            new_role=request.role,
            new_group=request.group
        )
        
        if success:
            return {"success": True, "message": message}
        else:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": message}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to update role: {str(e)}"}
        )

@app.post("/api/admin/toggle-status")
def toggle_user_status(request: ToggleStatusRequest, req: Request):
    """Admin: Toggle user active/inactive status"""
    try:
        auth_header = req.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Unauthorized"}
            )
        
        session_token = auth_header.replace('Bearer ', '')
        success, message = auth_service.toggle_user_status(
            admin_session_token=session_token,
            target_email=request.target_email,
            is_active=request.is_active
        )
        
        if success:
            return {"success": True, "message": message}
        else:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": message}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to toggle status: {str(e)}"}
        )

@app.post("/api/admin/delete-user")
def delete_user(request: DeleteUserRequest, req: Request):
    """Admin: Permanently delete a user"""
    try:
        auth_header = req.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Unauthorized"}
            )
        
        session_token = auth_header.replace('Bearer ', '')
        success, message = auth_service.delete_user(
            admin_session_token=session_token,
            target_email=request.target_email
        )
        
        if success:
            return {"success": True, "message": message}
        else:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": message}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Failed to delete user: {str(e)}"}
        )


# ============================================
# PROJECT CONTEXT MANAGEMENT ENDPOINTS
# ============================================

@app.get("/api/projects")
def get_projects(type: Optional[str] = None):
    """Get all projects, accounts, or products"""
    try:
        if type:
            return {"items": projects_data.get(f"{type}s", []), "type": type}
        return projects_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects")
def create_project(project: ProjectCreate):
    """Create a new project, account, or product"""
    try:
        # Auto-assign group field based on project name
        # For Contributors, assign the group to the project name itself
        # This allows automatic filtering by the user's assigned groups
        new_project = {
            "id": f"{project.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(projects_data.get(f'{project.type}s', [])) + 1}",
            "name": project.name,
            "description": project.description,
            "type": project.type,
            "group": project.name,  # Group field matches the project name for RBAC filtering
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": project.creator_email or get_current_user()
        }
        
        key = f"{project.type}s"
        if key not in projects_data:
            projects_data[key] = []
        
        projects_data[key].append(new_project)
        save_projects()
        
        # If a Contributor created this, automatically add the project to their assigned groups
        if project.creator_email and project.creator_role and project.creator_role != 'Admin':
            from auth import auth_service
            success, message = auth_service.add_group_to_user(project.creator_email, project.name)
            if success:
                print(f"[API] Auto-assigned group '{project.name}' to user {project.creator_email}")
            else:
                print(f"[API] Warning: Could not auto-assign group to user: {message}")
        
        return {"success": True, "project": new_project}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, project: ProjectCreate):
    """Update an existing project"""
    try:
        key = f"{project.type}s"
        if key not in projects_data:
            raise HTTPException(status_code=404, detail="Project type not found")
        
        for i, p in enumerate(projects_data[key]):
            if p["id"] == project_id:
                projects_data[key][i].update({
                    "name": project.name,
                    "description": project.description,
                    "updated_at": datetime.now().isoformat()
                })
                save_projects()
                return {"success": True, "project": projects_data[key][i]}
        
        raise HTTPException(status_code=404, detail="Project not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, type: str = "project"):
    """Delete a project"""
    try:
        key = f"{type}s"
        if key not in projects_data:
            raise HTTPException(status_code=404, detail="Project type not found")
        
        for i, p in enumerate(projects_data[key]):
            if p["id"] == project_id:
                deleted_project = projects_data[key].pop(i)
                save_projects()
                return {"success": True, "deleted": deleted_project}
        
        raise HTTPException(status_code=404, detail="Project not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request):
    """OAuth callback endpoint for Databricks authentication - auto-closes tab"""
    # Get query parameters (code, state, etc.)
    params = dict(request.query_params)
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Authentication Successful</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: #fff;
            }
            .container {
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                padding: 3rem;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                max-width: 500px;
            }
            .icon {
                font-size: 4rem;
                margin-bottom: 1.5rem;
                animation: scaleIn 0.5s ease-out;
            }
            h1 {
                margin: 0 0 1rem 0;
                font-size: 2rem;
                font-weight: 600;
            }
            p {
                margin: 0.5rem 0;
                font-size: 1.1rem;
                opacity: 0.9;
            }
            .countdown {
                font-size: 3rem;
                font-weight: 700;
                margin: 1.5rem 0;
                animation: pulse 1s infinite;
            }
            @keyframes scaleIn {
                from {
                    transform: scale(0);
                    opacity: 0;
                }
                to {
                    transform: scale(1);
                    opacity: 1;
                }
            }
            @keyframes pulse {
                0%, 100% {
                    transform: scale(1);
                }
                50% {
                    transform: scale(1.05);
                }
            }
            .close-btn {
                margin-top: 2rem;
                padding: 0.8rem 2rem;
                font-size: 1rem;
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.5);
                color: white;
                border-radius: 50px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .close-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">✅</div>
            <h1>Authentication Successful!</h1>
            <p>Databricks connection authenticated successfully.</p>
            <p>This tab will close automatically in:</p>
            <div class="countdown" id="countdown">3</div>
            <button class="close-btn" onclick="window.close()">Close Now</button>
        </div>
        
        <script>
            let seconds = 3;
            const countdownEl = document.getElementById('countdown');
            
            const interval = setInterval(() => {
                seconds--;
                countdownEl.textContent = seconds;
                
                if (seconds <= 0) {
                    clearInterval(interval);
                    // Try multiple methods to close the tab
                    window.close();
                    
                    // Fallback: If window.close() doesn't work, redirect to a blank page
                    setTimeout(() => {
                        window.location.href = 'about:blank';
                    }, 500);
                }
            }, 1000);
            
            // Also try to close immediately if this is a popup
            setTimeout(() => {
                if (window.opener) {
                    window.close();
                }
            }, 3000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.get("/oauth/auto-close-script", response_class=HTMLResponse)
async def get_auto_close_script():
    """Provides a bookmarklet/script to auto-close Databricks OAuth tabs"""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Databricks OAuth Auto-Close Helper</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                max-width: 800px;
                margin: 2rem auto;
                padding: 2rem;
                background: #f7fafc;
            }
            .card {
                background: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 1.5rem;
            }
            h1 {
                color: #2d3748;
                margin-top: 0;
            }
            h2 {
                color: #4a5568;
                font-size: 1.3rem;
                margin-top: 1.5rem;
            }
            code {
                background: #edf2f7;
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
            }
            .script-box {
                background: #1a202c;
                color: #48bb78;
                padding: 1.5rem;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                overflow-x: auto;
                margin: 1rem 0;
            }
            .bookmarklet {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 50px;
                text-decoration: none;
                font-weight: 600;
                margin: 1rem 0;
                transition: transform 0.2s;
            }
            .bookmarklet:hover {
                transform: translateY(-2px);
            }
            .info {
                background: #ebf8ff;
                border-left: 4px solid #4299e1;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 4px;
            }
            .step {
                margin: 1rem 0;
                padding-left: 2rem;
            }
            .step-number {
                display: inline-block;
                background: #667eea;
                color: white;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                text-align: center;
                line-height: 28px;
                margin-left: -2rem;
                margin-right: 0.5rem;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 Databricks OAuth Auto-Close Helper</h1>
            <p>This page provides solutions to automatically close the Databricks OAuth callback tab.</p>
        </div>

        <div class="card">
            <h2>Solution 1: Browser Bookmarklet (Easiest)</h2>
            <p>Drag this button to your bookmarks bar, then click it when the "Please close this tab" message appears:</p>
            
            <a href="javascript:(function(){if(document.body.textContent.includes('Please close this tab')||document.body.textContent.includes('Databricks Sql Connector received a response')){setTimeout(function(){window.close();},1000);var d=document.createElement('div');d.style.cssText='position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:2rem;border-radius:20px;font-size:1.5rem;z-index:99999;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.3)';d.innerHTML='<div style=\"font-size:3rem;margin-bottom:1rem\">✅</div><div>Authentication Successful!</div><div style=\"margin-top:1rem;font-size:1.2rem\">Closing in <span id=\"counter\">3</span>s...</div>';document.body.appendChild(d);var c=3;var i=setInterval(function(){c--;document.getElementById('counter').textContent=c;if(c<=0){clearInterval(i);window.close()}},1000)}else{alert('This bookmarklet only works on Databricks OAuth callback pages.')}})();" 
               class="bookmarklet">
                📌 Auto-Close Databricks OAuth
            </a>
            
            <div class="info">
                <strong>How to use:</strong>
                <div class="step"><span class="step-number">1</span>Drag the button above to your bookmarks bar</div>
                <div class="step"><span class="step-number">2</span>When Databricks OAuth opens the "Please close this tab" page, click the bookmark</div>
                <div class="step"><span class="step-number">3</span>The tab will automatically close after 3 seconds</div>
            </div>
        </div>

        <div class="card">
            <h2>Solution 2: Browser Console Script</h2>
            <p>When the "Please close this tab" message appears, press <code>F12</code> to open Developer Tools, go to the Console tab, and paste this script:</p>
            
            <div class="script-box">
setTimeout(() => {<br>
&nbsp;&nbsp;const overlay = document.createElement('div');<br>
&nbsp;&nbsp;overlay.style.cssText = `<br>
&nbsp;&nbsp;&nbsp;&nbsp;position: fixed;<br>
&nbsp;&nbsp;&nbsp;&nbsp;top: 0; left: 0; right: 0; bottom: 0;<br>
&nbsp;&nbsp;&nbsp;&nbsp;background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);<br>
&nbsp;&nbsp;&nbsp;&nbsp;display: flex; align-items: center; justify-content: center;<br>
&nbsp;&nbsp;&nbsp;&nbsp;z-index: 999999;<br>
&nbsp;&nbsp;`;<br>
&nbsp;&nbsp;overlay.innerHTML = `<br>
&nbsp;&nbsp;&nbsp;&nbsp;&lt;div style="text-align:center;color:white"&gt;<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&lt;div style="font-size:4rem;margin-bottom:1rem"&gt;✅&lt;/div&gt;<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&lt;h1 style="margin:0;font-size:2rem"&gt;Authentication Successful!&lt;/h1&gt;<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&lt;p style="font-size:1.2rem;margin-top:1rem"&gt;Closing in &lt;span id="counter"&gt;3&lt;/span&gt;s...&lt;/p&gt;<br>
&nbsp;&nbsp;&nbsp;&nbsp;&lt;/div&gt;<br>
&nbsp;&nbsp;`;<br>
&nbsp;&nbsp;document.body.appendChild(overlay);<br>
&nbsp;&nbsp;let count = 3;<br>
&nbsp;&nbsp;const interval = setInterval(() => {<br>
&nbsp;&nbsp;&nbsp;&nbsp;count--;<br>
&nbsp;&nbsp;&nbsp;&nbsp;document.getElementById('counter').textContent = count;<br>
&nbsp;&nbsp;&nbsp;&nbsp;if (count <= 0) {<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;clearInterval(interval);<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;window.close();<br>
&nbsp;&nbsp;&nbsp;&nbsp;}<br>
&nbsp;&nbsp;}, 1000);<br>
}, 500);
            </div>
            
            <button onclick="copyScript()" style="background:#48bb78;color:white;border:none;padding:0.75rem 1.5rem;border-radius:8px;cursor:pointer;font-weight:600;margin-top:1rem">
                📋 Copy Script
            </button>
        </div>

        <div class="card">
            <h2>Solution 3: Custom OAuth App Configuration</h2>
            <p>For a permanent solution, configure your Databricks OAuth app to use our custom callback URL:</p>
            
            <div class="info">
                <strong>Redirect URI to use:</strong><br>
                <code id="callbackUrl">http://localhost:8000/oauth/callback</code>
                <button onclick="copyCallback()" style="margin-left:1rem;padding:0.5rem 1rem;border:1px solid #4299e1;background:white;border-radius:4px;cursor:pointer">Copy</button>
            </div>
            
            <p><strong>Steps:</strong></p>
            <div class="step"><span class="step-number">1</span>Go to your Databricks workspace settings</div>
            <div class="step"><span class="step-number">2</span>Navigate to <strong>Settings → Developer → OAuth Apps</strong></div>
            <div class="step"><span class="step-number">3</span>Edit your OAuth application</div>
            <div class="step"><span class="step-number">4</span>Add the redirect URI: <code>http://localhost:8000/oauth/callback</code></div>
            <div class="step"><span class="step-number">5</span>Save the configuration</div>
        </div>

        <script>
            function copyScript() {
                const script = `setTimeout(() => {
  const overlay = document.createElement('div');
  overlay.style.cssText = \`position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; z-index: 999999;\`;
  overlay.innerHTML = \`<div style="text-align:center;color:white"><div style="font-size:4rem;margin-bottom:1rem">✅</div><h1 style="margin:0;font-size:2rem">Authentication Successful!</h1><p style="font-size:1.2rem;margin-top:1rem">Closing in <span id="counter">3</span>s...</p></div>\`;
  document.body.appendChild(overlay);
  let count = 3;
  const interval = setInterval(() => {
    count--;
    document.getElementById('counter').textContent = count;
    if (count <= 0) {
      clearInterval(interval);
      window.close();
    }
  }, 1000);
}, 500);`;
                
                navigator.clipboard.writeText(script).then(() => {
                    alert('✅ Script copied to clipboard!');
                });
            }
            
            function copyCallback() {
                const url = document.getElementById('callbackUrl').textContent;
                navigator.clipboard.writeText(url).then(() => {
                    alert('✅ Callback URL copied to clipboard!');
                });
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.get("/oauth/databricks-auto-close.user.js")
async def get_userscript():
    """Provides a userscript for automatic Databricks OAuth tab closure"""
    
    userscript = """// ==UserScript==
// @name         Databricks OAuth Safe Auto-Close v5.0
// @namespace    http://localhost:8000/
// @version      5.0
// @description  Safely closes ONLY Databricks OAuth callback tabs on port 8020
// @author       ETL Validation Framework
// @match        *://localhost:8020/*
// @match        *://127.0.0.1:8020/*
// @grant        window.close
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('[🚀 Databricks Auto-Close v5.0] Script loaded at:', new Date().toLocaleTimeString());
    console.log('[🌐 URL]:', window.location.href);
    console.log('[🔌 Port]:', window.location.port);
    console.log('[⏰ Run-at]: document-start (runs immediately)');
    
    // SAFETY CHECK: Only run on port 8020
    if (window.location.port !== '8020') {
        console.log('[🛑 Auto-Close] Not on port 8020, exiting...');
        return;
    }
    
    console.log('[✅ Port Check] Running on port 8020 - SAFE TO PROCEED');
    
    // URL parameter check - OAuth callback always has 'code' parameter
    const urlParams = new URLSearchParams(window.location.search);
    const hasOAuthCode = urlParams.has('code') || urlParams.has('state');
    
    console.log('[🔍 URL Check] Has OAuth code/state parameter:', hasOAuthCode);
    
    if (hasOAuthCode) {
        console.log('[🎯 DETECTED] OAuth callback URL - proceeding with auto-close');
        
        // Immediate visual feedback
        const style = document.createElement('style');
        style.textContent = `
            body { margin: 0; padding: 0; overflow: hidden; }
            @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        `;
        document.head.appendChild(style);
        
        // Create overlay immediately
        const overlay = document.createElement('div');
        overlay.id = 'oauth-close-overlay';
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 999999;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            display: flex; align-items: center; justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: white; animation: fadeIn 0.3s;
        `;
        overlay.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <div style="font-size: 6rem; margin-bottom: 1rem; animation: pulse 1s infinite;">✅</div>
                <h1 style="margin: 0; font-size: 2.5rem; font-weight: 600;">Authentication Successful!</h1>
                <p style="margin: 1.5rem 0; font-size: 1.3rem; opacity: 0.95;">
                    Databricks connection established
                </p>
                <p style="margin: 1rem 0; font-size: 1.5rem; font-weight: 700;">
                    Closing in <span id="countdown">2</span>s
                </p>
                <button id="close-now-btn" style="
                    margin-top: 2rem; padding: 1rem 2.5rem; font-size: 1.1rem;
                    background: white; color: #10b981; border: none;
                    border-radius: 50px; cursor: pointer; font-weight: 600;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    transition: transform 0.2s, box-shadow 0.2s;
                " onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 16px rgba(0,0,0,0.3)'"
                   onmouseout="this.style.transform='';this.style.boxShadow='0 4px 12px rgba(0,0,0,0.2)'">
                    Close Now
                </button>
            </div>
        `;
        
        // Add overlay when DOM is ready
        function addOverlay() {
            if (document.body) {
                document.body.innerHTML = '';
                document.body.appendChild(overlay);
                console.log('[✨ UI] Overlay displayed');
                
                // Setup close button
                const closeBtn = document.getElementById('close-now-btn');
                if (closeBtn) {
                    closeBtn.onclick = () => {
                        console.log('[👆 User Action] Close button clicked');
                        window.close();
                    };
                }
                
                // Start countdown
                let count = 2;
                const countdownElement = document.getElementById('countdown');
                const countdownTimer = setInterval(() => {
                    count--;
                    if (countdownElement) {
                        countdownElement.textContent = count;
                    }
                    console.log('[⏱️ Countdown]:', count);
                    
                    if (count <= 0) {
                        clearInterval(countdownTimer);
                        console.log('[🚪 CLOSING] Attempting to close window...');
                        
                        // Try to close
                        try {
                            window.close();
                            console.log('[✅ SUCCESS] window.close() executed');
                        } catch (e) {
                            console.log('[⚠️ BLOCKED] Could not close automatically:', e.message);
                            if (countdownElement) {
                                countdownElement.parentElement.innerHTML = `
                                    <p style="font-size: 1.2rem; margin-top: 1rem;">
                                        Press <kbd style="background:white;color:#10b981;padding:0.3rem 0.6rem;border-radius:4px;font-weight:700;">Ctrl+W</kbd> to close this tab
                                    </p>
                                `;
                            }
                        }
                    }
                }, 1000);
                
            } else {
                setTimeout(addOverlay, 50);
            }
        }
        
        // Start immediately
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', addOverlay);
        } else {
            addOverlay();
        }
        
        // Also try to close after a delay as backup
        setTimeout(() => {
            console.log('[⏰ Backup Timer] Attempting close...');
            window.close();
        }, 2500);
        
    } else {
        console.log('[ℹ️ INFO] Not an OAuth callback - no code parameter found');
        console.log('[👀 Monitoring] Waiting for OAuth redirect...');
    }
    
})();
"""
    
    return Response(content=userscript, media_type="text/javascript")


@app.get("/oauth/install", response_class=HTMLResponse)
async def install_userscript():
    """Installation page for the userscript"""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Install Databricks Auto-Close Script</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 800px;
                width: 100%;
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 3rem 2rem;
                text-align: center;
            }
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
            }
            .header p {
                font-size: 1.2rem;
                opacity: 0.9;
            }
            .content {
                padding: 2rem;
            }
            .step {
                background: #f7fafc;
                border-left: 4px solid #667eea;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 8px;
            }
            .step-number {
                display: inline-block;
                background: #667eea;
                color: white;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                text-align: center;
                line-height: 36px;
                font-weight: bold;
                font-size: 1.2rem;
                margin-right: 1rem;
            }
            .step h3 {
                display: inline-block;
                color: #2d3748;
                font-size: 1.3rem;
                margin-bottom: 0.5rem;
            }
            .step p {
                margin-top: 1rem;
                color: #4a5568;
                line-height: 1.6;
                margin-left: 3rem;
            }
            .install-btn {
                display: block;
                width: 100%;
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                padding: 1.5rem;
                border: none;
                border-radius: 12px;
                font-size: 1.3rem;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                text-align: center;
                margin: 2rem 0;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .install-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(72, 187, 120, 0.4);
            }
            .install-btn i {
                margin-right: 0.5rem;
                font-size: 1.5rem;
            }
            .info-box {
                background: #ebf8ff;
                border-left: 4px solid #4299e1;
                padding: 1rem;
                border-radius: 8px;
                margin: 1.5rem 0;
            }
            .info-box strong {
                color: #2c5282;
                display: block;
                margin-bottom: 0.5rem;
            }
            .info-box p {
                color: #2d3748;
                margin: 0;
                line-height: 1.6;
            }
            .extension-icons {
                display: flex;
                gap: 1rem;
                justify-content: center;
                margin: 2rem 0;
            }
            .extension-icon {
                text-align: center;
                padding: 1rem;
                background: #f7fafc;
                border-radius: 12px;
                flex: 1;
                transition: background 0.2s;
            }
            .extension-icon:hover {
                background: #edf2f7;
            }
            .extension-icon img {
                width: 48px;
                height: 48px;
                margin-bottom: 0.5rem;
            }
            .extension-icon a {
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
            }
            .success-icon {
                font-size: 4rem;
                text-align: center;
                margin: 2rem 0;
            }
            code {
                background: #2d3748;
                color: #68d391;
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🚀</div>
                <h1>Databricks OAuth Auto-Close</h1>
                <p>Automatic tab closing for seamless authentication</p>
            </div>
            
            <div class="content">
                <div class="info-box">
                    <strong>⚡ What does this do?</strong>
                    <p>Automatically detects and closes the Databricks OAuth callback tab after successful authentication, so you don't have to manually close it every time.</p>
                </div>
                
                <h2 style="margin: 2rem 0 1rem 0; color: #2d3748; text-align: center;">Installation Steps</h2>
                
                <div class="step">
                    <span class="step-number">1</span>
                    <h3>Install Tampermonkey Extension</h3>
                    <p>First, install the Tampermonkey browser extension (if you don't have it already):</p>
                </div>
                
                <div class="extension-icons">
                    <div class="extension-icon">
                        <i class="fab fa-chrome" style="font-size: 3rem; color: #4285F4;"></i>
                        <p><a href="https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo" target="_blank">Chrome</a></p>
                    </div>
                    <div class="extension-icon">
                        <i class="fab fa-firefox" style="font-size: 3rem; color: #FF7139;"></i>
                        <p><a href="https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/" target="_blank">Firefox</a></p>
                    </div>
                    <div class="extension-icon">
                        <i class="fab fa-edge" style="font-size: 3rem; color: #0078D7;"></i>
                        <p><a href="https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd" target="_blank">Edge</a></p>
                    </div>
                </div>
                
                <div class="step">
                    <span class="step-number">2</span>
                    <h3>Install the Auto-Close Script</h3>
                    <p>Click the button below to install the userscript. Tampermonkey will open and ask for confirmation.</p>
                </div>
                
                <a href="/oauth/databricks-auto-close.user.js" class="install-btn">
                    <i class="fas fa-download"></i>
                    Install Databricks Auto-Close Script
                </a>
                
                <div class="step">
                    <span class="step-number">3</span>
                    <h3>Test the Installation</h3>
                    <p>Before testing with real Databricks OAuth, verify the userscript is working:</p>
                    <a href="/oauth/test-autoclose" target="_blank" style="display:inline-block;margin:1rem 0;padding:0.75rem 1.5rem;background:#10b981;color:white;text-decoration:none;border-radius:8px;font-weight:600;">
                        🧪 Open Test Page
                    </a>
                    <p style="margin-top:0.5rem;color:#718096;font-size:0.9rem;">This will help verify if Tampermonkey is running the script correctly.</p>
                </div>
                
                <div class="step">
                    <span class="step-number">4</span>
                    <h3>Done! Use with Databricks</h3>
                    <p>The next time you authenticate with Databricks using OAuth, the callback tab will automatically close after 2 seconds with a beautiful success animation.</p>
                </div>
                
                <div class="success-icon">✨ 🎉 ✨</div>
                
                <div class="info-box" style="background: #f0fff4; border-color: #48bb78;">
                    <strong style="color: #22543d;">🎯 How it works:</strong>
                    <p>The script monitors all localhost ports (including <code>localhost:8020</code>) and <strong>INSTANTLY</strong> detects and closes OAuth callback windows. Version 3.0 closes immediately without any countdown or animation.</p>
                </div>
                
                <div class="info-box" style="background: #fff3cd; border-color: #ffc107; margin-top: 2rem;">
                    <strong style="color: #856404;">⚡ Nuclear Option: PowerShell Auto-Closer</strong>
                    <p style="margin-bottom: 1rem;">If the userscript doesn't work or you prefer a more aggressive approach, use the PowerShell background monitor:</p>
                    <ol style="margin-left: 1.5rem; color: #856404;">
                        <li>Open PowerShell as Administrator in your project folder</li>
                        <li>Run: <code style="background: #212529; color: #ffc107; padding: 0.3rem 0.6rem; border-radius: 4px; display: inline-block; margin: 0.5rem 0;">powershell -ExecutionPolicy Bypass -File close_oauth_windows.ps1</code></li>
                        <li>Or simply double-click: <code>run_oauth_closer.bat</code></li>
                        <li>Leave it running in the background - it will instantly close ALL OAuth callback windows</li>
                    </ol>
                    <p style="margin-top: 1rem; font-size: 0.9rem;">This runs continuously and kills callback windows every 100ms. Press Ctrl+C to stop.</p>
                </div>
                
                <div style="text-align: center; margin-top: 2rem; padding-top: 2rem; border-top: 2px solid #e2e8f0;">
                    <p style="color: #718096;">
                        <a href="/oauth/test-autoclose" target="_blank" style="color: #10b981; font-weight: 600;">🧪 Test Page</a> | 
                        <a href="/oauth/auto-close-script" style="color: #667eea;">Alternative Solutions</a>
                    </p>
                </div>
                </div>
            </div>
        </div>
        
        <script>
            // Detect if user clicked the install button
            document.querySelector('.install-btn').addEventListener('click', function() {
                setTimeout(() => {
                    alert('✅ After Tampermonkey shows the installation page, click "Install" to complete the setup!');
                }, 100);
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.get("/oauth/test-autoclose", response_class=HTMLResponse)
async def test_autoclose():
    """Test page that simulates Databricks OAuth callback to verify userscript works"""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Databricks OAuth Callback Test</title>
        <style>
            body {
                margin: 0;
                padding: 2rem;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f7fafc;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            h1 { color: #2d3748; }
            .status {
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                font-weight: 600;
            }
            .success { background: #c6f6d5; color: #22543d; }
            .warning { background: #feebc8; color: #744210; }
            .info { background: #bee3f8; color: #2c5282; }
            code {
                background: #edf2f7;
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-family: monospace;
            }
            .test-trigger {
                margin: 2rem 0;
                padding: 2rem;
                background: #f7fafc;
                border-radius: 8px;
                border: 2px dashed #cbd5e0;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                margin: 0.5rem;
            }
            button:hover {
                background: #5a67d8;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 Databricks Auto-Close Test Page</h1>
            
            <div class="status info">
                <strong>ℹ️ Instructions:</strong><br>
                This page helps you verify if the Tampermonkey userscript is working correctly.
            </div>
            
            <div class="test-trigger">
                <h3>Step 1: Check if userscript is active</h3>
                <p>Open your browser console (<code>F12</code> → Console tab) and look for:</p>
                <code>[Databricks Auto-Close v2.0] Script initialized</code>
                
                <div id="scriptStatus" style="margin-top: 1rem; padding: 1rem; border-radius: 4px; background: #fee;"></div>
            </div>
            
            <div class="test-trigger">
                <h3>Step 2: Trigger the auto-close</h3>
                <p>Click the button below to simulate the Databricks OAuth callback message:</p>
                <button onclick="triggerAutoClose()">🧪 Simulate OAuth Callback</button>
                <p style="margin-top: 1rem; color: #718096; font-size: 0.9rem;">
                    If the userscript is working, you should see a success overlay and this tab should attempt to close.
                </p>
            </div>
            
            <div class="test-trigger">
                <h3>Step 3: Update userscript if needed</h3>
                <p>If the test doesn't work:</p>
                <ol>
                    <li>Click Tampermonkey icon in your browser</li>
                    <li>Click "Dashboard"</li>
                    <li>Find "Databricks OAuth Auto-Close"</li>
                    <li>Click the trash icon to remove it</li>
                    <li>Go back to <a href="/oauth/install" target="_blank">installation page</a></li>
                    <li>Click "Install" again</li>
                </ol>
                <button onclick="window.open('/oauth/install', '_blank')" style="background: #48bb78;">
                    🔄 Re-install Userscript
                </button>
            </div>
            
            <div class="status warning">
                <strong>⚠️ Note about window.close():</strong><br>
                Modern browsers only allow <code>window.close()</code> to work on windows opened by JavaScript.
                If this test page was opened by clicking a link, the browser might block the close attempt.
                However, the Databricks OAuth callback (opened automatically) should close successfully.
            </div>
        </div>
        
        <script>
            // Check if userscript is loaded
            window.addEventListener('load', function() {
                setTimeout(() => {
                    const statusDiv = document.getElementById('scriptStatus');
                    // The userscript should log to console
                    statusDiv.innerHTML = '<strong>Check your browser console (F12).</strong><br>Look for log messages starting with <code>[Databricks Auto-Close]</code>';
                    statusDiv.style.background = '#fef3c7';
                }, 500);
            });
            
            function triggerAutoClose() {
                // Add the trigger text that the userscript looks for
                const trigger = document.createElement('div');
                trigger.style.display = 'none';
                trigger.textContent = 'Please close this tab. The Databricks Sql Connector received a response. You may close this tab.';
                document.body.appendChild(trigger);
                
                console.log('🧪 TEST: Added trigger text to page');
                console.log('🧪 TEST: Userscript should detect this and show overlay');
                
                // Force mutation observer to detect changes
                document.body.appendChild(document.createTextNode(' '));
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.post("/api/db/test")
async def test_database_connection(request: dict):
    """Test database connection"""
    try:
        db_type = request.get('type')
        auth_type = request.get('authType', 'windows')
        print(f"[DEBUG] Testing connection for type: {db_type}, auth: {auth_type}")
        print(f"[DEBUG] Request data: {request}")
        
        # For SQL Server with custom authType, use create_custom_connection
        if db_type == 'sqlserver' and auth_type == 'ActiveDirectoryMfa':
            try:
                conn = create_custom_connection(request)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                return {"success": True, "message": "Connection successful!"}
            except Exception as e:
                print(f"[ERROR] Connection test failed: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e)}
        
        # Create connector based on type for other auth methods
        from config.db_config import (
            SQLServerConnector, MySQLConnector, PostgreSQLConnector,
            OracleConnector, MongoDBConnector, S3Connector,
            AzureBlobConnector, GCSConnector, DatabricksConnector,
            PowerBIConnector, AzureSynapseConnector, MicrosoftFabricConnector
        )
        
        connector = None
        
        if db_type == 'sqlserver':
            # Fix double backslash issue in server name
            server_name = request.get('server', '').replace('\\\\', '\\')
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'trusted_connection': request.get('trusted_connection', 'yes'),
                'username': request.get('username'),
                'password': request.get('password')
            }
            print(f"[DEBUG] SQL Server config: server={config['server']}, database={config['database']}, trusted_connection={config['trusted_connection']}")
            connector = SQLServerConnector(config)
        
        elif db_type == 'azuresynapse':
            server_name = request.get('server', '').replace('\\\\', '\\')
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'username': request.get('username'),
                'password': request.get('password'),
                'authentication': request.get('authentication'),
                'encrypt': request.get('encrypt', True),
                'trust_server_certificate': request.get('trust_server_certificate', False)
            }
            print(f"[DEBUG] Azure Synapse config: server={config['server']}, database={config['database']}")
            connector = AzureSynapseConnector(config)
        
        elif db_type == 'fabric':
            server_name = request.get('server', '').replace('\\\\', '\\')
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'username': request.get('username'),
                'password': request.get('password'),
                'authentication': request.get('authentication'),
                'client_id': request.get('client_id'),
                'client_secret': request.get('client_secret'),
                'encrypt': request.get('encrypt', True),
                'trust_server_certificate': request.get('trust_server_certificate', True)
            }
            print(f"[DEBUG] Microsoft Fabric config: server={config['server']}, database={config['database']}")
            connector = MicrosoftFabricConnector(config)
        
        elif db_type == 'mysql':
            config = {
                'host': request.get('server'),
                'username': request.get('username'),
                'password': request.get('password'),
                'database': request.get('database')
            }
            connector = MySQLConnector(config)
        
        elif db_type == 'postgresql':
            config = {
                'host': request.get('server'),
                'username': request.get('username'),
                'password': request.get('password'),
                'database': request.get('database')
            }
            connector = PostgreSQLConnector(config)
        
        elif db_type == 'oracle':
            config = {
                'host': request.get('server'),
                'port': request.get('port', 1521),
                'username': request.get('username'),
                'password': request.get('password'),
                'service_name': request.get('service_name')
            }
            connector = OracleConnector(config)
        
        elif db_type == 'mongodb':
            config = {
                'uri': request.get('uri'),
                'database': request.get('database')
            }
            connector = MongoDBConnector(config)
        
        elif db_type == 's3':
            config = {
                'access_key': request.get('access_key'),
                'secret_key': request.get('secret_key'),
                'region': request.get('region')
            }
            connector = S3Connector(config)
        
        elif db_type == 'azureblob':
            config = {
                'connection_string': request.get('connection_string')
            }
            connector = AzureBlobConnector(config)
        
        elif db_type == 'gcs':
            config = {
                'key_file': request.get('key_file')
            }
            connector = GCSConnector(config)
        
        elif db_type == 'databricks':
            config = {
                'workspace_url': request.get('workspace_url'),
                'http_path': request.get('http_path'),
                'catalog': request.get('catalog'),
                'schema': request.get('schema'),
                'auth_type': request.get('databricks_auth_type', 'token'),
                'access_token': request.get('access_token'),
                'azure_tenant_id': request.get('azure_tenant_id'),
                'azure_client_id': request.get('azure_client_id'),
                'azure_client_secret': request.get('azure_client_secret')
            }
            print(f"[DEBUG] Databricks config: workspace={config['workspace_url']}, auth={config['auth_type']}")
            connector = DatabricksConnector(config)
        
        elif db_type == 'powerbi':
            config = {
                'client_id': request.get('client_id'),
                'client_secret': request.get('client_secret'),
                'tenant_id': request.get('tenant_id')
            }
            connector = PowerBIConnector(config)
        
        else:
            return {"success": False, "error": f"Unsupported database type: {db_type}"}
        
        # Test connection
        if connector:
            try:
                print(f"[DEBUG] Testing connection for {db_type}...")
                connection = connector.connect()
                print(f"[DEBUG] Connection result: {connection}")
                if connection:
                    connector.disconnect()
                    return {"success": True, "message": "Connection successful!"}
                else:
                    error_msg = "Failed to establish connection. Please check your credentials and server details."
                    print(f"[ERROR] Connection failed: {error_msg}")
                    return {"success": False, "error": error_msg}
            except Exception as conn_err:
                print(f"[ERROR] Exception during connection: {conn_err}")
                import traceback
                traceback.print_exc()
                error_msg = str(conn_err)
                if "Login failed" in error_msg:
                    return {"success": False, "error": "Login failed. Please check username and password."}
                elif "SQL Server does not exist" in error_msg or "server was not found" in error_msg.lower():
                    return {"success": False, "error": f"Server '{request.get('server')}' not found or not accessible."}
                elif "Cannot open database" in error_msg:
                    return {"success": False, "error": f"Database '{request.get('database')}' does not exist or cannot be accessed."}
                else:
                    return {"success": False, "error": f"Connection error: {error_msg}"}
        
        return {"success": False, "error": "Failed to create connector"}
        
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


@app.post("/api/db/tables")
async def get_tables_for_connection(request: dict):
    """Get list of tables from a database using provided connection details"""
    try:
        db_type = request.get('type')
        auth_type = request.get('authType', 'windows')
        print(f"[DEBUG] Fetching tables for type: {db_type}, auth: {auth_type}")
        print(f"[DEBUG] Request data: {request}")
        
        # For SQL Server with ActiveDirectoryMfa, use create_custom_connection
        if db_type == 'sqlserver' and auth_type == 'ActiveDirectoryMfa':
            try:
                conn = create_custom_connection(request)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TABLE_SCHEMA, TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """)
                tables = [f"{row[0]}.{row[1]}" for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                print(f"[DEBUG] Found {len(tables)} tables")
                return {"success": True, "tables": tables}
            except Exception as e:
                print(f"[ERROR] Failed to fetch tables: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e)}
        
        # Import connectors for other database types
        from config.db_config import (
            SQLServerConnector, MySQLConnector, PostgreSQLConnector,
            OracleConnector, DatabricksConnector, AzureSynapseConnector, 
            MicrosoftFabricConnector
        )
        
        connector = None
        
        if db_type == 'sqlserver':
            server_name = request.get('server', '').replace('\\\\', '\\')
            auth_type = request.get('authType', 'windows')
            
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'username': request.get('username'),
                'password': request.get('password')
            }
            
            # Handle Azure AD authentication
            if auth_type == 'ActiveDirectoryMfa' or auth_type == 'ActiveDirectoryInteractive':
                config['authentication'] = 'ActiveDirectoryInteractive'
                config['encrypt'] = True
                config['trust_server_certificate'] = False
                config['trusted_connection'] = 'no'
            elif auth_type == 'ActiveDirectoryPassword':
                config['authentication'] = 'ActiveDirectoryPassword'
                config['encrypt'] = True
                config['trust_server_certificate'] = False
                config['trusted_connection'] = 'no'
            elif auth_type == 'sql':
                config['trusted_connection'] = 'no'
            else:  # windows
                config['trusted_connection'] = request.get('trusted_connection', 'yes')
            
            connector = SQLServerConnector(config)
        
        elif db_type == 'azuresynapse':
            server_name = request.get('server', '').replace('\\\\', '\\')
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'username': request.get('username'),
                'password': request.get('password'),
                'authentication': request.get('authentication'),
                'encrypt': request.get('encrypt', True),
                'trust_server_certificate': request.get('trust_server_certificate', False)
            }
            connector = AzureSynapseConnector(config)
        
        elif db_type == 'fabric':
            server_name = request.get('server', '').replace('\\\\', '\\')
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'username': request.get('username'),
                'password': request.get('password'),
                'authentication': request.get('authentication'),
                'client_id': request.get('client_id'),
                'client_secret': request.get('client_secret'),
                'encrypt': request.get('encrypt', True),
                'trust_server_certificate': request.get('trust_server_certificate', True)
            }
            connector = MicrosoftFabricConnector(config)
        
        elif db_type == 'mysql':
            config = {
                'host': request.get('server'),
                'username': request.get('username'),
                'password': request.get('password'),
                'database': request.get('database')
            }
            connector = MySQLConnector(config)
        
        elif db_type == 'postgresql':
            config = {
                'host': request.get('server'),
                'username': request.get('username'),
                'password': request.get('password'),
                'database': request.get('database')
            }
            connector = PostgreSQLConnector(config)
        
        elif db_type == 'oracle':
            config = {
                'host': request.get('server'),
                'port': request.get('port', 1521),
                'username': request.get('username'),
                'password': request.get('password'),
                'service_name': request.get('service_name')
            }
            connector = OracleConnector(config)
        
        elif db_type == 'databricks':
            config = {
                'workspace_url': request.get('workspace_url'),
                'http_path': request.get('http_path'),
                'catalog': request.get('catalog', 'main'),
                'schema': request.get('schema', 'default'),
                'auth_type': request.get('databricks_auth_type', 'token'),
                'access_token': request.get('access_token'),
                'azure_tenant_id': request.get('azure_tenant_id'),
                'azure_client_id': request.get('azure_client_id'),
                'azure_client_secret': request.get('azure_client_secret')
            }
            print(f"[DEBUG] Databricks config: workspace={config['workspace_url']}, catalog={config['catalog']}, schema={config['schema']}")
            connector = DatabricksConnector(config)
        
        else:
            return {"success": False, "error": f"Unsupported database type: {db_type}", "tables": []}
        
        # Connect and get tables
        if connector:
            try:
                print(f"[DEBUG] Connecting to {db_type} to fetch tables...")
                connection = connector.connect()
                
                if not connection:
                    return {"success": False, "error": "Failed to establish connection", "tables": []}
                
                cursor = connection.cursor()
                tables = []
                
                if db_type in ['sqlserver', 'azuresynapse', 'fabric']:
                    cursor.execute("""
                        SELECT TABLE_SCHEMA, TABLE_NAME
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_SCHEMA, TABLE_NAME
                    """)
                    for row in cursor.fetchall():
                        tables.append(f"{row[0]}.{row[1]}")
                
                elif db_type == 'mysql':
                    cursor.execute("""
                        SELECT TABLE_SCHEMA, TABLE_NAME
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_SCHEMA, TABLE_NAME
                    """)
                    for row in cursor.fetchall():
                        tables.append(f"{row[0]}.{row[1]}")
                
                elif db_type == 'postgresql':
                    cursor.execute("""
                        SELECT schemaname, tablename
                        FROM pg_tables
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                        ORDER BY schemaname, tablename
                    """)
                    for row in cursor.fetchall():
                        tables.append(f"{row[0]}.{row[1]}")
                
                elif db_type == 'oracle':
                    cursor.execute("""
                        SELECT owner, table_name
                        FROM all_tables
                        WHERE owner NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS', 'WMSYS', 'XDB', 'ANONYMOUS', 'CTXSYS', 'ORDSYS', 'ORDDATA', 'MDSYS', 'OLAPSYS', 'EXFSYS', 'SYSMAN', 'MDDATA', 'SPATIAL_WFS_ADMIN_USR', 'SPATIAL_CSW_ADMIN_USR', 'SI_INFORMTN_SCHEMA', 'SPATIAL_WFS_ADMIN', 'SPATIAL_CSW_ADMIN', 'XS$NULL', 'LBACSYS', 'DVSYS', 'DVF', 'AUDSYS', 'GSMADMIN_INTERNAL', 'GSMUSER', 'REMOTE_SCHEDULER_AGENT', 'SYSBACKUP', 'SYSDG', 'SYSKM', 'SYSRAC')
                        ORDER BY owner, table_name
                    """)
                    for row in cursor.fetchall():
                        tables.append(f"{row[0]}.{row[1]}")
                
                elif db_type == 'databricks':
                    catalog = config.get('catalog', 'main')
                    schema = config.get('schema', 'default')
                    
                    # Use catalog.schema context
                    cursor.execute(f"USE CATALOG {catalog}")
                    cursor.execute(f"USE SCHEMA {schema}")
                    cursor.execute("SHOW TABLES")
                    
                    for row in cursor.fetchall():
                        # Databricks SHOW TABLES returns database, table_name, is_temporary
                        if len(row) >= 2:
                            db_name = row[0] if row[0] else schema
                            table_name = row[1]
                            # Return fully qualified name
                            tables.append(f"{catalog}.{db_name}.{table_name}")
                
                cursor.close()
                connector.disconnect()
                
                print(f"[DEBUG] Found {len(tables)} tables")
                return {"success": True, "tables": tables, "error": None}
                
            except Exception as e:
                print(f"[ERROR] Failed to fetch tables: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e), "tables": []}
        
        return {"success": False, "error": "Failed to create connector", "tables": []}
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Unexpected error: {str(e)}", "tables": []}


@app.post("/api/db/views")
async def get_views_for_connection(request: dict):
    """Get list of views from a database using provided connection details"""
    try:
        db_type = request.get('type')
        auth_type = request.get('authType', 'windows')
        print(f"[DEBUG] Fetching views for type: {db_type}, auth: {auth_type}")
        print(f"[DEBUG] Request data: {request}")
        
        # For SQL Server with ActiveDirectoryMfa, use create_custom_connection
        if db_type == 'sqlserver' and auth_type == 'ActiveDirectoryMfa':
            try:
                conn = create_custom_connection(request)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TABLE_SCHEMA, TABLE_NAME
                    FROM INFORMATION_SCHEMA.VIEWS
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                """)
                views = [f"{row[0]}.{row[1]}" for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                print(f"[DEBUG] Found {len(views)} views")
                return {"success": True, "views": views}
            except Exception as e:
                print(f"[ERROR] Failed to fetch views: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e), "views": []}
        
        # Import connectors for other database types
        from config.db_config import (
            SQLServerConnector, MySQLConnector, PostgreSQLConnector,
            OracleConnector, DatabricksConnector, AzureSynapseConnector, 
            MicrosoftFabricConnector
        )
        
        connector = None
        
        if db_type == 'sqlserver':
            server_name = request.get('server', '').replace('\\\\', '\\')
            auth_type = request.get('authType', 'windows')
            
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'username': request.get('username'),
                'password': request.get('password')
            }
            
            # Handle Azure AD authentication
            if auth_type == 'ActiveDirectoryMfa' or auth_type == 'ActiveDirectoryInteractive':
                config['authentication'] = 'ActiveDirectoryInteractive'
                config['encrypt'] = True
                config['trust_server_certificate'] = False
                config['trusted_connection'] = 'no'
            elif auth_type == 'ActiveDirectoryPassword':
                config['authentication'] = 'ActiveDirectoryPassword'
                config['encrypt'] = True
                config['trust_server_certificate'] = False
                config['trusted_connection'] = 'no'
            elif auth_type == 'sql':
                config['trusted_connection'] = 'no'
            else:  # windows
                config['trusted_connection'] = request.get('trusted_connection', 'yes')
            
            connector = SQLServerConnector(config)
        
        elif db_type == 'azuresynapse':
            server_name = request.get('server', '').replace('\\\\', '\\')
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'username': request.get('username'),
                'password': request.get('password'),
                'authentication': request.get('authentication'),
                'encrypt': request.get('encrypt', True),
                'trust_server_certificate': request.get('trust_server_certificate', False)
            }
            connector = AzureSynapseConnector(config)
        
        elif db_type == 'fabric':
            server_name = request.get('server', '').replace('\\\\', '\\')
            config = {
                'driver': request.get('driver', 'ODBC Driver 17 for SQL Server'),
                'server': server_name,
                'database': request.get('database'),
                'username': request.get('username'),
                'password': request.get('password'),
                'authentication': request.get('authentication'),
                'client_id': request.get('client_id'),
                'client_secret': request.get('client_secret'),
                'encrypt': request.get('encrypt', True),
                'trust_server_certificate': request.get('trust_server_certificate', True)
            }
            connector = MicrosoftFabricConnector(config)
        
        elif db_type == 'mysql':
            config = {
                'host': request.get('server'),
                'username': request.get('username'),
                'password': request.get('password'),
                'database': request.get('database')
            }
            connector = MySQLConnector(config)
        
        elif db_type == 'postgresql':
            config = {
                'host': request.get('server'),
                'username': request.get('username'),
                'password': request.get('password'),
                'database': request.get('database')
            }
            connector = PostgreSQLConnector(config)
        
        elif db_type == 'oracle':
            config = {
                'host': request.get('server'),
                'port': request.get('port', 1521),
                'username': request.get('username'),
                'password': request.get('password'),
                'service_name': request.get('service_name')
            }
            connector = OracleConnector(config)
        
        elif db_type == 'databricks':
            config = {
                'workspace_url': request.get('workspace_url'),
                'http_path': request.get('http_path'),
                'catalog': request.get('catalog', 'main'),
                'schema': request.get('schema', 'default'),
                'auth_type': request.get('databricks_auth_type', 'token'),
                'access_token': request.get('access_token'),
                'azure_tenant_id': request.get('azure_tenant_id'),
                'azure_client_id': request.get('azure_client_id'),
                'azure_client_secret': request.get('azure_client_secret')
            }
            print(f"[DEBUG] Databricks config: workspace={config['workspace_url']}, catalog={config['catalog']}, schema={config['schema']}")
            connector = DatabricksConnector(config)
        
        else:
            return {"success": False, "error": f"Unsupported database type: {db_type}", "views": []}
        
        # Connect and get views
        if connector:
            try:
                print(f"[DEBUG] Connecting to {db_type} to fetch views...")
                connection = connector.connect()
                
                if not connection:
                    return {"success": False, "error": "Failed to establish connection", "views": []}
                
                cursor = connection.cursor()
                views = []
                
                if db_type in ['sqlserver', 'azuresynapse', 'fabric']:
                    cursor.execute("""
                        SELECT TABLE_SCHEMA, TABLE_NAME
                        FROM INFORMATION_SCHEMA.VIEWS
                        ORDER BY TABLE_SCHEMA, TABLE_NAME
                    """)
                    for row in cursor.fetchall():
                        views.append(f"{row[0]}.{row[1]}")
                
                elif db_type == 'mysql':
                    cursor.execute("""
                        SELECT TABLE_SCHEMA, TABLE_NAME
                        FROM INFORMATION_SCHEMA.VIEWS
                        ORDER BY TABLE_SCHEMA, TABLE_NAME
                    """)
                    for row in cursor.fetchall():
                        views.append(f"{row[0]}.{row[1]}")
                
                elif db_type == 'postgresql':
                    cursor.execute("""
                        SELECT schemaname, viewname
                        FROM pg_views
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                        ORDER BY schemaname, viewname
                    """)
                    for row in cursor.fetchall():
                        views.append(f"{row[0]}.{row[1]}")
                
                elif db_type == 'oracle':
                    cursor.execute("""
                        SELECT owner, view_name
                        FROM all_views
                        WHERE owner NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS', 'WMSYS', 'XDB', 'ANONYMOUS', 'CTXSYS', 'ORDSYS', 'ORDDATA', 'MDSYS', 'OLAPSYS', 'EXFSYS', 'SYSMAN', 'MDDATA', 'SPATIAL_WFS_ADMIN_USR', 'SPATIAL_CSW_ADMIN_USR', 'SI_INFORMTN_SCHEMA', 'SPATIAL_WFS_ADMIN', 'SPATIAL_CSW_ADMIN', 'XS$NULL', 'LBACSYS', 'DVSYS', 'DVF', 'AUDSYS', 'GSMADMIN_INTERNAL', 'GSMUSER', 'REMOTE_SCHEDULER_AGENT', 'SYSBACKUP', 'SYSDG', 'SYSKM', 'SYSRAC')
                        ORDER BY owner, view_name
                    """)
                    for row in cursor.fetchall():
                        views.append(f"{row[0]}.{row[1]}")
                
                elif db_type == 'databricks':
                    catalog = config.get('catalog', 'main')
                    schema = config.get('schema', 'default')
                    
                    # Use catalog.schema context
                    cursor.execute(f"USE CATALOG {catalog}")
                    cursor.execute(f"USE SCHEMA {schema}")
                    cursor.execute("SHOW VIEWS")
                    
                    for row in cursor.fetchall():
                        # Databricks SHOW VIEWS returns database, view_name, is_temporary
                        if len(row) >= 2:
                            db_name = row[0] if row[0] else schema
                            view_name = row[1]
                            # Return fully qualified name
                            views.append(f"{catalog}.{db_name}.{view_name}")
                
                cursor.close()
                connector.disconnect()
                
                print(f"[DEBUG] Found {len(views)} views")
                return {"success": True, "views": views, "error": None}
                
            except Exception as e:
                print(f"[ERROR] Failed to fetch views: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e), "views": []}
        
        return {"success": False, "error": "Failed to create connector", "views": []}
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Unexpected error: {str(e)}", "views": []}


@app.post("/api/db/save")
async def save_database_config(request: dict):
    """Save database configuration to data_sources.json"""
    try:
        config_name = request.get('name', 'custom')
        db_type = request.get('type')
        project_id = request.get('project_id')  # Get project context
        
        # Build configuration based on type
        config = {"type": db_type}
        
        # Add project context if provided
        if project_id:
            config['project_id'] = project_id
        
        if db_type == 'sqlserver':
            config['driver'] = request.get('driver', 'ODBC Driver 17 for SQL Server')
            config['server'] = request.get('server')
            config['database'] = request.get('database')
            config['trusted_connection'] = request.get('trusted_connection', 'yes')
            if request.get('username'):
                config['username'] = request.get('username')
                config['password'] = request.get('password')
        
        elif db_type == 'azuresynapse':
            config['driver'] = request.get('driver', 'ODBC Driver 17 for SQL Server')
            config['server'] = request.get('server')
            config['database'] = request.get('database')
            config['username'] = request.get('username')
            config['password'] = request.get('password')
            config['authentication'] = request.get('authentication')
            config['encrypt'] = request.get('encrypt', True)
            config['trust_server_certificate'] = request.get('trust_server_certificate', False)
        
        elif db_type == 'fabric':
            config['driver'] = request.get('driver', 'ODBC Driver 17 for SQL Server')
            config['server'] = request.get('server')
            config['database'] = request.get('database')
            config['username'] = request.get('username')
            config['password'] = request.get('password')
            config['authentication'] = request.get('authentication')
            if request.get('client_id'):
                config['client_id'] = request.get('client_id')
                config['client_secret'] = request.get('client_secret')
            config['encrypt'] = request.get('encrypt', True)
            config['trust_server_certificate'] = request.get('trust_server_certificate', True)
        
        elif db_type == 'mysql':
            config['host'] = request.get('server')
            config['username'] = request.get('username')
            config['password'] = request.get('password')
            config['database'] = request.get('database')
        
        elif db_type == 'postgresql':
            config['host'] = request.get('server')
            config['username'] = request.get('username')
            config['password'] = request.get('password')
            config['database'] = request.get('database')
        
        elif db_type == 'oracle':
            config['host'] = request.get('server')
            config['port'] = request.get('port', 1521)
            config['username'] = request.get('username')
            config['password'] = request.get('password')
            config['service_name'] = request.get('service_name')
        
        elif db_type == 'mongodb':
            config['uri'] = request.get('uri')
            config['database'] = request.get('database')
        
        elif db_type == 's3':
            config['access_key'] = request.get('access_key')
            config['secret_key'] = request.get('secret_key')
            config['region'] = request.get('region')
        
        elif db_type == 'azureblob':
            config['connection_string'] = request.get('connection_string')
        
        elif db_type == 'gcs':
            config['key_file'] = request.get('key_file')
        
        elif db_type == 'databricks':
            config['server_hostname'] = request.get('server_hostname')
            config['http_path'] = request.get('http_path')
            config['access_token'] = request.get('access_token')
        
        elif db_type == 'powerbi':
            config['client_id'] = request.get('client_id')
            config['client_secret'] = request.get('client_secret')
            config['tenant_id'] = request.get('tenant_id')
        
        else:
            return {"success": False, "error": f"Unsupported database type: {db_type}"}
        
        # Load existing configs
        config_path = os.path.join(PROJECT_PATH, 'config', 'data_sources.json')
        
        with open(config_path, 'r') as f:
            configs = json.load(f)
        
        # Add or update config
        configs[config_name] = config
        
        # Save configs
        with open(config_path, 'w') as f:
            json.dump(configs, f, indent=4)
        
        return {"success": True, "message": f"Configuration '{config_name}' saved successfully!", "name": config_name}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/db/configs")
def get_database_configs(project_id: Optional[str] = None):
    """Get list of saved database configurations, optionally filtered by project"""
    try:
        config_path = os.path.join(PROJECT_PATH, 'config', 'data_sources.json')
        
        with open(config_path, 'r') as f:
            configs = json.load(f)
        
        # Return config names and types (without sensitive data)
        result = {}
        for name, config in configs.items():
            # Filter by project_id if specified
            if project_id and config.get('project_id') != project_id:
                continue
            
            result[name] = {
                'type': config.get('type'),
                'server': config.get('server', config.get('host', config.get('uri', 'N/A'))),
                'database': config.get('database', 'N/A'),
                'project_id': config.get('project_id')
            }
        
        return {"success": True, "configs": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/tables")
def get_tables(database: str = "default"):
    """Get list of available tables from the specified database"""
    try:
        from config.db_config import create_connection
        conn = create_connection(database)
        if not conn:
            return {"tables": [], "error": f"Database connection failed for {database}. Please check db_config.py"}

        cursor = conn.cursor()

        # Get database type from config
        from config.db_config import load_data_source_config
        config = load_data_source_config(database)
        db_type = config.get('type', 'sqlserver')

        if db_type in ['sqlserver', 'azuresynapse', 'fabric']:
            # SQL Server, Azure Synapse, and Microsoft Fabric
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "schema_name": row[0],
                    "table_name": row[1],
                    "full_name": f"{row[0]}.{row[1]}"
                })

        elif db_type == 'mysql':
            # MySQL
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "schema_name": row[0],
                    "table_name": row[1],
                    "full_name": f"{row[0]}.{row[1]}"
                })

        elif db_type == 'postgresql':
            # PostgreSQL
            cursor.execute("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename
            """)
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "schema_name": row[0],
                    "table_name": row[1],
                    "full_name": f"{row[0]}.{row[1]}"
                })

        elif db_type == 'oracle':
            # Oracle
            cursor.execute("""
                SELECT owner, table_name
                FROM all_tables
                WHERE owner NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS', 'WMSYS', 'XDB', 'ANONYMOUS', 'CTXSYS', 'ORDSYS', 'ORDDATA', 'MDSYS', 'OLAPSYS', 'EXFSYS', 'SYSMAN', 'MDDATA', 'SPATIAL_WFS_ADMIN_USR', 'SPATIAL_CSW_ADMIN_USR', 'SI_INFORMTN_SCHEMA', 'SPATIAL_WFS_ADMIN', 'SPATIAL_CSW_ADMIN', 'XS$NULL', 'LBACSYS', 'DVSYS', 'DVF', 'AUDSYS', 'GSMADMIN_INTERNAL', 'GSMUSER', 'REMOTE_SCHEDULER_AGENT', 'SYSBACKUP', 'SYSDG', 'SYSKM', 'SYSRAC')
                ORDER BY owner, table_name
            """)
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "schema_name": row[0],
                    "table_name": row[1],
                    "full_name": f"{row[0]}.{row[1]}"
                })

        elif db_type == 'databricks':
            # Databricks (uses Spark SQL)
            cursor.execute("""
                SHOW TABLES
            """)
            tables = []
            for row in cursor.fetchall():
                # Databricks SHOW TABLES returns database, table_name, is_temporary
                if len(row) >= 2:
                    db_name = row[0] if row[0] else 'default'
                    table_name = row[1]
                    tables.append({
                        "schema_name": db_name,
                        "table_name": table_name,
                        "full_name": f"{db_name}.{table_name}"
                    })

        else:
            return {"tables": [], "error": f"Unsupported database type: {db_type}"}

        conn.close()
        return {"tables": tables, "error": None}

    except Exception as e:
        return {"tables": [], "error": str(e)}


@app.post("/api/tables/custom")
async def get_tables_with_custom_config(config: dict):
    """Get list of available tables using custom database configuration"""
    try:
        db_type = config.get('type', 'sqlserver')
        
        print(f"\n=== Custom DB Connection Request ===")
        print(f"DB Type: {db_type}")
        print(f"Config: {config}")
        print(f"====================================\n")
        
        # Handle Databricks separately (different field requirements)
        if db_type == 'databricks':
            # Databricks Unity Catalog connection
            from config.db_config import DatabricksConnector
            
            databricks_config = {
                'workspace_url': config.get('workspace_url'),
                'http_path': config.get('http_path'),
                'catalog': config.get('catalog'),
                'schema': config.get('schema'),
                'auth_type': config.get('databricks_auth_type', 'token'),
                'access_token': config.get('access_token'),
                'azure_tenant_id': config.get('azure_tenant_id'),
                'azure_client_id': config.get('azure_client_id'),
                'azure_client_secret': config.get('azure_client_secret')
            }
            
            connector = DatabricksConnector(databricks_config)
            conn = connector.connect()
            
            if not conn:
                return {"tables": [], "error": "Failed to connect to Databricks"}
            
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            
            tables = []
            for row in cursor.fetchall():
                # Databricks SHOW TABLES returns database, table_name, is_temporary
                if len(row) >= 2:
                    db_name = row[0] if row[0] else 'default'
                    table_name = row[1]
                    tables.append({
                        "schema_name": db_name,
                        "table_name": table_name,
                        "full_name": f"{db_name}.{table_name}"
                    })
            
            connector.disconnect()
            
            print(f"Successfully loaded {len(tables)} tables from Databricks")
            return {"tables": tables, "error": None}
        
        # For SQL-based databases, get standard fields
        server = config.get('server', '').strip()
        database = config.get('database', '').strip()
        port = config.get('port', '').strip()
        auth_type = config.get('authType', 'windows')
        username = config.get('username', '').strip()
        password = config.get('password', '').strip()
        
        print(f"Server (raw): {repr(server)}")
        print(f"Database: {database}")
        print(f"Auth Type: {auth_type}")
        
        # Validate required fields for SQL databases
        if not server:
            return {"tables": [], "error": "Server/Host is required"}
        if not database:
            return {"tables": [], "error": "Database name is required"}
        
        conn = None
        
        if db_type in ['default', 'sqlserver', 'azuresynapse', 'fabric']:
            try:
                import pyodbc
            except ImportError:
                return {"tables": [], "error": "pyodbc driver not installed"}
            
            # Use create_custom_connection for ALL connection types to ensure consistency
            try:
                print(f"[DEBUG] Using create_custom_connection for tables endpoint")
                conn = create_custom_connection(config)
            except Exception as e:
                print(f"[ERROR] Connection failed: {e}")
                return {"tables": [], "error": f"Connection failed: {str(e)}"}
            
            # Old logic below (keeping for reference but not used)
            if False:
                # SQL Server, Azure Synapse, or Fabric connection - build connection string carefully
                # Check if this is Azure SQL Database
                is_azure_sql = '.database.windows.net' in server.lower()
                
                # For Azure AD MFA, MUST use Driver 18 (Driver 17 doesn't fully support it)
                if auth_type == 'ActiveDirectoryMfa':
                    driver = 'ODBC Driver 18 for SQL Server'
                elif is_azure_sql:
                    driver = 'ODBC Driver 18 for SQL Server'
                else:
                    driver = 'ODBC Driver 17 for SQL Server'
                
                conn_params = [
                    f"DRIVER={{{driver}}}",
                    f"SERVER={server}"
                ]
                
                # Only add DATABASE if it's provided
                if database:
                    conn_params.append(f"DATABASE={database}")
                
                # Add port if specified (format: SERVER\INSTANCE,port)
                if port:
                    # Replace the server param to include port
                    conn_params[1] = f"SERVER={server},{port}"
                
                # Authentication
                if auth_type == 'windows':
                    conn_params.append("Trusted_Connection=yes")
                else:
                    if not username:
                        return {"tables": [], "error": "Username is required for SQL Server authentication"}
                    conn_params.append(f"UID={username}")
                    conn_params.append(f"PWD={password}")
                
                # Azure-specific parameters
                if db_type in ['azuresynapse', 'fabric'] or is_azure_sql:
                    conn_params.append("Encrypt=yes")
                    if db_type == 'fabric':
                        conn_params.append("TrustServerCertificate=yes")
                    else:
                        conn_params.append("TrustServerCertificate=no")
                
                # Add timeout and other helpful parameters
                conn_params.append("Connection Timeout=30")
                
                conn_str = ";".join(conn_params) + ";"
                
                print(f"Attempting {db_type.upper()} connection with: SERVER={server}, DATABASE={database}, AUTH={auth_type}")
                print(f"Connection string: {conn_str.replace(password, '***') if password else conn_str}")
                
                try:
                    conn = pyodbc.connect(conn_str)
                except pyodbc.Error as e:
                    # If Driver 18 fails, try Driver 17
                    if is_azure_sql and 'Driver' in str(e):
                        print(f"[DEBUG] Driver 18 failed, trying Driver 17...")
                        conn_str = conn_str.replace('ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server')
                        conn = pyodbc.connect(conn_str)
                    else:
                        raise
            cursor = conn.cursor()
            
            # First, let's check what database we're connected to
            cursor.execute("SELECT DB_NAME()")
            current_db = cursor.fetchone()[0]
            print(f"Connected to database: {current_db}")
            
            # Now fetch all tables including system tables to see what's there
            cursor.execute("""
                SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            all_rows = cursor.fetchall()
            print(f"Total tables/views found: {len(all_rows)}")
            for row in all_rows:
                print(f"  - {row[0]}.{row[1]}.{row[2]} (Type: {row[3]})")
            
            # Now get only BASE TABLEs
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            
            # Fetch tables
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "schema_name": row[0],
                    "table_name": row[1],
                    "full_name": f"{row[0]}.{row[1]}"
                })
            
            if conn:
                conn.close()
            
            print(f"Successfully loaded {len(tables)} BASE TABLE(s) from database: {database}")
            return {"tables": tables, "error": None, "database": database}
            
        elif db_type in ['mysql_example', 'mysql']:
            try:
                import pymysql
            except ImportError:
                return {"tables": [], "error": "pymysql driver not installed"}
            
            # MySQL connection
            conn = pymysql.connect(
                host=server,
                port=int(port) if port else 3306,
                user=username,
                password=password,
                database=database,
                connect_timeout=30
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            
            # Fetch tables for MySQL
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "schema_name": row[0],
                    "table_name": row[1],
                    "full_name": f"{row[0]}.{row[1]}"
                })
            
            if conn:
                conn.close()
            
            print(f"Successfully loaded {len(tables)} tables from MySQL database: {database}")
            return {"tables": tables, "error": None, "database": database}
            
        elif db_type in ['postgres_example', 'postgresql']:
            try:
                import psycopg2
            except ImportError:
                return {"tables": [], "error": "psycopg2 driver not installed"}
            
            # PostgreSQL connection
            conn = psycopg2.connect(
                host=server,
                port=int(port) if port else 5432,
                user=username,
                password=password,
                database=database,
                connect_timeout=30
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename
            """)
            
            # Fetch tables for PostgreSQL
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "schema_name": row[0],
                    "table_name": row[1],
                    "full_name": f"{row[0]}.{row[1]}"
                })
            
            if conn:
                conn.close()
            
            print(f"Successfully loaded {len(tables)} tables from PostgreSQL database: {database}")
            return {"tables": tables, "error": None, "database": database}
            
        else:
            return {"tables": [], "error": f"Unsupported database type: {db_type}"}
        
    except Exception as e:
        error_msg = str(e)
        # Provide more helpful error messages
        if "cannot connect" in error_msg.lower() or "08001" in error_msg:
            error_msg = f"Cannot connect to server '{server}'. Please verify: 1) Server name is correct (e.g., 'DESKTOP-NAME\\SQLEXPRESS'), 2) SQL Server is running, 3) TCP/IP is enabled in SQL Server Configuration Manager"
        elif "login failed" in error_msg.lower():
            error_msg = f"Login failed. Please check your username and password"
        elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
            error_msg = f"Database '{database}' does not exist on server '{server}'"
        
        return {"tables": [], "error": error_msg}


@app.get("/api/validations")
def get_available_validations():
    """Get list of available validation types"""
    validations = [
        {
            "id": "structure_validation",
            "name": "Structure Validation",
            "description": "Compare table structures, column names, data types, and primary keys",
            "default": True
        },
        {
            "id": "count_validation",
            "name": "Record Count Validation",
            "description": "Compare row counts between source and target tables",
            "default": True
        },
        {
            "id": "null_check",
            "name": "Null Check",
            "description": "Check for NULL values and constraint violations",
            "default": True
        },
        {
            "id": "duplicate_check",
            "name": "Duplicate Check",
            "description": "Find duplicate records based on primary key or composite keys",
            "default": True
        },
        {
            "id": "row_data_validation",
            "name": "Row-wise Data Validation",
            "description": "Compare actual data row by row between source and target",
            "default": True
        }
    ]
    return {"validations": validations}


# Power BI Endpoints
@app.get("/api/powerbi/datasets")
def get_powerbi_datasets():
    """Get Power BI datasets"""
    try:
        from config.db_config import create_connection
        powerbi = create_connection('powerbi_example')
        datasets = powerbi.get_datasets()
        if datasets:
            return {"datasets": datasets.get('value', [])}
        else:
            return {"error": "Failed to retrieve datasets from Power BI", "datasets": []}
    except Exception as e:
        error_msg = str(e)
        if "access_token" in error_msg.lower() or "authentication" in error_msg.lower() or "401" in error_msg:
            error_msg = "Power BI authentication failed. Please check your credentials in the .env file."
        return {"error": error_msg, "datasets": []}
#
#
# @app.get("/api/powerbi/reports")
# def get_powerbi_reports():
#     """Get Power BI reports"""
#     try:
#         from config.db_config import create_connection
#         powerbi = create_connection('powerbi_example')
#         reports = powerbi.get_reports()
#         if reports:
#             return {"reports": reports.get('value', [])}
#         else:
#             return {"error": "Failed to retrieve reports from Power BI", "reports": []}
#     except Exception as e:
#         error_msg = str(e)
#         if "access_token" in error_msg.lower() or "authentication" in error_msg.lower():
#             error_msg = "Power BI authentication failed. Please check your credentials in the .env file."
#         return {"error": error_msg, "reports": []}
#
#
# @app.post("/api/powerbi/execute-dax")
# def execute_dax_query(request: dict):
#     """Execute DAX query"""
#     try:
#         from config.db_config import create_connection
#         powerbi = create_connection('powerbi_example')
#         dataset_id = request.get('dataset_id')
#         dax_query = request.get('dax_query')
#
#         if not dataset_id or not dax_query:
#             return {"error": "Dataset ID and DAX query are required"}
#
#         result = powerbi.execute_dax_query(dataset_id, dax_query)
#         if result:
#             return {"results": result}
#         else:
#             return {"error": "Failed to execute DAX query"}
#     except Exception as e:
#         error_msg = str(e)
#         if "access_token" in error_msg.lower() or "authentication" in error_msg.lower():
#             error_msg = "Power BI authentication failed. Please check your credentials in the .env file."
#         return {"error": error_msg}
#
#
# @app.post("/api/powerbi/validate-measures")
# def validate_measures(request: dict):
#     """Validate Power BI measures"""
#     try:
#         from config.db_config import create_connection
#         from src.advanced_validate import validate_powerbi_measures
#
#         powerbi = create_connection('powerbi_example')
#         dataset_id = request.get('dataset_id')
#
#         if not dataset_id:
#             return {"error": "Dataset ID is required", "valid": False}
#
#         # Get measures from dataset
#         measures_data = powerbi.get_dataset_measures(dataset_id)
#         measures = [m['name'] for m in measures_data.get('value', [])] if measures_data else []
#
#         valid, missing = validate_powerbi_measures(powerbi, dataset_id, measures)
#         return {
#             "valid": valid,
#             "details": f"Missing measures: {missing}" if not valid else "All measures validated successfully"
#         }
#     except Exception as e:
#         error_msg = str(e)
#         if "access_token" in error_msg.lower() or "authentication" in error_msg.lower():
#             error_msg = "Power BI authentication failed. Please check your credentials in the .env file."
#        return {"error": error_msg, "valid": False}


@app.post("/api/execute-query")
def execute_query(request: dict):
    """Execute a SQL query and return results"""
    try:
        query = request.get('query', '').strip()
        db_config = request.get('dbConfig', {})
        
        if not query:
            return {"success": False, "error": "Query is required"}
        
        # Extract database configuration
        db_type = db_config.get('type', 'default')
        server = db_config.get('server', '').strip()
        database = db_config.get('database', '').strip()
        port = db_config.get('port', '').strip()
        auth_type = db_config.get('authType', 'windows')
        username = db_config.get('username', '').strip()
        password = db_config.get('password', '').strip()
        
        print(f"\n=== Execute Query Request ===")
        print(f"DB Type: {db_type}")
        print(f"Server: {server}")
        print(f"Database: {database}")
        print(f"Auth Type: {auth_type}")
        print(f"Query (first 100 chars): {query[:100]}...")
        print(f"=============================\n")
        
        # Validate required fields (skip for databricks which uses different fields)
        if db_type not in ['databricks', 'databricks_example']:
            if not server:
                return {"success": False, "error": "Server/Host is required"}
            if not database:
                return {"success": False, "error": "Database name is required"}
        
        # Create connection based on database type
        conn = None
        
        if db_type in ['default', 'sqlserver', 'azuresynapse', 'fabric']:
            # Use create_custom_connection for SQL Server to support all auth types
            try:
                conn = create_custom_connection(db_config)
            except Exception as e:
                return {"success": False, "error": f"Connection failed: {str(e)}"}
        
        elif db_type in ['mysql_example', 'mysql']:
            try:
                import pymysql
            except ImportError:
                return {"success": False, "error": "pymysql driver not installed"}
            
            conn = pymysql.connect(
                host=server,
                port=int(port) if port else 3306,
                user=username,
                password=password,
                database=database,
                connect_timeout=30
            )
        
        elif db_type in ['postgres_example', 'postgresql']:
            try:
                import psycopg2
            except ImportError:
                return {"success": False, "error": "psycopg2 driver not installed"}
            
            conn = psycopg2.connect(
                host=server,
                port=int(port) if port else 5432,
                user=username,
                password=password,
                database=database,
                connect_timeout=30
            )
        
        elif db_type in ['databricks', 'databricks_example']:
            # Databricks Unity Catalog connection
            try:
                from config.db_config import DatabricksConnector
                
                # Get Databricks-specific config
                workspace_url = db_config.get('workspace_url', '').strip()
                http_path = db_config.get('http_path', '').strip()
                catalog = db_config.get('catalog', '').strip()
                schema = db_config.get('schema', '').strip()
                databricks_auth_type = db_config.get('databricks_auth_type', 'token')
                access_token = db_config.get('access_token', '').strip()
                azure_tenant_id = db_config.get('azure_tenant_id', '').strip()
                azure_client_id = db_config.get('azure_client_id', '').strip()
                azure_client_secret = db_config.get('azure_client_secret', '').strip()
                
                # Validate Databricks-specific fields
                if not workspace_url:
                    return {"success": False, "error": "Workspace URL is required for Databricks"}
                if not http_path:
                    return {"success": False, "error": "HTTP Path is required for Databricks"}
                
                databricks_config = {
                    'workspace_url': workspace_url,
                    'http_path': http_path,
                    'catalog': catalog,
                    'schema': schema,
                    'auth_type': databricks_auth_type,
                    'access_token': access_token,
                    'azure_tenant_id': azure_tenant_id,
                    'azure_client_id': azure_client_id,
                    'azure_client_secret': azure_client_secret
                }
                
                print(f"[DEBUG] Databricks query config: workspace={workspace_url}, auth={databricks_auth_type}")
                
                connector = DatabricksConnector(databricks_config)
                conn = connector.connect()
                
                if not conn:
                    return {"success": False, "error": "Failed to connect to Databricks"}
                    
            except ImportError:
                return {"success": False, "error": "databricks-sql-connector not installed. Run: pip install databricks-sql-connector"}
            except Exception as e:
                return {"success": False, "error": f"Databricks connection failed: {str(e)}"}
        
        else:
            return {"success": False, "error": f"Unsupported database type: {db_type}"}
        
        if not conn:
            return {"success": False, "error": f"Failed to connect to database: {database}"}
        
        cursor = conn.cursor()
        
        # Check if query is a SELECT statement or DML (UPDATE, INSERT, DELETE)
        query_type = query.split()[0].upper() if query else ""
        is_select = query_type == "SELECT"
        is_dml = query_type in ["UPDATE", "INSERT", "DELETE"]
        
        cursor.execute(query)
        
        if is_select:
            # Fetch results for SELECT queries
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Convert rows to list of dicts for JSON serialization
            results = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    val = row[i]
                    # Handle non-JSON serializable types
                    if hasattr(val, 'isoformat'):
                        val = val.isoformat()
                    elif isinstance(val, bytes):
                        val = val.decode('utf-8', errors='replace')
                    row_dict[col] = val
                results.append(row_dict)
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "query_type": "SELECT",
                "columns": columns,
                "rows": results,
                "row_count": len(results),
                "query": query
            }
        elif is_dml:
            # For UPDATE, INSERT, DELETE - commit and return affected rows
            affected_rows = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "query_type": query_type,
                "affected_rows": affected_rows,
                "message": f"{query_type} executed successfully. {affected_rows} row(s) affected.",
                "query": query
            }
        else:
            # For other statements (CREATE, DROP, etc.)
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "query_type": query_type,
                "message": f"{query_type} statement executed successfully.",
                "query": query
            }
        
    except Exception as e:
        try:
            if conn:
                conn.rollback()
                conn.close()
        except:
            pass
        return {"success": False, "error": str(e), "query": request.get('query', '')}


def create_custom_connection(db_config: dict):
    """Create a database connection from custom configuration"""
    import pyodbc
    
    try:
        db_type = db_config.get('type', 'sqlserver')
        server = db_config.get('server', '').replace('\\\\', '\\').strip()
        database = db_config.get('database', '').strip()
        port = db_config.get('port', '1433')
        auth_type = db_config.get('authType', 'windows')
        username = db_config.get('username', '').strip()
        password = db_config.get('password', '').strip()
        
        print(f"[DEBUG] Creating custom connection:")
        print(f"  type={db_type}")
        print(f"  server={server}")
        print(f"  database={database}")
        print(f"  auth={auth_type}")
        print(f"  username={username}")
        
        if db_type == 'sqlserver' or db_type == 'default':
            # Check if this is Azure SQL Database (server ends with .database.windows.net)
            is_azure_sql = '.database.windows.net' in server.lower()
            
            # For Azure AD MFA, MUST use Driver 18 (Driver 17 doesn't fully support it)
            if auth_type == 'ActiveDirectoryMfa':
                driver = 'ODBC Driver 18 for SQL Server'
            elif is_azure_sql:
                driver = 'ODBC Driver 18 for SQL Server'
            else:
                driver = 'ODBC Driver 17 for SQL Server'
            
            conn_str_parts = [
                f'DRIVER={{{driver}}}',
                f'SERVER={server}',
                f'DATABASE={database}'
            ]
            
            if auth_type == 'windows' or auth_type == 'yes':
                conn_str_parts.append('Trusted_Connection=yes')
            elif auth_type == 'ActiveDirectoryMfa':
                # Azure AD Universal with MFA - requires ODBC Driver 18
                # Check if Driver 18 is available
                test_drivers = pyodbc.drivers()
                has_driver_18 = any('ODBC Driver 18' in d for d in test_drivers)
                
                print(f"[DEBUG] Available ODBC drivers: {test_drivers}")
                print(f"[DEBUG] Driver 18 detected: {has_driver_18}")
                
                if not has_driver_18:
                    raise Exception(
                        "Azure AD MFA authentication requires ODBC Driver 18 for SQL Server.\n\n"
                        f"Available drivers on your system: {', '.join(test_drivers)}\n\n"
                        "Please install ODBC Driver 18 from: https://go.microsoft.com/fwlink/?linkid=2268169\n\n"
                        "Alternatively, you can:\n"
                        "1. Use 'SQL Server Authentication' with your Azure SQL username and password\n"
                        "2. Use 'Windows Authentication' if connecting to on-premises SQL Server"
                    )
                    
                conn_str_parts.append('Authentication=ActiveDirectoryInteractive')
                if username:
                    conn_str_parts.append(f'UID={username}')
                conn_str_parts.append('Encrypt=yes')
                conn_str_parts.append('TrustServerCertificate=no')
            else:
                # SQL Server authentication or other Azure AD methods
                conn_str_parts.append(f'UID={username}')
                conn_str_parts.append(f'PWD={password}')
                # For Azure SQL, add encryption settings
                if is_azure_sql:
                    conn_str_parts.append('Encrypt=yes')
                    conn_str_parts.append('TrustServerCertificate=no')
            
            conn_str_parts.append('Connection Timeout=30')
            conn_str = ';'.join(conn_str_parts)
            
            print(f"[DEBUG] Connection string: {conn_str.replace(password, '***') if password else conn_str}")
            
            try:
                conn = pyodbc.connect(conn_str)
                print(f"[DEBUG] Connection successful!")
                return conn
            except pyodbc.Error as e:
                error_msg = str(e)
                print(f"[ERROR] Connection failed: {error_msg}")
                
                # Check if this is actually a driver issue or an authentication issue
                is_driver_missing = 'Data source name not found' in error_msg or 'Driver not found' in error_msg
                is_auth_issue = 'Login failed' in error_msg or '18456' in error_msg or 'token-identified principal' in error_msg
                
                # If Driver 18 fails (not installed), try Driver 17 for non-MFA auth
                if is_driver_missing and 'ODBC Driver 18' in conn_str and auth_type != 'ActiveDirectoryMfa':
                    print(f"[DEBUG] Driver 18 not found, trying Driver 17...")
                    conn_str = conn_str.replace('ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server')
                    print(f"[DEBUG] Retry connection string: {conn_str.replace(password, '***') if password else conn_str}")
                    conn = pyodbc.connect(conn_str)
                    print(f"[DEBUG] Connection successful with Driver 17!")
                    return conn
                elif auth_type == 'ActiveDirectoryMfa' and is_driver_missing:
                    # MFA requires Driver 18 and it's actually missing
                    raise Exception(f"Azure AD MFA authentication requires ODBC Driver 18 for SQL Server. Please install it from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
                elif auth_type == 'ActiveDirectoryMfa' and is_auth_issue:
                    # This is an authentication/permission issue, not a driver issue
                    raise Exception(f"Azure AD authentication failed. Please check:\n1. Your Azure AD account has access to the database\n2. The database name is correct\n3. You have completed the MFA prompt\n\nOriginal error: {error_msg}")
                else:
                    raise
                    
        elif db_type == 'databricks' or db_type == 'databricks_example':
            # Databricks Unity Catalog connection
            from config.db_config import DatabricksConnector
            
            databricks_config = {
                'workspace_url': db_config.get('workspace_url'),
                'http_path': db_config.get('http_path'),
                'catalog': db_config.get('catalog'),
                'schema': db_config.get('schema'),
                'auth_type': db_config.get('databricks_auth_type', 'token'),
                'access_token': db_config.get('access_token'),
                'azure_tenant_id': db_config.get('azure_tenant_id'),
                'azure_client_id': db_config.get('azure_client_id'),
                'azure_client_secret': db_config.get('azure_client_secret')
            }
            
            print(f"[DEBUG] Creating Databricks connection with config: workspace={databricks_config['workspace_url']}")
            connector = DatabricksConnector(databricks_config)
            conn = connector.connect()
            
            if not conn:
                raise Exception("Failed to connect to Databricks")
            
            print(f"[DEBUG] Databricks connection successful!")
            return conn
            
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
            
    except Exception as e:
        print(f"[ERROR] Failed to create custom connection: {e}")
        raise


@app.post("/api/run")
def run_validation(request: ValidationRequest):
    """Execute ETL validation pipeline and return detailed results
    
    PERFORMANCE NOTES:
    - For large datasets (>100K rows), use sample_size parameter to limit validation scope
    - Row-level validation is most resource-intensive; consider using count/structure only for large tables
    - Queries are optimized with NOLOCK hints (SQL Server) to prevent blocking
    - Column lists are used instead of SELECT * to reduce data transfer
    """
    start_time = time.time()
    execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    sample_size = request.sample_size if hasattr(request, 'sample_size') else 0
    
    # PERFORMANCE: Log performance metrics
    perf_metrics = {
        "connection_time": 0,
        "query_execution_time": 0,
        "validation_time": 0,
        "total_time": 0
    }
    
    results = {
        "execution_id": execution_id,
        "source_table": request.source_table,
        "target_table": request.target_table,
        "timestamp": datetime.now().isoformat(),
        "sample_size": sample_size,
        "validations": {},
        "logs": {},
        "status": "RUNNING",
        "performance_metrics": perf_metrics,
        "project_id": request.project_id  # Add project context
    }
    
    try:
        # Use custom database configurations if provided, otherwise use default
        conn_start = time.time()
        source_conn = None
        target_conn = None
        
        print(f"[PERFORMANCE] Starting validation - Execution ID: {execution_id}")
        print(f"[PERFORMANCE] Sample size: {sample_size if sample_size > 0 else 'ALL RECORDS'}")
        print(f"[DEBUG] Validation request received:")
        print(f"  source_db_config: {request.source_db_config}")
        print(f"  target_db_config: {request.target_db_config}")
        
        if request.source_db_config:
            print(f"[DEBUG] Creating source connection with custom config...")
            source_conn = create_custom_connection(request.source_db_config)
            source_conn.autocommit = True  # Enable autocommit for DDL operations
            print(f"[DEBUG] Source connection created successfully")
        else:
            print(f"[WARNING] No source_db_config provided, will use default connection")
            
        if request.target_db_config:
            print(f"[DEBUG] Creating target connection with custom config...")
            target_conn = create_custom_connection(request.target_db_config)
            target_conn.autocommit = True  # Enable autocommit for DDL operations
            print(f"[DEBUG] Target connection created successfully")
        else:
            print(f"[WARNING] No target_db_config provided, will use default connection")
        
        # If no custom configs, use default connection
        if not source_conn or not target_conn:
            print(f"[DEBUG] Using default connection for missing configs")
            default_conn = get_db_connection()
            if not default_conn:
                results["status"] = "FAILED"
                results["error"] = "Database connection failed"
                return results
            source_conn = source_conn or default_conn
            target_conn = target_conn or default_conn
        
        perf_metrics["connection_time"] = round(time.time() - conn_start, 2)
        print(f"[PERFORMANCE] Connections established in {perf_metrics['connection_time']}s")
        
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Import validation functions
        from src.validate import (
            structure_validation,
            count_validation,
            null_check,
            duplicate_check,
            row_data_validation,
        )
        
        source_table = request.source_table
        target_table = request.target_table
        source_query = request.source_query
        target_query = request.target_query
        source_database = request.source_database
        target_database = request.target_database
        validations = request.validations
        
        # Store original source/target names for display
        # Extract table names from queries if available
        import re
        
        def extract_table_names(query):
            """Extract table names from SQL query"""
            if not query:
                return []
            
            # Remove comments and normalize query
            query = re.sub(r'--.*?$', '', query, flags=re.MULTILINE)  # Remove line comments
            query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)  # Remove block comments
            query = ' '.join(query.split())  # Normalize whitespace
            
            # Pattern to match FROM and various JOIN types with optional schema/database qualifiers
            # Handles: FROM table, FROM schema.table, FROM [schema].[table], FROM database.schema.table
            pattern = r'\b(?:FROM|JOIN|INTO)\s+(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?\.)?(?:\[?(\w+)\]?)(?:\s+(?:AS\s+)?\w+)?'
            matches = re.findall(pattern, query, re.IGNORECASE)
            
            table_names = []
            for match in matches:
                # Get non-empty parts and construct table name
                parts = [part for part in match if part]
                if parts:
                    # If multiple parts (schema.table or db.schema.table), join them
                    if len(parts) >= 2:
                        table_names.append('.'.join(parts[-2:]))  # Use last two parts (schema.table)
                    else:
                        table_names.append(parts[-1])  # Just table name
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tables = []
            for table in table_names:
                if table.lower() not in seen:
                    seen.add(table.lower())
                    unique_tables.append(table)
            
            return unique_tables
        
        if source_table:
            original_source_name = source_table
        elif source_query:
            tables = extract_table_names(source_query)
            original_source_name = ", ".join(tables) if tables else "Source Query"
        else:
            original_source_name = "Source"
            
        if target_table:
            original_target_name = target_table
        elif target_query:
            tables = extract_table_names(target_query)
            original_target_name = ", ".join(tables) if tables else "Target Query"
        else:
            original_target_name = "Target"
        
        # Update results with extracted table names for display
        results["source_table"] = original_source_name
        results["target_table"] = original_target_name

        # Detect database types
        source_db_type = request.source_db_config.get('type', 'sql_server') if request.source_db_config else 'sql_server'
        target_db_type = request.target_db_config.get('type', 'sql_server') if request.target_db_config else 'sql_server'
        
        is_source_databricks = source_db_type in ['databricks', 'databricks_example']
        is_target_databricks = target_db_type in ['databricks', 'databricks_example']
        
        # Create temp tables with database-specific syntax
        # SQL Server uses ##TempTable (global temp table)
        # Databricks uses regular table names for temp views
        if is_source_databricks:
            temp_source_table = f"temp_source_{execution_id}"
        else:
            temp_source_table = f"##TempSource_{execution_id}"
            
        if is_target_databricks:
            temp_target_table = f"temp_target_{execution_id}"
        else:
            temp_target_table = f"##TempTarget_{execution_id}"
        
        # Apply sampling if sample_size is specified
        sample_size = request.sample_size if hasattr(request, 'sample_size') else 0
        
        # Strip trailing semicolons from queries before wrapping (prevents syntax errors)
        clean_source_query = source_query.rstrip().rstrip(';')
        clean_target_query = target_query.rstrip().rstrip(';')
        
        # Helper function to check if query has ORDER BY clause
        def has_order_by(query):
            # Remove line comments and block comments
            query_clean = re.sub(r'--.*?$', '', query, flags=re.MULTILINE)
            query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
            # Check for ORDER BY (must not be inside a subquery)
            # Simple heuristic: if ORDER BY appears after the last closing parenthesis
            last_paren = query_clean.rfind(')')
            search_from = last_paren if last_paren != -1 else 0
            return bool(re.search(r'\bORDER\s+BY\b', query_clean[search_from:], re.IGNORECASE))
        
        # Add ORDER BY for deterministic results if not already present
        # This ensures sampling returns the same subset from source and target
        # Determine ORDER BY clause for deterministic ordering (but don't add to query yet for SQL Server)
        source_order_by = ""
        target_order_by = ""
        
        if not has_order_by(clean_source_query):
            # Get column count by executing query with LIMIT 0
            try:
                if is_source_databricks:
                    source_cursor.execute(f"SELECT * FROM ({clean_source_query}) AS temp_col_check LIMIT 0")
                else:
                    source_cursor.execute(f"SELECT TOP 0 * FROM ({clean_source_query}) AS temp_col_check")
                col_count = len(source_cursor.description)
                # Create ORDER BY using column positions (works for both SQL Server and Databricks)
                source_order_by = "ORDER BY " + ", ".join(str(i+1) for i in range(min(col_count, 10)))  # Limit to first 10 cols for performance
                
                # For Databricks, we can add ORDER BY to the subquery directly
                if is_source_databricks:
                    clean_source_query = f"SELECT * FROM ({clean_source_query}) AS OrderedSource {source_order_by}"
                    print(f"[DEBUG] Auto-added ORDER BY to source query for deterministic sampling")
                else:
                    print(f"[DEBUG] Will apply ORDER BY when creating temp table (SQL Server compatibility)")
            except Exception as e:
                print(f"[WARNING] Could not determine ORDER BY for source query: {e}")
        
        if not has_order_by(clean_target_query):
            try:
                if is_target_databricks:
                    target_cursor.execute(f"SELECT * FROM ({clean_target_query}) AS temp_col_check LIMIT 0")
                else:
                    target_cursor.execute(f"SELECT TOP 0 * FROM ({clean_target_query}) AS temp_col_check")
                col_count = len(target_cursor.description)
                target_order_by = "ORDER BY " + ", ".join(str(i+1) for i in range(min(col_count, 10)))
                
                # For Databricks, we can add ORDER BY to the subquery directly
                if is_target_databricks:
                    clean_target_query = f"SELECT * FROM ({clean_target_query}) AS OrderedTarget {target_order_by}"
                    print(f"[DEBUG] Auto-added ORDER BY to target query for deterministic sampling")
                else:
                    print(f"[DEBUG] Will apply ORDER BY when creating temp table (SQL Server compatibility)")
            except Exception as e:
                print(f"[WARNING] Could not determine ORDER BY for target query: {e}")
        
        # SMART SAMPLING STRATEGY:
        # - Temp tables contain FULL dataset (no sampling applied here)
        # - Structure/Count/Null/Duplicate validations run on FULL data
        # - Only Row-wise validation uses sampling (applied in validate.py)
        print(f"[DEBUG] Creating temp tables with full dataset for comprehensive validation")
        if sample_size > 0:
            print(f"[DEBUG] Row-wise comparison will sample {sample_size} records (other checks use full data)")
        else:
            print(f"[DEBUG] Processing all records for all validation types")
        
        # Execute queries on their respective connections and create temp tables
        try:
            print(f"[DEBUG] Creating temp source table from query: {clean_source_query[:100]}...")
            print(f"[DEBUG] Full source query length: {len(clean_source_query)} characters")
            if is_source_databricks:
                # Databricks: Use CREATE TEMPORARY VIEW
                source_cursor.execute(f"CREATE TEMPORARY VIEW {temp_source_table} AS {clean_source_query}")
            else:
                # SQL Server: Use SELECT INTO
                # Note: We don't add ORDER BY here because temp tables should contain all data
                # ORDER BY will be applied when sampling in row_data_validation if needed
                sql = f"SELECT * INTO {temp_source_table} FROM ({clean_source_query}) AS SourceData"
                source_cursor.execute(sql)
            print(f"[DEBUG] Source temp table created successfully")
        except Exception as e:
            results["status"] = "FAILED"
            results["error"] = f"Failed to execute source query: {str(e)}"
            print(f"[ERROR] Source query failed: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return results
            
        try:
            print(f"[DEBUG] Creating temp target table from query: {clean_target_query[:100]}...")
            print(f"[DEBUG] Full target query length: {len(clean_target_query)} characters")
            if is_target_databricks:
                # Databricks: Use CREATE TEMPORARY VIEW
                target_cursor.execute(f"CREATE TEMPORARY VIEW {temp_target_table} AS {clean_target_query}")
            else:
                # SQL Server: Use SELECT INTO
                # Note: We don't add ORDER BY here because temp tables should contain all data
                # ORDER BY will be applied when sampling in row_data_validation if needed
                sql = f"SELECT * INTO {temp_target_table} FROM ({clean_target_query}) AS TargetData"
                target_cursor.execute(sql)
            print(f"[DEBUG] Target temp table created successfully")
        except Exception as e:
            # Clean up source temp table
            try:
                if is_source_databricks:
                    source_cursor.execute(f"DROP VIEW IF EXISTS {temp_source_table}")
                else:
                    source_cursor.execute(f"DROP TABLE IF EXISTS {temp_source_table}")
            except:
                pass
            results["status"] = "FAILED"
            results["error"] = f"Failed to execute target query: {str(e)}"
            print(f"[ERROR] Target query failed: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return results

        # Clear log files before validation
        log_files_to_clear = [
            os.path.join(LOGS_PATH, "etl_log.txt"),
            os.path.join(LOGS_PATH, "duplicate_combined_log.txt"),
            os.path.join(LOGS_PATH, "row_data_mismatch_log.txt")
        ]
        for log_file in log_files_to_clear:
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write("")  # Clear the file
            except Exception as e:
                print(f"Warning: Could not clear log file {log_file}: {e}")

        # Prepare to log validation outputs
        validation_start = time.time()
        etl_log_path = os.path.join(LOGS_PATH, "etl_log.txt")
        with open(etl_log_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"ETL Validation Execution - {execution_id}\n")
            log_file.write(f"PERFORMANCE OPTIMIZATION ENABLED\n")
            if sample_size > 0:
                log_file.write(f"SAMPLING ENABLED: Processing TOP {sample_size} records for faster validation\n")
                log_file.write(f"💡 TIP: Sampling significantly improves performance for large datasets\n")
            else:
                log_file.write(f"FULL SCAN: Processing all records\n")
                log_file.write(f"⚠️ WARNING: Full scan may be slow for large tables. Consider using sample size.\n")
            log_file.write(f"Source Query: {source_query[:200]}...\\n")
            log_file.write(f"Target Query: {target_query[:200]}...\\n")
            log_file.write(f"Timestamp: {datetime.now().isoformat()}\\n\\n")

        # Run Structure Validation
        if validations.get("structure_validation", True):
            try:
                struct_start = time.time()
                print(f"[PERFORMANCE] Starting Structure Validation...")
                output, result = structure_validation(
                    source_cursor, 
                    temp_source_table, 
                    temp_target_table, 
                    source_name=original_source_name,
                    target_name=original_target_name,
                    return_output=True,
                    source_cursor=source_cursor,
                    target_cursor=target_cursor
                )
                struct_time = round(time.time() - struct_start, 2)
                print(f"[PERFORMANCE] Structure Validation completed in {struct_time}s")
                results["validations"]["structure_validation"] = {
                    "name": "Structure Validation",
                    "passed": result,
                    "output": output,
                    "execution_time": f"{struct_time}s"
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Structure Validation (⏱️ {struct_time}s):\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["structure_validation"] = {
                    "name": "Structure Validation",
                    "passed": False,
                    "output": error_msg
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Structure Validation Error:\n{error_msg}\n\n")
        
        # Run Count Validation
        if validations.get("count_validation", True):
            try:
                count_start = time.time()
                print(f"[PERFORMANCE] Starting Count Validation...")
                result, output = count_validation(
                    source_cursor, 
                    temp_source_table, 
                    temp_target_table, 
                    source_name=original_source_name,
                    target_name=original_target_name,
                    return_output=True,
                    source_cursor=source_cursor,
                    target_cursor=target_cursor
                )
                count_time = round(time.time() - count_start, 2)
                print(f"[PERFORMANCE] Count Validation completed in {count_time}s")
                results["validations"]["count_validation"] = {
                    "name": "Record Count Validation",
                    "passed": result,
                    "output": output,
                    "execution_time": f"{count_time}s"
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Record Count Validation (⏱️ {count_time}s):\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["count_validation"] = {
                    "name": "Record Count Validation",
                    "passed": False,
                    "output": error_msg
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Record Count Validation Error:\n{error_msg}\n\n")
        
        # Run Null Check
        if validations.get("null_check", True):
            try:
                null_start = time.time()
                print(f"[PERFORMANCE] Starting Null Check...")
                source_output = null_check(source_cursor, temp_source_table, return_output=True, source_name=f"Source ({original_source_name})")
                target_output = null_check(target_cursor, temp_target_table, return_output=True, source_name=f"Target ({original_target_name})")
                null_time = round(time.time() - null_start, 2)
                print(f"[PERFORMANCE] Null Check completed in {null_time}s")
                
                # Add clear separation between source and target outputs
                separator = "\n" + "="*80 + "\n"
                combined_output = f"{source_output}{separator}{target_output}"
                
                results["validations"]["null_check"] = {
                    "name": "Null Check",
                    "passed": "❌" not in str(source_output) and "❌" not in str(target_output),
                    "output": combined_output,
                    "execution_time": f"{null_time}s"
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Null Check (⏱️ {null_time}s):\n{combined_output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["null_check"] = {
                    "name": "Null Check",
                    "passed": False,
                    "output": error_msg
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Null Check Error:\n{error_msg}\n\n")
        
        # Run Duplicate Check
        if validations.get("duplicate_check", True):
            try:
                dup_start = time.time()
                print(f"[PERFORMANCE] Starting Duplicate Check...")
                source_output = duplicate_check(source_cursor, temp_source_table, use_all_columns=True, return_output=True, label="Source")
                target_output = duplicate_check(target_cursor, temp_target_table, use_all_columns=True, return_output=True, label="Target")
                dup_time = round(time.time() - dup_start, 2)
                print(f"[PERFORMANCE] Duplicate Check completed in {dup_time}s")
                combined_output = f"SOURCE TABLE:\n{source_output}\n\nTARGET TABLE:\n{target_output}"
                results["validations"]["duplicate_check"] = {
                    "name": "Duplicate Check",
                    "passed": "❌" not in str(source_output) and "❌" not in str(target_output),
                    "output": combined_output,
                    "execution_time": f"{dup_time}s"
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Duplicate Check (⏱️ {dup_time}s):\n{combined_output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["duplicate_check"] = {
                    "name": "Duplicate Check",
                    "passed": False,
                    "output": error_msg
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Duplicate Check Error:\n{error_msg}\n\n")
        
        # Run Row Data Validation
        if validations.get("row_data_validation", True):
            try:
                row_start = time.time()
                print(f"[PERFORMANCE] Starting Row Data Validation (most resource-intensive)...")
                output = row_data_validation(
                    source_cursor, temp_source_table, temp_target_table,
                    return_output=True,
                    mismatch_log_file=os.path.join(LOGS_PATH, "row_data_mismatch_log.txt"),
                    source_name=original_source_name,
                    target_name=original_target_name,
                    source_cursor=source_cursor,
                    target_cursor=target_cursor,
                    sample_size=sample_size
                )
                row_time = round(time.time() - row_start, 2)
                print(f"[PERFORMANCE] Row Data Validation completed in {row_time}s")
                output_lower = str(output).lower()
                # Check for mismatches in HTML output
                has_mismatch = ("total mismatched records" in output_lower or 
                              "source-only rows exported" in output_lower or
                              "target-only rows exported" in output_lower or
                              "different number of columns" in output_lower)
                results["validations"]["row_data_validation"] = {
                    "name": "Row-wise Data Validation",
                    "passed": not has_mismatch,
                    "output": output,
                    "execution_time": f"{row_time}s"
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Row-wise Data Validation (⏱️ {row_time}s):\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["row_data_validation"] = {
                    "name": "Row-wise Data Validation",
                    "passed": False,
                    "output": error_msg
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Row-wise Data Validation Error:\n{error_msg}\n\n")
        
        # Calculate total validation time
        perf_metrics["validation_time"] = round(time.time() - validation_start, 2)
        print(f"[PERFORMANCE] All validations completed in {perf_metrics['validation_time']}s")
        
        # Add source and target query info to results for display
        results["source_query"] = source_query[:200] + "..." if len(source_query) > 200 else source_query
        results["target_query"] = target_query[:200] + "..." if len(target_query) > 200 else target_query
        
        # Clean up temp tables
        try:
            source_cursor.execute(f"DROP TABLE IF EXISTS {temp_source_table}")
            source_conn.commit()
        except Exception as e:
            print(f"[WARNING] Could not drop source temp table: {e}")
            
        try:
            source_cursor.execute(f"DROP TABLE IF EXISTS {temp_target_table}")
            source_conn.commit()
        except Exception as e:
            print(f"[WARNING] Could not drop target temp table: {e}")
        
        # Close connections
        try:
            source_conn.close()
        except:
            pass
        try:
            if target_conn != source_conn:
                target_conn.close()
        except:
            pass
        
        # Read log files
        results["logs"] = get_all_logs()

        # Determine overall status
        all_passed = all(v.get("passed", False) for v in results["validations"].values())
        results["status"] = "SUCCESS" if all_passed else "COMPLETED_WITH_ISSUES"

        # Generate dynamic reports
        print(f"[INFO] Generating reports...")
        print(f"[INFO] Source: {original_source_name}, Target: {original_target_name}")
        import importlib
        import src.report_generator
        importlib.reload(src.report_generator)
        from src.report_generator import generate_excel_report, generate_html_dashboard, set_table_names
        set_table_names(original_source_name, original_target_name)
        report_results = convert_results_for_reporting(results)
        # Change to project directory for report generation (since it uses relative paths)
        original_cwd = os.getcwd()
        os.chdir(PROJECT_PATH)
        try:
            print(f"[INFO] Generating HTML dashboard to: reports/etl_dashboard.html")
            generate_html_dashboard(report_results, output_file="reports/etl_dashboard.html", source_table=original_source_name, target_table=original_target_name)
            print(f"[INFO] Generating Excel report to: reports/etl_validation_report.xlsx")
            generate_excel_report(report_results, output_file="reports/etl_validation_report.xlsx", source_table=original_source_name, target_table=original_target_name, sample_size=sample_size, source_db_config=request.source_db_config, target_db_config=request.target_db_config)
            print(f"[INFO] Reports generated successfully!")
        except Exception as report_error:
            print(f"[ERROR] Report generation failed: {report_error}")
            print(f"[ERROR] Full traceback:")
            import traceback as tb
            tb.print_exc()
        finally:
            os.chdir(original_cwd)

        # Store results
        execution_results[execution_id] = results
        validation_outputs[execution_id] = results
        print(f"[DEBUG] Storing metadata for execution_id: {execution_id}")
        print(f"[DEBUG] source_table: '{original_source_name}', target_table: '{original_target_name}'")
        execution_metadata[execution_id] = {
            "target_table": original_target_name,
            "source_table": original_source_name,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        print(f"[DEBUG] Metadata stored: {execution_metadata[execution_id]}")

        # Calculate and add execution time
        end_time = time.time()
        execution_time = end_time - start_time
        perf_metrics["total_time"] = round(execution_time, 2)
        results["execution_time"] = round(execution_time, 2)
        
        # Log performance summary
        print(f"\n{'='*60}")
        print(f"PERFORMANCE SUMMARY - Execution ID: {execution_id}")
        print(f"{'='*60}")
        print(f"Connection Time:    {perf_metrics['connection_time']}s")
        print(f"Validation Time:    {perf_metrics['validation_time']}s")
        print(f"Total Time:         {perf_metrics['total_time']}s")
        print(f"Sample Size:        {sample_size if sample_size > 0 else 'ALL RECORDS'}")
        if sample_size > 0:
            print(f"💡 Performance Tip: Sampling reduced processing time significantly")
        else:
            print(f"⚠️ Performance Tip: Consider using sample size for faster validations")
        print(f"{'='*60}\n")

        # Log pipeline execution
        log_pipeline_execution(
            pipeline_name="ETL Pipeline Validation",
            table_name=f"{original_source_name} -> {original_target_name}",
            status=results["status"],
            start_date=datetime.fromtimestamp(start_time).isoformat(),
            end_date=datetime.fromtimestamp(end_time).isoformat(),
            execution_time=f"{execution_time:.2f}s",
            error_name=None,
            log_content=f"Performance: Connection={perf_metrics['connection_time']}s, Validation={perf_metrics['validation_time']}s, Total={perf_metrics['total_time']}s",
            project_id=request.project_id
        )

        return results
    
    except Exception as e:
        results["status"] = "FAILED"
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()
        end_time = time.time()
        results["execution_time"] = round(end_time - start_time, 2)
        execution_results[execution_id] = results
        
        # Log pipeline execution failure
        log_pipeline_execution(
            pipeline_name="ETL Pipeline Validation",
            table_name=f"{request.source_table} -> {request.target_table}",
            status="FAILED",
            start_date=datetime.fromtimestamp(start_time).isoformat(),
            end_date=datetime.fromtimestamp(end_time).isoformat(),
            execution_time=f"{results['execution_time']:.2f}s",
            error_name=type(e).__name__,
            log_content=str(e),
            project_id=request.project_id
        )
        
        return results


@app.post("/api/run-flatfile")
async def run_flatfile_validation(
    file: UploadFile = File(...),
    target_table: str = Form(...),
    target_query: str = Form(""),
    target_database: str = Form("default"),
    validations: str = Form("{}"),
    source_name: str = Form(""),
    target_db_config: str = Form(None)  # Added support for custom target database
):
    """Execute ETL validation pipeline for flat file source with support for cross-database validation"""
    start_time = time.time()
    execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use the provided source_name (file name) or default to FLAT_FILE
    source_display_name = source_name if source_name else file.filename
    
    results = {
        "execution_id": execution_id,
        "source_table": source_display_name,
        "target_table": target_table,
        "timestamp": datetime.now().isoformat(),
        "validations": {},
        "logs": {},
        "status": "RUNNING"
    }
    
    source_conn = None
    target_conn = None
    
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_PATH, f"{execution_id}_{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"[INFO] File saved to: {file_path}")
        
        # Parse validations
        try:
            validations_dict = json.loads(validations)
        except:
            validations_dict = {}
        
        # Parse target database config if provided
        target_db_config_dict = None
        if target_db_config and target_db_config != "null":
            try:
                target_db_config_dict = json.loads(target_db_config)
                print(f"[INFO] Using custom target database configuration: {target_db_config_dict.get('type')}")
            except Exception as e:
                print(f"[WARNING] Failed to parse target_db_config: {e}")
        
        # Connect to target database
        if target_db_config_dict:
            print(f"[INFO] Creating custom target connection...")
            target_conn = create_custom_connection(target_db_config_dict)
            if not target_conn:
                results["status"] = "FAILED"
                results["error"] = "Failed to connect to target database"
                return results
            target_conn.autocommit = True
            target_cursor = target_conn.cursor()
            target_db_type = target_db_config_dict.get('type', 'sqlserver')
            print(f"[INFO] Target connection established: {target_db_type}")
        else:
            # Use default connection
            print(f"[INFO] Using default database connection for target")
            target_conn = get_db_connection()
            if not target_conn:
                results["status"] = "FAILED"
                results["error"] = "Database connection failed"
                return results
            target_cursor = target_conn.cursor()
            target_db_type = 'sqlserver'
            
        # For source, we need a connection to load the CSV data
        # If target is SQL Server, we can use the same connection
        # If target is Databricks or other, we'll load CSV to Databricks temp view
        is_target_databricks = target_db_type in ['databricks', 'databricks_example']
        
        if is_target_databricks:
            # For Databricks, load CSV directly to a temp view on Databricks
            source_cursor = target_cursor  # Use same connection for both
            source_conn = target_conn
            print(f"[INFO] Loading CSV to Databricks temp view...")
        else:
            # For SQL Server or other databases, use the target connection
            source_cursor = target_cursor
            source_conn = target_conn
            print(f"[INFO] Loading CSV to SQL Server temp table...")
        
        # Import validation functions
        from src.validate import (
            structure_validation,
            count_validation,
            null_check,
            duplicate_check,
            row_data_validation,
        )
        
        # Load flat file data into a temporary table
        if is_target_databricks:
            temp_source_table = f"temp_source_{execution_id}"
        else:
            temp_source_table = f"##TempSource_{execution_id}"
            
        try:
            if is_target_databricks:
                # Load CSV to Databricks temp view
                load_flatfile_to_databricks(source_cursor, file_path, temp_source_table)
                print(f"[INFO] Loaded flat file into Databricks temp view: {temp_source_table}")
            else:
                # Load CSV to SQL Server temp table
                load_flatfile_to_table(source_cursor, file_path, temp_source_table)
                print(f"[INFO] Loaded flat file into temp table: {temp_source_table}")
        except Exception as e:
            print(f"[ERROR] Error loading flat file: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            results["status"] = "FAILED"
            results["error"] = f"Failed to load flat file: {str(e)}"
            return results
        
        # Clear log files before validation
        log_files_to_clear = [
            os.path.join(LOGS_PATH, "etl_log.txt"),
            os.path.join(LOGS_PATH, "duplicate_combined_log.txt"),
            os.path.join(LOGS_PATH, "row_data_mismatch_log.txt")
        ]
        for log_file in log_files_to_clear:
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write("")
            except:
                pass

        # Prepare to log validation outputs
        etl_log_path = os.path.join(LOGS_PATH, "etl_log.txt")
        with open(etl_log_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"ETL Validation Execution - {execution_id}\n")
            log_file.write(f"Source: Flat File ({file.filename})\n")
            log_file.write(f"Target Table: {target_table}\n")
            log_file.write(f"Timestamp: {datetime.now().isoformat()}\n\n")

        # Run Structure Validation
        if validations_dict.get("structure_validation", True):
            try:
                output, result = structure_validation(
                    source_cursor, 
                    temp_source_table, 
                    target_table, 
                    source_name=source_display_name,
                    target_name=target_table,
                    return_output=True,
                    source_cursor=source_cursor,
                    target_cursor=target_cursor
                )
                results["validations"]["structure_validation"] = {
                    "name": "Structure Validation",
                    "passed": result,
                    "output": output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Structure Validation:\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["structure_validation"] = {
                    "name": "Structure Validation",
                    "passed": False,
                    "output": error_msg
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Structure Validation Error:\n{error_msg}\n\n")
        
        # Run Count Validation
        if validations_dict.get("count_validation", True):
            try:
                result, output = count_validation(
                    source_cursor, 
                    temp_source_table, 
                    target_table, 
                    source_name=source_display_name,
                    target_name=target_table,
                    return_output=True,
                    source_cursor=source_cursor,
                    target_cursor=target_cursor
                )
                results["validations"]["count_validation"] = {
                    "name": "Record Count Validation",
                    "passed": result,
                    "output": output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Record Count Validation:\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["count_validation"] = {
                    "name": "Record Count Validation",
                    "passed": False,
                    "output": error_msg
                }
        
        # Run Null Check
        if validations_dict.get("null_check", True):
            try:
                source_output = null_check(source_cursor, temp_source_table, return_output=True)
                target_output = null_check(target_cursor, target_table, return_output=True)
                combined_output = f"SOURCE TABLE (Flat File):\n{source_output}\n\nTARGET TABLE:\n{target_output}"
                results["validations"]["null_check"] = {
                    "name": "Null Check",
                    "passed": "❌" not in str(source_output) and "❌" not in str(target_output),
                    "output": combined_output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Null Check:\n{combined_output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["null_check"] = {
                    "name": "Null Check",
                    "passed": False,
                    "output": error_msg
                }
        
        # Run Duplicate Check
        if validations_dict.get("duplicate_check", True):
            try:
                source_output = duplicate_check(source_cursor, temp_source_table, use_primary_key=True, return_output=True, label="Source (Flat File)")
                target_output = duplicate_check(target_cursor, target_table, use_primary_key=True, return_output=True, label="Target")
                combined_output = f"SOURCE TABLE (Flat File):\n{source_output}\n\nTARGET TABLE:\n{target_output}"
                results["validations"]["duplicate_check"] = {
                    "name": "Duplicate Check",
                    "passed": "❌" not in str(source_output) and "❌" not in str(target_output),
                    "output": combined_output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Duplicate Check:\n{combined_output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["duplicate_check"] = {
                    "name": "Duplicate Check",
                    "passed": False,
                    "output": error_msg
                }
        
        # Run Row Data Validation
        if validations_dict.get("row_data_validation", True):
            try:
                output = row_data_validation(
                    source_cursor, 
                    temp_source_table, 
                    target_table,
                    source_name=source_display_name,
                    target_name=target_table,
                    return_output=True,
                    mismatch_log_file=os.path.join(LOGS_PATH, "row_data_mismatch_log.txt"),
                    source_cursor=source_cursor,
                    target_cursor=target_cursor
                )
                output_lower = str(output).lower()
                has_mismatch = ("only in source" in output_lower or 
                              "only in target" in output_lower or 
                              "rows present only in source" in output_lower or
                              "rows present only in target" in output_lower or
                              "different number of columns" in output_lower)
                results["validations"]["row_data_validation"] = {
                    "name": "Row-wise Data Validation",
                    "passed": not has_mismatch,
                    "output": output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Row-wise Data Validation:\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["row_data_validation"] = {
                    "name": "Row-wise Data Validation",
                    "passed": False,
                    "output": error_msg
                }
        
        # Clean up temp table/view
        try:
            if is_target_databricks:
                source_cursor.execute(f"DROP VIEW IF EXISTS {temp_source_table}")
            else:
                source_cursor.execute(f"DROP TABLE IF EXISTS {temp_source_table}")
            if source_conn:
                source_conn.commit()
        except Exception as cleanup_error:
            print(f"[WARNING] Failed to clean up temp table: {cleanup_error}")
        
        # Close connections
        if target_conn:
            target_conn.close()
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        # Read log files
        results["logs"] = get_all_logs()

        # Determine overall status
        all_passed = all(v.get("passed", False) for v in results["validations"].values())
        results["status"] = "SUCCESS" if all_passed else "COMPLETED_WITH_ISSUES"
        
        # Generate dynamic reports
        print(f"[INFO] Generating reports for flat file validation...")
        print(f"[INFO] Source: {source_display_name}, Target: {target_table}")
        import importlib
        import src.report_generator
        importlib.reload(src.report_generator)
        from src.report_generator import generate_excel_report, generate_html_dashboard, set_table_names
        set_table_names(source_display_name, target_table)
        report_results = convert_results_for_reporting(results)
        # Change to project directory for report generation (since it uses relative paths)
        original_cwd = os.getcwd()
        os.chdir(PROJECT_PATH)
        try:
            print(f"[INFO] Generating HTML dashboard to: reports/etl_dashboard.html")
            generate_html_dashboard(report_results, output_file="reports/etl_dashboard.html", source_table=source_display_name, target_table=target_table)
            print(f"[INFO] Generating Excel report to: reports/etl_validation_report.xlsx")
            # Create source config for flat file
            source_config = {
                'type': 'File Upload',
                'server': 'Local File System',
                'database': 'N/A',
                'authType': 'N/A'
            }
            # Create target config from actual database config or use default
            if target_db_config_dict:
                target_config = {
                    'type': target_db_config_dict.get('type', 'Unknown'),
                    'server': target_db_config_dict.get('server') or target_db_config_dict.get('workspace_url', 'Custom Database'),
                    'database': target_db_config_dict.get('database') or target_db_config_dict.get('catalog', 'N/A'),
                    'authType': target_db_config_dict.get('auth_type') or target_db_config_dict.get('databricks_auth_type', 'N/A')
                }
            else:
                target_config = {
                    'type': 'sqlserver',
                    'server': 'Default Connection',
                    'database': target_database if target_database and target_database != 'default' else 'N/A',
                    'authType': 'Windows'
                }
            generate_excel_report(report_results, output_file="reports/etl_validation_report.xlsx", source_table=source_display_name, target_table=target_table, source_db_config=source_config, target_db_config=target_config)
            print(f"[INFO] Reports generated successfully!")
        except Exception as report_error:
            print(f"[ERROR] Report generation failed: {report_error}")
        finally:
            os.chdir(original_cwd)
        
        # Store results
        execution_results[execution_id] = results
        validation_outputs[execution_id] = results
        execution_metadata[execution_id] = {
            "target_table": target_table,
            "source_table": source_display_name,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }

        # Calculate and add execution time
        end_time = time.time()
        execution_time = end_time - start_time
        results["execution_time"] = round(execution_time, 2)
        print(f"[INFO] Flatfile validation completed in {execution_time:.2f} seconds")

        return results
    
    except Exception as e:
        results["status"] = "FAILED"
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()
        end_time = time.time()
        results["execution_time"] = round(end_time - start_time, 2)
        execution_results[execution_id] = results
        return results


@app.post("/api/run-file-to-file")
async def run_file_to_file_validation(
    source_file: UploadFile = File(...),
    target_file: UploadFile = File(...),
    validations: str = Form("{}"),
    source_name: str = Form(""),
    target_name: str = Form(""),
    sample_size: str = Form("0")
):
    """Execute ETL validation pipeline for file-to-file comparison (e.g., CSV to CSV, Excel to JSON, etc.)"""
    start_time = time.time()
    execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use the provided file names or default
    source_display_name = source_name if source_name else source_file.filename
    target_display_name = target_name if target_name else target_file.filename
    
    results = {
        "execution_id": execution_id,
        "source_table": source_display_name,
        "target_table": target_display_name,
        "timestamp": datetime.now().isoformat(),
        "validations": {},
        "logs": {},
        "status": "RUNNING"
    }
    
    source_conn = None
    temp_source_table = None
    temp_target_table = None
    
    try:
        # Parse sample size
        try:
            sample_size_int = int(sample_size) if sample_size else 0
        except:
            sample_size_int = 0
        
        # Save uploaded files
        source_file_path = os.path.join(UPLOAD_PATH, f"{execution_id}_source_{source_file.filename}")
        target_file_path = os.path.join(UPLOAD_PATH, f"{execution_id}_target_{target_file.filename}")
        
        with open(source_file_path, "wb") as f:
            content = await source_file.read()
            f.write(content)
        
        with open(target_file_path, "wb") as f:
            content = await target_file.read()
            f.write(content)
        
        print(f"[INFO] Source file saved to: {source_file_path}")
        print(f"[INFO] Target file saved to: {target_file_path}")
        
        # Parse validations
        try:
            validations_dict = json.loads(validations)
        except:
            validations_dict = {}
        
        # For file-to-file comparison, use SQLite in-memory database (no external DB required)
        import sqlite3
        source_conn = sqlite3.connect(':memory:')
        source_cursor = source_conn.cursor()
        target_cursor = source_cursor  # Same connection for both
        
        # Import validation functions
        from src.validate import (
            structure_validation,
            count_validation,
            null_check,
            duplicate_check,
            row_data_validation,
        )
        
        # Load both files into SQLite temporary tables
        temp_source_table = f"TempSource_{execution_id}"
        temp_target_table = f"TempTarget_{execution_id}"
        
        try:
            load_flatfile_to_sqlite(source_cursor, source_file_path, temp_source_table)
            print(f"[INFO] Source file loaded into SQLite table: {temp_source_table}")
        except Exception as e:
            print(f"[ERROR] Error loading source file: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            results["status"] = "FAILED"
            results["error"] = f"Failed to load source file: {str(e)}"
            return results
        
        try:
            load_flatfile_to_sqlite(target_cursor, target_file_path, temp_target_table)
            print(f"[INFO] Target file loaded into SQLite table: {temp_target_table}")
        except Exception as e:
            print(f"[ERROR] Error loading target file: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            results["status"] = "FAILED"
            results["error"] = f"Failed to load target file: {str(e)}"
            # Clean up source temp table
            try:
                source_cursor.execute(f"DROP TABLE IF EXISTS {temp_source_table}")
            except:
                pass
            return results
        
        # Clear log files before validation
        log_files_to_clear = [
            os.path.join(LOGS_PATH, "etl_log.txt"),
            os.path.join(LOGS_PATH, "duplicate_combined_log.txt"),
            os.path.join(LOGS_PATH, "row_data_mismatch_log.txt")
        ]
        for log_file in log_files_to_clear:
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write("")
            except:
                pass

        # Prepare to log validation outputs
        etl_log_path = os.path.join(LOGS_PATH, "etl_log.txt")
        with open(etl_log_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"ETL Validation Execution - File-to-File Comparison - {execution_id}\n")
            log_file.write(f"Source File: {source_display_name}\n")
            log_file.write(f"Target File: {target_display_name}\n")
            if sample_size_int > 0:
                log_file.write(f"Sample Size: {sample_size_int} records\n")
            log_file.write(f"Timestamp: {datetime.now().isoformat()}\n\n")

        # Run Structure Validation
        if validations_dict.get("structure_validation", True):
            try:
                output, result = structure_validation(
                    source_cursor, 
                    temp_source_table, 
                    temp_target_table, 
                    source_name=source_display_name,
                    target_name=target_display_name,
                    return_output=True,
                    source_cursor=source_cursor,
                    target_cursor=target_cursor
                )
                results["validations"]["structure_validation"] = {
                    "name": "Structure Validation",
                    "passed": result,
                    "output": output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Structure Validation:\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["structure_validation"] = {
                    "name": "Structure Validation",
                    "passed": False,
                    "output": error_msg
                }
        
        # Run Count Validation
        if validations_dict.get("count_validation", True):
            try:
                result, output = count_validation(
                    source_cursor, 
                    temp_source_table, 
                    temp_target_table, 
                    source_name=source_display_name,
                    target_name=target_display_name,
                    return_output=True,
                    source_cursor=source_cursor,
                    target_cursor=target_cursor
                )
                results["validations"]["count_validation"] = {
                    "name": "Record Count Validation",
                    "passed": result,
                    "output": output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Record Count Validation:\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["count_validation"] = {
                    "name": "Record Count Validation",
                    "passed": False,
                    "output": error_msg
                }
        
        # Run Null Check
        if validations_dict.get("null_check", True):
            try:
                source_output = null_check(source_cursor, temp_source_table, return_output=True)
                target_output = null_check(target_cursor, temp_target_table, return_output=True)
                combined_output = f"SOURCE FILE ({source_display_name}):\n{source_output}\n\nTARGET FILE ({target_display_name}):\n{target_output}"
                results["validations"]["null_check"] = {
                    "name": "Null Check",
                    "passed": "❌" not in str(source_output) and "❌" not in str(target_output),
                    "output": combined_output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Null Check:\n{combined_output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["null_check"] = {
                    "name": "Null Check",
                    "passed": False,
                    "output": error_msg
                }
        
        # Run Duplicate Check
        if validations_dict.get("duplicate_check", True):
            try:
                source_output = duplicate_check(source_cursor, temp_source_table, use_primary_key=True, return_output=True, label=f"Source ({source_display_name})")
                target_output = duplicate_check(target_cursor, temp_target_table, use_primary_key=True, return_output=True, label=f"Target ({target_display_name})")
                combined_output = f"SOURCE FILE ({source_display_name}):\n{source_output}\n\nTARGET FILE ({target_display_name}):\n{target_output}"
                results["validations"]["duplicate_check"] = {
                    "name": "Duplicate Check",
                    "passed": "❌" not in str(source_output) and "❌" not in str(target_output),
                    "output": combined_output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Duplicate Check:\n{combined_output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["duplicate_check"] = {
                    "name": "Duplicate Check",
                    "passed": False,
                    "output": error_msg
                }
        
        # Run Row Data Validation
        if validations_dict.get("row_data_validation", True):
            try:
                output = row_data_validation(
                    source_cursor, 
                    temp_source_table, 
                    temp_target_table,
                    source_name=source_display_name,
                    target_name=target_display_name,
                    return_output=True,
                    mismatch_log_file=os.path.join(LOGS_PATH, "row_data_mismatch_log.txt"),
                    source_cursor=source_cursor,
                    target_cursor=target_cursor,
                    sample_size=sample_size_int
                )
                output_lower = str(output).lower()
                has_mismatch = ("only in source" in output_lower or 
                              "only in target" in output_lower or 
                              "rows present only in source" in output_lower or
                              "rows present only in target" in output_lower or
                              "different number of columns" in output_lower)
                results["validations"]["row_data_validation"] = {
                    "name": "Row-wise Data Validation",
                    "passed": not has_mismatch,
                    "output": output
                }
                with open(etl_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Row-wise Data Validation:\n{output}\n\n")
            except Exception as e:
                error_msg = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                results["validations"]["row_data_validation"] = {
                    "name": "Row-wise Data Validation",
                    "passed": False,
                    "output": error_msg
                }
        
        # Clean up temp tables
        try:
            source_cursor.execute(f"DROP TABLE IF EXISTS {temp_source_table}")
            source_cursor.execute(f"DROP TABLE IF EXISTS {temp_target_table}")
            if source_conn:
                source_conn.commit()
        except Exception as cleanup_error:
            print(f"[WARNING] Failed to clean up temp tables: {cleanup_error}")
        
        # Close connections
        if source_conn:
            source_conn.close()
        
        # Clean up uploaded files
        try:
            os.remove(source_file_path)
            os.remove(target_file_path)
        except:
            pass
        
        # Read log files
        results["logs"] = get_all_logs()

        # Determine overall status
        all_passed = all(v.get("passed", False) for v in results["validations"].values())
        results["status"] = "SUCCESS" if all_passed else "COMPLETED_WITH_ISSUES"
        
        # Generate dynamic reports
        print(f"[INFO] Generating reports for file-to-file validation...")
        print(f"[INFO] Source: {source_display_name}, Target: {target_display_name}")
        import importlib
        import src.report_generator
        importlib.reload(src.report_generator)
        from src.report_generator import generate_excel_report, generate_html_dashboard, set_table_names
        set_table_names(source_display_name, target_display_name)
        report_results = convert_results_for_reporting(results)
        # Change to project directory for report generation
        original_cwd = os.getcwd()
        os.chdir(PROJECT_PATH)
        try:
            print(f"[INFO] Generating HTML dashboard to: reports/etl_dashboard.html")
            generate_html_dashboard(report_results, output_file="reports/etl_dashboard.html", source_table=source_display_name, target_table=target_display_name)
            print(f"[INFO] Generating Excel report to: reports/etl_validation_report.xlsx")
            # Create source and target configs for file-to-file
            source_config = {
                'type': 'File Upload',
                'server': 'Local File System',
                'database': 'N/A',
                'authType': 'N/A'
            }
            target_config = {
                'type': 'File Upload',
                'server': 'Local File System',
                'database': 'N/A',
                'authType': 'N/A'
            }
            generate_excel_report(report_results, output_file="reports/etl_validation_report.xlsx", source_table=source_display_name, target_table=target_display_name, source_db_config=source_config, target_db_config=target_config)
            print(f"[INFO] Reports generated successfully!")
        except Exception as report_error:
            print(f"[ERROR] Report generation failed: {report_error}")
        finally:
            os.chdir(original_cwd)
        
        # Store results
        execution_results[execution_id] = results
        validation_outputs[execution_id] = results
        execution_metadata[execution_id] = {
            "target_table": target_display_name,
            "source_table": source_display_name,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        }

        # Calculate and add execution time
        end_time = time.time()
        execution_time = end_time - start_time
        results["execution_time"] = round(execution_time, 2)
        print(f"[INFO] File-to-file validation completed in {execution_time:.2f} seconds")

        return results
    
    except Exception as e:
        results["status"] = "FAILED"
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()
        end_time = time.time()
        results["execution_time"] = round(end_time - start_time, 2)
        execution_results[execution_id] = results
        return results


def load_flatfile_to_sqlite(cursor, file_path, table_name):
    """Load data from flat file into a SQLite table (for file-to-file comparisons)"""
    import pandas as pd
    import re
    
    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Read file based on extension
    if file_ext == '.csv':
        df = pd.read_csv(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif file_ext == '.json':
        # Try different JSON reading strategies with proper encoding handling (handles BOM)
        import json
        df = None
        
        # Try multiple encodings (utf-8-sig handles BOM, utf-8 is standard)
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                
                print(f"[DEBUG] Successfully read JSON with encoding: {encoding}")
                
                # Convert JSON to DataFrame based on structure
                if isinstance(data, dict) and len(data) == 1:
                    key = list(data.keys())[0]
                    if isinstance(data[key], list):
                        df = pd.DataFrame(data[key])
                    else:
                        df = pd.json_normalize(data)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    df = pd.json_normalize(data)
                else:
                    raise ValueError(f"Unsupported JSON structure: {type(data)}")
                
                break  # Success, exit the encoding loop
                
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                print(f"[DEBUG] Failed with encoding {encoding}: {e}")
                if encoding == 'latin-1':  # Last encoding attempt
                    raise ValueError(f"Failed to read JSON file. Tried multiple encodings. Last error: {str(e)}")
        
        if df is None:
            raise ValueError("Failed to read JSON file after all attempts")
    elif file_ext == '.parquet':
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
    
    # Clean column names thoroughly for SQLite compatibility
    # Replace spaces, special chars, and ensure columns don't start with numbers
    cleaned_columns = []
    for col in df.columns:
        # Convert to string first
        col_str = str(col)
        # Replace spaces and special chars with underscore
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', col_str)
        # If starts with number, prefix with 'col_'
        if cleaned and cleaned[0].isdigit():
            cleaned = f'col_{cleaned}'
        # If empty or just underscores, use a default name
        if not cleaned or cleaned.strip('_') == '':
            cleaned = f'column_{len(cleaned_columns)}'
        cleaned_columns.append(cleaned)
    
    df.columns = cleaned_columns
    
    # Convert nested JSON structures (dict/list) to JSON strings for SQLite compatibility
    import json
    for col in df.columns:
        # Check if column contains dict or list objects
        if df[col].dtype == 'object':
            # Check first non-null value
            sample_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
            if isinstance(sample_val, (dict, list)):
                print(f"[DEBUG] Converting nested JSON column '{col}' to string")
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    
    # Use pandas to_sql which handles all SQLite quirks automatically
    conn = cursor.connection
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    print(f"[INFO] Loaded {len(df)} rows into SQLite table {table_name}")



def load_flatfile_to_table(cursor, file_path, table_name):
    """Load data from flat file into a database table"""
    import pandas as pd
    
    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Read file based on extension
    if file_ext == '.csv':
        df = pd.read_csv(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif file_ext == '.json':
        # Try different JSON reading strategies with proper encoding handling (handles BOM)
        import json
        df = None
        
        # Try multiple encodings (utf-8-sig handles BOM, utf-8 is standard)
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                
                print(f"[DEBUG] Successfully read JSON with encoding: {encoding}")
                
                # Convert JSON to DataFrame based on structure
                if isinstance(data, dict) and len(data) == 1:
                    key = list(data.keys())[0]
                    if isinstance(data[key], list):
                        df = pd.DataFrame(data[key])
                    else:
                        df = pd.json_normalize(data)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    df = pd.json_normalize(data)
                else:
                    raise ValueError(f"Unsupported JSON structure: {type(data)}")
                
                break  # Success, exit the encoding loop
                
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                print(f"[DEBUG] Failed with encoding {encoding}: {e}")
                if encoding == 'latin-1':  # Last encoding attempt
                    raise ValueError(f"Failed to read JSON file. Tried multiple encodings. Last error: {str(e)}")
        
        if df is None:
            raise ValueError("Failed to read JSON file after all attempts")
    elif file_ext == '.parquet':
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
    
    # Clean column names (replace spaces and special chars)
    df.columns = [col.replace(' ', '_').replace('-', '_').replace('.', '_') for col in df.columns]
    
    # Convert nested JSON structures (dict/list) to JSON strings for SQL compatibility
    import json
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if column contains dict or list objects
            sample_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
            if isinstance(sample_val, (dict, list)):
                print(f"[DEBUG] Converting nested JSON column '{col}' to string")
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    
    # Get column data types
    columns_with_types = []
    for col in df.columns:
        dtype = df[col].dtype
        if dtype == 'object':
            columns_with_types.append(f"{col} NVARCHAR(MAX)")
        elif dtype == 'int64':
            columns_with_types.append(f"{col} BIGINT")
        elif dtype == 'float64':
            columns_with_types.append(f"{col} FLOAT")
        elif dtype == 'bool':
            columns_with_types.append(f"{col} BIT")
        elif 'datetime' in str(dtype):
            columns_with_types.append(f"{col} DATETIME")
        else:
            columns_with_types.append(f"{col} NVARCHAR(MAX)")
    
    # Create table
    create_table_sql = f"""
        IF OBJECT_ID('{table_name}', 'U') IS NOT NULL
            DROP TABLE {table_name}
        
        CREATE TABLE {table_name} (
            {', '.join(columns_with_types)}
        )
    """
    cursor.execute(create_table_sql)
    
    # Insert data in batches
    batch_size = 1000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        
        # Build INSERT statement
        cols = ', '.join(df.columns)
        placeholders = ', '.join(['?' for _ in df.columns])
        insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        
        # Convert DataFrame rows to list of tuples
        for _, row in batch.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append(None)
                elif isinstance(val, (pd.Timestamp,)):
                    values.append(val.to_pydatetime())
                elif hasattr(val, 'strftime'):  # datetime-like objects
                    values.append(val)
                elif isinstance(val, (dict, list)):  # Handle nested JSON
                    import json
                    values.append(json.dumps(val))
                else:
                    values.append(val)
            cursor.execute(insert_sql, values)
    
    cursor.connection.commit()
    print(f"Loaded {len(df)} rows into {table_name}")


def load_flatfile_to_databricks(cursor, file_path, table_name):
    """Load data from flat file into a Databricks temporary view"""
    import pandas as pd
    
    print(f"[INFO] Loading flat file to Databricks temp view: {table_name}")
    
    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Read file based on extension
    if file_ext == '.csv':
        df = pd.read_csv(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif file_ext == '.json':
        # Try different JSON reading strategies with proper encoding handling (handles BOM)
        import json
        df = None
        
        # Try multiple encodings (utf-8-sig handles BOM, utf-8 is standard)
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                
                print(f"[DEBUG] Successfully read JSON with encoding: {encoding}")
                
                # Convert JSON to DataFrame based on structure
                if isinstance(data, dict) and len(data) == 1:
                    key = list(data.keys())[0]
                    if isinstance(data[key], list):
                        df = pd.DataFrame(data[key])
                    else:
                        df = pd.json_normalize(data)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    df = pd.json_normalize(data)
                else:
                    raise ValueError(f"Unsupported JSON structure: {type(data)}")
                
                break  # Success, exit the encoding loop
                
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                print(f"[DEBUG] Failed with encoding {encoding}: {e}")
                if encoding == 'latin-1':  # Last encoding attempt
                    raise ValueError(f"Failed to read JSON file. Tried multiple encodings. Last error: {str(e)}")
        
        if df is None:
            raise ValueError("Failed to read JSON file after all attempts")
    elif file_ext == '.parquet':
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
    
    # Clean column names (replace spaces and special chars to be Databricks-compatible)
    df.columns = [col.replace(' ', '_').replace('-', '_').replace('.', '_').replace('[', '').replace(']', '') for col in df.columns]
    
    # Convert nested JSON structures (dict/list) to JSON strings for Databricks compatibility
    import json
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if column contains dict or list objects
            sample_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
            if isinstance(sample_val, (dict, list)):
                print(f"[DEBUG] Converting nested JSON column '{col}' to string for Databricks")
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    
    print(f"[INFO] DataFrame loaded with {len(df)} rows and {len(df.columns)} columns")
    print(f"[INFO] Columns: {', '.join(df.columns)}")
    
    # Get column data types for Databricks
    columns_with_types = []
    for col in df.columns:
        dtype = df[col].dtype
        if dtype == 'object':
            columns_with_types.append(f"`{col}` STRING")
        elif dtype == 'int64' or dtype == 'int32':
            columns_with_types.append(f"`{col}` BIGINT")
        elif dtype == 'float64' or dtype == 'float32':
            columns_with_types.append(f"`{col}` DOUBLE")
        elif dtype == 'bool':
            columns_with_types.append(f"`{col}` BOOLEAN")
        elif 'datetime' in str(dtype):
            columns_with_types.append(f"`{col}` TIMESTAMP")
        else:
            columns_with_types.append(f"`{col}` STRING")
    
    try:
        # Drop existing view if it exists
        drop_sql = f"DROP VIEW IF EXISTS {table_name}"
        cursor.execute(drop_sql)
        print(f"[DEBUG] Dropped existing view if present")
        
        # Create an empty temp view with the schema
        # Build SELECT list for empty view
        select_parts = []
        for col in columns_with_types:
            col_type = col.split()[1]
            col_name = col.split()[0].strip('`')
            select_parts.append(f'CAST(NULL AS {col_type}) AS {col_name}')
        
        create_sql = f"CREATE TEMPORARY VIEW {table_name} ({', '.join(columns_with_types)}) AS SELECT {', '.join(select_parts)} WHERE 1=0"
        cursor.execute(create_sql)
        print(f"[DEBUG] Created temp view schema")
        
        # Since Databricks doesn't support direct INSERT with pyodbc well,
        # we'll use a workaround: create a VALUES clause with all data
        # For large datasets, this should ideally use file upload to DBFS, but for POC this works
        
        if len(df) > 0:
            # Drop and recreate with actual data using VALUES
            cursor.execute(f"DROP VIEW IF EXISTS {table_name}")
            
            # Build VALUES clause (limit to reasonable size to avoid query length issues)
            max_rows_per_batch = 1000
            if len(df) > max_rows_per_batch:
                print(f"[WARNING] Large dataset detected ({len(df)} rows). Processing in batches...")
                
            # For simplicity, create a single VALUES statement (can be optimized for larger files)
            values_rows = []
            for idx, row in df.head(max_rows_per_batch).iterrows():
                row_values = []
                for val in row:
                    if pd.isna(val):
                        row_values.append("NULL")
                    elif isinstance(val, str):
                        # Escape single quotes
                        escaped_val = val.replace("'", "''")
                        row_values.append(f"'{escaped_val}'")
                    elif isinstance(val, (pd.Timestamp,)):
                        row_values.append(f"TIMESTAMP '{val.strftime('%Y-%m-%d %H:%M:%S')}'")
                    elif isinstance(val, bool):
                        row_values.append("TRUE" if val else "FALSE")
                    else:
                        row_values.append(str(val))
                values_rows.append(f"({', '.join(row_values)})")
            
            if values_rows:
                # Build column list with backticks
                col_list = ', '.join([f'`{col}`' for col in df.columns])
                # Create temp view from VALUES
                values_clause = ',\n'.join(values_rows)
                create_with_data_sql = f"""
                CREATE TEMPORARY VIEW {table_name} AS 
                SELECT * FROM VALUES
                {values_clause}
                AS t({col_list})
                """
                cursor.execute(create_with_data_sql)
                print(f"[INFO] Loaded {min(len(df), max_rows_per_batch)} rows into Databricks temp view {table_name}")
                
                if len(df) > max_rows_per_batch:
                    print(f"[WARNING] Only loaded first {max_rows_per_batch} rows of {len(df)} total rows")
        else:
            print(f"[WARNING] Empty DataFrame, created view with schema only")
            
    except Exception as e:
        print(f"[ERROR] Failed to create Databricks temp view: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise


def get_all_logs():
    """Read all log files and return their contents"""
    logs = {}

    log_files = {
        "etl": "etl_log.txt",
        "duplicates": "duplicate_combined_log.txt",
        "mismatches": "row_data_mismatch_log.txt"
    }

    for log_type, filename in log_files.items():
        log_path = os.path.join(LOGS_PATH, filename)
        try:
            if os.path.exists(log_path):
                with open(log_path, encoding="utf-8") as f:
                    content = f.read()
                    logs[log_type] = content if content.strip() else "No data in log file"
            else:
                logs[log_type] = "Log file not found"
        except Exception as e:
            logs[log_type] = f"Error reading log: {str(e)}"

    return logs


def convert_results_for_reporting(api_results):
    """Convert API results format to structured report format with pass/fail status"""
    
    # IMMEDIATE DEBUG - Write to file to confirm function is called
    debug_file_path = os.path.join(LOGS_PATH, "split_debug.txt")
    try:
        with open(debug_file_path, "w", encoding="utf-8") as f:
            f.write(f"=== convert_results_for_reporting CALLED at {datetime.now()} ===\n")
            f.write(f"api_results keys: {list(api_results.keys())}\n")
            f.write(f"validations keys: {list(api_results.get('validations', {}).keys())}\n")
        print(f"[DEBUG CONVERT] Function called, debug file created", flush=True)
    except Exception as e:
        print(f"[DEBUG CONVERT] ERROR creating debug file: {e}", flush=True)
    
    report_results = {}

    # Mapping from API keys to report keys
    key_mapping = {
        "structure_validation": "Structure Validation",
        "count_validation": "Record Count Check",
        "null_check": "Null Check (Source Table)",  # This will be split
        "duplicate_check": "Duplicate Check (Source Table)",  # This will be split
        "row_data_validation": "Row-wise Data Validation"
    }

    for api_key, report_key in key_mapping.items():
        if api_key in api_results["validations"]:
            val = api_results["validations"][api_key]
            
            if api_key == "null_check":
                # Split source and target null checks
                # The format is: source_output + "\n" + "="*80 + "\n" + target_output
                full_output = val["output"]
                
                # Append to debug file
                with open(debug_file_path, "a", encoding="utf-8") as f:
                    f.write(f"\n=== PROCESSING NULL_CHECK ===\n")
                    f.write(f"Full output length: {len(full_output)}\n")
                    f.write(f"Full output first 800 chars:\n{full_output[:800]}\n\n")
                
                print(f"[DEBUG NULL_CHECK] Full null check output length: {len(full_output)}", flush=True)
                
                # The separator includes newlines: "\n" + "="*80 + "\n"
                separator = "\n" + "=" * 80 + "\n"
                
                if separator in full_output:
                    # Split on the full separator  
                    parts = full_output.split(separator)
                    source_output = parts[0].strip() if len(parts) > 0 else ""
                    target_output = parts[1].strip() if len(parts) > 1 else ""
                    
                    with open(debug_file_path, "a", encoding="utf-8") as f:
                        f.write(f"\nSeparator FOUND! Split into {len(parts)} parts\n")
                        f.write(f"Source output length: {len(source_output)}\n")
                        f.write(f"Target output length: {len(target_output)}\n")
                        f.write(f"\n--- TARGET OUTPUT (first 600 chars) ---\n{target_output[:600]}\n\n")
                    
                    print(f"[DEBUG NULL_CHECK] Separator FOUND - Split into {len(parts)} parts", flush=True)
                    print(f"[DEBUG NULL_CHECK] Target output length: {len(target_output)}", flush=True)
                else:
                    # Fallback: try without leading newline
                    separator_no_leading = "=" * 80 + "\n"
                    if separator_no_leading in full_output:
                        parts = full_output.split(separator_no_leading)
                        source_output = parts[0].strip() if len(parts) > 0 else ""
                        target_output = parts[1].strip() if len(parts) > 1 else ""
                        
                        with open(debug_file_path, "a", encoding="utf-8") as f:
                            f.write(f"\nSeparator (no leading newline) FOUND!\n")
                            f.write(f"Target output length: {len(target_output)}\n")
                        
                        print(f"[DEBUG NULL_CHECK] Separator (no leading newline) FOUND", flush=True)
                    else:
                        # No separator found
                        with open(debug_file_path, "a", encoding="utf-8") as f:
                            f.write(f"\nERROR: No separator found!\n")
                        
                        print(f"[DEBUG NULL_CHECK] WARNING: Separator NOT FOUND!", flush=True)
                        source_output = full_output
                        target_output = ""
                
                print(f"[DEBUG NULL_CHECK] Target will be stored with length: {len(target_output)}", flush=True)
                
                source_passed = "❌" not in source_output
                target_passed = "❌" not in target_output
                
                report_results["Null Check (Source Table)"] = {
                    "passed": source_passed,
                    "output": source_output
                }
                report_results["Null Check (Target Table)"] = {
                    "passed": target_passed,
                    "output": target_output
                }
                
                # Write final stored values
                with open(debug_file_path, "a", encoding="utf-8") as f:
                    f.write(f"\n=== FINAL STORED VALUES ===\n")
                    f.write(f"Source passed: {source_passed}, output length: {len(source_output)}\n")
                    f.write(f"Target passed: {target_passed}, output length: {len(target_output)}\n")
                    f.write(f"Target output stored (first 500):\n{target_output[:500]}\n")
                
            elif api_key == "duplicate_check":
                # Split source and target duplicate checks
                source_output = val["output"].split("\n\nTARGET TABLE:\n")[0].replace("SOURCE TABLE:\n", "")
                target_output = val["output"].split("\n\nTARGET TABLE:\n")[1] if "\n\nTARGET TABLE:\n" in val["output"] else ""
                
                source_passed = "❌" not in source_output
                target_passed = "❌" not in target_output
                
                report_results["Duplicate Check (Source Table)"] = {
                    "passed": source_passed,
                    "output": source_output
                }
                report_results["Duplicate Check (Target Table)"] = {
                    "passed": target_passed,
                    "output": target_output
                }
                
            else:
                # Keep structured format with passed status
                report_results[report_key] = {
                    "passed": val.get("passed", False),
                    "output": val["output"]
                }

    return report_results


@app.post("/api/run-pytest")
def run_pytest_validation(request: ValidationRequest):
    """Execute validation using pytest"""
    try:
        execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set environment variables
        os.environ["SOURCE_TABLE"] = request.source_table
        os.environ["TARGET_TABLE"] = request.target_table
        
        for key, value in request.validations.items():
            os.environ[key.upper()] = str(value)
        
        # Run pytest with allure reporting
        cmd = [
            "pytest",
            "-v",
            "--alluredir=reports/allure-results",
            "tests/"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=PROJECT_PATH,
            capture_output=True,
            text=True,
            shell=True
        )
        
        return {
            "execution_id": execution_id,
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
            "message": "PyTest Execution Completed",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "logs": get_all_logs()
        }
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "ERROR", "message": str(e)}
        )


@app.get("/api/download/excel/{execution_id}")
def download_excel(execution_id: str = None):
    """Download Excel report"""
    file_path = os.path.join(REPORT_PATH, "etl_validation_report.xlsx")
    
    if os.path.exists(file_path):
        # Get metadata for filename
        print(f"[DEBUG] Download request for execution_id: {execution_id}")
        print(f"[DEBUG] Available execution_ids in metadata: {list(execution_metadata.keys())}")
        
        # Try to get metadata from execution_id
        metadata = execution_metadata.get(execution_id, {})
        
        # If metadata not found and we have a 'latest' request, use the most recent execution
        if not metadata and (execution_id == 'latest' or execution_id is None):
            if execution_metadata:
                # Get the most recent execution_id (sorted by timestamp)
                latest_exec_id = max(execution_metadata.keys())
                metadata = execution_metadata.get(latest_exec_id, {})
                print(f"[DEBUG] Using latest execution_id: {latest_exec_id}")
        
        # If still no metadata, try to get from execution_results
        if not metadata and execution_id in execution_results:
            result = execution_results[execution_id]
            metadata = {
                "target_table": result.get("target_table", "DataValidation"),
                "source_table": result.get("source_table", ""),
                "timestamp": execution_id if execution_id else datetime.now().strftime("%Y%m%d_%H%M%S")
            }
            print(f"[DEBUG] Retrieved metadata from execution_results: {metadata}")
        
        print(f"[DEBUG] Retrieved metadata: {metadata}")
        target_table = metadata.get("target_table", "DataValidation")
        source_table = metadata.get("source_table", "")
        timestamp = metadata.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        # Clean table name for filename (remove special chars, spaces)
        clean_target = target_table.replace(' ', '_').replace(',', '').replace('.', '_').replace('(', '').replace(')', '').replace('/', '_')
        
        # Create filename with target table name
        filename = f"ETL_Validation_Report_{clean_target}_{timestamp}.xlsx"
        
        print(f"[DEBUG] Generated filename: {filename}")
        
        # IMPORTANT: Prevent browser caching with cache-control headers
        # This ensures the browser always downloads the fresh Excel file
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    raise HTTPException(status_code=404, detail="Excel report not found")


@app.get("/api/download/excel")
def download_excel_default():
    """Download Excel report (default)"""
    return download_excel(None)


@app.get("/api/download/csv/{csv_type}")
def download_csv(csv_type: str):
    """Download CSV files (matched, source_only, target_only)"""
    csv_files = {
        "matched": "matched_rows.csv",
        "source_only": "source_only_rows.csv",
        "target_only": "target_only_rows.csv"
    }
    
    if csv_type not in csv_files:
        raise HTTPException(status_code=400, detail="Invalid CSV type")
    
    csv_path = os.path.join(LOGS_PATH, csv_files[csv_type])
    
    if os.path.exists(csv_path):
        return FileResponse(
            path=csv_path,
            media_type="text/csv",
            filename=csv_files[csv_type],
            headers={"Cache-Control": "no-cache"}
        )
    raise HTTPException(status_code=404, detail=f"{csv_type} CSV file not found")


@app.get("/api/dashboard/{execution_id}")
def get_dashboard(execution_id: str = None):
    """Get HTML dashboard"""
    file_path = os.path.join(REPORT_PATH, "etl_dashboard.html")

    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            return HTMLResponse(
                content=content,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
            )
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/api/dashboard")
def get_dashboard_default():
    """Get HTML dashboard (default)"""
    return get_dashboard(None)


@app.get("/api/logs/{log_type}")
def get_logs(log_type: str):
    """Get log files"""
    log_files = {
        "etl": "etl_log.txt",
        "duplicates": "duplicate_combined_log.txt",
        "mismatches": "row_data_mismatch_log.txt"
    }
    
    if log_type not in log_files:
        raise HTTPException(status_code=400, detail="Invalid log type")
    
    log_path = os.path.join(LOGS_PATH, log_files[log_type])
    
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            content = f.read()
            return {"log_type": log_type, "content": content if content.strip() else "Log file is empty"}
    
    return {"log_type": log_type, "content": "Log file not found"}


@app.delete("/api/logs/{log_type}")
def clear_log(log_type: str):
    """Clear specific log file"""
    log_files = {
        "etl": "etl_log.txt",
        "duplicates": "duplicate_combined_log.txt",
        "mismatches": "row_data_mismatch_log.txt"
    }
    
    if log_type not in log_files:
        raise HTTPException(status_code=400, detail="Invalid log type")
    
    log_path = os.path.join(LOGS_PATH, log_files[log_type])
    
    try:
        if os.path.exists(log_path):
            # Clear the file by opening in write mode
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('')
            return {"message": f"{log_type.capitalize()} log cleared successfully", "log_type": log_type}
        else:
            return {"message": f"{log_type.capitalize()} log file not found (nothing to clear)", "log_type": log_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear log: {str(e)}")


@app.get("/api/logs")
def get_all_logs_endpoint():
    """Get all log files"""
    return {"logs": get_all_logs()}


@app.get("/api/pipeline-logs")
def get_pipeline_logs(page: int = 1, page_size: int = 10, project_id: Optional[str] = None):
    """Get pipeline execution logs with pagination and optional project filtering"""
    # Filter by project if specified
    filtered_logs = pipeline_execution_logs
    if project_id:
        filtered_logs = [log for log in pipeline_execution_logs if log.get("project_id") == project_id]
    
    # Sort by most recent first
    sorted_logs = sorted(filtered_logs, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Reassign IDs in descending order (newest = 1)
    for idx, log in enumerate(sorted_logs):
        log["id"] = idx + 1
    
    # Calculate pagination
    total_logs = len(sorted_logs)
    total_pages = (total_logs + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_logs = sorted_logs[start_idx:end_idx]
    
    return {
        "logs": paginated_logs,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_logs": total_logs,
            "total_pages": total_pages
        }
    }


@app.get("/api/pipeline-logs/export")
def export_pipeline_logs():
    """Export pipeline logs to Excel"""
    if not pipeline_execution_logs:
        raise HTTPException(status_code=404, detail="No logs available to export")
    
    # Create DataFrame from logs
    df = pd.DataFrame(pipeline_execution_logs)
    
    # Reorder columns for better readability
    columns_order = ["id", "pipeline_name", "table_name", "status", "error_name", 
                    "log_content", "start_date", "end_date", "execution_time", "user_name", "timestamp"]
    df = df[[col for col in columns_order if col in df.columns]]
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Pipeline Logs', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Pipeline Logs']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    output.seek(0)
    
    filename = f"pipeline_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.delete("/api/pipeline-logs")
def clear_pipeline_logs():
    """Clear all pipeline execution logs"""
    global pipeline_execution_logs
    count = len(pipeline_execution_logs)
    pipeline_execution_logs = []
    save_pipeline_logs()  # Persist the cleared state
    return {"message": f"Successfully cleared {count} log entries", "cleared_count": count}


@app.post("/api/pipeline-logs/delete-selected")
def delete_selected_pipeline_logs(request: dict):
    """Delete selected pipeline logs by IDs"""
    global pipeline_execution_logs
    log_ids = request.get('log_ids', [])
    
    if not log_ids:
        # If no IDs provided, clear all
        count = len(pipeline_execution_logs)
        pipeline_execution_logs = []
        save_pipeline_logs()
        return {"message": f"Successfully cleared all {count} log entries", "cleared_count": count}
    
    # Filter out logs with IDs in the list
    initial_count = len(pipeline_execution_logs)
    pipeline_execution_logs = [log for log in pipeline_execution_logs if log['id'] not in log_ids]
    cleared_count = initial_count - len(pipeline_execution_logs)
    
    save_pipeline_logs()
    return {"message": f"Successfully cleared {cleared_count} log entries", "cleared_count": cleared_count}


@app.post("/api/log-cancellation")
def log_cancellation(request: dict):
    """Log a cancelled validation to pipeline logs"""
    try:
        pipeline_name = request.get('pipeline_name', 'ETL Validation')
        table_name = request.get('table_name', 'Unknown')
        start_date = request.get('start_date')
        end_date = request.get('end_date')
        execution_time = request.get('execution_time', '0s')
        source_table = request.get('source_table', '')
        target_table = request.get('target_table', '')
        project_id = request.get('project_id')
        
        # Build log content
        log_content = f"Validation cancelled by user. Source: {source_table}, Target: {target_table}"
        
        # Log the cancellation
        log_entry = log_pipeline_execution(
            pipeline_name=pipeline_name,
            table_name=table_name,
            status='CANCELLED',
            start_date=start_date,
            end_date=end_date,
            execution_time=execution_time,
            error_name='Cancelled by user',
            log_content=log_content,
            project_id=project_id
        )
        
        return {
            "status": "success",
            "message": "Cancellation logged successfully",
            "log_entry": log_entry
        }
    except Exception as e:
        print(f"[ERROR] Failed to log cancellation: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/api/results/{execution_id}")
def get_results(execution_id: str):
    """Get execution results"""
    if execution_id in execution_results:
        return execution_results[execution_id]
    raise HTTPException(status_code=404, detail="Execution not found")


@app.get("/api/results")
def get_latest_results():
    """Get latest execution results"""
    if validation_outputs:
        latest_id = max(validation_outputs.keys())
        return validation_outputs[latest_id]
    return {"message": "No results available"}


@app.get("/api/history")
def get_execution_history(project_id: Optional[str] = None):
    """Get execution history, optionally filtered by project"""
    executions = list(execution_results.values())
    
    # Filter by project_id if specified
    if project_id:
        executions = [e for e in executions if e.get('project_id') == project_id]
    
    return {"executions": executions}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
