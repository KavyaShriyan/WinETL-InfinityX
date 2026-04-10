# WinETL InfinityX - Quick Start Guide

**Get started with the ETL Validation Framework in 5 minutes!**

---

## Prerequisites

✅ Python 3.8+ installed  
✅ ODBC Driver 17 or 18 for SQL Server (if using SQL Server/Azure)  
✅ Modern web browser (Chrome, Edge, Firefox, Safari)  

---

## Installation

### 1. Install Dependencies

```bash
# Navigate to project directory
cd "ETL_DEMO_Pytest14"

# Create virtual environment (optional but recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
# OR
source .venv/bin/activate      # Linux/Mac

# Install backend packages
pip install -r backend/requirements.txt

# Install validation framework packages
pip install -r DataValidation/requirements.txt
```

### 2. Start the Server

**Windows:**
```bash
.\run_server.bat
```

**Linux/Mac:**
```bash
cd backend
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the Application

Open your browser and go to: **http://localhost:8000**

You'll be automatically redirected to the login page.

### 4. Login

**Use the default admin credentials:**

```
Email: nilanchal.tripathy@winwire.com
Password: Admin@123
```

✅ **First-Time Tip:** Change this password after logging in, or create new admin users via the signup page.

**Understanding User Roles:**
- **Admin**: Full access to all projects and user management
- **Contributor**: Can create projects, work on assigned groups only
- **User**: View-only access to assigned projects

After logging in, you'll see your name and role in the top-right corner of the dashboard.

---

## First Validation

### Step 1: Configure Source Database

1. Click on **"Source & Target Configuration"** tab
2. Select your database type (SQL Server, MySQL, PostgreSQL, etc.)
3. Enter connection details:
   - Server name
   - Database name
   - Authentication method
   - Username (if required)
4. Click **"Test Connection"** to verify
5. **Save connection** (optional) for future use

### Step 2: Configure Target Database

Repeat the same steps for your target database.

### Step 3: Select Tables

1. Use **"Select Table"** dropdown to browse available tables, OR
2. Enter a custom SQL query in the **"Custom Query"** field

### Step 4: Choose Validations

Select which validations to run:
- ✅ **Structure Validation** - Compare schemas
- ✅ **Record Count** - Compare row counts
- ✅ **Null Check** - Validate NULL constraints
- ✅ **Duplicate Check** - Find duplicate records
- ✅ **Row Data Validation** - Compare actual data

### Step 5: Run Validation

1. Click **"Execute Validation"** button
2. Watch real-time progress
3. View results in the dashboard

### Step 6: Download Reports

- **Excel Report**: Detailed validation results with formatting
- **HTML Dashboard**: Interactive web-based report

---

## Common Use Cases

### Use Case 1: Database Migration Validation

**Scenario:** Migrating data from SQL Server to Databricks

```
Source: SQL Server (Production)
Target: Databricks (New Platform)
Validations: All (Structure + Count + Data)
Sample: All Records
```

### Use Case 2: Daily ETL Pipeline Validation

**Scenario:** Validate nightly ETL pipeline results

```
Source: Staging Table
Target: Production Table
Validations: Count + Null + Duplicate + Data
Sample: First 1000 rows (for quick check)
```

### Use Case 3: File to Database Validation

**Scenario:** Validate CSV import results

```
Source: Upload CSV file
Target: Database table
Validations: All
Sample: All Records
```

---

## User Management (Admin Only)

### Creating New Users

**Option 1 - Self-Signup:**
1. Users visit **http://localhost:8000/signup.html**
2. Complete registration form with OTP verification
3. Admin approves via Admin Dashboard

**Option 2 - Admin Creates:**
1. Login as Admin
2. Click **"Admin"** button (top-right)
3. Manually add user to `users.xlsx` or use Admin Dashboard

### Managing User Roles & Groups

1. Navigate to **Admin Dashboard** (http://localhost:8000/admin.html)
2. Search for the user
3. Click **"Edit"** button
4. Assign:
   - **Role**: Admin, Contributor, or User
   - **Group**: Select from actual project/account names (multi-select for Contributor/User)
5. Click **"Save Changes"**

### Understanding Groups

- **Groups = Project/Account Names**: Groups are dynamically populated from your actual projects
- **Auto-Assignment**: When Contributors create projects, they're automatically added to that project's group
- **Multi-Group Access**: Contributors and Users can belong to multiple groups (e.g., "Peets,CHOP,HPE")
- **Filtering**: Users only see data for projects in their assigned groups

### Example User Setup

**Scenario:** You have projects "Peets", "CHOP", and "HPE"

```
Admin User:
  Role: Admin
  Group: All
  → Sees all projects

