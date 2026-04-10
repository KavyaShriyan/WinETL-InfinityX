# Azure Synapse and Microsoft Fabric Support

This framework now supports **Azure Synapse Analytics** and **Microsoft Fabric** as data sources for ETL validation.

## Supported Azure Data Platforms

### 1. Azure Synapse Analytics
- Dedicated SQL pools (formerly SQL DW)
- Serverless SQL pools
- Full T-SQL compatibility
- Azure AD authentication support

### 2. Microsoft Fabric
- Fabric Data Warehouse
- Lakehouse SQL endpoint
- **Medallion Architecture (Bronze/Silver/Gold layers)**
- Delta Lake tables
- Shortcuts and external tables
- Modern cloud data platform
- Azure AD authentication support

## Configuration

### Azure Synapse Example

```json
{
  "type": "azuresynapse",
  "driver": "ODBC Driver 17 for SQL Server",
  "server": "<workspace-name>.sql.azuresynapse.net",
  "database": "<database-name>",
  "username": "<username>",
  "password": "<password>",
  "encrypt": true,
  "trust_server_certificate": false
}
```

### Microsoft Fabric Example

```json
{
  "type": "fabric",
  "driver": "ODBC Driver 17 for SQL Server",
  "server": "<workspace-name>.datawarehouse.fabric.microsoft.com",
  "database": "<database-name>",
  "authentication": "ActiveDirectoryInteractive",
  "encrypt": true,
  "trust_server_certificate": true
}
```

## Authentication Methods

### SQL Authentication
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

### Azure Active Directory - Interactive
```json
{
  "authentication": "ActiveDirectoryInteractive"
}
```
This will open a browser for interactive login.

### Azure Active Directory - Password
```json
{
  "authentication": "ActiveDirectoryPassword",
  "username": "user@domain.com",
  "password": "your_password"
}
```

### Azure Active Directory - Service Principal (Fabric only)
```json
{
  "authentication": "ActiveDirectoryServicePrincipal",
  "client_id": "your_app_id",
  "client_secret": "your_app_secret"
}
```

## Usage in Web Interface

1. **Start the application**
   ```bash
   .\run_server.bat
   ```

2. **Select Database Type**
   - For source or target, choose "Azure Synapse Analytics" or "Microsoft Fabric"

3. **Enter Connection Details**
   - Server: Your workspace SQL endpoint
     - Synapse: `<workspace>.sql.azuresynapse.net`
     - Fabric: `<workspace>.datawarehouse.fabric.microsoft.com`
   - Database: Your database name
   - Authentication: Choose SQL or Azure AD method
   - Credentials: Enter based on authentication type

4. **Test Connection**
   - Click "Test Connection" to verify
   - Tables will automatically load on success

5. **Run Validations**
   - Select source and target tables
   - Choose validation options
   - Execute validation

## Connection String Examples

### Azure Synapse with SQL Auth
```python
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=myworkspace.sql.azuresynapse.net;
DATABASE=mydatabase;
UID=myuser;
PWD=mypassword;
Encrypt=yes;
```

### Microsoft Fabric with Azure AD Interactive
```python
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=myworkspace.datawarehouse.fabric.microsoft.com;
DATABASE=mydatabase;
Authentication=ActiveDirectoryInteractive;
Encrypt=yes;
TrustServerCertificate=yes;
```

## Prerequisites

- **ODBC Driver 17 for SQL Server** or later
  - Download: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

- **Python packages** (already included in requirements.txt)
  - `pyodbc` for database connectivity

- **Azure Permissions**
  - Read access to Synapse/Fabric workspace
  - Database read permissions on target databases

## Features Supported

✅ Connection testing
✅ Table discovery (all schemas including bronze/silver/gold)
✅ Schema validation
✅ Data validation (row count, structure, duplicates, nulls)
✅ Row-wise data comparison
✅ Cross-layer validation (Bronze → Silver → Gold)
✅ Medallion architecture support
✅ Delta Lake table validation
✅ Report generation (Excel, HTML dashboards)
✅ Save and reuse connection configurations

