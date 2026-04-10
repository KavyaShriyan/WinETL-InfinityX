"""
Authentication and Authorization Service
Handles user signup, login, RBAC, OTP verification, and Excel-based user storage
"""
import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import openpyxl
from openpyxl import Workbook
import re
import random
import time

# Path to user database Excel file
USER_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'users.xlsx')

# In-memory session storage (user_id -> session_data)
SESSIONS = {}

# In-memory OTP storage (mobile_number -> {otp, expiry, attempts})
OTP_STORAGE = {}

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "nilanchal.tripathy@winwire.com"
DEFAULT_ADMIN_PASSWORD = "Admin@123"  # Should be changed on first login

class AuthService:
    """Authentication and user management service"""
    
    def __init__(self):
        self.user_db_path = USER_DB_PATH
        self._initialize_user_database()
    
    def _initialize_user_database(self):
        """Create user database Excel file if it doesn't exist"""
        if not os.path.exists(self.user_db_path):
            print(f"[AUTH] Creating user database at {self.user_db_path}")
            wb = Workbook()
            ws = wb.active
            ws.title = "Users"
            
            # Create header row
            headers = ['Email', 'UserID', 'UserName', 'PasswordHash', 'MobileNumber', 
                      'Role', 'Group', 'IsActive', 'CreatedDate', 'LastLogin']
            ws.append(headers)
            
            # Add default admin user
            admin_password_hash = self._hash_password(DEFAULT_ADMIN_PASSWORD)
            admin_row = [
                DEFAULT_ADMIN_EMAIL,
                'admin',
                'System Administrator',
                admin_password_hash,
                '',
                'Admin',
                'All',
                'Yes',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ''
            ]
            ws.append(admin_row)
            
            # Style the header
            from openpyxl.styles import Font, PatternFill
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column = list(column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column[0].column_letter].width = adjusted_width
            
            wb.save(self.user_db_path)
            print(f"[AUTH] User database created with default admin: {DEFAULT_ADMIN_EMAIL}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256 with salt"""
        salt = "ETL_VALIDATION_SALT_2026"  # Fixed salt for simplicity
        return hashlib.sha256((salt + password).encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        return True, "Valid"
    
    def _validate_mobile(self, mobile: str) -> bool:
        """Validate mobile number format"""
        pattern = r'^\+?[1-9]\d{9,14}$'
        return re.match(pattern, mobile) is not None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users from database"""
        try:
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            users = []
            headers = [cell.value for cell in ws[1]]
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                user = dict(zip(headers, row))
                # Don't expose password hash
                if 'PasswordHash' in user:
                    del user['PasswordHash']
                users.append(user)
            
            return users
        except Exception as e:
            print(f"[AUTH] Error reading users: {e}")
            return []
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            headers = [cell.value for cell in ws[1]]
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                user = dict(zip(headers, row))
                if user.get('Email', '').lower() == email.lower():
                    return user
            
            return None
        except Exception as e:
            print(f"[AUTH] Error getting user: {e}")
            return None
    
    def get_user_by_userid(self, user_id: str) -> Optional[Dict]:
        """Get user by UserID"""
        try:
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            headers = [cell.value for cell in ws[1]]
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                user = dict(zip(headers, row))
                if user.get('UserID', '').lower() == user_id.lower():
                    return user
            
            return None
        except Exception as e:
            print(f"[AUTH] Error getting user: {e}")
            return None
    
    def generate_otp(self, mobile_number: str) -> str:
        """Generate 6-digit OTP and store with expiry"""
        otp = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=5)  # 5 minute expiry
        
        OTP_STORAGE[mobile_number] = {
            'otp': otp,
            'expiry': expiry,
            'attempts': 0
        }
        
        print(f"[AUTH] OTP generated for {mobile_number}: {otp} (expires at {expiry})")
        return otp
    
    def verify_otp(self, mobile_number: str, otp: str) -> tuple[bool, str]:
        """Verify OTP"""
        if mobile_number not in OTP_STORAGE:
            return False, "OTP not found. Please request a new OTP."
        
        stored = OTP_STORAGE[mobile_number]
        
        # Check expiry
        if datetime.now() > stored['expiry']:
            del OTP_STORAGE[mobile_number]
            return False, "OTP expired. Please request a new OTP."
        
        # Check attempts
        if stored['attempts'] >= 3:
            del OTP_STORAGE[mobile_number]
            return False, "Too many failed attempts. Please request a new OTP."
        
        # Verify OTP
        if stored['otp'] == otp:
            del OTP_STORAGE[mobile_number]
            return True, "OTP verified successfully"
        else:
            stored['attempts'] += 1
            return False, f"Invalid OTP. {3 - stored['attempts']} attempts remaining."
    
    def signup(self, email: str, user_id: str, username: str, password: str, mobile_number: str, otp_verified: bool = False) -> tuple[bool, str]:
        """Register new user"""
        try:
            # Validate inputs
            if not self._validate_email(email):
                return False, "Invalid email format"
            
            valid_pwd, pwd_msg = self._validate_password(password)
            if not valid_pwd:
                return False, pwd_msg
            
            # Make mobile number and OTP optional for now
            if mobile_number and not self._validate_mobile(mobile_number):
                return False, "Invalid mobile number format"
            
            # OTP verification disabled for demo purposes
            # if not otp_verified:
            #     return False, "Mobile number must be verified with OTP before signup"
            
            # Check for duplicates
            if self.get_user_by_email(email):
                return False, "Email already registered"
            
            if self.get_user_by_userid(user_id):
                return False, "User ID already taken"
            
            # Add user to Excel
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            password_hash = self._hash_password(password)
            new_row = [
                email,
                user_id,
                username,
                password_hash,
                mobile_number,
                '',  # Role (blank, admin will assign)
                '',  # Group (blank, admin will assign)
                'Yes',  # IsActive
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # CreatedDate
                ''  # LastLogin
            ]
            
            ws.append(new_row)
            wb.save(self.user_db_path)
            
            print(f"[AUTH] User registered: {email}")
            return True, "Signup successful! Please wait for admin to assign your role and group."
            
        except Exception as e:
            print(f"[AUTH] Signup error: {e}")
            return False, f"Signup failed: {str(e)}"
    
    def login(self, email_or_userid: str, password: str) -> tuple[bool, Optional[Dict], str]:
        """Authenticate user and create session"""
        try:
            # Try to find user by email or user_id
            user = self.get_user_by_email(email_or_userid)
            if not user:
                user = self.get_user_by_userid(email_or_userid)
            
            if not user:
                return False, None, "Invalid credentials"
            
            # Check if account is active
            if user.get('IsActive', '').lower() != 'yes':
                return False, None, "Account is inactive. Please contact administrator."
            
            # Verify password
            if not self._verify_password(password, user['PasswordHash']):
                return False, None, "Invalid credentials"
            
            # Check if role/group assigned (except for admin)
            if user.get('Role') != 'Admin' and not user.get('Role'):
                return False, None, "Your account is pending approval. Please wait for admin to assign your role."
            
            # Update last login
            self._update_last_login(user['Email'])
            
            # Create session
            session_token = self._generate_session_token()
            session_data = {
                'email': user['Email'],
                'user_id': user['UserID'],
                'username': user['UserName'],
                'role': user.get('Role', ''),
                'group': user.get('Group', ''),
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(hours=8)  # 8 hour session
            }
            
            SESSIONS[session_token] = session_data
            
            # Remove password hash from user data
            user_data = {k: v for k, v in user.items() if k != 'PasswordHash'}
            user_data['session_token'] = session_token
            
            print(f"[AUTH] User logged in: {user['Email']} (Role: {user.get('Role', 'None')})")
            return True, user_data, "Login successful"
            
        except Exception as e:
            print(f"[AUTH] Login error: {e}")
            return False, None, f"Login failed: {str(e)}"
    
    def _update_last_login(self, email: str):
        """Update last login timestamp"""
        try:
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            headers = [cell.value for cell in ws[1]]
            last_login_col = headers.index('LastLogin') + 1
            email_col = headers.index('Email') + 1
            
            for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
                if row[email_col - 1].value.lower() == email.lower():
                    ws.cell(row=row_idx, column=last_login_col).value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    break
            
            wb.save(self.user_db_path)
        except Exception as e:
            print(f"[AUTH] Error updating last login: {e}")
    
    def logout(self, session_token: str) -> bool:
        """Destroy session"""
        if session_token in SESSIONS:
            del SESSIONS[session_token]
            return True
        return False
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token and return user data"""
        if session_token not in SESSIONS:
            return None
        
        session = SESSIONS[session_token]
        
        # Check expiry
        if datetime.now() > session['expires_at']:
            del SESSIONS[session_token]
            return None
        
        # Refresh user data from database to get latest group assignments
        email = session.get('email')
        if email:
            user = self.get_user_by_email(email)
            if user:
                # Update session with latest group data
                session['group'] = user.get('Group', session.get('group', ''))
                session['role'] = user.get('Role', session.get('role', ''))
                SESSIONS[session_token] = session
        
        return session
    
    def check_permission(self, session_token: str, required_role: str = None, required_group: str = None) -> tuple[bool, str]:
        """Check if user has required permissions"""
        session = self.validate_session(session_token)
        
        if not session:
            return False, "Invalid or expired session"
        
        role = session.get('role', '')
        group = session.get('group', '')
        
        # Admin has full access
        if role == 'Admin':
            return True, "Access granted"
        
        # Check role requirement
        if required_role and role != required_role:
            return False, f"Access denied. Required role: {required_role}"
        
        # Check group requirement
        if required_group and group != required_group:
            return False, f"Access denied. Required group: {required_group}"
        
        return True, "Access granted"
    
    def update_user_role(self, admin_session_token: str, target_email: str, new_role: str, new_group: str) -> tuple[bool, str]:
        """Admin: Update user role and group"""
        # Check if requester is admin
        session = self.validate_session(admin_session_token)
        if not session or session.get('role') != 'Admin':
            return False, "Only admins can update user roles"
        
        try:
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            headers = [cell.value for cell in ws[1]]
            email_col = headers.index('Email') + 1
            role_col = headers.index('Role') + 1
            group_col = headers.index('Group') + 1
            
            found = False
            for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
                if row[email_col - 1].value.lower() == target_email.lower():
                    ws.cell(row=row_idx, column=role_col).value = new_role
                    ws.cell(row=row_idx, column=group_col).value = new_group
                    found = True
                    break
            
            if not found:
                return False, "User not found"
            
            wb.save(self.user_db_path)
            print(f"[AUTH] Admin updated user {target_email}: Role={new_role}, Group={new_group}")
            return True, "User role updated successfully"
            
        except Exception as e:
            print(f"[AUTH] Error updating role: {e}")
            return False, f"Failed to update role: {str(e)}"
    
    def toggle_user_status(self, admin_session_token: str, target_email: str, is_active: str) -> tuple[bool, str]:
        """Admin: Toggle user active/inactive status"""
        # Check if requester is admin
        session = self.validate_session(admin_session_token)
        if not session or session.get('role') != 'Admin':
            return False, "Only admins can toggle user status"
        
        # Prevent deactivating self
        if session.get('email', '').lower() == target_email.lower() and is_active == 'No':
            return False, "Cannot deactivate your own account"
        
        try:
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            headers = [cell.value for cell in ws[1]]
            email_col = headers.index('Email') + 1
            is_active_col = headers.index('IsActive') + 1
            
            found = False
            for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
                if row[email_col - 1].value.lower() == target_email.lower():
                    ws.cell(row=row_idx, column=is_active_col).value = is_active
                    found = True
                    break
            
            if not found:
                return False, "User not found"
            
            wb.save(self.user_db_path)
            
            # Invalidate user's sessions if being deactivated
            if is_active == 'No':
                sessions_to_remove = [token for token, sess in SESSIONS.items() if sess.get('email', '').lower() == target_email.lower()]
                for token in sessions_to_remove:
                    del SESSIONS[token]
                print(f"[AUTH] Invalidated {len(sessions_to_remove)} sessions for deactivated user {target_email}")
            
            status_text = "activated" if is_active == "Yes" else "deactivated"
            print(f"[AUTH] Admin {status_text} user {target_email}")
            return True, f"User {status_text} successfully"
            
        except Exception as e:
            print(f"[AUTH] Error toggling user status: {e}")
            return False, f"Failed to toggle status: {str(e)}"
    
    def delete_user(self, admin_session_token: str, target_email: str) -> tuple[bool, str]:
        """Admin: Permanently delete a user"""
        # Check if requester is admin
        session = self.validate_session(admin_session_token)
        if not session or session.get('role') != 'Admin':
            return False, "Only admins can delete users"
        
        # Prevent deleting self
        if session.get('email', '').lower() == target_email.lower():
            return False, "Cannot delete your own account"
        
        try:
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            headers = [cell.value for cell in ws[1]]
            email_col = headers.index('Email') + 1
            
            found = False
            for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
                if row[email_col - 1].value.lower() == target_email.lower():
                    ws.delete_rows(row_idx)
                    found = True
                    break
            
            if not found:
                return False, "User not found"
            
            wb.save(self.user_db_path)
            
            # Invalidate all user's sessions
            sessions_to_remove = [token for token, sess in SESSIONS.items() if sess.get('email', '').lower() == target_email.lower()]
            for token in sessions_to_remove:
                del SESSIONS[token]
            
            print(f"[AUTH] Admin deleted user {target_email} and invalidated {len(sessions_to_remove)} sessions")
            return True, "User deleted successfully"
            
        except Exception as e:
            print(f"[AUTH] Error deleting user: {e}")
            return False, f"Failed to delete user: {str(e)}"
    
    def get_filtered_data(self, session_token: str, data_type: str, all_items: List[Dict]) -> List[Dict]:
        """Filter data based on user's role and group"""
        session = self.validate_session(session_token)
        
        if not session:
            return []
        
        role = session.get('role', '')
        group = session.get('group', '')
        
        # Admin sees everything
        if role == 'Admin' or group == 'All':
            return all_items
        
        # Filter by group
        filtered = []
        for item in all_items:
            item_group = item.get('group', '') or item.get('Group', '')
            if item_group == group:
                filtered.append(item)
        
        return filtered
    
    def add_group_to_user(self, email: str, new_group: str) -> tuple[bool, str]:
        """Add a group to user's existing groups (used when Contributor creates a project)"""
        try:
            wb = openpyxl.load_workbook(self.user_db_path)
            ws = wb.active
            
            headers = [cell.value for cell in ws[1]]
            email_col = headers.index('Email') + 1
            group_col = headers.index('Group') + 1
            
            found = False
            for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
                if row[email_col - 1].value and row[email_col - 1].value.lower() == email.lower():
                    current_groups = row[group_col - 1].value or ''
                    # Parse existing groups (comma-separated)
                    existing_groups = [g.strip() for g in current_groups.split(',') if g.strip()]
                    
                    # Add new group if not already present
                    if new_group not in existing_groups:
                        existing_groups.append(new_group)
                        updated_groups = ','.join(existing_groups)
                        ws.cell(row=row_idx, column=group_col).value = updated_groups
                        wb.save(self.user_db_path)
                        print(f"[AUTH] Added group '{new_group}' to user {email}. New groups: {updated_groups}")
                        found = True
                    else:
                        print(f"[AUTH] Group '{new_group}' already exists for user {email}")
                        found = True
                    break
            
            if not found:
                return False, "User not found"
            
            return True, "Group added successfully"
            
        except Exception as e:
            print(f"[AUTH] Error adding group to user: {e}")
            return False, f"Failed to add group: {str(e)}"


# Global auth service instance
auth_service = AuthService()
