# Microsoft Fabric Medallion Architecture - Quick Start Guide

## What is Medallion Architecture?

A data design pattern with three progressive layers:
- 🥉 **Bronze**: Raw data (as-is from source)
- 🥈 **Silver**: Cleaned & validated data
- 🥇 **Gold**: Business-ready aggregated data

## Quick Setup

### 1. Get Your Fabric SQL Endpoint
- Open your Fabric workspace
- Go to your Lakehouse or Data Warehouse
- Copy the SQL endpoint: `<workspace>.datawarehouse.fabric.microsoft.com`

### 2. Start the Application
```bash
.\run_server.bat
```
Open: http://localhost:8000

### 3. Configure Connection

**Source (Bronze Layer):**
- Database Type: `Microsoft Fabric`
- Server: `workspace.datawarehouse.fabric.microsoft.com`
- Database: `YourLakehouse`
- Authentication: `ActiveDirectoryInteractive` (easiest)
- Table: `bronze.raw_table` or select from picker

**Target (Silver/Gold Layer):**
- Same server (or different workspace)
- Same or different database
- Table: `silver.clean_table` or `gold.summary_table`

### 4. Run Validation
- ✅ Structure Validation
- ✅ Record Count
- ✅ Null Check
- ✅ Duplicate Check
- ✅ Row-wise Data Validation

Click **"Run Validation"** → View results → Download reports

## Common Validation Patterns

### Pattern 1: Bronze → Silver (Data Quality)
**Purpose**: Ensure raw data was cleaned correctly

**Source**: `bronze.customer_raw`
**Target**: `silver.customer_clean`

**Expected**:
- Row count may be LESS (invalid records filtered)
- No nulls in required fields (Target)
- No duplicates on primary key (Target)

### Pattern 2: Silver → Gold (Aggregation)
**Purpose**: Validate aggregations and business logic

**Source Query**:
```sql
SELECT product_id, SUM(quantity) as total
FROM silver.orders
GROUP BY product_id
```

**Target**: `gold.product_summary`

**Validations**:
- Aggregation sums match
- No missing products
- Calculations correct

### Pattern 3: Cross-Workspace (Dev → Prod)
**Purpose**: Ensure production matches tested dev data

**Source**: `dev-workspace → bronze.table`
**Target**: `prod-workspace → bronze.table`

**Validations**:
- Schema identical
- Row counts match
- Data identical

## Fabric Table Access Patterns

Your Fabric data is accessible via SQL endpoint in these ways:

| Layer | Schema Name | Example Table Reference |
|-------|-------------|------------------------|
| Bronze | `bronze` | `bronze.raw_sales` |
| Silver | `silver` | `silver.sales_validated` |
| Gold | `gold` | `gold.fact_sales` |

OR using separate databases:

| Layer | Database | Example |
|-------|----------|---------|
| Bronze | `Lakehouse_Bronze` | `Lakehouse_Bronze.dbo.sales` |
| Silver | `Lakehouse_Silver` | `Lakehouse_Silver.dbo.sales` |
| Gold | `Lakehouse_Gold` | `Lakehouse_Gold.dbo.sales` |

Both patterns work with the framework - just use the full qualified name.

## Authentication Quick Guide

### Option 1: Interactive (Easiest)
- Authentication: `ActiveDirectoryInteractive`
- Browser popup for login
- Best for manual testing

### Option 2: Username/Password
- Authentication: `ActiveDirectoryPassword`
- Username: `user@domain.com`
- Password: Your AAD password
- Best for attended automation

### Option 3: Service Principal (Automation)
- Authentication: `ActiveDirectoryServicePrincipal`
- Client ID: Your app registration ID
- Client Secret: Your app secret
- Best for unattended automation

## Sample Validation Workflow

```
1. Open browser → http://localhost:8000

2. SOURCE CONFIGURATION:
   - Type: Microsoft Fabric
   - Server: myworkspace.datawarehouse.fabric.microsoft.com
   - Database: SalesLakehouse
   - Auth: ActiveDirectoryInteractive
   - [Test Connection] → Success!
   - Table: Select "bronze.raw_orders"

3. TARGET CONFIGURATION:
   - Type: Microsoft Fabric
   - Server: myworkspace.datawarehouse.fabric.microsoft.com
   - Database: SalesLakehouse
   - Auth: ActiveDirectoryInteractive
   - [Test Connection] → Success!
   - Table: Select "silver.orders_validated"

4. SELECT VALIDATIONS:
   ✅ Structure Validation
   ✅ Record Count Validation
   ✅ Null Check
   ✅ Duplicate Check
   ✅ Row-wise Data Validation

5. [Run Validation]

6. VIEW RESULTS:
   - Record Count: Source=10,000 / Target=9,856 ✓ (144 invalid records filtered)
   - Structure: Match ✓
   - Duplicates: 0 ✓
   - Nulls: 0 critical nulls ✓
   - Download Excel Report
   - Download HTML Dashboard
```

## Custom Queries for Advanced Scenarios

### Incremental Validation (Today's Data Only)
**Source Query**:
```sql
SELECT * FROM bronze.events 
WHERE event_date = CAST(GETDATE() AS DATE)
```

**Target Query**:
```sql
SELECT * FROM silver.events_processed 
WHERE process_date = CAST(GETDATE() AS DATE)
```

### Partition Validation
**Source**:
```sql
SELECT * FROM silver.sales 
WHERE year = 2026 AND month = 2
```

**Target**:
```sql
SELECT * FROM gold.monthly_sales 
WHERE year = 2026 AND month = 2
```

### Time Travel Comparison
**Source (Current)**:
```sql
SELECT * FROM gold.fact_sales
```

**Target (Historical)**:
```sql
SELECT * FROM gold.fact_sales 
TIMESTAMP AS OF '2026-02-01'
```

## Troubleshooting

### "Cannot connect to server"
- ✅ Check workspace name is correct
- ✅ Ensure you have workspace access in Fabric
- ✅ Verify SQL endpoint is enabled on Lakehouse/Warehouse

### "Table not found"
- ✅ Use schema prefix: `bronze.tablename` not just `tablename`
- ✅ Check table exists using Fabric workspace UI
- ✅ Verify you have read permissions

### "Authentication failed"
- ✅ For AAD Interactive: Allow popup windows
- ✅ For Service Principal: Check app has workspace permissions
- ✅ Verify credentials are correct

### "Row count mismatch" (Expected)
- This is NORMAL for Bronze → Silver (filtering invalid data)
- Check validation logs to see which records were filtered
- Document expected filtering rules

## Tips for Success

1. **Start Simple**: Test Bronze → Silver with same workspace first
2. **Use Test Connection**: Always verify connectivity before running validations
3. **Save Configurations**: Save your connection settings for reuse
4. **Document Expectations**: Not all validations should match 100%
5. **Check Logs**: Row-level mismatch logs show exact differences
6. **Schedule Validations**: Run after each layer refresh/pipeline

## Need More Help?

See detailed documentation:
- [AZURE_SUPPORT.md](../AZURE_SUPPORT.md) - Complete Fabric/Synapse guide
- [fabric_medallion_example.json](fabric_medallion_example.json) - Configuration examples
- [README.md](../README.md) - General framework documentation