## Microsoft Fabric Medallion Architecture Support

The framework fully supports validating data across **Bronze, Silver, and Gold layers** in Microsoft Fabric.

### Common Medallion Architecture Patterns

#### 1. **Bronze Layer (Raw Data)**
- Raw ingested data
- Minimal transformations
- Historical snapshots
- Typically in `bronze` schema or folder

#### 2. **Silver Layer (Cleansed Data)**
- Cleaned and validated data
- Standardized formats
- Business rules applied
- Typically in `silver` schema or folder

#### 3. **Gold Layer (Curated Data)**
- Aggregated business metrics
- Dimension and fact tables
- Report-ready data
- Typically in `gold` schema or folder

### Validation Scenarios

#### Scenario 1: Bronze to Silver Validation
Validate that data transformation from Bronze to Silver is correct:

```json
{
  "source": {
    "type": "fabric",
    "server": "myworkspace.datawarehouse.fabric.microsoft.com",
    "database": "MyLakehouse",
    "table": "bronze.raw_customer_data"
  },
  "target": {
    "type": "fabric",
    "server": "myworkspace.datawarehouse.fabric.microsoft.com",
    "database": "MyLakehouse",
    "table": "silver.customer_data"
  }
}
```

**Use the web interface:**
1. Source: Select Fabric → `bronze.raw_customer_data`
2. Target: Select Fabric → `silver.customer_data`
3. Validate: Row counts, data quality, transformations

#### Scenario 2: Silver to Gold Validation
Validate aggregations and business logic:

```json
{
  "source": {
    "table": "silver.transactions"
  },
  "target": {
    "table": "gold.monthly_sales_summary"
  }
}
```

**Validations:**
- ✅ Aggregation accuracy (SUM, COUNT, AVG)
- ✅ No duplicate keys in Gold layer
- ✅ Referential integrity maintained

#### Scenario 3: Cross-Workspace Validation
Validate data across different Fabric workspaces:

```python
# Source: Development workspace (Bronze)
source_config = {
    "type": "fabric",
    "server": "dev-workspace.datawarehouse.fabric.microsoft.com",
    "database": "DevLakehouse",
    "table": "bronze.source_table"
}

# Target: Production workspace (Gold)
target_config = {
    "type": "fabric",
    "server": "prod-workspace.datawarehouse.fabric.microsoft.com",
    "database": "ProdLakehouse",
    "table": "gold.target_table"
}
```

#### Scenario 4: Lakehouse SQL Endpoint Validation
Access tables directly from Lakehouse via SQL endpoint:

**Connection String:**
```
Server: myworkspace.datawarehouse.fabric.microsoft.com
Database: MyLakehouse
```

**Available Tables:**
- All Delta tables in the Lakehouse
- Shortcuts to external data sources
- Views and managed tables

### How to Use in Web Interface

1. **Start the server** (if not already running)
   ```bash
   .\run_server.bat
   ```

2. **Configure Source (Bronze Layer)**
   - Database Type: Microsoft Fabric
   - Server: `workspace.datawarehouse.fabric.microsoft.com`
   - Database: Your Lakehouse or Data Warehouse name
   - Table: `bronze.tablename` or use the table picker

3. **Configure Target (Silver/Gold Layer)**
   - Database Type: Microsoft Fabric (can be same or different workspace)
   - Server: Same or different Fabric workspace
   - Database: Same or different Lakehouse/Warehouse
   - Table: `silver.tablename` or `gold.tablename`

4. **Select Validations**
   - ✅ Structure Validation (schema changes)
   - ✅ Record Count (row count matching)
   - ✅ Null Check (data quality)
   - ✅ Duplicate Check (uniqueness constraints)
   - ✅ Row-wise Data Validation (detailed comparison)

5. **Execute and Review**
   - Click "Run Validation"
   - View real-time results
   - Download Excel/HTML reports
   - Check logs for row-level mismatches

