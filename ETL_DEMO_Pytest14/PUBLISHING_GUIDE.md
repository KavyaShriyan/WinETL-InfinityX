# WinETL InfinityX - Publishing & Deployment Checklist

**Complete guide to publish the ETL Validation Framework to production**

---

## Pre-Publishing Requirements

### 1. Required Software & Tools

| Component | Purpose | Download Link |
|-----------|---------|---------------|
| **Python 3.10+** | Runtime environment | https://www.python.org/downloads/ |
| **ODBC Driver 18 for SQL Server** | SQL Server connectivity | https://learn.microsoft.com/en-us/sql/connect/odbc/download |
| **Git** (optional) | Version control | https://git-scm.com/downloads |
| **Docker** (optional) | Containerized deployment | https://www.docker.com/products/docker-desktop |

### 2. Server Requirements

**Production Server Specifications:**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Disk Space** | 10 GB | 50+ GB SSD |
| **OS** | Windows Server 2016+<br>Ubuntu 18.04+<br>RHEL 7+ | Windows Server 2019+<br>Ubuntu 20.04+<br>RHEL 8+ |
| **Network** | 10 Mbps | 100+ Mbps |

### 3. Network Requirements

**Firewall Rules:**
- **Inbound:** Port 8000 (or custom port) for web access
- **Outbound:** Access to target databases (varies by database)
- Allow Python and Uvicorn through Windows Firewall

**DNS Configuration:**
- Domain name (e.g., `etl-validation.company.com`)
- SSL certificate for HTTPS

---

## Code Preparation Checklist

### Security Updates Required

- [ ] **Configure User Authentication**
  - Review `backend/users.xlsx` and remove/update default admin credentials
  - Default admin: `nilanchal.tripathy@winwire.com` / `Admin@123`
  - Either change password or delete and create new admin via signup
  - Ensure all users have appropriate roles (Admin, Contributor, User) and groups

- [ ] **User Database Security**
  ```python
  # Ensure users.xlsx has proper file permissions
  # Windows: Grant read/write only to application service account
  # Linux: chmod 600 backend/users.xlsx
  ```
  - Consider migrating from Excel to SQL database for production (future enhancement)
  - Ensure password hashing is using SHA-256 (already implemented)
  - Set up regular backups of users.xlsx

- [ ] **Session Security**
  ```python
  # File: backend/auth.py
  # Verify session timeout (default: 8 hours)
  SESSION_EXPIRY_HOURS = 8
  
  # Consider reducing for production:
  SESSION_EXPIRY_HOURS = 4  # 4 hours for higher security
  ```

- [ ] **Remove hardcoded credentials**
  - Check `secrets.py`
  - Check `data_sources.json`
  - Check any `.env` files

- [ ] **Update API_BASE URL in frontend**
  ```javascript
  // File: frontend/index.html (line ~5517)
  // File: frontend/login.html
  // File: frontend/signup.html
  // File: frontend/admin.html
  // File: frontend/assets/auth.js
  
  // Change from:
  const API_BASE = 'http://localhost:8000';
  // To:
  const API_BASE = 'https://etl-validation.company.com';
  ```

- [ ] **Disable debug mode**
  ```python
  # File: backend/api.py
  # Change from:
  if __name__ == "__main__":
      uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
  # To:
  if __name__ == "__main__":
      uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
  ```