Contributor User (Jane):
  Role: Contributor
  Group: Peets,CHOP
  → Can create projects
  → Automatically added to groups when creating projects
  → Sees only Peets and CHOP data

Regular User (John):
  Role: User
  Group: CHOP
  → Cannot create projects
  → Sees only CHOP data
```

---

## Supported Databases

| Database | Connection Type |
|----------|----------------|
| **SQL Server** | ODBC (Windows/SQL Auth) |
| **Azure Synapse** | ODBC (Azure AD) |
| **Databricks** | SQL Connector (OAuth/Token) |
| **MySQL** | PyMySQL |
| **PostgreSQL** | psycopg2 |
| **Oracle** | oracledb |
| **MongoDB** | pymongo |

---

## Quick Tips

💡 **Save your connections** - Click "Save Connection" to reuse settings  
💡 **Use sampling** - For large tables, use "First 100" or "Random 1000" for faster validation  
💡 **Project context** - Create projects to organize different validation scenarios  
💡 **Custom queries** - Write custom SQL for complex validation logic  
💡 **View history** - Access past validations in the "History" section  
💡 **Change default password** - Update admin credentials immediately after first login  
💡 **Assign appropriate roles** - Use Contributor role for team members who create projects, User role for view-only access  
💡 **Use groups** - Leverage group-based filtering to control what data users can see  
💡 **Session timeout** - Sessions expire after 8 hours; users will need to re-login  
💡 **Admin dashboard** - Regularly review pending users and approve/assign roles via Admin Dashboard  

---

## Troubleshooting

### Authentication Issues

**Issue: Cannot login with default admin credentials**

**Check:**
- Ensure you're using the correct email: `nilanchal.tripathy@winwire.com`
- Password is case-sensitive: `Admin@123`
- Clear browser cache and try again
- Verify `users.xlsx` exists in `backend/` folder

**Issue: "Unauthorized" error after login**

**Check:**
- Session may have expired (8-hour timeout)
- Clear browser localStorage and login again
- Check browser console for errors

**Issue: User created project but can't see it**

**Solution:**
- Wait a few seconds and refresh the page (session refresh happens automatically)
- Check that the user's role is Contributor or Admin
- Verify user is in the correct group via Admin Dashboard

**Issue: Admin Dashboard not accessible**

**Check:**
- Your role must be "Admin" (not Contributor or User)
- Check `users.xlsx` - Group column should be "All" for Admin users

### Database Connection Issues

**Issue: Cannot connect to database**

**Check:**
- Network connectivity to database server
- Firewall rules allow connection
- Credentials are correct
- ODBC drivers are installed (for SQL Server)

### Performance Issues

**Issue: Validation is slow**

**Try:**
- Use sampling instead of "All Records"
- Add indexes to source/target tables
- Check network speed
- Reduce validation types

### Report Issues

**Issue: Excel download fails**

**Check:**
- Enough disk space available
- Validation completed successfully
- Check browser download settings

---

## Next Steps

📖 Read the [Full Documentation](FRAMEWORK_DOCUMENTATION.md) for advanced features  
🔐 Read [Authentication Guide](AUTH_README.md) for detailed RBAC setup  
🚀 Deploy to production using the [Publishing Guide](PUBLISHING_GUIDE.md)  
👥 Set up user accounts and assign appropriate roles  
📊 Create custom validation rules  
🔄 Configure automated validations  

---

## Support

For issues or questions:
- Check the full documentation
- Review logs in `DataValidation/logs/`
- Contact: support@winwire.com

---

**You're ready to go! Start validating your data! 🎉**
