"""
Generate comprehensive ETL Framework Documentation in Word format
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime

def add_heading_with_color(doc, text, level, color=(0, 102, 204)):
    """Add a colored heading to the document"""
    heading = doc.add_heading(text, level)
    run = heading.runs[0]
    run.font.color.rgb = RGBColor(*color)
    return heading

def add_bullet_point(doc, text, level=0):
    """Add a bullet point with indentation"""
    paragraph = doc.add_paragraph(text, style='List Bullet')
    if level > 0:
        paragraph.paragraph_format.left_indent = Inches(0.5 * level)
    return paragraph

def add_numbered_point(doc, text):
    """Add a numbered point"""
    return doc.add_paragraph(text, style='List Number')

def add_table_with_style(doc, data, headers):
    """Add a styled table to the document"""
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    # Add headers
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        # Make header bold
        for paragraph in hdr_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    # Add data rows
    for row_data in data:
        row_cells = table.add_row().cells
        for i, cell_data in enumerate(row_data):
            row_cells[i].text = str(cell_data)
    
    return table

def add_code_block(doc, code, language="python"):
    """Add a code block with formatting"""
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.5)
    run = paragraph.add_run(code)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    # Light gray background
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), 'F0F0F0')
    paragraph._element.get_or_add_pPr().append(shading_elm)
    return paragraph

def create_documentation():
    """Create the complete framework documentation"""
    doc = Document()
    
    # ========== TITLE PAGE ==========
    title = doc.add_heading('ETL Validation Framework', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.runs[0]
    title_run.font.size = Pt(36)
    title_run.font.color.rgb = RGBColor(0, 102, 204)
    
    subtitle = doc.add_paragraph('Comprehensive Data Validation & Quality Framework')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.runs[0].font.size = Pt(16)
    subtitle.runs[0].font.italic = True
    
    doc.add_paragraph()
    
    version_info = doc.add_paragraph(f'Version: 1.0.0\nGenerated: {datetime.now().strftime("%B %d, %Y")}')
    version_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_page_break()
    
    # ========== TABLE OF CONTENTS ==========
    add_heading_with_color(doc, 'Table of Contents', 1)
    toc_items = [
        '1. Executive Overview',
        '2. Framework Architecture',
        '3. Key Features & Capabilities',
        '4. Core Components',
        '5. Data Source Support',
        '6. Validation Types',
        '7. Web Interface',
        '8. API Endpoints',
        '9. Testing Framework',
        '10. Reports & Dashboards',
        '11. Installation & Configuration',
        '12. Usage Examples',
        '13. Best Practices',
        '14. Technical Specifications'
    ]
    for item in toc_items:
        doc.add_paragraph(item, style='List Number')
    
    doc.add_page_break()
    
    # ========== 1. EXECUTIVE OVERVIEW ==========
    add_heading_with_color(doc, '1. Executive Overview', 1)
    
    doc.add_paragraph(
        'The ETL Validation Framework is an enterprise-grade, comprehensive data validation and '
        'quality assurance solution designed for modern data engineering pipelines. Built with '
        'Python, PyTest, FastAPI, and a modern web interface, it provides end-to-end validation '
        'of Extract, Transform, and Load (ETL) processes across multiple data platforms.'
    )
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Key Highlights:', 2, color=(204, 0, 0))
    
    highlights = [
        'Web-based user interface with real-time execution monitoring',
        'Support for 15+ data sources including SQL Server, Azure Synapse, Microsoft Fabric, Oracle, MySQL, PostgreSQL, MongoDB, and more',
        'Medallion Architecture support for Bronze/Silver/Gold layer validation',
        'Comprehensive validation suite: Structure, Count, Null, Duplicate, and Row-wise Data validation',
        'Automated report generation in Excel, HTML, JSON, and Power BI formats',
        'PyTest integration for CI/CD pipelines',
        'RESTful API for programmatic access',
        'Configurable validation rules and data sources',
        'Real-time log viewing and execution history tracking'
    ]
    for highlight in highlights:
        add_bullet_point(doc, highlight)
    
    doc.add_page_break()
    
    # ========== 2. FRAMEWORK ARCHITECTURE ==========
    add_heading_with_color(doc, '2. Framework Architecture', 1)
    
    doc.add_paragraph(
        'The framework follows a modular, layered architecture that separates concerns and '
        'enables independent scaling and maintenance of components.'
    )
    
    add_heading_with_color(doc, 'Architecture Layers:', 2, color=(204, 0, 0))
    
    arch_layers = [
        ('Presentation Layer', 'Web UI (HTML/CSS/JavaScript), RESTful API (FastAPI)'),
        ('Business Logic Layer', 'ETL Core (Extract, Transform, Load, Validate), Report Generators'),
        ('Data Access Layer', 'Database Connectors, API Clients, File Handlers'),
        ('Configuration Layer', 'Data Sources Config, Validation Rules, Environment Variables'),
        ('Testing Layer', 'PyTest Test Suite, Fixtures, Test Data')
    ]
    
    for layer, description in arch_layers:
        p = doc.add_paragraph()
        p.add_run(f'{layer}: ').bold = True
        p.add_run(description)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Project Structure:', 2, color=(204, 0, 0))
    
    structure_code = '''ETL_DEMO_Pytest14/
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
│   │   └── __pycache__/
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
│   │   └── __pycache__/
│   │
│   ├── tests/                        # PyTest Test Suite
│   │   ├── conftest.py               # PyTest fixtures & configuration
│   │   ├── test_validate.py          # Validation function tests
│   │   ├── test_extract.py           # Extraction tests
│   │   ├── test_transform.py         # Transformation tests
│   │   ├── test_main.py              # Integration tests
│   │   └── __pycache__/
│   │
│   ├── DataValidation/               # Nested validation workspace
│   │   ├── logs/                     # Workspace-specific logs
│   │   └── reports/                  # Workspace-specific reports
│   │
│   ├── logs/                         # Main Execution Logs
│   │   ├── etl_log.txt               # General ETL execution logs
│   │   ├── duplicate_combined_log.txt # Duplicate record logs
│   │   └── row_data_mismatch_log.txt # Row-level mismatch logs
│   │
│   ├── reports/                      # Generated Reports
│   │   ├── etl_dashboard.html        # HTML dashboard
│   │   ├── etl_validation_report.xlsx # Excel report
│   │   ├── validation_results.json   # JSON report
│   │   └── loaded_data.csv           # Loaded data output
│   │
│   ├── uploads/                      # File Upload Storage
│   ├── test_data/                    # Test Datasets
│   │   └── sample_input.csv
│   │
│   ├── .env.example                  # Environment variables template
│   ├── .github/                      # GitHub configurations
│   ├── main.py                       # Main ETL pipeline orchestrator
│   ├── generate_test_report.py       # PyTest report generator
│   ├── pytest.ini                    # PyTest configuration
│   ├── requirements.txt              # Framework dependencies
│   ├── README.md                     # Framework documentation
│   └── __pycache__/
│
├── etl_project_two_tables/           # Sample Project Workspace
│   ├── logs/                         # Project execution logs
│   ├── reports/                      # Project reports
│   └── uploads/                      # Project file uploads
│
├── Documentation & Guides
├── ETL_Validation_Framework_Documentation.docx # 60+ page documentation
├── AZURE_SUPPORT.md                  # Azure integration guide
├── MEDALLION_QUICKSTART.md           # Medallion architecture guide
├── UI_IMPLEMENTATION_GUIDE.md        # Web UI guide
├── VALIDATION_FIX_README.md          # Validation fixes
│
├── Configuration & Setup Files
├── run_server.bat                    # Windows quick-start script
├── generate_framework_documentation.py # Doc generator script
├── test_mismatch_report.py           # Mismatch report utility
├── openapi.json                      # OpenAPI specification
│
├── .venv/                            # Python virtual environment
├── .pytest_cache/                    # PyTest cache
└── README.md                         # Main documentation'''
    
    add_code_block(doc, structure_code, 'text')
    
    doc.add_page_break()
    
    # ========== 3. KEY FEATURES & CAPABILITIES ==========
    add_heading_with_color(doc, '3. Key Features & Capabilities', 1)
    
    features_sections = {
        'Data Source Support': [
            'Relational Databases: SQL Server, MySQL, PostgreSQL, Oracle',
            'Cloud Data Warehouses: Azure Synapse Analytics, Databricks Unity Catalog',
            'Microsoft Fabric: Bronze/Silver/Gold Medallion Architecture',
            'NoSQL Databases: MongoDB, Cassandra, DynamoDB',
            'Cloud Storage: AWS S3, Azure Blob Storage, Google Cloud Storage',
            'Flat Files: CSV, Excel, JSON, XML',
            'REST APIs and Web Services',
            'Power BI Datasets, Dataflows, and Semantic Models'
        ],
        'Validation Capabilities': [
            'Structure Validation: Schema comparison, data type verification, primary key validation',
            'Record Count Validation: Source vs target count comparison with detailed statistics',
            'Null Check: Constraint violations, missing data detection, null pattern analysis',
            'Duplicate Check: Composite key duplicates, single column duplicates, intelligent detection',
            'Row-wise Data Validation: Complete record-by-record comparison with mismatch reporting',
            'Data Freshness Validation: SLA compliance checking, timestamp validation',
            'Referential Integrity: Foreign key validation, relationship verification',
            'Data Quality Metrics: Completeness, accuracy, consistency, timeliness'
        ],
        'Automation & Integration': [
            'Rule-based validation execution from JSON configuration',
            'Scheduled validation jobs with cron-like syntax',
            'CI/CD pipeline integration (GitHub Actions, Azure DevOps, Jenkins)',
            'Event-driven validation triggers',
            'Parallel validation job execution for performance',
            'Metadata-driven automation for dynamic table discovery',
            'Integration with Airflow, Azure Data Factory, dbt'
        ],
        'Reporting & Analytics': [
            'Excel Reports: Multi-sheet reports with executive summary, detailed findings',
            'HTML Dashboards: Interactive visualizations with charts and metrics',
            'JSON Reports: Machine-readable format for downstream systems',
            'Power BI Integration: Direct dataset validation and measure verification',
            'Real-time Log Viewing: ETL logs, duplicate logs, mismatch logs',
            'Execution History: Track validation runs over time',
            'Data Quality Scorecards: KPI tracking and trend analysis'
        ],
        'Security & Compliance': [
            'Environment variable-based credential management',
            'Support for Azure Key Vault integration',
            'Data masking and anonymization capabilities',
            'Audit trail of all validation executions',
            'Row-level security validation for Power BI',
            'Compliance checking (GDPR, HIPAA, SOX)',
            'Secure token management for API authentication'
        ]
    }
    
    for section_title, items in features_sections.items():
        add_heading_with_color(doc, section_title, 2, color=(204, 0, 0))
        for item in items:
            add_bullet_point(doc, item)
        doc.add_paragraph()
    
    doc.add_page_break()
    
    # ========== 4. CORE COMPONENTS ==========
    add_heading_with_color(doc, '4. Core Components', 1)
    
    components = {
        'Extract Module (extract.py)': {
            'Purpose': 'Extract data from various source systems',
            'Key Functions': [
                'extract_data(cursor, table_name): Fetches all data from a specified table',
                'Supports SQL queries, file reading, API calls',
                'Returns column metadata and raw data'
            ],
            'Example': 'columns, data = extract_data(cursor, "dbo.emp_source")'
        },
        'Transform Module (transform.py)': {
            'Purpose': 'Apply business rules and transformations to extracted data',
            'Key Functions': [
                'transform_data(columns, data): Applies column mapping and transformations',
                'Intelligent column name normalization',
                'Data type conversions and formatting',
                'Business rule application (e.g., name capitalization)'
            ],
            'Example': 'transformed_data = transform_data(columns, raw_data)'
        },
        'Load Module (load.py)': {
            'Purpose': 'Load transformed data into target destination',
            'Key Functions': [
                'load_data(data, filename): Writes data to CSV or other formats',
                'Supports database inserts, file writes, API posts',
                'Automatic directory creation and error handling'
            ],
            'Example': 'load_data(transformed_data, "reports/loaded_data.csv")'
        },
        'Validate Module (validate.py)': {
            'Purpose': 'Execute comprehensive data validation checks',
            'Key Functions': [
                'structure_validation(cursor, table1, table2): Compare schemas',
                'count_validation(cursor, table1, table2): Compare record counts',
                'null_check(cursor, table): Identify null/constraint violations',
                'duplicate_check(cursor, table, columns): Find duplicate records',
                'row_data_validation(cursor, table1, table2, mapping): Row-by-row comparison'
            ],
            'Example': 'passed, output = structure_validation(cursor, src, tgt)'
        },
        'Report Generator (report_generator.py)': {
            'Purpose': 'Generate comprehensive validation reports',
            'Key Functions': [
                'generate_excel_report(results): Creates multi-sheet Excel workbook',
                'generate_html_dashboard(results): Interactive HTML dashboard',
                'generate_json_report(results): Machine-readable JSON output',
                'generate_powerbi_dashboard(results): Power BI report generation'
            ],
            'Example': 'excel_path = generate_excel_report(validation_results)'
        },
        'Main Orchestrator (main.py)': {
            'Purpose': 'Coordinate the entire ETL validation pipeline',
            'Key Functions': [
                'run_etl(source_query, target_query, source_type, target_type): Main entry point',
                'Intelligent column mapping between source and target',
                'Sequential execution of all validations',
                'Report and log generation',
                'Success/failure determination'
            ],
            'Example': 'success = run_etl("SELECT * FROM source", "SELECT * FROM target")'
        }
    }
    
    for component_name, details in components.items():
        add_heading_with_color(doc, component_name, 2, color=(0, 102, 0))
        
        p = doc.add_paragraph()
        p.add_run('Purpose: ').bold = True
        p.add_run(details['Purpose'])
        
        doc.add_paragraph('Key Functions:').runs[0].bold = True
        for func in details['Key Functions']:
            add_bullet_point(doc, func)
        
        p = doc.add_paragraph()
        p.add_run('Usage Example: ').bold = True
        add_code_block(doc, details['Example'])
        
        doc.add_paragraph()
    
    doc.add_page_break()
    
    # ========== 5. DATA SOURCE SUPPORT ==========
    add_heading_with_color(doc, '5. Data Source Support', 1)
    
    doc.add_paragraph(
        'The framework supports a wide variety of data sources through a unified connection '
        'interface defined in config/data_sources.json. Each connector type has specific '
        'configuration requirements.'
    )
    
    data_sources = [
        ['Data Source', 'Type', 'Authentication', 'Key Features'],
        ['SQL Server', 'sqlserver', 'Windows Auth / SQL Auth', 'Full T-SQL support, ODBC Driver 17'],
        ['Azure Synapse', 'synapse', 'Azure AD / SQL Auth', 'Dedicated/Serverless pools, MPP queries'],
        ['Microsoft Fabric', 'fabric', 'Azure AD / Service Principal', 'Medallion architecture, OneLake'],
        ['MySQL', 'mysql', 'Username/Password', 'Standard SQL, InnoDB support'],
        ['PostgreSQL', 'postgresql', 'Username/Password', 'Advanced SQL, JSON support'],
        ['Oracle', 'oracle', 'Username/Password', 'PL/SQL, RAC support'],
        ['MongoDB', 'mongodb', 'Connection URI', 'NoSQL, document queries'],
        ['Databricks', 'databricks', 'Personal Token', 'Unity Catalog, SQL Warehouse'],
        ['Power BI', 'powerbi', 'OAuth / Service Principal', 'Dataset REST API, DAX queries'],
        ['AWS S3', 's3', 'Access Key/Secret', 'Object storage, CSV/Parquet'],
        ['REST API', 'api', 'API Key / OAuth', 'Custom endpoints, JSON/XML']
    ]
    
    add_table_with_style(doc, data_sources[1:], data_sources[0])
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Configuration Example:', 2, color=(204, 0, 0))
    
    config_example = '''{
  "default": {
    "type": "sqlserver",
    "driver": "ODBC Driver 17 for SQL Server",
    "server": "SERVER_NAME",
    "database": "DATABASE_NAME",
    "trusted_connection": "yes"
  },
  "azure_synapse": {
    "type": "synapse",
    "server": "synapse-workspace.sql.azuresynapse.net",
    "database": "pool_name",
    "authentication": "ActiveDirectoryPassword",
    "username": "user@domain.com",
    "password": "${AZURE_PASSWORD}"
  }
}'''
    
    add_code_block(doc, config_example, 'json')
    
    doc.add_page_break()
    
    # ========== 6. VALIDATION TYPES ==========
    add_heading_with_color(doc, '6. Validation Types', 1)
    
    validations = {
        'Structure Validation': {
            'Description': 'Compares the schema of source and target tables to ensure structural compatibility.',
            'Checks': [
                'Column names and ordering',
                'Data types consistency (VARCHAR, INT, DATE, etc.)',
                'Primary key definitions',
                'Nullable constraints',
                'Schema compatibility score'
            ],
            'Output': 'Pass/Fail with detailed column-by-column comparison',
            'Use Cases': [
                'Schema migration verification',
                'ETL pipeline initial setup validation',
                'Database refactoring impact analysis'
            ]
        },
        'Record Count Validation': {
            'Description': 'Verifies that the number of records in source and target tables match, accounting for filters.',
            'Checks': [
                'Total row count in source',
                'Total row count in target',
                'Count difference calculation',
                'Percentage match calculation'
            ],
            'Output': 'Pass (if counts match) / Fail (with count details)',
            'Use Cases': [
                'Data load completeness verification',
                'Incremental load validation',
                'Data loss detection'
            ]
        },
        'Null Check': {
            'Description': 'Identifies NULL values in columns and validates against constraints.',
            'Checks': [
                'Columns with NULL values',
                'Count of NULLs per column',
                'Constraint violations (NOT NULL columns with NULL values)',
                'NULL pattern analysis'
            ],
            'Output': 'List of columns with NULLs and violation details',
            'Use Cases': [
                'Data quality assessment',
                'Mandatory field validation',
                'Constraint compliance checking'
            ]
        },
        'Duplicate Check': {
            'Description': 'Detects duplicate records based on primary key or composite key combinations.',
            'Checks': [
                'Single column duplicates',
                'Composite key duplicates (multiple columns)',
                'Duplicate count and affected records',
                'Intelligent duplicate detection with smart column selection'
            ],
            'Output': 'List of duplicate records with full row details',
            'Use Cases': [
                'Primary key violation detection',
                'Data deduplication requirements',
                'Unique constraint verification'
            ]
        },
        'Row-wise Data Validation': {
            'Description': 'Performs complete record-by-record comparison between source and target tables.',
            'Checks': [
                'Field-level value matching',
                'Records only in source (missing in target)',
                'Records only in target (extra records)',
                'Mismatched field values with before/after comparison',
                'Intelligent column mapping between different schemas'
            ],
            'Output': 'Detailed mismatch report with exact differences',
            'Use Cases': [
                'Data transformation accuracy verification',
                'Data synchronization validation',
                'Migration completeness testing'
            ]
        }
    }
    
    for validation_name, details in validations.items():
        add_heading_with_color(doc, validation_name, 2, color=(0, 102, 0))
        
        doc.add_paragraph(details['Description'])
        
        doc.add_paragraph('What It Checks:').runs[0].bold = True
        for check in details['Checks']:
            add_bullet_point(doc, check)
        
        p = doc.add_paragraph()
        p.add_run('Output Format: ').bold = True
        p.add_run(details['Output'])
        
        doc.add_paragraph('Common Use Cases:').runs[0].bold = True
        for use_case in details['Use Cases']:
            add_bullet_point(doc, use_case)
        
        doc.add_paragraph()
    
    doc.add_page_break()
    
    # ========== 7. WEB INTERFACE ==========
    add_heading_with_color(doc, '7. Web Interface', 1)
    
    doc.add_paragraph(
        'The framework includes a modern, responsive web interface built with HTML, CSS, and '
        'JavaScript. The UI provides an intuitive way to configure and execute validations '
        'without writing code.'
    )
    
    add_heading_with_color(doc, 'Key Interface Features:', 2, color=(204, 0, 0))
    
    ui_features = [
        'Database Connection Manager: Configure multiple data sources',
        'Table Selection: Dropdown lists populated from database metadata',
        'Custom Query Input: Enter complex SQL queries for source and target',
        'Validation Selector: Checkboxes to choose which validations to run',
        'Real-time Execution: Progress indicators and live status updates',
        'Report Viewer: Inline display of HTML dashboards',
        'Log Viewer: Tabs for ETL logs, duplicate logs, and mismatch logs',
        'Download Reports: Excel, JSON, and dashboard downloads',
        'Execution History: Timeline of past validation runs with results',
        'Power BI Integration: Browse datasets, execute DAX queries'
    ]
    
    for feature in ui_features:
        add_bullet_point(doc, feature)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'User Workflow:', 2, color=(204, 0, 0))
    
    workflow_steps = [
        'Access the web interface at http://localhost:8000',
        'Configure data source connections (optional - uses default config)',
        'Select or enter source table/query',
        'Select or enter target table/query',
        'Choose validation types to execute',
        'Click "Run Validation" or "Run PyTest"',
        'Monitor real-time execution progress',
        'Review results in the dashboard',
        'Download reports for further analysis',
        'Check detailed logs for issues'
    ]
    
    for i, step in enumerate(workflow_steps, 1):
        add_numbered_point(doc, step)
    
    doc.add_page_break()
    
    # ========== 8. API ENDPOINTS ==========
    add_heading_with_color(doc, '8. API Endpoints', 1)
    
    doc.add_paragraph(
        'The FastAPI backend exposes RESTful endpoints for programmatic access to all '
        'framework functionality. This enables integration with external systems and automation.'
    )
    
    api_endpoints = [
        ['Endpoint', 'Method', 'Description', 'Parameters'],
        ['/api/health', 'GET', 'Health check endpoint', 'None'],
        ['/api/tables', 'GET', 'List all available tables', 'db_type (optional)'],
        ['/api/validations', 'GET', 'Get available validation types', 'None'],
        ['/api/run', 'POST', 'Execute validation pipeline', 'source_query, target_query, validations, source_type, target_type'],
        ['/api/run-pytest', 'POST', 'Run via PyTest framework', 'source_query, target_query, validations'],
        ['/api/download/excel', 'GET', 'Download Excel report', 'None'],
        ['/api/dashboard', 'GET', 'Get HTML dashboard content', 'None'],
        ['/api/logs/{type}', 'GET', 'Retrieve log files', 'type: etl|duplicate|mismatch'],
        ['/api/history', 'GET', 'Get execution history', 'limit (optional)'],
        ['/api/test-connection', 'POST', 'Test database connection', 'db_type, connection_params'],
        ['/docs', 'GET', 'Interactive API documentation (Swagger)', 'None']
    ]
    
    add_table_with_style(doc, api_endpoints[1:], api_endpoints[0])
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'API Usage Example:', 2, color=(204, 0, 0))
    
    api_example = '''import requests
import json

# Execute validation
url = "http://localhost:8000/api/run"
payload = {
    "source_query": "SELECT * FROM dbo.emp_source",
    "target_query": "SELECT * FROM dbo.emp_target",
    "validations": ["structure", "count", "null", "duplicate", "row_data"],
    "source_type": "default",
    "target_type": "default"
}

response = requests.post(url, json=payload)
result = response.json()

if result["status"] == "success":
    print(f"Validation passed: {result['passed']}")
    print(f"Excel report: {result['excel_report']}")
else:
    print(f"Error: {result['message']}")'''
    
    add_code_block(doc, api_example)
    
    doc.add_page_break()
    
    # ========== 9. TESTING FRAMEWORK ==========
    add_heading_with_color(doc, '9. Testing Framework', 1)
    
    doc.add_paragraph(
        'The framework is built with PyTest for robust, automated testing. Test cases cover '
        'all core functionality and can be integrated into CI/CD pipelines.'
    )
    
    add_heading_with_color(doc, 'Test Suite Structure:', 2, color=(204, 0, 0))
    
    test_files = [
        ('tests/conftest.py', 'PyTest configuration and shared fixtures'),
        ('tests/test_validate.py', 'Validation function tests'),
        ('tests/test_extract.py', 'Data extraction tests'),
        ('tests/test_transform.py', 'Data transformation tests'),
        ('tests/test_main.py', 'End-to-end integration tests')
    ]
    
    for test_file, description in test_files:
        p = doc.add_paragraph()
        p.add_run(f'{test_file}: ').bold = True
        p.add_run(description)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Running Tests:', 2, color=(204, 0, 0))
    
    test_commands = '''# Run all tests
pytest -v

# Run specific test file
pytest tests/test_validate.py -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run with allure reporting
pytest --alluredir=allure-results
allure serve allure-results

# Run in CI/CD mode
pytest --junitxml=test-results.xml'''
    
    add_code_block(doc, test_commands, 'bash')
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Test Fixtures:', 2, color=(204, 0, 0))
    
    doc.add_paragraph(
        'The conftest.py file provides reusable fixtures for database connections, '
        'sample data, and test configuration:'
    )
    
    fixture_example = '''@pytest.fixture
def sample_dataframe():
    """Provide sample test data"""
    data = {
        "id": [1, 2, 3],
        "name": ["A", "B", "C"],
        "salary": [1000, 2000, 3000]
    }
    return pd.DataFrame(data)

@pytest.fixture
def db_connection():
    """Provide database connection for tests"""
    conn = create_connection('default')
    yield conn
    conn.close()'''
    
    add_code_block(doc, fixture_example)
    
    doc.add_page_break()
    
    # ========== 10. REPORTS & DASHBOARDS ==========
    add_heading_with_color(doc, '10. Reports & Dashboards', 1)
    
    doc.add_paragraph(
        'The framework generates comprehensive, professional reports in multiple formats '
        'to suit different audiences and use cases.'
    )
    
    reports = {
        'Excel Report (XLSX)': {
            'Sheets': [
                'Executive Summary: High-level pass/fail status, key metrics',
                'Mismatch Records: Source vs Target comparison with side-by-side view',
                'Duplicate Records (Source): Detailed duplicate entries from source',
                'Duplicate Records (Target): Detailed duplicate entries from target',
                'Structure Details: Column-by-column schema comparison',
                'Validation Logs: Complete execution logs'
            ],
            'Features': [
                'Color-coded cells (green=pass, red=fail)',
                'Formatted tables with headers',
                'Formulas for calculations',
                'Print-ready layout'
            ],
            'Use Case': 'Business stakeholders, audit documentation, compliance reporting'
        },
        'HTML Dashboard': {
            'Sections': [
                'Summary Cards: Count matches, structure status, data quality score',
                'Validation Results: Visual pass/fail indicators',
                'Charts & Graphs: Pie charts for validation distribution',
                'Detailed Findings: Expandable sections for each validation',
                'Log Preview: Inline log viewing'
            ],
            'Features': [
                'Responsive design for mobile/desktop',
                'Interactive elements (tooltips, collapsible sections)',
                'Professional styling with modern CSS',
                'Direct hyperlinks to source data'
            ],
            'Use Case': 'Real-time monitoring, web-based reporting, dashboard embedding'
        },
        'JSON Report': {
            'Structure': [
                'Metadata: Execution timestamp, source/target info',
                'Results: Structured validation outcomes',
                'Metrics: Counts, percentages, quality scores',
                'Findings: Arrays of issues and successes'
            ],
            'Features': [
                'Machine-readable format',
                'Easy parsing and integration',
                'Nested structure for complex data',
                'Complete audit trail'
            ],
            'Use Case': 'API consumers, data pipeline integration, automated processing'
        },
        'Power BI Report': {
            'Components': [
                'Dataset Validation: Schema and metadata verification',
                'Measure Validation: DAX expression testing',
                'Visual Validation: Report element checking',
                'Row-Level Security: RLS rule validation'
            ],
            'Features': [
                'Direct Power BI REST API integration',
                'DAX query execution and validation',
                'Workspace and dataset browsing',
                'Service principal authentication support'
            ],
            'Use Case': 'Power BI governance, BI testing, semantic model validation'
        }
    }
    
    for report_type, details in reports.items():
        add_heading_with_color(doc, report_type, 2, color=(0, 102, 0))
        
        if 'Sheets' in details:
            doc.add_paragraph('Report Sheets:').runs[0].bold = True
            for sheet in details['Sheets']:
                add_bullet_point(doc, sheet)
        elif 'Sections' in details:
            doc.add_paragraph('Dashboard Sections:').runs[0].bold = True
            for section in details['Sections']:
                add_bullet_point(doc, section)
        elif 'Structure' in details:
            doc.add_paragraph('JSON Structure:').runs[0].bold = True
            for struct in details['Structure']:
                add_bullet_point(doc, struct)
        elif 'Components' in details:
            doc.add_paragraph('Validation Components:').runs[0].bold = True
            for comp in details['Components']:
                add_bullet_point(doc, comp)
        
        doc.add_paragraph('Key Features:').runs[0].bold = True
        for feature in details['Features']:
            add_bullet_point(doc, feature)
        
        p = doc.add_paragraph()
        p.add_run('Best Use Case: ').bold = True
        p.add_run(details['Use Case'])
        
        doc.add_paragraph()
    
    doc.add_page_break()
    
    # ========== 11. INSTALLATION & CONFIGURATION ==========
    add_heading_with_color(doc, '11. Installation & Configuration', 1)
    
    add_heading_with_color(doc, 'System Requirements:', 2, color=(204, 0, 0))
    
    requirements = [
        'Python 3.8 or higher',
        'SQL Server with ODBC Driver 17 for SQL Server (for SQL Server sources)',
        'pip package manager',
        'Windows, Linux, or macOS operating system',
        'Minimum 4GB RAM (8GB recommended for large datasets)',
        'Network access to target data sources'
    ]
    
    for req in requirements:
        add_bullet_point(doc, req)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Installation Steps:', 2, color=(204, 0, 0))
    
    install_steps = [
        'Clone or download the project repository',
        'Navigate to the project directory',
        'Install Python dependencies: pip install -r backend/requirements.txt',
        'Configure database connections in DataValidation/config/data_sources.json',
        'Set up environment variables (optional for secure credential storage)',
        'Test the installation: python -m pytest -v'
    ]
    
    for i, step in enumerate(install_steps, 1):
        add_numbered_point(doc, step)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Configuration Files:', 2, color=(204, 0, 0))
    
    config_files = [
        ('data_sources.json', 'Define database connections and credentials'),
        ('validation_rules.json', 'Configure automated validation rules'),
        ('db_config.py', 'Connection factory and helper functions'),
        ('pytest.ini', 'PyTest configuration and test discovery'),
        ('.env (optional)', 'Environment variables for sensitive data')
    ]
    
    for config_file, purpose in config_files:
        p = doc.add_paragraph()
        p.add_run(f'{config_file}: ').bold = True
        p.add_run(purpose)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Starting the Application:', 2, color=(204, 0, 0))
    
    start_commands = '''# Windows - Quick Start
run_server.bat

# Manual Start (All Platforms)
cd backend
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Access Points
# Web UI: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Health Check: http://localhost:8000/api/health'''
    
    add_code_block(doc, start_commands, 'bash')
    
    doc.add_page_break()
    
    # ========== 12. USAGE EXAMPLES ==========
    add_heading_with_color(doc, '12. Usage Examples', 1)
    
    add_heading_with_color(doc, 'Example 1: Simple Validation', 2, color=(0, 102, 0))
    
    example1 = '''from main import run_etl

# Validate two tables with default settings
success, excel, json_report, powerbi, html = run_etl(
    source_query="SELECT * FROM dbo.emp_source",
    target_query="SELECT * FROM dbo.emp_target",
    source_type="default",
    target_type="default"
)

if success:
    print("✅ Validation passed!")
    print(f"Excel report: {excel}")
else:
    print("❌ Validation failed - check reports for details")'''
    
    add_code_block(doc, example1)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Example 2: Custom Query Validation', 2, color=(0, 102, 0))
    
    example2 = '''# Compare filtered datasets
source_query = """
SELECT employee_id, first_name, last_name, salary
FROM dbo.employees
WHERE department = 'Sales' AND hire_date >= '2023-01-01'
"""

target_query = """
SELECT emp_id, fname, lname, compensation
FROM dbo.employee_archive
WHERE dept = 'Sales' AND start_date >= '2023-01-01'
"""

success, excel, json_report, powerbi, html = run_etl(
    source_query=source_query,
    target_query=target_query,
    source_type="sqlserver",
    target_type="azure_synapse"
)'''
    
    add_code_block(doc, example2)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Example 3: Cross-Platform Validation', 2, color=(0, 102, 0))
    
    example3 = '''# Validate data migration from MySQL to SQL Server
success, excel, json_report, powerbi, html = run_etl(
    source_query="SELECT * FROM customer_data",
    target_query="SELECT * FROM dbo.customers",
    source_type="mysql_example",
    target_type="default"
)

# Check specific validation results
with open(json_report) as f:
    results = json.load(f)
    
    if results['count_validation']['passed']:
        print("✅ Record counts match")
    else:
        print(f"❌ Count mismatch: {results['count_validation']['details']}")'''
    
    add_code_block(doc, example3)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Example 4: Automated Rule-Based Validation', 2, color=(0, 102, 0))
    
    example4 = '''from src.automation import ValidationEngine

# Load validation rules from configuration
engine = ValidationEngine('config/validation_rules.json')

# Execute all configured rules
results = engine.run_validation()

# Generate summary report
for rule_name, result in results.items():
    status = "✅ PASS" if result['passed'] else "❌ FAIL"
    print(f"{rule_name}: {status}")
    if not result['passed']:
        print(f"  Details: {result['message']}")'''
    
    add_code_block(doc, example4)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Example 5: CI/CD Integration', 2, color=(0, 102, 0))
    
    example5 = '''# GitHub Actions Workflow
name: Data Validation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      
      - name: Run validation tests
        env:
          DB_SERVER: ${{ secrets.DB_SERVER }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        run: pytest -v --junitxml=test-results.xml
      
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: validation-reports
          path: DataValidation/reports/'''
    
    add_code_block(doc, example5, 'yaml')
    
    doc.add_page_break()
    
    # ========== 13. BEST PRACTICES ==========
    add_heading_with_color(doc, '13. Best Practices', 1)
    
    best_practices_sections = {
        'Data Source Configuration': [
            'Use environment variables for passwords and sensitive credentials',
            'Configure separate connections for development, staging, and production',
            'Test connections before running validations (use /api/test-connection)',
            'Use read-only database accounts for validation queries',
            'Implement connection pooling for high-volume validations'
        ],
        'Validation Strategy': [
            'Start with structure validation before data validation',
            'Run count validation to identify obvious data loss',
            'Use null checks to ensure data quality',
            'Apply duplicate checks based on business keys',
            'Perform row-wise validation for critical datasets only (performance intensive)',
            'Filter large tables with WHERE clauses rather than validating all data'
        ],
        'Performance Optimization': [
            'Limit row-wise validation to manageable dataset sizes (< 1M rows)',
            'Use indexed columns in validation queries',
            'Run validations during off-peak hours for production systems',
            'Consider parallel execution for multiple table validations',
            'Archive old reports and logs regularly',
            'Use incremental validation for large tables (validate only recent changes)'
        ],
        'Reporting Best Practices': [
            'Generate Excel reports for stakeholder communication',
            'Use HTML dashboards for real-time monitoring',
            'Store JSON reports for automated processing and trending',
            'Retain validation history for audit trails',
            'Include timestamps and metadata in all reports',
            'Set up automated report distribution via email or shared folders'
        ],
        'Testing & Quality': [
            'Write unit tests for custom validation logic',
            'Use PyTest fixtures for reusable test data',
            'Run tests before deploying to production',
            'Maintain test coverage above 80%',
            'Document test scenarios and expected outcomes',
            'Include positive and negative test cases'
        ],
        'Security & Compliance': [
            'Never commit credentials to version control',
            'Use Azure Key Vault or similar for secret management',
            'Implement role-based access control for web interface (future enhancement)',
            'Audit all validation executions with user tracking',
            'Mask sensitive data in reports (PII, financial data)',
            'Comply with data residency requirements for cloud sources',
            'Regularly rotate access tokens and passwords'
        ],
        'CI/CD Integration': [
            'Integrate validation into deployment pipelines',
            'Fail builds if critical validations fail',
            'Generate trend reports to track data quality over time',
            'Use automated scheduling for recurring validations',
            'Set up alerts for validation failures',
            'Version control validation rules and configurations'
        ]
    }
    
    for section, practices in best_practices_sections.items():
        add_heading_with_color(doc, section, 2, color=(204, 0, 0))
        for practice in practices:
            add_bullet_point(doc, practice)
        doc.add_paragraph()
    
    doc.add_page_break()
    
    # ========== 14. TECHNICAL SPECIFICATIONS ==========
    add_heading_with_color(doc, '14. Technical Specifications', 1)
    
    add_heading_with_color(doc, 'Technology Stack:', 2, color=(204, 0, 0))
    
    tech_stack = [
        ['Component', 'Technology', 'Version', 'Purpose'],
        ['Backend Framework', 'FastAPI', '0.100+', 'REST API server'],
        ['Testing Framework', 'PyTest', '7.0+', 'Automated testing'],
        ['Database Driver', 'pyodbc', '4.0+', 'SQL Server connectivity'],
        ['Excel Generation', 'openpyxl', '3.0+', 'Excel report creation'],
        ['Web Server', 'Uvicorn', '0.20+', 'ASGI web server'],
        ['Data Processing', 'Pandas', '1.3+', 'Data manipulation'],
        ['HTTP Client', 'Requests', '2.28+', 'API communication'],
        ['Authentication', 'MSAL', '1.20+', 'Azure AD authentication']
    ]
    
    add_table_with_style(doc, tech_stack[1:], tech_stack[0])
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Supported Python Versions:', 2, color=(204, 0, 0))
    
    doc.add_paragraph('Python 3.8, 3.9, 3.10, 3.11, 3.12')
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'API Specifications:', 2, color=(204, 0, 0))
    
    api_specs = [
        'REST API following OpenAPI 3.0 specification',
        'JSON request/response format',
        'CORS enabled for cross-origin requests',
        'Auto-generated interactive documentation (Swagger UI)',
        'Support for multipart file uploads',
        'Streaming responses for large datasets',
        'HTTP status codes following RFC 7231',
        'Rate limiting ready (can be configured)'
    ]
    
    for spec in api_specs:
        add_bullet_point(doc, spec)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Performance Characteristics:', 2, color=(204, 0, 0))
    
    performance = [
        ('Small Tables (< 10K rows)', 'Validation completes in < 5 seconds'),
        ('Medium Tables (10K - 100K rows)', 'Validation completes in < 30 seconds'),
        ('Large Tables (100K - 1M rows)', 'Validation completes in 1-5 minutes'),
        ('Very Large Tables (> 1M rows)', 'Recommend filtered queries or incremental validation')
    ]
    
    for size, timing in performance:
        p = doc.add_paragraph()
        p.add_run(f'{size}: ').bold = True
        p.add_run(timing)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Scalability Considerations:', 2, color=(204, 0, 0))
    
    scalability = [
        'Horizontal scaling: Deploy multiple API server instances behind load balancer',
        'Vertical scaling: Increase server RAM for large dataset processing',
        'Database connection pooling to handle concurrent requests',
        'Asynchronous processing for long-running validations (roadmap)',
        'Caching layer for frequently accessed metadata (roadmap)',
        'Distributed validation execution across worker nodes (roadmap)'
    ]
    
    for item in scalability:
        add_bullet_point(doc, item)
    
    doc.add_paragraph()
    add_heading_with_color(doc, 'Logging & Monitoring:', 2, color=(204, 0, 0))
    
    logging_info = [
        'Structured logging to text files (ETL log, duplicate log, mismatch log)',
        'Timestamp and severity level for all log entries',
        'Configurable log rotation and retention',
        'Integration ready for ELK, Splunk, or Application Insights',
        'Performance metrics: execution time, record counts, validation results',
        'Error tracking with full stack traces'
    ]
    
    for item in logging_info:
        add_bullet_point(doc, item)
    
    doc.add_page_break()
    
    # ========== APPENDIX: TROUBLESHOOTING ==========
    add_heading_with_color(doc, 'Appendix A: Troubleshooting Guide', 1)
    
    troubleshooting = {
        'Database Connection Errors': {
            'Symptoms': 'Cannot connect to database, timeout errors',
            'Solutions': [
                'Verify server name and database name in data_sources.json',
                'Check network connectivity and firewall rules',
                'Ensure ODBC Driver 17 for SQL Server is installed',
                'Test connection using SQL Server Management Studio',
                'Verify authentication credentials',
                'For Azure: Check if your IP is whitelisted in firewall rules'
            ]
        },
        'Validation Failures': {
            'Symptoms': 'All validations show FAIL status',
            'Solutions': [
                'Check if tables exist and are accessible',
                'Verify table names include schema (e.g., dbo.tablename)',
                'Ensure user has SELECT permissions on tables',
                'Review logs for specific error messages',
                'Test queries directly in database client first'
            ]
        },
        'Performance Issues': {
            'Symptoms': 'Validations take too long or timeout',
            'Solutions': [
                'Add WHERE clauses to filter large tables',
                'Create indexes on comparison columns',
                'Increase timeout values in configuration',
                'Run validations during off-peak hours',
                'Consider incremental validation approach',
                'Use COUNT(*) first to verify table sizes'
            ]
        },
        'Report Generation Errors': {
            'Symptoms': 'Excel or HTML reports are missing or corrupted',
            'Solutions': [
                'Check write permissions on reports directory',
                'Verify disk space availability',
                'Ensure openpyxl library is installed correctly',
                'Review report_generator.py logs for errors',
                'Try regenerating with smaller dataset first'
            ]
        },
        'Web Interface Not Loading': {
            'Symptoms': 'Cannot access http://localhost:8000',
            'Solutions': [
                'Verify server is running (check terminal output)',
                'Ensure port 8000 is not in use by another application',
                'Check for errors in uvicorn startup logs',
                'Try accessing http://127.0.0.1:8000 instead',
                'Disable browser extensions that might block content',
                'Clear browser cache and cookies'
            ]
        }
    }
    
    for issue, details in troubleshooting.items():
        add_heading_with_color(doc, issue, 2, color=(153, 0, 0))
        
        p = doc.add_paragraph()
        p.add_run('Symptoms: ').bold = True
        p.add_run(details['Symptoms'])
        
        doc.add_paragraph('Solutions:').runs[0].bold = True
        for solution in details['Solutions']:
            add_bullet_point(doc, solution)
        
        doc.add_paragraph()
    
    doc.add_page_break()
    
    # ========== APPENDIX: FAQ ==========
    add_heading_with_color(doc, 'Appendix B: Frequently Asked Questions', 1)
    
    faqs = [
        {
            'Q': 'Can I use this framework with cloud databases like Azure SQL?',
            'A': 'Yes, absolutely. The framework supports Azure SQL Database, Azure Synapse Analytics, and Microsoft Fabric. Configure the connection in data_sources.json with the appropriate server and authentication details.'
        },
        {
            'Q': 'How do I validate tables with different column names?',
            'A': 'The framework includes intelligent column mapping that automatically matches columns based on common naming patterns. You can also use custom SQL queries to alias columns to match names.'
        },
        {
            'Q': 'What happens if my source and target have different row counts?',
            'A': 'The count validation will report the mismatch and the row-wise validation will identify which specific records are missing or extra. All details are included in the mismatch report.'
        },
        {
            'Q': 'Can I schedule automated validations?',
            'A': 'Yes, you can integrate the framework with task schedulers (Windows Task Scheduler, cron) or CI/CD tools (GitHub Actions, Azure DevOps). See the CI/CD integration examples in this document.'
        },
        {
            'Q': 'How do I validate only specific columns?',
            'A': 'Use custom SQL queries with SELECT clauses listing only the columns you want to validate. The framework will validate only the columns present in your query results.'
        },
        {
            'Q': 'Is there a limit to the table size I can validate?',
            'A': 'There\'s no hard limit, but performance degrades with very large tables (> 1M rows). For best results, use filtered queries or incremental validation approaches for large datasets.'
        },
        {
            'Q': 'Can I extend the framework with custom validations?',
            'A': 'Yes, the framework is modular. You can add new validation functions to src/validate.py and integrate them into the main pipeline in main.py.'
        },
        {
            'Q': 'How do I secure sensitive credentials?',
            'A': 'Use environment variables instead of hardcoding credentials. The framework supports ${ENV_VAR} syntax in data_sources.json. For production, integrate with Azure Key Vault or similar secret management services.'
        },
        {
            'Q': 'Can I compare data across different database platforms?',
            'A': 'Yes, absolutely. You can validate data from SQL Server to MySQL, Oracle to PostgreSQL, or any combination of supported platforms.'
        },
        {
            'Q': 'What\'s the difference between "Run Validation" and "Run PyTest"?',
            'A': '"Run Validation" executes the ETL pipeline directly and generates reports. "Run PyTest" runs the same validations through the PyTest framework, which provides additional test reporting and CI/CD integration features.'
        }
    ]
    
    for i, faq in enumerate(faqs, 1):
        p = doc.add_paragraph()
        p.add_run(f'Q{i}: {faq["Q"]}').bold = True
        
        answer = doc.add_paragraph(f'A: {faq["A"]}')
        answer.paragraph_format.left_indent = Inches(0.3)
        
        doc.add_paragraph()
    
    doc.add_page_break()
    
    # ========== FOOTER PAGE ==========
    closing = doc.add_heading('Framework Summary', 1)
    closing.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    summary_text = doc.add_paragraph(
        'The ETL Validation Framework provides a comprehensive, enterprise-ready solution for '
        'data validation across multiple platforms. With its intuitive web interface, powerful '
        'API, and extensive validation capabilities, it streamlines the validation process and '
        'ensures data quality throughout your ETL pipelines.'
    )
    summary_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    doc.add_paragraph('Key Benefits:').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('✓ Reduced manual validation effort').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('✓ Improved data quality and accuracy').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('✓ Faster issue detection and resolution').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('✓ Comprehensive audit trails and reporting').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('✓ Seamless CI/CD integration').alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    doc.add_paragraph()
    
    footer_text = doc.add_paragraph(
        'For support, questions, or contributions, please refer to the project repository.'
    )
    footer_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_text.runs[0].font.italic = True
    footer_text.runs[0].font.size = Pt(10)
    
    # Save document
    output_path = "ETL_Validation_Framework_Documentation.docx"
    doc.save(output_path)
    print(f"\n✅ Documentation generated successfully: {output_path}")
    return output_path

if __name__ == "__main__":
    try:
        create_documentation()
    except Exception as e:
        print(f"❌ Error generating documentation: {e}")
        import traceback
        traceback.print_exc()
