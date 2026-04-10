# WinETL InfinityX - Enterprise ETL Validation Framework

**Version 8.0**  
A comprehensive web-based ETL (Extract, Transform, Load) validation framework built with PyTest, FastAPI, and a modern HTML/CSS/JavaScript frontend.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[Quick Start Guide](QUICKSTART_GUIDE.md)** | Get started in 5 minutes! |
| **[Full Documentation](FRAMEWORK_DOCUMENTATION.md)** | Complete technical documentation (100+ pages) |
| **[Publishing Guide](PUBLISHING_GUIDE.md)** | Deploy to production step-by-step |
| **This README** | Overview and features |

---

## 🚀 Features

- **Web-Based UI**: Modern, responsive interface for selecting tables and validations
- **User Authentication**: Complete login/signup system with role-based access control (RBAC)
  - **Admin Role**: Full access to all data, user management via Admin Dashboard
  - **Contributor Role**: Create projects, work on assigned groups only
  - **User Role**: View-only access to assigned projects
  - **Group-Based Filtering**: Dynamic groups from actual project/account names
- **Multiple Data Sources**: SQL Server, Azure Synapse Analytics, Microsoft Fabric, MySQL, PostgreSQL, Oracle, Databricks, and more
- **Medallion Architecture**: Full support for Bronze/Silver/Gold layer validation in Microsoft Fabric (see [Quickstart](MEDALLION_QUICKSTART.md))
- **Table Selection**: Choose source and target tables from database or enter manually
- **Validation Options**: Select which validations to run:
  - Structure Validation (columns, data types, primary keys)
  - Record Count Validation
  - Null Check (constraint violations)
  - Duplicate Check (primary key based)
  - Row-wise Data Validation
- **Real-time Execution**: Run validations and see results immediately
- **Report Generation**: Excel reports and HTML dashboards
- **Log Viewing**: View ETL logs, duplicate logs, and mismatch logs
- **Execution History**: Track past validation runs
- **Azure Integration**: Full support for Azure Synapse and Microsoft Fabric (see [AZURE_SUPPORT.md](AZURE_SUPPORT.md))

## 🔐 Authentication & User Management

### Default Admin Credentials

**When you first access the application**, use these credentials to login:

```
Email: nilanchal.tripathy@winwire.com
Password: Admin@123
```

⚠️ **IMPORTANT**: Change the default password immediately after first login, or delete this user and create a new admin account.

### User Roles

The framework implements Role-Based Access Control (RBAC) with three roles:

| Role | Permissions | Group Access |
|------|-------------|--------------|
| **Admin** | • Full access to all projects/accounts/products<br>• User management via Admin Dashboard<br>• Assign roles and groups to users | "All" - sees everything |
| **Contributor** | • Create new projects and accounts<br>• Work on assigned groups only<br>• Projects automatically assign to creator's groups | Multiple groups (e.g., "ProjectA,ProjectB") |
| **User** | • View and work on assigned projects only<br>• Cannot create new projects<br>• Read-only access | Single or multiple assigned groups |

### Creating New Users

**Option 1 - Signup Page (Recommended)**:
1. Visit http://localhost:8000/signup.html
2. Complete registration with OTP verification
3. Admin approves and assigns role/group via Admin Dashboard

**Option 2 - Admin Manual Creation**:
1. Login as Admin
2. Click "Admin" button in top-right corner
3. Add user directly in users.xlsx or manage via Admin Dashboard

### Admin Dashboard

Access at http://localhost:8000/admin.html (Admin role only)

Features:
- View all registered users
- Search and filter users by role
- Assign/update roles and groups
- Activate/deactivate user accounts
- Track user statistics and activity

### Group-Based Access

- **Groups are dynamic**: Automatically populated from actual project/account names
- **Auto-assignment**: When Contributors create projects, they're automatically added to that group
- **Session refresh**: User groups update from database on every session validation
- **Filtering**: All dashboard views filter by user's assigned groups
- **Blank state**: Non-Admin users see "No Project Selected" when no project context is active

--- 📁 Project Structure

