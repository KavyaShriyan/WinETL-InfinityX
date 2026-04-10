# WinETL InfinityX - Enterprise ETL Validation Framework
## Complete Technical Documentation & Deployment Guide

**Version:** 8.0  
**Framework Name:** WinETL InfinityX  
**Type:** Enterprise ETL Validation & Data Reconciliation Engine  
**Last Updated:** April 8, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Frontend Technology Stack](#frontend-technology-stack)
4. [Backend Technology Stack](#backend-technology-stack)
5. [Features](#features)
6. [System Requirements](#system-requirements)
7. [Installation & Setup](#installation--setup)
8. [Deployment Guide](#deployment-guide)
9. [Configuration](#configuration)
10. [API Documentation](#api-documentation)
11. [Database Support](#database-support)
12. [Publishing Checklist](#publishing-checklist)
13. [Security Considerations](#security-considerations)
14. [Performance Optimization](#performance-optimization)
15. [Troubleshooting](#troubleshooting)

---

## Overview

WinETL InfinityX is a comprehensive enterprise-grade ETL (Extract, Transform, Load) validation and data reconciliation framework designed to validate data integrity across multiple database platforms and file formats.

### Key Capabilities

- **Multi-User Authentication:** Complete login/signup system with Role-Based Access Control (RBAC)
- **Role-Based Access:** Admin, Contributor, and User roles with group-based data filtering
- **Multi-Database Support:** SQL Server, Azure Synapse, MySQL, PostgreSQL, Oracle, MongoDB, Databricks, Cassandra
- **Cloud Platform Integration:** Azure, AWS S3, Google Cloud Storage
- **File Format Support:** CSV, JSON, Excel, Parquet
- **Validation Types:**
  - Structure/Schema validation
  - Record count comparison
  - NULL constraint checks
  - Duplicate detection
  - Row-wise data comparison
  - Data type validation
- **Medallion Architecture:** Bronze/Silver/Gold layer validation for Microsoft Fabric
- **Real-time Execution:** Live validation with progress tracking
- **Comprehensive Reporting:** Excel reports and HTML dashboards
- **Project Management:** Multi-project support with context switching and group-based access control

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Browser                            │
│              (Single-Page Application)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 FastAPI Backend                              │
│              (Python 3.8+)                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  API Layer (api.py)                                 │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐    │
│  │  Validation Engine (validate.py)                     │    │
│  │  - Structure validation                              │    │
│  │  - Count validation                                  │    │
│  │  - Null checks                                       │    │
│  │  - Duplicate detection                               │    │
│  │  - Row-wise comparison                               │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐    │
│  │  Database Connector Factory (db_config.py)          │    │
│  │  - Multi-database support                            │    │
│  │  - Connection pooling                                │    │
│  │  - Authentication handlers                           │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────┐    │
│  │  Report Generator (report_generator.py)             │    │
│  │  - Excel reports with openpyxl                       │    │
│  │  - HTML dashboards                                   │    │
│  │  - Data visualization                                │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
┌────▼────┐      ┌────▼────┐      ┌────▼────┐
│ Source  │      │ Target  │      │  File   │
│   DB    │      │   DB    │      │ Storage │
└─────────┘      └─────────┘      └─────────┘
```

### Component Breakdown

1. **Frontend (SPA)**
   - Single HTML file with embedded CSS and JavaScript
   - Client-side routing and state management
   - Real-time API communication
   - Responsive UI with modern design

2. **Backend (FastAPI)**
   - RESTful API endpoints
   - Async request handling
   - CORS enabled for cross-origin requests
   - Built-in API documentation (Swagger/OpenAPI)

3. **Validation Engine**
   - PyTest-based validation framework
   - Modular validation functions
   - Configurable validation rules
   - Sampling support for large datasets

4. **Database Layer**
   - Factory pattern for database connections
   - Support for 10+ database types
   - Connection string management
   - OAuth 2.0 support for Azure/Databricks

5. **Reporting Layer**
   - Excel export with formatting and styling
   - HTML dashboard generation
   - Log file management
   - Execution history tracking

---

## Frontend Technology Stack

### Core Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **HTML5** | - | Semantic markup structure |
| **CSS3** | - | Styling with custom properties |
| **JavaScript (ES6+)** | - | Application logic and interactivity |
| **Fetch API** | Native | HTTP requests to backend |
| **LocalStorage API** | Native | Client-side data persistence |
| **Font Awesome** | 6.4.0 | Icon library (CDN) |
| **Google Fonts** | - | Inter font family |

### Frontend Architecture

```javascript
// Main Components
- Single-Page Application (SPA) architecture
- ~14,242 lines of code in single file
- No framework dependencies (Vanilla JS)
- Event-driven architecture
- Component-based modular functions

// Key Modules
1. Project Management
2. Database Connection Management
3. Query Builder & Table Selection
4. Validation Execution Engine
5. Real-time Progress Tracking
6. Dashboard & Reporting
7. History Management
8. File Upload Handler
```

### Frontend Features

- **Responsive Design:** Mobile-friendly with flexbox/grid layout
- **Dark/Light Theme:** Custom CSS variables for theming
- **Animations:** CSS keyframe animations for smooth transitions
- **Form Validation:** Client-side validation before API calls
- **Toast Notifications:** Real-time feedback to users
- **Modal Dialogs:** Dynamic modal creation
- **Progress Indicators:** Real-time validation progress
- **Tab Navigation:** Multi-section navigation system
- **Auto-save:** LocalStorage for user preferences

### Frontend File Structure

```
frontend/
├── index.html          # ~14,242 lines (Main Dashboard - HTML + CSS + JS)
├── login.html          # Professional Azure-style login page
├── signup.html         # User registration page with OTP verification
├── admin.html          # Admin dashboard for user management
├── assets/
│   ├── etl-hero-banner.jpg
│   └── auth.js         # Authentication module (session management, validation)
```

### Authentication Flow

```
1. User visits http://localhost:8000
2. auth.js checks for sessionToken in localStorage
3. If no token → redirect to login.html
4. If token exists → validate with backend
5. If valid → load user context (name, role, group) in header
6. If invalid → redirect to login.html
7. User data filters all dashboard views by assigned groups
```

---

```javascript
const API_BASE = 'http://localhost:8000';

// Example: Execute Validation
async function executeValidation(payload) {
    const response = await fetch(`${API_BASE}/api/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    return await response.json();
}

// Example: Download Excel Report
function downloadExcelReport(executionId) {
    window.location.href = `${API_BASE}/api/download/excel/${executionId}`;
}
```

---

## Backend Technology Stack

### Core Framework

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | FastAPI | ≥0.104.0 | High-performance async web framework |
| **ASGI Server** | Uvicorn | ≥0.24.0 | Production-grade ASGI server |
| **Data Validation** | Pydantic | ≥2.0.0 | Request/response validation |
| **File Handling** | python-multipart | ≥0.0.6 | Multipart form data support |
| **Testing** | PyTest | ≥7.4.0 | Unit and integration testing |

### Database Connectors

| Database | Driver | Version | Notes |
|----------|--------|---------|-------|
| **SQL Server / Azure Synapse** | pyodbc | ≥4.0.39 | ODBC Driver 17/18 for SQL Server |
| **MySQL** | pymysql | ≥1.1.0 | Pure Python MySQL client |
| **PostgreSQL** | psycopg2 | ≥2.9.0 | PostgreSQL adapter |
| **Oracle** | oracledb | ≥1.4.0 | Python-oracledb (thin mode) |
| **MongoDB** | pymongo | ≥4.6.0 | Official MongoDB driver |
| **Cassandra** | cassandra-driver | ≥3.29.0 | DataStax Cassandra driver |
| **Databricks** | databricks-sql-connector | ≥3.0.0 | Official Databricks connector |

### Cloud Storage Support

| Platform | Library | Version |
|----------|---------|---------|
| **AWS S3** | boto3 | ≥1.34.0 |
| **Azure Blob** | azure-storage-blob | ≥12.19.0 |
| **Google Cloud** | google-cloud-storage | ≥2.14.0 |

### Data Processing

| Library | Version | Purpose |
|---------|---------|---------|
| **pandas** | ≥2.0.0 | Data manipulation and analysis |
| **openpyxl** | ≥3.1.0 | Excel file creation and styling |
| **pyarrow** | ≥14.0.0 | Parquet file support |

### Utilities

| Library | Version | Purpose |
|---------|---------|---------|
| **requests** | ≥2.31.0 | HTTP client for external APIs |
| **python-dotenv** | ≥1.0.0 | Environment variable management |

### Backend File Structure

```
backend/
├── api.py                      # FastAPI application and routes
├── auth.py                     # Authentication service (login, signup, RBAC, session management)
├── users.xlsx                  # Excel-based user database (email, hash, role, group)
├── requirements.txt            # Python dependencies
└── __pycache__/               # Compiled Python files

DataValidation/
├── main.py                     # Main ETL pipeline orchestrator
├── pytest.ini                  # PyTest configuration
├── requirements.txt            # Validation framework dependencies
├── config/
│   ├── db_config.py           # Database connection factory
│   ├── data_sources.json      # Connection configurations
│   ├── validation_rules.json  # Automated validation rules
│   ├── secrets.py             # Credentials management
│   └── fabric_medallion_example.json
├── src/
│   ├── validate.py            # Core validation functions
│   ├── advanced_validate.py   # Advanced validation logic
│   ├── extract.py             # Data extraction module
│   ├── transform.py           # Data transformation module
│   ├── load.py                # Data loading module
│   ├── report_generator.py    # Report generation
│   └── automation.py          # Validation automation
├── tests/
│   ├── conftest.py            # PyTest fixtures
│   ├── test_validate.py       # Validation tests
│   ├── test_extract.py        # Extraction tests
│   ├── test_transform.py      # Transformation tests
│   └── test_main.py           # Integration tests
├── logs/                      # Execution logs
├── reports/                   # Generated reports
├── uploads/                   # Uploaded files
└── test_data/                 # Test datasets
```

### Authentication API Endpoints

```python
# User Authentication
POST   /api/auth/signup          # Register new user with OTP verification
POST   /api/auth/login           # Authenticate user and create session
POST   /api/auth/logout          # Destroy user session
GET    /api/auth/validate        # Validate session token and refresh user data

# OTP Verification
POST   /api/auth/request-otp     # Generate and send OTP
POST   /api/auth/verify-otp      # Verify OTP code

# Admin Operations
GET    /api/admin/users          # Get all users (Admin only)
POST   /api/admin/update-role    # Update user role/group (Admin only)
DELETE /api/admin/delete-user    # Delete user (Admin only)
POST   /api/admin/toggle-status  # Activate/deactivate user (Admin only)
```

---

## Features

### 1. Database Connectivity

**Supported Databases:**
- Microsoft SQL Server
- Azure Synapse Analytics
- Microsoft Fabric (Medallion Architecture)
- MySQL
- PostgreSQL
- Oracle
- MongoDB
- Cassandra
- Databricks SQL Warehouse

**Authentication Methods:**
- Windows Authentication
- SQL Authentication
- Azure Active Directory (OAuth 2.0)
- Azure AD Interactive (MFA)
- Token-based authentication
- Databricks Personal Access Token

### 2. Validation Types

#### Structure Validation
- Column name comparison
- Data type validation
- Nullable constraint checks
- Primary key validation
- Schema mismatch detection

#### Record Count Validation
- Source vs. Target count comparison
- Variance threshold support
- Percentage difference calculation

#### NULL Constraint Check
- NOT NULL constraint validation
- Primary key NULL detection
- Violation reporting

#### Duplicate Detection
- Primary key-based duplicate detection
- Composite key support
- Duplicate record logging

#### Row-wise Data Validation
- Complete data comparison
- Column-level mismatch detection
- Similarity matching for date/time differences
- Intelligent pairing with fuzzy matching
- Support for sampling (e.g., first 100 rows, random sample)

### 3. File-based Validation

**Supported Formats:**
- CSV files
- JSON files
- Excel files (.xlsx, .xls)
- Parquet files

**Validation Scenarios:**
- File to Database
- Database to File
- File to File
- Multi-source comparison

### 4. Reporting

**Excel Reports:**
- Executive summary sheet
- Mismatch records with source/target comparison
- Matched records
- Structure validation details
- Record count comparison
- Null check results
- Duplicate detection results
- Professional styling with color-coding
- Auto-column width adjustment
- Cell highlighting for mismatches

**HTML Dashboards:**
- Interactive data tables
- Visual charts and metrics
- Source/target comparison view
- Drill-down capabilities
- Responsive design

**Logs:**
- ETL execution logs
- Duplicate logs
- Row mismatch logs
- Pipeline execution history

### 5. Project Management

- Multi-project workspace support
- Project context switching
- Connection templates per project
- Query history per project
- Validation history filtering

### 6. Authentication & Multi-User Management

**Complete Role-Based Access Control (RBAC) System:**

#### User Authentication
- **Login/Signup System:** Professional Azure-style login page with signup workflow
- **Session Management:** Secure 8-hour session tokens with auto-refresh from user database
- **Password Security:** SHA-256 password hashing
- **Remember Me:** Optional persistent login
- **Excel-based User Database:** users.xlsx with comprehensive user profile management

#### User Roles & Permissions
- **Admin:** Full system access to all projects, accounts, and products; user management capabilities
- **Contributor:** Create new projects and work on assigned groups; projects auto-assign to user's groups
- **User:** Work on assigned projects only; view-only access to group-specific data

#### Group-Based Access Control
- **Dynamic Groups:** Groups are automatically generated from actual project/account names
- **Auto-Assignment:** When Contributors create projects, groups are automatically assigned and added to their profile
- **Session Refresh:** User groups and roles refresh from database on every session validation
- **Filtering:** All data displays (validation history, dashboard, logs, query history) filter by user's assigned groups
- **Blank State Enforcement:** Non-Admin users see "No Project Selected" message when no project context is active

#### Admin Dashboard
- **User Management:** View, search, filter, and manage all registered users
- **Role Assignment:** Assign or update user roles and groups
- **User Statistics:** Monitor total users, active users, and pending approvals
- **Activity Tracking:** Track user creation dates and last login times
- **Account Status:** Activate or deactivate user accounts

#### Default Admin Credentials
```
Email: nilanchal.tripathy@winwire.com
Password: Admin@123
Role: Admin
Group: All
```

#### Authentication Features
- **Multi-factor Ready:** OTP verification system for signup (mobile verification)
- **Duplicate Prevention:** Prevents duplicate email/user ID registration
- **Session Validation:** Backend validates and refreshes user data on every API call
- **Logout:** Secure session destruction
- **Auto-redirect:** Already-logged-in users auto-redirect to dashboard

### 7. Advanced Features

- **Sampling:** Validate subsets of data (first N, last N, random)
- **Real-time Progress:** Live progress updates during validation
- **Abort Capability:** Cancel long-running validations
- **Connection Caching:** Save and reuse connection configurations
- **Query Templates:** Save frequently used queries
- **OAuth Auto-close:** Automatic browser window closure after OAuth
- **Azure Integration:** Full Azure Synapse and Fabric support

---

## System Requirements

### Server Requirements

**Minimum:**
- **OS:** Windows Server 2016+, Linux (Ubuntu 18.04+), macOS 10.15+
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disk:** 10 GB free space
- **Python:** 3.8 or higher

**Recommended:**
- **OS:** Windows Server 2019+, Linux (Ubuntu 20.04+)
- **CPU:** 4+ cores
- **RAM:** 8 GB+
- **Disk:** 50 GB+ SSD
- **Python:** 3.10 or higher

### Client Requirements

**Web Browser (any modern browser):**
- Google Chrome 90+
- Microsoft Edge 90+
- Firefox 88+
- Safari 14+

**Internet Connection:**
- Required for CDN resources (Font Awesome, Google Fonts)
- Can be made offline by downloading CDN resources locally

### Database Requirements

**ODBC Drivers (for SQL Server/Azure):**
- ODBC Driver 17 for SQL Server (minimum)
- ODBC Driver 18 for SQL Server (recommended)

**Database Client Libraries:**
- Install based on target databases (see Backend Technology Stack)

### Network Requirements

- **Outbound:** Access to target databases (various ports)
- **Inbound:** Port 8000 for web interface
- **Firewall:** Allow Python and Uvicorn through firewall

---

## Installation & Setup

### Step 1: Install Python

```bash
# Windows (via Chocolatey)
choco install python --version=3.10

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3.10 python3-pip

# macOS (via Homebrew)
brew install python@3.10
```

### Step 2: Clone/Extract Framework

```bash
cd "d:\OneDrive - WinWire\Documents\ETL Framework"
cd ETL_DEMO_Pytest_V8\ETL_DEMO_Pytest14
```

### Step 3: Create Virtual Environment

```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4: Install Backend Dependencies

```bash
# Install backend packages
pip install -r backend/requirements.txt

# Install validation framework packages
pip install -r DataValidation/requirements.txt
```

### Step 5: Install Database Drivers

**For SQL Server/Azure Synapse:**

Windows:
```bash
# Download ODBC Driver 18 from Microsoft
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

Linux:
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

**For Oracle:**
```bash
# Download Oracle Instant Client
# https://www.oracle.com/database/technologies/instant-client.html
```

### Step 6: Configure Environment

Create `.env` file in `backend/` directory:

```ini
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Database Credentials (Optional - can be stored in secrets.py)
DEFAULT_DB_SERVER=your-server.database.windows.net
DEFAULT_DB_NAME=YourDatabase
DEFAULT_DB_USERNAME=your-username

# Azure Configuration (for OAuth)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id

# Logging
LOG_LEVEL=INFO
```

### Step 7: Configure Database Connections

Edit `DataValidation/config/secrets.py`:

```python
# Database connection secrets
SECRETS = {
    "sql_server": {
        "server": "your-server.database.windows.net",
        "database": "YourDatabase",
        "username": "your-username",
        "password": "your-password"  # Use Azure Key Vault in production
    },
    "azure_synapse": {
        "server": "your-synapse.sql.azuresynapse.net",
        "database": "YourDW",
        "authentication": "ActiveDirectoryInteractive"
    }
}
```

### Step 8: Set Up User Authentication

**Default Admin User:**

The framework comes with a pre-configured admin user in `backend/users.xlsx`:

```
Email: nilanchal.tripathy@winwire.com
Password: Admin@123
Role: Admin
Group: All
```

**⚠️ IMPORTANT for Production:**
1. Change the default admin password immediately after first login
2. Or delete the default admin row and create a new admin user via signup

**User Database Structure:**

The `users.xlsx` file contains the following columns:
- **Email:** User's email address (unique identifier)
- **UserID:** Optional user ID (can be used for login)
- **UserName:** Full name of user
- **PasswordHash:** SHA-256 hashed password (never store plain text)
- **MobileNumber:** Phone number for OTP verification
- **Role:** Admin, Contributor, or User
- **Group:** Comma-separated list of project/account groups (e.g., "Peets,CHOP,HPE")
- **IsActive:** TRUE or FALSE
- **CreatedDate:** Timestamp of account creation
- **LastLogin:** Timestamp of last successful login

**User Roles Explained:**
- **Admin:** 
  - Full access to all projects, accounts, and products
  - Can manage users via Admin Dashboard
  - Can assign roles and groups to other users
  - Group must be set to "All"

- **Contributor:**
  - Can create new projects and accounts
  - Automatically assigned to groups when creating projects
  - Can work on projects in their assigned groups only
  - Group field contains comma-separated list (e.g., "ProjectA,ProjectB")

- **User:**
  - Can only view and work on assigned projects
  - Cannot create new projects
  - Limited to single or multiple assigned groups

**Adding New Users:**

Option 1 - Via Signup Page:
1. Users visit `http://localhost:8000/signup.html`
2. Complete signup with OTP verification
3. Admin assigns role and group via Admin Dashboard

Option 2 - Manual Excel Entry:
1. Open `backend/users.xlsx`
2. Add new row with user details
3. Use SHA-256 hash for password (or let user reset via UI)
4. Set role and group appropriately
5. Save file

**Session Management:**
- Sessions expire after 8 hours of inactivity
- Session tokens stored in browser localStorage
- Backend validates and refreshes user data from Excel on every API call
- Users can enable "Remember Me" for persistent login

### Step 9: Run the Application

**Option 1: Using batch file (Windows)**
```bash
.\run_server.bat
```

**Option 2: Manual start**
```bash
cd backend
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: With custom configuration**
```bash
cd backend
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

### Step 10: Access the Application

Open your web browser and navigate to:
- **Login Page:** http://localhost:8000 (auto-redirects to login.html)
- **Web Dashboard:** http://localhost:8000/index.html (after login)
- **Admin Dashboard:** http://localhost:8000/admin.html (Admin role only)
- **API Documentation:** http://localhost:8000/docs
- **API Redoc:** http://localhost:8000/redoc

**First-Time Setup:**
1. Navigate to http://localhost:8000
2. Login with default admin credentials
3. Click "Admin" button in top-right corner
4. Review and approve any pending user signups
5. Assign appropriate roles and groups to users
6. Change default admin password (recommended)

---

## Deployment Guide

### Production Deployment Options

#### Option 1: Windows Server with IIS

1. **Install IIS and required components**
2. **Install HTTP Platform Handler**
3. **Configure web.config:**

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified"/>
    </handlers>
    <httpPlatform processPath="D:\path\to\.venv\Scripts\python.exe"
                  arguments="-m uvicorn api:app --host 0.0.0.0 --port %HTTP_PLATFORM_PORT%"
                  startupTimeLimit="60"
                  startupRetryCount="3"
                  stdoutLogEnabled="true"
                  stdoutLogFile=".\logs\stdout.log">
      <environmentVariables>
        <environmentVariable name="PYTHONPATH" value="D:\path\to\backend" />
      </environmentVariables>
    </httpPlatform>
  </system.webServer>
</configuration>
```

4. **Create IIS website pointing to backend folder**

#### Option 2: Linux with Nginx + Gunicorn

1. **Install Nginx:**
```bash
sudo apt install nginx
```

2. **Create systemd service file** (`/etc/systemd/system/etl-framework.service`):
```ini
[Unit]
Description=ETL Validation Framework
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/etl-framework/backend
Environment="PATH=/opt/etl-framework/.venv/bin"
ExecStart=/opt/etl-framework/.venv/bin/gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

3. **Configure Nginx** (`/etc/nginx/sites-available/etl-framework`):
```nginx
server {
    listen 80;
    server_name etl.yourcompany.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    location /api/run {
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 1800s;  # 30 minutes for long validations
        proxy_connect_timeout 75s;
    }
}
```

4. **Start services:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable etl-framework
sudo systemctl start etl-framework
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### Option 3: Docker Container

1. **Create Dockerfile:**

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Set working directory
WORKDIR /app

# Copy application files
COPY backend/ ./backend/
COPY DataValidation/ ./DataValidation/
COPY frontend/ ./frontend/

# Install Python dependencies
COPY backend/requirements.txt ./backend/
COPY DataValidation/requirements.txt ./DataValidation/
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r DataValidation/requirements.txt

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  etl-framework:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - LOG_LEVEL=INFO
    volumes:
      - ./DataValidation/logs:/app/DataValidation/logs
      - ./DataValidation/reports:/app/DataValidation/reports
    restart: unless-stopped
```

3. **Build and run:**
```bash
docker-compose up -d
```

#### Option 4: Azure App Service

1. **Prepare for deployment:**
```bash
# Create requirements.txt in root
cat backend/requirements.txt DataValidation/requirements.txt > requirements.txt

# Create startup script (startup.sh)
#!/bin/bash
cd /home/site/wwwroot/backend
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

2. **Deploy via Azure CLI:**
```bash
az webapp up --name etl-framework --resource-group YourResourceGroup --runtime PYTHON:3.10
```

3. **Configure App Service:**
- Set startup command: `startup.sh`
- Add application settings for environment variables
- Enable CORS if needed

#### Option 5: AWS Elastic Beanstalk

1. **Create Procfile:**
```
web: cd backend && uvicorn api:app --host 0.0.0.0 --port 8000
```

2. **Create .ebextensions/python.config:**
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: backend.api:app
```

3. **Deploy:**
```bash
eb init -p python-3.10 etl-framework
eb create etl-framework-prod
eb deploy
```

---

## Configuration

### Database Configuration

Edit `DataValidation/config/data_sources.json`:

```json
{
  "connections": [
    {
      "name": "Production SQL Server",
      "type": "sqlserver",
      "server": "prod-server.database.windows.net",
      "database": "ProductionDB",
      "authentication": "ActiveDirectoryMfa",
      "username": "admin@company.com"
    },
    {
      "name": "Databricks Warehouse",
      "type": "databricks",
      "workspace_url": "https://adb-xxxxx.azuredatabricks.net",
      "http_path": "/sql/1.0/warehouses/xxxxx",
      "catalog": "prod_catalog",
      "schema": "analytics",
      "auth_type": "azure_ad_interactive"
    }
  ]
}
```

### Validation Rules

Edit `DataValidation/config/validation_rules.json`:

```json
{
  "default_rules": {
    "enable_structure_validation": true,
    "enable_count_validation": true,
    "enable_null_check": true,
    "enable_duplicate_check": true,
    "enable_row_data_validation": true,
    "count_variance_threshold": 0.01,
    "sample_size": "all"
  },
  "table_specific_rules": {
    "DimCustomer": {
      "sample_size": 1000,
      "primary_key": ["CustomerID"],
      "ignore_columns": ["LastModifiedDate"]
    }
  }
}
```

### Logging Configuration

Edit `DataValidation/pytest.ini`:

```ini
[pytest]
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

log_file = logs/pytest.log
log_file_level = DEBUG
log_file_format = %(asctime)s [%(levelname)8s] %(name)s - %(message)s
log_file_date_format = %Y-%m-%d %H:%M:%S
```

---

## API Documentation

### Core Endpoints

#### Health Check
```
GET /
Response: {"status": "healthy", "message": "ETL Validation API is running", "version": "8.0"}
```

#### Execute Validation
```
POST /api/run
Content-Type: application/json

Request Body:
{
  "source_db_config": {
    "type": "default",
    "server": "server.database.windows.net",
    "database": "SourceDB",
    "authType": "ActiveDirectoryMfa",
    "username": "user@company.com"
  },
  "target_db_config": {
    "type": "databricks",
    "workspace_url": "https://adb-xxxxx.azuredatabricks.net",
    "http_path": "/sql/1.0/warehouses/xxxxx",
    "catalog": "target_catalog",
    "schema": "target_schema"
  },
  "source_table": "dbo.SourceTable",
  "target_table": "target_table",
  "source_query": "SELECT * FROM dbo.SourceTable",
  "target_query": "SELECT * FROM target_table",
  "validations": ["structure", "count", "null", "duplicate", "data"],
  "sample_size": "all",
  "project_context": {
    "id": "project_123",
    "name": "Data Migration Project"
  }
}

Response: 200 OK
{
  "status": "success",
  "execution_id": "20260408_153517",
  "results": { ... },
  "metadata": { ... }
}
```

#### Download Excel Report
```
GET /api/download/excel/{execution_id}
Response: Excel file download
```

#### Download HTML Dashboard
```
GET /api/download/dashboard/{execution_id}
Response: HTML file download
```

#### Get Logs
```
GET /api/logs/etl
GET /api/logs/duplicate
GET /api/logs/mismatch
Response: 200 OK with log content
```

#### List Tables
```
POST /api/tables
Content-Type: application/json

Request Body:
{
  "db_config": { ... }
}

Response: 200 OK
{
  "tables": ["schema1.table1", "schema2.table2", ...]
}
```

#### Project Management
```
GET /api/projects
Response: {"projects": [...], "accounts": [...], "products": [...]}

POST /api/projects
Request Body: {"type": "project", "name": "New Project"}
Response: 201 Created

DELETE /api/projects/{project_id}
Response: 200 OK
```

---

## Database Support

### Connection String Examples

**SQL Server (Windows Auth):**
```
DRIVER={ODBC Driver 18 for SQL Server};SERVER=server.domain.com;DATABASE=DB1;Trusted_Connection=yes;Encrypt=yes
```

**SQL Server (SQL Auth):**
```
DRIVER={ODBC Driver 18 for SQL Server};SERVER=server.domain.com;DATABASE=DB1;UID=username;PWD=password;Encrypt=yes
```

**Azure SQL / Synapse (Azure AD Interactive):**
```
DRIVER={ODBC Driver 18 for SQL Server};SERVER=server.database.windows.net;DATABASE=DB1;Authentication=ActiveDirectoryInteractive;UID=user@company.com;Encrypt=yes
```

**Databricks:**
```python
connection = sql.connect(
    server_hostname="adb-xxxxx.azuredatabricks.net",
    http_path="/sql/1.0/warehouses/xxxxx",
    access_token="dapi..."  # Or use Azure AD auth
)
```

**MySQL:**
```python
connection = pymysql.connect(
    host='mysql.server.com',
    user='username',
    password='password',
    database='db_name',
    port=3306
)
```

**PostgreSQL:**
```python
connection = psycopg2.connect(
    host='postgres.server.com',
    database='db_name',
    user='username',
    password='password',
    port=5432
)
```

**MongoDB:**
```python
client = pymongo.MongoClient('mongodb://username:password@mongodb.server.com:27017/')
```

---

## Publishing Checklist

### Pre-Deployment Checklist

- [ ] **Code Review**
  - [ ] Remove all hardcoded credentials
  - [ ] Remove debug print statements
  - [ ] Update version numbers
  - [ ] Check for TODO/FIXME comments

- [ ] **Security**
  - [ ] Implement proper authentication/authorization
  - [ ] Use environment variables for secrets
  - [ ] Enable HTTPS/SSL
  - [ ] Implement rate limiting
  - [ ] Add CORS configuration
  - [ ] Sanitize user inputs
  - [ ] Implement SQL injection prevention

- [ ] **Configuration**
  - [ ] Update API_BASE URL in frontend
  - [ ] Configure production database connections
  - [ ] Set up logging to proper location
  - [ ] Configure file upload limits
  - [ ] Set appropriate timeouts

- [ ] **Testing**
  - [ ] Run all unit tests (`pytest`)
  - [ ] Test all database connections
  - [ ] Test end-to-end validation workflows
  - [ ] Load testing with large datasets
  - [ ] Cross-browser testing
  - [ ] Mobile responsiveness testing

- [ ] **Documentation**
  - [ ] User guide / manual
  - [ ] API documentation
  - [ ] Database connection guide
  - [ ] Troubleshooting guide
  - [ ] Admin guide

- [ ] **Performance**
  - [ ] Optimize database queries
  - [ ] Implement connection pooling
  - [ ] Enable caching where appropriate
  - [ ] Optimize Excel generation for large datasets
  - [ ] Configure appropriate workers/threads

- [ ] **Monitoring**
  - [ ] Set up application logging
  - [ ] Configure log rotation
  - [ ] Set up error alerting
  - [ ] Monitor API endpoint response times
  - [ ] Track validation execution times

### Infrastructure Requirements

**Production Server:**
- [ ] Python 3.10+ installed
- [ ] Required ODBC drivers installed
- [ ] Database client libraries installed
- [ ] Sufficient disk space for reports/logs
- [ ] Network access to all target databases
- [ ] Firewall rules configured
- [ ] SSL certificate (for HTTPS)
- [ ] Backup strategy for reports/logs

**Domain & DNS:**
- [ ] Domain name (e.g., etl.company.com)
- [ ] DNS A record configured
- [ ] SSL certificate purchased/configured

**User Access:**
- [ ] User accounts created
- [ ] Permissions configured
- [ ] Training materials prepared

### Deployment Steps

1. **Prepare Production Environment**
   ```bash
   # Create application directory
   sudo mkdir -p /opt/etl-framework
   cd /opt/etl-framework
   
   # Copy application files
   sudo cp -r /path/to/source/* .
   
   # Create virtual environment
   sudo python3.10 -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r backend/requirements.txt
   pip install -r DataValidation/requirements.txt
   ```

2. **Configure Production Settings**
   ```bash
   # Create .env file with production settings
   sudo nano backend/.env
   
   # Set proper permissions
   sudo chmod 600 backend/.env
   sudo chown www-data:www-data backend/.env
   ```

3. **Set Up Reverse Proxy (Nginx/IIS)**
   - Configure as per deployment guide above

4. **Configure Systemd Service** (Linux)
   ```bash
   sudo systemctl enable etl-framework
   sudo systemctl start etl-framework
   sudo systemctl status etl-framework
   ```

5. **Verify Deployment**
   - Access web interface
   - Test database connections
   - Run sample validation
   - Check logs for errors

6. **Set Up Monitoring**
   - Configure log monitoring
   - Set up uptime monitoring
   - Configure alerting

7. **User Training**
   - Conduct training sessions
   - Provide documentation
   - Set up support channel

---

## Security Considerations

### Authentication & Authorization

**Current State:** No built-in authentication  
**Recommendations for Production:**

1. **Implement OAuth 2.0:**
   ```python
   from fastapi import Depends, HTTPException
   from fastapi.security import OAuth2PasswordBearer
   
   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
   
   @app.post("/api/run")
   async def execute_validation(token: str = Depends(oauth2_scheme)):
       # Verify token and proceed
       pass
   ```

2. **Use Azure AD for Enterprise:**
   - Integrate with Microsoft Authentication Library (MSAL)
   - Support single sign-on (SSO)

3. **Implement Role-Based Access Control (RBAC):**
   - Admin: Full access
   - Developer: Run validations, view reports
   - Viewer: View reports only

### Data Security

1. **Encrypt Sensitive Data:**
   - Use Azure Key Vault for secrets
   - Encrypt database passwords
   - Use HTTPS for all communication

2. **Secure Database Connections:**
   - Use encrypted connections (TLS/SSL)
   - Implement connection string encryption
   - Use managed identities where possible

3. **Audit Logging:**
   - Log all user actions
   - Track validation executions
   - Monitor database access

### Code Security

1. **Input Validation:**
   - Sanitize all user inputs
   - Use parameterized queries
   - Validate file uploads

2. **Dependency Management:**
   - Regularly update dependencies
   - Scan for vulnerabilities
   - Use `pip-audit` or Snyk

3. **Secrets Management:**
   - Never commit secrets to version control
   - Use environment variables
   - Implement secret rotation

---

## Performance Optimization

### Backend Optimization

1. **Connection Pooling:**
   ```python
   # Implement connection pool
   from sqlalchemy.pool import QueuePool
   
   pool = QueuePool(create_connection, pool_size=10, max_overflow=20)
   ```

2. **Async Processing:**
   - Use async/await for I/O operations
   - Implement background tasks for long validations
   - Use Celery for distributed processing

3. **Caching:**
   - Cache database schema information
   - Cache frequently accessed data
   - Use Redis for distributed cache

4. **Query Optimization:**
   - Add appropriate indexes
   - Use LIMIT/TOP for sampling
   - Optimize JOIN operations

### Frontend Optimization

1. **Code Splitting:**
   - Split large JavaScript into modules
   - Lazy load non-critical components

2. **Asset Optimization:**
   - Minify JavaScript and CSS
   - Compress images
   - Use CDN for static assets

3. **Caching:**
   - Implement browser caching
   - Use service workers for offline support

### Database Optimization

1. **Indexing:**
   - Create indexes on frequently queried columns
   - Use composite indexes for multi-column queries

2. **Query Optimization:**
   - Use EXPLAIN to analyze queries
   - Avoid SELECT * in queries
   - Use EXISTS instead of IN for subqueries

3. **Sampling Strategy:**
   - Use statistical sampling for large tables
   - Implement stratified sampling

---

## Troubleshooting

### Common Issues

#### Issue: "ODBC Driver not found"
**Solution:**
- Install ODBC Driver 17 or 18 for SQL Server
- Verify installation: `odbcinst -j`
- Check available drivers: `odbcinst -q -d`

#### Issue: "Authentication failed" (Azure AD)
**Solution:**
- Use ActiveDirectoryInteractive for MFA
- Ensure user has proper permissions
- Check tenant ID and client ID
- Clear browser cache/cookies

#### Issue: "Connection timeout"
**Solution:**
- Increase timeout in connection string
- Check firewall rules
- Verify network connectivity
- Check if database server is accessible

#### Issue: "Excel generation fails for large datasets"
**Solution:**
- Increase memory allocation
- Use sampling instead of full validation
- Implement pagination in Excel export
- Consider splitting into multiple files

#### Issue: "Slow validation performance"
**Solution:**
- Add database indexes
- Use sampling for initial validation
- Enable connection pooling
- Optimize queries
- Consider parallel processing

#### Issue: "OAuth window not closing automatically"
**Solution:**
- Run `oauth_auto_closer.py` script
- Use `run_oauth_closer.bat` to start listener
- Check if port 8765 is available

### Debug Mode

Enable debug logging:

```python
# In api.py
import logging
logging.basicConfig(level=logging.DEBUG)

# In validate.py
print("[DEBUG] Debug message here")
```

### Log Locations

- **ETL Logs:** `DataValidation/logs/etl_log.txt`
- **Duplicate Logs:** `DataValidation/logs/duplicate_combined_log.txt`
- **Mismatch Logs:** `DataValidation/logs/row_data_mismatch_log.txt`
- **Pipeline Logs:** `etl_project_two_tables/logs/pipeline_execution_logs.json`
- **Uvicorn Logs:** Console output or redirected to file

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor log files for errors
- Check application uptime
- Verify validation executions

**Weekly:**
- Review performance metrics
- Clean up old reports and logs
- Check disk space usage

**Monthly:**
- Update Python packages
- Review and update dependencies
- Security vulnerability scanning
- Backup configuration files

**Quarterly:**
- Performance optimization review
- User feedback collection
- Feature enhancement planning
- Infrastructure capacity review

### Backup Strategy

**What to Backup:**
- Configuration files (db_config.py, data_sources.json, secrets.py)
- Custom queries and validation rules
- Project configuration (projects.json)
- Connection templates
- Generated reports (if needed)

**Backup Schedule:**
- Daily: Incremental backup of configurations
- Weekly: Full backup of application and data
- Monthly: Off-site backup

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 8.0 | 2026-04-08 | - Fixed Excel export date normalization<br>- Improved record pairing algorithm<br>- Enhanced debug logging<br>- Added fuzzy matching for records |
| 7.0 | 2026-03 | - Added Medallion Architecture support<br>- Project context management<br>- OAuth auto-close feature |
| 6.0 | 2026-02 | - Databricks support<br>- File-to-file validation<br>- Real-time progress tracking |

---

## License

**This framework is proprietary software developed for WinWire Technologies.**

For licensing inquiries, contact: licensing@winwire.com

---

## Contact & Support

**Development Team:** WinWire Technologies  
**Email:** support@winwire.com  
**Documentation:** [Internal Wiki URL]  
**Issue Tracking:** [JIRA/Azure DevOps URL]

---

## Appendix

### A. Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| API_HOST | API server host | 0.0.0.0 | No |
| API_PORT | API server port | 8000 | No |
| LOG_LEVEL | Logging level | INFO | No |
| DEFAULT_DB_SERVER | Default database server | - | No |
| AZURE_TENANT_ID | Azure AD tenant ID | - | For Azure AD |
| AZURE_CLIENT_ID | Azure AD client ID | - | For Azure AD |

### B. API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Resource created |
| 400 | Bad request (invalid input) |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Resource not found |
| 500 | Internal server error |
| 503 | Service unavailable |

### C. Useful Commands

```bash
# Start server
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest DataValidation/tests/ -v

# Check dependencies
pip list

# Update dependencies
pip install --upgrade -r requirements.txt

# Check ODBC drivers
odbcinst -q -d

# View logs
tail -f DataValidation/logs/etl_log.txt

# Check port usage
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac
```

---

**End of Documentation**

*Last Updated: April 8, 2026*  
*Version: 8.0*  
*Framework: WinETL InfinityX*
