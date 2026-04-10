# Data Automation Framework

A comprehensive ETL validation and data quality framework supporting multiple data sources, advanced validations, automation, and reporting.

## Features

### Data Source Support
- **Relational Databases**: MySQL, Oracle, PostgreSQL, SQL Server
- **Cloud Data Warehouses**: Azure Synapse Analytics, Microsoft Fabric, Databricks Unity Catalog
- **NoSQL Databases**: MongoDB, Cassandra, DynamoDB
- **Flat Files**: CSV, Excel, JSON, XML
- **APIs**: REST API data sources
- **Cloud Data Stores**: S3, Azure Blob Storage, Google Cloud Storage
- **BI & Analytics**: Power BI Datasets, Dataflows, Semantic Models, REST APIs

### Data Operations
- ETL (Extract, Transform, Load)
- Data validation & reconciliation
- Schema & constraint validation
- Duplicate & anomaly detection
- Referential integrity checks
- Data masking & anonymization
- Data freshness & SLA validation
- Incremental refresh & partition validation

### Automation Capabilities
- Rule-based data validation
- Row-level & aggregate validations
- Cross-system data comparison
- Incremental & delta data validation
- Scheduled & event-based execution
- Metadata-driven automation
- BI semantic validation (DAX measures, KPIs, visuals)

### Framework Design
- Modular & reusable validation components
- Configuration-driven execution
- Data-driven test rules
- SQL & query abstraction layer
- Environment-specific configuration
- Custom validation libraries
- Power BI abstraction layer
- Secure token & credential management

### Execution & Reporting
- Parallel data validation jobs
- Detailed row-level failure reports
- Audit logs & execution summaries
- Data quality metrics & dashboards
- Error categorization & trend analysis
- Exportable reports (Excel, HTML, JSON)
- Power BI validation reporting
- Measure-level failure diagnostics
- Dataset & visual health scorecards

### CI/CD & Advanced
- CI/CD pipeline integration
- Cloud-native execution support
- Version-controlled test rules
- Integration with data pipelines (Airflow, Azure Data Factory)
- Compliance & governance checks
- Scalability for large data volumes
- Power BI CI/CD automation
- Pre-deployment & post-deployment BI validation
- RLS (Row-Level Security) validation
- Dataset ownership & governance checks

## 📁 Complete Project Structure

```
DataValidation/                       # Core ETL Validation Framework
│
├── config/                           # Configuration Directory
│   ├── db_config.py                  # Database connection factory (15+ sources)
│   ├── data_sources.json             # Connection configs (SQL, Azure, Fabric, etc.)
│   ├── validation_rules.json         # Automated validation rule definitions
│   ├── secrets.py                    # Secrets & credential management
│   ├── fabric_medallion_example.json # Microsoft Fabric medallion config
│   └── __pycache__/                  # Python bytecode cache
│
├── src/                              # Source Code Modules
│   ├── validate.py                   # Core validations (structure, count, null, duplicate, row)
│   ├── advanced_validate.py          # Advanced validations (freshness, referential integrity)
│   ├── extract.py                    # Data extraction from multiple sources
│   ├── transform.py                  # Data transformation & business rules
│   ├── load.py                       # Data loading to target systems
│   ├── report_generator.py           # Report generation (Excel, HTML, JSON, Power BI)
│   ├── automation.py                 # Rule-based validation automation engine
│   ├── _init__.py                    # Package initializer
│   └── __pycache__/                  # Python bytecode cache
│
├── tests/                            # PyTest Test Suite
│   ├── conftest.py                   # PyTest fixtures & shared configuration
│   ├── test_validate.py              # Unit tests for validation functions
│   ├── test_extract.py               # Unit tests for data extraction
│   ├── test_transform.py             # Unit tests for data transformation
│   ├── test_main.py                  # End-to-end integration tests
│   └── __pycache__/                  # Python bytecode cache
│
├── DataValidation/                   # Nested Workspace (legacy structure)
│   ├── logs/                         # Workspace-specific logs
│   │   └── row_data_mismatch_log.txt # Row-level mismatches
│   └── reports/                      # Workspace-specific reports
│
├── logs/                             # Main Execution Logs
│   ├── etl_log.txt                   # General ETL pipeline execution logs
│   ├── duplicate_combined_log.txt    # Combined duplicate records from source & target
│   └── row_data_mismatch_log.txt     # Detailed row-by-row comparison mismatches
│
├── reports/                          # Generated Reports
│   ├── etl_dashboard.html            # Interactive HTML dashboard
│   ├── loaded_data.csv               # Loaded/transformed data output
│   ├── etl_validation_report.xlsx    # Excel report (auto-generated)
│   └── validation_results.json       # JSON report (auto-generated)
│
├── uploads/                          # File Upload Storage
│   ├── 20260128_124647_emp_source.csv
│   ├── 20260128_124659_emp_source.csv
│   ├── 20260128_124706_emp_source.csv
│   └── 20260128_124708_emp_source.csv
│
├── test_data/                        # Test Datasets
│   └── sample_input.csv              # Sample CSV for testing
│
├── .github/                          # GitHub Workflows (CI/CD)
│   └── workflows/                    # GitHub Actions definitions
│
├── .pytest_cache/                    # PyTest cache directory
├── __pycache__/                      # Python bytecode cache
│
├── Configuration Files
├── .env.example                      # Environment variables template
├── pytest.ini                        # PyTest configuration settings
├── requirements.txt                  # Python package dependencies
│
├── Main Scripts
├── main.py                           # Main ETL pipeline orchestrator
├── generate_test_report.py           # Automated test report generator
│
└── README.md                         # Framework documentation (this file)
```