- [ ] **Configure CORS for production domains**
  ```python
  # File: backend/api.py
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://etl-validation.company.com"],  # Specific domain
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

- [ ] **Set up environment variables**
  ```bash
  # Create .env file
  API_HOST=0.0.0.0
  API_PORT=8000
  LOG_LEVEL=INFO
  ENVIRONMENT=production
  
  # Authentication settings
  SESSION_SECRET_KEY=your-random-secret-key-here  # Generate with: openssl rand -hex 32
  SESSION_EXPIRY_HOURS=8
  ```

### Configuration Updates

- [ ] **Secure users.xlsx file location**
  ```python
  # Consider moving users.xlsx outside web root
  # Update path in backend/auth.py
  USER_DB_PATH = "C:\\SecureData\\users.xlsx"  # Windows
  USER_DB_PATH = "/var/secure/users.xlsx"  # Linux
  ```

- [ ] **Configure user registration settings**
  ```python
  # File: backend/auth.py
  # Decide if public signup should be enabled in production
  ALLOW_PUBLIC_SIGNUP = False  # Disable if admin-only user creation
  REQUIRE_ADMIN_APPROVAL = True  # Users need admin approval after signup
  ```

- [ ] **Update logging paths**
  ```python
  # Ensure logs go to appropriate directory
  LOG_DIR = "/var/log/etl-framework"  # Linux
  # OR
  LOG_DIR = "C:\\Logs\\ETL-Framework"  # Windows
  ```

- [ ] **Set production database connections**
  ```json
  // File: DataValidation/config/data_sources.json
  {
    "connections": [
      {
        "name": "Production SQL Server",
        "type": "sqlserver",
        "server": "prod-server.company.com",
        "database": "ProductionDB"
      }
    ]
  }
  ```

- [ ] **Configure file upload limits**
  ```python
  # File: backend/api.py
  MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
  ```

### Authentication Pages Checklist

- [ ] **Update frontend authentication files:**
  - `frontend/login.html` - Update API_BASE URL
  - `frontend/signup.html` - Update API_BASE URL, decide if enabled
  - `frontend/admin.html` - Update API_BASE URL
  - `frontend/assets/auth.js` - Update API_BASE URL

- [ ] **Customize login page branding:**
  - Update ETL logo in login.html (SVG logo or image path)
  - Adjust color scheme if needed
  - Update company name/footer text

- [ ] **Configure OTP settings (if using SMS):**
  ```python
  # File: backend/auth.py
  # Configure SMS provider for OTP delivery
  SMS_PROVIDER = "twilio"  # or "aws-sns", "azure-communication"
  SMS_API_KEY = "your-api-key"
  ```

---

## Deployment Methods

### Option 1: Windows Server with IIS (Recommended for Windows)

**Prerequisites:**
- Windows Server 2016 or later
- IIS installed with required features
- HTTP Platform Handler module

**Steps:**

1. **Install IIS and HTTP Platform Handler**
   ```powershell
   # Install IIS
   Install-WindowsFeature -name Web-Server -IncludeManagementTools
   
   # Download and install HTTP Platform Handler
   # https://www.iis.net/downloads/microsoft/httpplatformhandler
   ```

2. **Create application directory**
   ```powershell
   New-Item -Path "C:\inetpub\etl-framework" -ItemType Directory
   Copy-Item -Path ".\*" -Destination "C:\inetpub\etl-framework" -Recurse
   ```

3. **Create web.config**
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <configuration>
     <system.webServer>
       <handlers>
         <add name="PythonHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified"/>
       </handlers>
       <httpPlatform processPath="C:\inetpub\etl-framework\.venv\Scripts\python.exe"
                     arguments="-m uvicorn backend.api:app --host 0.0.0.0 --port %HTTP_PLATFORM_PORT%"
                     startupTimeLimit="60"
                     startupRetryCount="3"
                     stdoutLogEnabled="true"
                     stdoutLogFile=".\logs\stdout.log">
         <environmentVariables>
           <environmentVariable name="PYTHONPATH" value="C:\inetpub\etl-framework" />
           <environmentVariable name="ENVIRONMENT" value="production" />
         </environmentVariables>
       </httpPlatform>
     </system.webServer>
   </configuration>
   ```

4. **Create IIS website**
   ```powershell
   New-WebSite -Name "ETL-Framework" -Port 80 -PhysicalPath "C:\inetpub\etl-framework\backend"
   ```

5. **Configure SSL (recommended)**
   - Bind SSL certificate to IIS site
   - Force HTTPS redirect

**Cost:** Free (Windows Server license required)

---

### Option 2: Linux with Nginx + Systemd (Recommended for Linux)

**Prerequisites:**
- Ubuntu 20.04+ or RHEL 8+
- Root or sudo access

**Steps:**