```
ETL_DEMO_Pytest14/
├── backend/                          # REST API Backend
│   ├── api.py                        # FastAPI server with all endpoints
│   ├── requirements.txt              # Backend Python dependencies
│   └── __pycache__/                  # Python bytecode cache
│
├── frontend/                         # Web User Interface
│   └── index.html                    # Single-page web application
│
├── DataValidation/                   # Core Validation Framework
│   ├── config/                       # Configuration Files
│   │   ├── db_config.py              # Database connection factory
│   │   ├── data_sources.json         # Multi-source connection configs
│   │   ├── validation_rules.json     # Automated validation rules
│   │   ├── secrets.py                # Secrets & credentials management
│   │   ├── fabric_medallion_example.json # Fabric medallion config
│   │   └── __pycache__/              # Python bytecode cache
│   │
│   ├── src/                          # Source Code Modules
│   │   ├── validate.py               # Core validation functions
│   │   ├── advanced_validate.py      # Advanced validation logic
│   │   ├── extract.py                # Data extraction module
│   │   ├── transform.py              # Data transformation module
│   │   ├── load.py                   # Data loading module
│   │   ├── report_generator.py       # Multi-format report generation
│   │   ├── automation.py             # Validation automation engine
│   │   ├── _init__.py                # Package initializer
│   │   └── __pycache__/              # Python bytecode cache
│   │
│   ├── tests/                        # PyTest Test Suite
│   │   ├── conftest.py               # PyTest fixtures & configuration
│   │   ├── test_validate.py          # Validation function tests
│   │   ├── test_extract.py           # Extraction tests
│   │   ├── test_transform.py         # Transformation tests
│   │   ├── test_main.py              # End-to-end integration tests
│   │   └── __pycache__/              # Python bytecode cache
│   │
│   ├── DataValidation/               # Nested validation workspace
│   │   ├── logs/                     # Workspace-specific logs
│   │   │   └── row_data_mismatch_log.txt
│   │   └── reports/                  # Workspace-specific reports
│   │
│   ├── logs/                         # Main Execution Logs
│   │   ├── etl_log.txt               # General ETL execution logs
│   │   ├── duplicate_combined_log.txt # Duplicate record logs
│   │   └── row_data_mismatch_log.txt # Row-level mismatch logs
│   │
│   ├── reports/                      # Generated Reports
│   │   ├── etl_dashboard.html        # HTML dashboard
│   │   └── loaded_data.csv           # Loaded data output
│   │
│   ├── uploads/                      # File Upload Storage
│   │   ├── 20260128_124647_emp_source.csv
│   │   ├── 20260128_124659_emp_source.csv
│   │   ├── 20260128_124706_emp_source.csv
│   │   └── 20260128_124708_emp_source.csv
│   │
│   ├── test_data/                    # Test Datasets
│   │   └── sample_input.csv          # Sample test data
│   │
│   ├── .env.example                  # Environment variables template
│   ├── .github/                      # GitHub configurations
│   ├── main.py                       # Main ETL pipeline orchestrator
│   ├── generate_test_report.py       # PyTest report generator
│   ├── pytest.ini                    # PyTest configuration
│   ├── requirements.txt              # Framework dependencies
│   ├── README.md                     # Framework documentation
│   └── __pycache__/                  # Python bytecode cache
│
├── etl_project_two_tables/           # Sample Project Workspace
│   ├── logs/                         # Project execution logs
│   │   ├── duplicate_combined_log.txt
│   │   ├── etl_log.txt
│   │   └── row_data_mismatch_log.txt
│   ├── reports/                      # Project reports
│   │   └── etl_dashboard.html
│   └── uploads/                      # Project file uploads
│
├── .venv/                            # Python virtual environment
├── .pytest_cache/                    # PyTest cache directory
├── __pycache__/                      # Python bytecode cache
│
├── Documentation & Guides
├── ETL_Validation_Framework_Documentation.docx  # Complete 60+ page documentation
├── AZURE_SUPPORT.md                  # Azure Synapse & Fabric integration guide
├── MEDALLION_QUICKSTART.md           # Medallion architecture quickstart
├── UI_IMPLEMENTATION_GUIDE.md        # Web UI implementation guide
├── VALIDATION_FIX_README.md          # Validation fixes & improvements
│
├── Configuration & Setup Files
├── run_server.bat                    # Windows quick-start script
├── generate_framework_documentation.py  # Documentation generator script
├── test_mismatch_report.py           # Mismatch report testing utility
├── openapi.json                      # OpenAPI specification
│
└── README.md                         # Main project documentation (this file)
```

### Key Directories Explained