### 📂 Directory Purpose Overview

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| **config/** | All configuration files for connections and rules | data_sources.json, db_config.py |
| **src/** | Core framework source code modules | validate.py, extract.py, transform.py, load.py |
| **tests/** | Complete PyTest test suite | test_validate.py, test_main.py, conftest.py |
| **logs/** | Execution logs for debugging and audit | etl_log.txt, duplicate_combined_log.txt |
| **reports/** | Generated validation reports | etl_dashboard.html, *.xlsx, *.json |
| **uploads/** | Uploaded CSV/Excel files for validation | Timestamped source files |
| **test_data/** | Sample datasets for testing | sample_input.csv |

### 🔧 Key Configuration Files

- **data_sources.json**: Defines 15+ data source connections (SQL Server, Azure, Fabric, MySQL, PostgreSQL, MongoDB, S3, Power BI, etc.)
- **validation_rules.json**: Automated validation rules for scheduled/event-driven execution
- **db_config.py**: Connection factory with support for all configured data sources
- **secrets.py**: Secure credential and secret management
- **pytest.ini**: PyTest settings including markers, paths, and output configuration

### 📝 Main Scripts

- **main.py**: Core ETL pipeline orchestrator - coordinates extract, transform, load, and validate
- **generate_test_report.py**: Generates comprehensive test execution reports

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Optional: Copy `.env.example` to `.env` and configure your credentials
4. Configure data sources in `config/data_sources.json`
5. Set up validation rules in `config/validation_rules.json`

## Usage

### Web Interface
Start the web server:
```bash
./run_server.bat
```
Access at http://localhost:8000

Features:
- Enter custom SQL queries for source and target data
- Select from multiple data source types (SQL Server, Azure Synapse, Microsoft Fabric, MySQL, PostgreSQL, MongoDB, S3, APIs, Power BI, Databricks)
- Choose validation checks
- View Power BI datasets, reports, and execute DAX queries
- Generate comprehensive reports

### Programmatic Usage
```python
from main import run_etl

success, excel_report, json_report, powerbi_report, html_dashboard = run_etl(
    source_query="SELECT * FROM source_table WHERE active = 1",
    target_query="SELECT * FROM target_table WHERE processed = 1",
    source_type="default",
    target_type="mysql_example"
)
```

### Advanced Automation
```python
from src.automation import ValidationEngine

engine = ValidationEngine('config/validation_rules.json')
results = engine.run_validation()
```

### Power BI Validation
```python
from config.db_config import create_connection

powerbi = create_connection('powerbi_example')
datasets = powerbi.get_datasets()
measures = powerbi.get_dataset_measures(dataset_id)
```

## Configuration

### Data Sources
Configure various data sources in `config/data_sources.json`:

```json
{
  "sqlserver_example": {
    "type": "sqlserver",
    "server": "server_name",
    "database": "db_name",
    "username": "user",
    "password": "pass"
  },
  "powerbi_example": {
    "type": "powerbi",
    "access_token": "token"
  }
}
```

### Validation Rules
Define validation rules in `config/validation_rules.json`:

```json
{
  "rules": [
    {
      "name": "count_check",
      "rule_type": "count_validation",
      "params": {
        "table1": "source",
        "table2": "target"
      }
    }
  ]
}
```

## Security

Credentials are managed through environment variables defined in `.env` file. Never commit sensitive information to version control.

## CI/CD

The framework includes GitHub Actions workflow for automated testing and validation. Configure secrets in your repository settings for database and API credentials.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.