### Schema Naming Conventions

Fabric supports multiple schema naming patterns:

| Pattern | Source Example | Target Example |
|---------|---------------|----------------|
| **Schema-based** | `bronze.customers` | `silver.customers` |
| **Prefix-based** | `bronze_customers` | `silver_customers` |
| **Folder-based** | `Bronze/Customers` | `Silver/Customers` |
| **Database-based** | `BronzeDB.customers` | `SilverDB.customers` |

The framework works with **all patterns** - just specify the full table name.

### Example Validation Queries

#### Bronze to Silver Row Count Check
```sql
-- Source (Bronze)
SELECT COUNT(*) FROM bronze.customer_events 
WHERE event_date = '2026-02-06'

-- Target (Silver)
SELECT COUNT(*) FROM silver.customer_events_clean 
WHERE event_date = '2026-02-06'
```

#### Silver to Gold Aggregation Check
```sql
-- Source (Silver - detail level)
SELECT 
    product_id, 
    SUM(quantity) as total_qty,
    SUM(amount) as total_amount
FROM silver.order_details
WHERE order_date >= '2026-01-01'
GROUP BY product_id

-- Target (Gold - aggregated)
SELECT 
    product_id,
    total_quantity,
    total_sales
FROM gold.product_sales_summary
WHERE period = '2026-01'
```

### Delta Lake Specific Features

When validating Delta tables in Fabric Lakehouse:

✅ **Time Travel Support**: Query historical versions
```sql
SELECT * FROM bronze.events TIMESTAMP AS OF '2026-01-01'
```

✅ **ACID Transactions**: Ensure data consistency during validation

✅ **Schema Evolution**: Detect schema changes between layers

✅ **Partition Validation**: Validate partitioned data
```sql
SELECT * FROM silver.sales WHERE year = 2026 AND month = 2
```

### Best Practices for Medallion Validation

1. **Incremental Validation**
   - Validate only new/changed data using date filters
   - Use partition pruning for large tables

2. **Layer-Specific Checks**
   - **Bronze**: Focus on row counts and basic structure
   - **Silver**: Add data quality and business rule validation
   - **Gold**: Validate aggregations and calculations

3. **Automated Scheduling**
   - Run validations after each layer refresh
   - Alert on validation failures
   - Track data quality metrics over time

4. **Cross-Layer Lineage**
   - Document source-to-target mappings
   - Validate transformation logic
   - Ensure no data loss between layers

## Troubleshooting

### Connection Timeout
- Increase timeout in connection string
- Check firewall rules allow your IP
- Verify workspace is running (Synapse)

### Authentication Failed
- For Azure AD: Ensure you have proper AAD permissions
- For SQL Auth: Verify credentials are correct
- Check if SQL authentication is enabled on the workspace

### Driver Not Found
```
[Microsoft][ODBC Driver Manager] Data source name not found
```
**Solution**: Install ODBC Driver 17 for SQL Server

### SSL/TLS Errors
- For Fabric: Set `trust_server_certificate: true`
- For Synapse: Set `encrypt: true` and ensure valid SSL certificate

## Example Validation Workflow

1. **Source**: SQL Server on-premises
2. **Target**: Azure Synapse or Fabric Data Warehouse
3. **Validation**: Ensure data migration was successful

```python
# Programmatic usage
from config.db_config import create_connection

# Connect to Azure Synapse
synapse_conn = create_connection('my_synapse_config')

# Or Microsoft Fabric
fabric_conn = create_connection('my_fabric_config')
```

## Security Best Practices

1. **Never hardcode credentials** - Use environment variables
2. **Use Azure AD authentication** when possible
3. **Enable encryption** for all connections
4. **Store sensitive configs** in `.env` file (not in git)
5. **Use service principals** for automated workflows
6. **Rotate credentials regularly**

## Additional Resources

- [Azure Synapse Documentation](https://docs.microsoft.com/azure/synapse-analytics/)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [ODBC Connection Strings](https://www.connectionstrings.com/)