- **backend/**: FastAPI REST API server providing programmatic access
- **frontend/**: Single-page web application for user interaction
- **DataValidation/**: Core framework with all validation, ETL, and testing logic
- **etl_project_two_tables/**: Sample workspace demonstrating framework usage
- **.venv/**: Isolated Python environment with all dependencies

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- SQL Server with ODBC Driver 17
- pip (Python package manager)

### Setup

1. **Clone or download the project**

2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   pip install -r DataValidation/requirements.txt
   ```

3. **Configure database connection** in `DataValidation/config/data_sources.json`:
   - Update the default connection with your SQL Server details
   - Or use the web interface to configure connections dynamically

## 🚀 Running the Application

### Windows

Double-click `run_server.bat` or run:
```bash
run_server.bat
```

### Manual Start

```bash
cd backend
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application

Open your browser and navigate to:

- **Login Page**: http://localhost:8000 (auto-redirects to login.html)
- **Main Dashboard**: http://localhost:8000/index.html (after login)
- **Signup Page**: http://localhost:8000/signup.html
- **Admin Dashboard**: http://localhost:8000/admin.html (Admin role only)
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health

**First-Time Setup:**
1. Navigate to http://localhost:8000
2. You'll be redirected to the login page
3. Login with default admin credentials (see [Authentication section](#-authentication--user-management))
4. Change the default password or create new users
5. Start creating projects and running validations!

--- 📖 Usage Guide

### 1. Select Tables

- Use the dropdown menus to select source and target tables from the database
- Or manually enter table names (e.g., `dbo.emp_source`, `dbo.emp_target`)

### 2. Choose Validations

Select which validations to run:
- ✅ **Structure Validation**: Compare table schemas
- ✅ **Record Count Validation**: Compare row counts
- ✅ **Null Check**: Find NULL values and constraint violations
- ✅ **Duplicate Check**: Find duplicate records
- ✅ **Row Data Validation**: Compare actual data row by row

### 3. Execute

- Click **"Run Validation"** to execute the ETL pipeline directly
- Click **"Run PyTest"** to execute via pytest with allure reporting

### 4. View Results

- **Dashboard**: Visual HTML report of validation results
- **Logs**: View detailed logs for ETL, duplicates, and mismatches
- **Excel Report**: Download comprehensive Excel report
- **History**: View past execution results

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve web interface |
| `/api/health` | GET | Health check |
| `/api/tables` | GET | Get available tables |
| `/api/validations` | GET | Get validation options |
| `/api/run` | POST | Run validation pipeline |
| `/api/run-pytest` | POST | Run pytest validation |
| `/api/download/excel` | GET | Download Excel report |
| `/api/dashboard` | GET | Get HTML dashboard |
| `/api/logs/{type}` | GET | Get log files |
| `/api/history` | GET | Get execution history |

## 🧪 Running Tests Directly

```bash
cd DataValidation

# Run all tests
pytest -v

# Run specific validation tests
pytest tests/test_validate.py -v

# Run with custom source and target
pytest -v --source-table=dbo.emp_source --target-table=dbo.emp_target
```

## 📊 Validation Types

### Structure Validation
Compares:
- Column names
- Data types
- Nullability constraints
- Primary keys

### Record Count Validation
- Counts rows in source and target
- Reports match/mismatch

### Null Check
- Identifies NULL values per column
- Checks NOT NULL constraint violations
- Checks PRIMARY KEY NULL violations

### Duplicate Check
- Finds duplicate records based on primary key
- Can also check composite keys
- Logs duplicate records

### Row Data Validation
- Row-by-row comparison
- Identifies rows only in source
- Identifies rows only in target
- Logs mismatched records

## 📝 Generated Reports

### Excel Report (`reports/etl_validation_report.xlsx`)
- Comprehensive validation results
- Multiple sheets for different validations
- Detailed data comparisons

### HTML Dashboard (`reports/etl_dashboard.html`)
- Visual summary of validations
- Pass/fail indicators
- Interactive charts

### Log Files
- `logs/etl_log.txt` - General ETL logs
- `logs/duplicate_combined_log.txt` - Duplicate records
- `logs/row_data_mismatch_log.txt` - Mismatched rows

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SOURCE_TABLE` | Source table name | `dbo.emp_source2` |
| `TARGET_TABLE` | Target table name | `dbo.emp_target2` |
| `STRUCTURE_VALIDATION` | Enable structure check | `True` |
| `COUNT_VALIDATION` | Enable count check | `True` |
| `NULL_CHECK` | Enable null check | `True` |
| `DUPLICATE_CHECK` | Enable duplicate check | `True` |
| `ROW_DATA_VALIDATION` | Enable row validation | `True` |

## 🐛 Troubleshooting

### Database Connection Issues
- Verify SQL Server is running
- Check ODBC Driver 17 is installed
- Verify connection string in `db_config.py`

### API Not Starting
- Check port 8000 is available
- Verify all dependencies are installed
- Check Python version (3.8+)

### Tables Not Loading
- Verify database connection
- Check user has SELECT permissions
- Tables must be in INFORMATION_SCHEMA

## � Documentation

For comprehensive framework documentation:
- **Complete Guide**: See [ETL_Validation_Framework_Documentation.docx](ETL_Validation_Framework_Documentation.docx) - 60+ page detailed documentation
- **Azure Support**: See [AZURE_SUPPORT.md](AZURE_SUPPORT.md)
- **Medallion Architecture**: See [MEDALLION_QUICKSTART.md](MEDALLION_QUICKSTART.md)
- **UI Guide**: See [UI_IMPLEMENTATION_GUIDE.md](UI_IMPLEMENTATION_GUIDE.md)

## �📄 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!