1. **Install dependencies**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and pip
   sudo apt install python3.10 python3-pip python3-venv -y
   
   # Install Nginx
   sudo apt install nginx -y
   
   # Install ODBC Driver (if using SQL Server)
   curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
   curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
   sudo apt update
   sudo ACCEPT_EULA=Y apt install msodbcsql18 -y
   ```

2. **Set up application**
   ```bash
   # Create application directory
   sudo mkdir -p /opt/etl-framework
   sudo cp -r ./* /opt/etl-framework/
   cd /opt/etl-framework
   
   # Create virtual environment
   sudo python3.10 -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r backend/requirements.txt
   pip install -r DataValidation/requirements.txt
   pip install gunicorn
   ```

3. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/etl-framework.service
   ```
   
   Content:
   ```ini
   [Unit]
   Description=ETL Validation Framework
   After=network.target
   
   [Service]
   Type=notify
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/etl-framework/backend
   Environment="PATH=/opt/etl-framework/.venv/bin"
   ExecStart=/opt/etl-framework/.venv/bin/gunicorn backend.api:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 --timeout 300
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/etl-framework
   ```
   
   Content:
   ```nginx
   server {
       listen 80;
       server_name etl-validation.company.com;
       
       # Redirect to HTTPS
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name etl-validation.company.com;
       
       ssl_certificate /etc/ssl/certs/etl-framework.crt;
       ssl_certificate_key /etc/ssl/private/etl-framework.key;
       
       client_max_body_size 100M;
       
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
           proxy_read_timeout 1800s;  # 30 minutes for validations
           proxy_connect_timeout 75s;
       }
   }
   ```

5. **Enable and start services**
   ```bash
   # Enable Nginx site
   sudo ln -s /etc/nginx/sites-available/etl-framework /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   
   # Enable and start application
   sudo systemctl daemon-reload
   sudo systemctl enable etl-framework
   sudo systemctl start etl-framework
   
   # Check status
   sudo systemctl status etl-framework
   ```

**Cost:** Free (Linux + Nginx are open source)

---

### Option 3: Docker Container (Recommended for Cloud)

**Prerequisites:**
- Docker installed
- Docker Compose (optional)

**Steps:**

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.10-slim
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       unixodbc-dev \
       curl \
       gnupg \
       && rm -rf /var/lib/apt/lists/*
   
   # Install ODBC Driver
   RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
       && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
       && apt-get update \
       && ACCEPT_EULA=Y apt-get install -y msodbcsql18
   
   WORKDIR /app
   
   COPY backend/ ./backend/
   COPY DataValidation/ ./DataValidation/
   COPY frontend/ ./frontend/
   
   RUN pip install --no-cache-dir -r backend/requirements.txt
   RUN pip install --no-cache-dir -r DataValidation/requirements.txt
   
   EXPOSE 8000
   
   CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Create docker-compose.yml**
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
         - ENVIRONMENT=production
       volumes:
         - ./DataValidation/logs:/app/DataValidation/logs
         - ./DataValidation/reports:/app/DataValidation/reports
       restart: unless-stopped
   ```

3. **Build and run**
   ```bash
   docker-compose up -d
   ```

**Cost:** Free (Docker is open source)

---

### Option 4: Azure App Service

**Prerequisites:**
- Azure subscription
- Azure CLI installed

**Steps:**

1. **Prepare application**
   ```bash
   # Combine requirements
   cat backend/requirements.txt DataValidation/requirements.txt > requirements.txt
   
   # Create startup command file
   echo "cd /home/site/wwwroot/backend && gunicorn backend.api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000" > startup.sh
   ```

2. **Deploy to Azure**
   ```bash
   # Login to Azure
   az login
   
   # Create resource group
   az group create --name etl-framework-rg --location eastus
   
   # Create App Service plan
   az appservice plan create --name etl-framework-plan --resource-group etl-framework-rg --sku B1 --is-linux
   
   # Create web app
   az webapp create --resource-group etl-framework-rg --plan etl-framework-plan --name etl-framework-app --runtime "PYTHON:3.10"
   
   # Deploy code
   az webapp up --name etl-framework-app --resource-group etl-framework-rg --runtime PYTHON:3.10
   ```

3. **Configure App Service**
   ```bash
   # Set startup command
   az webapp config set --resource-group etl-framework-rg --name etl-framework-app --startup-file "startup.sh"
   
   # Configure application settings
   az webapp config appsettings set --resource-group etl-framework-rg --name etl-framework-app --settings ENVIRONMENT=production
   ```

**Cost:** ~$55/month (B1 Basic tier)

---

### Option 5: AWS Elastic Beanstalk

**Prerequisites:**
- AWS account
- EB CLI installed

**Steps:**

1. **Initialize Elastic Beanstalk**
   ```bash
   eb init -p python-3.10 etl-framework
   ```

2. **Create environment**
   ```bash
   eb create etl-framework-prod
   ```

3. **Deploy**
   ```bash
   eb deploy
   ```

**Cost:** ~$40/month (t2.small instance)

---

## Post-Deployment Checklist

### Testing

- [ ] **Authentication Testing**
  - Test login with valid credentials
  - Test login with invalid credentials
  - Test signup process with OTP verification
  - Test session timeout (wait 8+ hours or modify timeout for testing)
  - Test "Remember Me" functionality
  - Test logout and session destruction
  - Test auto-redirect when already logged in
  - Verify users can only see their assigned groups' data

- [ ] **Role-Based Access Control (RBAC) Testing**
  - **Admin Role:**
    - Verify Admin can access Admin Dashboard
    - Verify Admin sees all projects/accounts/products
    - Verify Admin can manage users (view, edit, delete, role assignment)
    - Test project creation and auto-group assignment
  - **Contributor Role:**
    - Verify Contributor can create new projects
    - Verify created projects auto-assign to Contributor's groups
    - Verify Contributor only sees assigned groups' data
    - Verify Contributor cannot access Admin Dashboard
    - Test blank state when no project selected
  - **User Role:**
    - Verify User cannot create projects
    - Verify User only sees assigned groups' data
    - Verify User cannot access Admin Dashboard
    - Test blank state enforcement

- [ ] **General Functionality Testing**
  - Access web interface via production URL
  - Test database connections from production server
  - Run sample validation end-to-end
  - Download Excel and HTML reports
  - Test all validation types
  - Verify logs are being written
  - Test with large datasets
  - Cross-browser testing (Chrome, Edge, Firefox, Safari)
  - Mobile responsiveness testing

--- Security

- [ ] **Enable HTTPS/SSL**
  - Install SSL certificate
  - Configure forced HTTPS redirect
  - Verify certificate validity

- [ ] **Configure User Authentication**
  - ✅ Authentication system already implemented
  - Change default admin password immediately
  - Create additional admin users as needed
  - Review and approve pending user signups
  - Set appropriate roles (Admin, Contributor, User) for all users
  - Assign groups based on project/account access requirements
  - Test login/logout functionality
  - Verify session timeout works correctly (default: 8 hours)
  - Test RBAC filtering (users should only see their assigned groups' data)

- [ ] **Secure User Database**
  - Move `users.xlsx` to secure location outside web root
  - Set restrictive file permissions (read/write only for app service account)
  - Set up automated backups of users.xlsx
  - Consider migrating to SQL database for enterprise scalability
  - Enable audit logging for user management operations

- [ ] **Configure Firewall**
  - Restrict access by IP (if applicable)
  - Block unauthorized ports
  - Enable DDoS protection (if available)

- [ ] **Secure Secrets**
  - Use Azure Key Vault or AWS Secrets Manager
  - Remove secrets from code
  - Implement secret rotation

- [ ] **Enable Logging**
  - Configure application logs
  - Set up access logs
  - Enable audit logging
  - Log all authentication events (login, logout, failed attempts)
  - Log all admin operations (role changes, user deletions)

--- Monitoring

- [ ] **Set up Monitoring**
  - Application uptime monitoring (Pingdom, UptimeRobot)
  - Performance monitoring (New Relic, DataDog)
  - Error tracking (Sentry, Rollbar)

- [ ] **Configure Alerts**
  - Email alerts for errors
  - SMS alerts for downtime
  - Slack/Teams integration

- [ ] **Log Management**
  - Set up log rotation
  - Configure log retention policy
  - Centralized logging (ELK stack, Azure Monitor)

### Documentation

- [ ] **User Documentation**
  - User manual/guide
  - Video tutorials
  - FAQ document
  - Troubleshooting guide

- [ ] **Admin Documentation**
  - Deployment guide
  - Maintenance procedures
  - Backup/restore procedures
  - Disaster recovery plan

- [ ] **Training**
  - Schedule training sessions
  - Create training materials
  - Designate support personnel

### Backup & Recovery

- [ ] **Implement Backup Strategy**
  - Daily backup of configurations
  - Weekly backup of reports (if needed)
  - Monthly off-site backup

- [ ] **Test Recovery Procedures**
  - Restore from backup
  - Validate functionality
  - Document recovery time

---

## Maintenance Schedule

### Daily
- Monitor application logs
- Check error rates
- Verify uptime

### Weekly
- Review performance metrics
- Check disk space
- Clean up old logs/reports

### Monthly
- Update Python packages (`pip install --upgrade -r requirements.txt`)
- Security vulnerability scan
- Backup configuration files
- Review user feedback

### Quarterly
- Major version updates
- Performance optimization review
- Infrastructure capacity planning
- Security audit

---

## Cost Estimates

### Self-Hosted (On-Premises)

| Item | One-Time | Annual |
|------|----------|--------|
| Server Hardware | $2,000 - $5,000 | - |
| Windows Server License | - | $500+ |
| SSL Certificate | - | $100 |
| Power & Cooling | - | $500 |
| **Total** | **$2,000 - $5,000** | **~$1,100** |

### Cloud Hosting

| Provider | Service | Monthly Cost |
|----------|---------|--------------|
| **Azure** | App Service (B1) | $55 |
| **AWS** | Elastic Beanstalk (t2.small) | $40 |
| **Google Cloud** | Cloud Run | $20 - $50 |
| **DigitalOcean** | Droplet (2GB RAM) | $18 |

**Additional Costs:**
- SSL Certificate: $0 (Let's Encrypt) - $100/year
- Domain Name: $10 - $50/year
- Monitoring: $0 - $100/month
- Backup Storage: $5 - $20/month

---

## Required Files for Deployment

### Minimum Required Files

```
📦 Deployment Package
├── 📂 backend/
│   ├── api.py                    ✅ REQUIRED
│   ├── requirements.txt          ✅ REQUIRED
│   └── .env                      ✅ REQUIRED (create from template)
├── 📂 DataValidation/
│   ├── requirements.txt          ✅ REQUIRED
│   ├── 📂 config/
│   │   ├── db_config.py          ✅ REQUIRED
│   │   ├── data_sources.json    ⚠️  OPTIONAL (if not using saved connections)
│   │   └── secrets.py           ✅ REQUIRED
│   ├── 📂 src/
│   │   ├── validate.py          ✅ REQUIRED
│   │   ├── report_generator.py  ✅ REQUIRED
│   │   ├── extract.py           ✅ REQUIRED
│   │   ├── transform.py         ✅ REQUIRED
│   │   └── load.py              ✅ REQUIRED
│   ├── 📂 logs/                 ✅ REQUIRED (create directory)
│   └── 📂 reports/              ✅ REQUIRED (create directory)
├── 📂 frontend/
│   ├── index.html               ✅ REQUIRED
│   └── 📂 assets/
│       └── etl-hero-banner.jpg  ⚠️  OPTIONAL
├── web.config                   ⚠️  REQUIRED for IIS
├── startup.sh                   ⚠️  REQUIRED for Linux
└── Dockerfile                   ⚠️  REQUIRED for Docker
```

---

## Go-Live Checklist

**24 Hours Before:**
- [ ] Final testing completed
- [ ] Backup created
- [ ] Team notified
- [ ] Rollback plan ready

**Go-Live Day:**
- [ ] Deploy application
- [ ] Verify deployment successful
- [ ] Run smoke tests
- [ ] Monitor for 2 hours
- [ ] Notify users

**Post Go-Live:**
- [ ] Monitor logs for 24 hours
- [ ] Collect user feedback
- [ ] Address immediate issues
- [ ] Document lessons learned

---

## Support Contacts

**Technical Support:** support@winwire.com  
**Emergency Hotline:** [Your number]  
**Documentation:** [Wiki/Confluence URL]  
**Issue Tracking:** [JIRA/DevOps URL]

---

**You're ready to publish! Good luck! 🚀**

*Last Updated: April 8, 2026*
