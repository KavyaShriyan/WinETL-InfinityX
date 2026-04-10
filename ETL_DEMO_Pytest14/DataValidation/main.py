
from config.db_config import create_connection
from src.validate import (
    structure_validation,
    count_validation,
    null_check,
    duplicate_check,
    row_data_validation,
)
from src.extract import extract_data
from src.transform import transform_data
from src.load import load_data
from src.report_generator import generate_excel_report, generate_html_dashboard, generate_json_report, generate_powerbi_dashboard
import os
import re

# ------------------------------------------------
# Utility: Get table columns and detect naming convention
# ------------------------------------------------
def get_table_columns(cursor, table_name):
    """Get column names for a table"""
    try:
        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        return [desc[0] for desc in cursor.description]
    except Exception as e:
        print(f"Warning: Could not get columns for {table_name}: {e}")
        return []

def get_smart_column_mapping(source_columns, target_columns):
    """Create intelligent column mapping between source and target"""
    # Standard mapping patterns
    mapping_patterns = {
        'employee_id': ['Emp_id', 'emp_id', 'EmployeeId', 'employee_id'],
        'first_name': ['FirstName', 'first_name', 'fname', 'First_Name'],
        'last_name': ['LastName', 'last_name', 'lname', 'Last_Name'], 
        'email': ['Email', 'email', 'email_address'],
        'phone_number': ['PhoneNumber', 'phone_number', 'phone', 'Phone_Number'],
        'hire_date': ['Hired_Date', 'hire_date', 'HireDate', 'Hire_Date'],
        'job_id': ['Job_Id', 'job_id', 'JobId', 'job_code'],
        'salary': ['Salary', 'salary'],
        'manager_id': ['Manager_id', 'manager_id', 'ManagerId'],
        'department_id': ['Department_id', 'department_id', 'DepartmentId']
    }
    
    # Find best mapping
    source_to_target = {}
    target_to_source = {}
    
    for source_col in source_columns:
        source_lower = source_col.lower()
        # Direct match first
        if source_col in target_columns:
            source_to_target[source_col] = source_col
            target_to_source[source_col] = source_col
            continue
            
        # Pattern matching
        found_mapping = False
        for pattern_key, pattern_variants in mapping_patterns.items():
            if source_lower == pattern_key or source_col in pattern_variants:
                for variant in pattern_variants:
                    if variant in target_columns:
                        source_to_target[source_col] = variant
                        target_to_source[variant] = source_col
                        found_mapping = True
                        break
                if found_mapping:
                    break
                    
        # If no mapping found, keep original name
        if not found_mapping:
            source_to_target[source_col] = source_col
    
    return source_to_target, target_to_source

def extract_table_from_query(query):
    """Extract table name from SQL query"""
    if not query:
        return None
    # Simple regex to extract table name from SELECT query
    import re
    match = re.search(r'FROM\s+([\w\.\[\]]+)', query, re.IGNORECASE)
    if match:
        table = match.group(1).strip()
        # Remove brackets if present
        table = table.replace('[', '').replace(']', '')
        return table
    return None

# ------------------------------------------------
# Utility: Extract record counts from output text
# ------------------------------------------------
def extract_counts_from_output(count_output):
    source_match = re.search(r"Source.*?:\s*(\d+)", count_output)
    target_match = re.search(r"Target.*?:\s*(\d+)", count_output)
    source_count = int(source_match.group(1)) if source_match else 0
    target_count = int(target_match.group(1)) if target_match else 0
    return source_count, target_count

# ------------------------------------------------
# Utility: Write combined duplicate records
# ------------------------------------------------
def write_combined_duplicate_log(all_records):
    log_path = os.path.join("logs", "duplicate_combined_log.txt")
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(str(record) + "\n")
    return os.path.abspath(log_path)

# ==========================================================
# MAIN ETL FUNCTION (PyTest + CLI Compatible)
# ==========================================================
def run_etl(source_query=None, target_query=None, source_type='default', target_type='default'):
    print("\n🚀 Starting ETL Validation Pipeline...\n")
    source_conn = create_connection(source_type)
    target_conn = create_connection(target_type) if source_type != target_type else source_conn

    if not source_conn or not target_conn:
        print("❌ Database connection failed.")
        return False
    try:
        # For SQL sources, get cursor; for others, use the connector directly
        if source_type in ['sqlserver', 'mysql', 'postgresql', 'oracle']:
            cursor = source_conn.cursor()
            target_cursor = target_conn.cursor() if source_conn != target_conn else cursor
        else:
            cursor = source_conn
            target_cursor = target_conn
        
        # ---------------- CONFIG ----------------
        # Extract table names from queries or use defaults
        source_table = extract_table_from_query(source_query) or os.environ.get("SOURCE_TABLE", "dbo.emp_source2")
        target_table = extract_table_from_query(target_query) or os.environ.get("TARGET_TABLE", "dbo.emp_target2")
        
        # Get actual column structures for intelligent mapping
        source_columns = get_table_columns(cursor, source_table)
        target_columns = get_table_columns(cursor, target_table)
        source_to_target, target_to_source = get_smart_column_mapping(source_columns, target_columns)
        
        print(f"[DEBUG] Source table: {source_table}, columns: {source_columns}")
        print(f"[DEBUG] Target table: {target_table}, columns: {target_columns}")
        print(f"[DEBUG] Column mapping: {source_to_target}")
        results = {}
        os.makedirs("logs", exist_ok=True)
        all_duplicate_logs = []
        # ---------------- STRUCTURE VALIDATION ----------------
        struct_output, _ = structure_validation(
            cursor, source_table, target_table, return_output=True
        )
        print(struct_output)
        results["Structure Validation"] = struct_output
        # ---------------- RECORD COUNT CHECK ----------------
        count_result, count_output = count_validation(
            cursor, source_table, target_table, return_output=True
        )
        print(count_output)
        results["Record Count Check"] = count_output
        # ---------------- NULL CHECK ----------------
      
        null_source = null_check(cursor, source_table, return_output=True)
        print(null_source)
        
        null_target = null_check(cursor, target_table, return_output=True)
        print(null_target)
        results["Null Check (Source Table)"] = null_source
        results["Null Check (Target Table)"] = null_target
        # ---------------- DUPLICATE CHECK (COMPOSITE KEY) ----------------
        print("\n📛 Duplicate Check (Source Table - Composite Key):")
        
        # Use intelligent column mapping for duplicate checks
        source_first_name = None
        source_email = None
        target_first_name = None
        target_last_name = None
        
        # Find appropriate columns for source table
        for col in source_columns:
            col_lower = col.lower()
            if col_lower in ['firstname', 'first_name', 'fname']:
                source_first_name = col
            elif col_lower in ['email', 'email_address']:
                source_email = col
                
        # Find appropriate columns for target table  
        for col in target_columns:
            col_lower = col.lower()
            if col_lower in ['firstname', 'first_name', 'fname']:
                target_first_name = col
            elif col_lower in ['lastname', 'last_name', 'lname']:
                target_last_name = col
        
        # Only run duplicate check if columns exist
        if source_first_name and source_email:
            dup_source = duplicate_check(
                cursor,
                source_table,
                columns=[source_first_name, source_email],
                return_output=True,
                label="Source",
                log_records=all_duplicate_logs
            )
            print(dup_source)
        else:
            dup_source = f"⚠️ Cannot perform composite duplicate check on source table. Required columns not found."
            print(dup_source)
            
        print("\n📛 Duplicate Check (Target Table - Composite Key):")
        if target_first_name and target_last_name:
            dup_target = duplicate_check(
                cursor,
                target_table,
                columns=[target_first_name, target_last_name],
                return_output=True,
                label="Target",
                log_records=all_duplicate_logs
            )
            print(dup_target)
        else:
            dup_target = f"⚠️ Cannot perform composite duplicate check on target table. Required columns not found."
            print(dup_target)
        results["Duplicate Check (Source Table)"] = dup_source
        results["Duplicate Check (Target Table)"] = dup_target
        # ---------------- DUPLICATE CHECK (PRIMARY KEY) ----------------
        print("\n📛 Duplicate Check By Primary Key (Source):")
        dup_source_pk = duplicate_check(
            cursor,
            source_table,
            use_primary_key=True,
            return_output=True,
            label="Source",
            log_records=all_duplicate_logs
        )
        print(dup_source_pk)
        print("\n📛 Duplicate Check By Primary Key (Target):")
        dup_target_pk = duplicate_check(
            cursor,
            target_table,
            use_primary_key=True,
            return_output=True,
            label="Target",
            log_records=all_duplicate_logs
        )
        print(dup_target_pk)
        results["Duplicate Check by PK (Source Table)"] = dup_source_pk
        results["Duplicate Check by PK (Target Table)"] = dup_target_pk
        # ---------------- WRITE DUPLICATE LOG ----------------
        dup_log_path = write_combined_duplicate_log(all_duplicate_logs)
        print(f"\n📜 Combined Duplicate Log Saved At:\n{dup_log_path}")
        # ---------------- ROW-WISE DATA VALIDATION ----------------
        source_count, target_count = extract_counts_from_output(count_output)
        mismatch_log_path = "logs/row_data_mismatch_log.txt"
        if source_count == 0 and target_count == 0:
            with open(mismatch_log_path, "w", encoding="utf-8") as f:
                f.write("")
            row_validation_output = "✅ Both source and target tables are empty."
        else:
            row_validation_output = row_data_validation(
                cursor,
                source_table,
                target_table,
                return_output=True,
                mismatch_log_file=mismatch_log_path
            )
         
        print(row_validation_output)
        results["Row-wise Data Validation"] = row_validation_output
        # ---------------- EXTRACT → TRANSFORM → LOAD ----------------
        print("\n📦 Extracting Source Data...")
        columns, data = extract_data(cursor, source_table)
        print("🔧 Transforming Data...")
        transformed_data = transform_data(columns, data)
        print("📁 Loading Data Into reports/loaded_data.csv...")
        load_data(transformed_data)
        # ---------------- REPORT GENERATION ----------------
        print("\n📝 Generating Reports...")
        excel_path = generate_excel_report(results)
        print(f"📊 Excel Report Generated At:\n{excel_path}")
        json_path = generate_json_report(results)
        print(f"📋 JSON Report Generated At:\n{json_path}")
        powerbi_path = generate_powerbi_dashboard(results)
        print(f"📈 Power BI Dashboard Data Generated At:\n{powerbi_path}")
        html_path = generate_html_dashboard(results)
        if html_path:
            print(f"🌐 HTML Dashboard Generated At:\n{html_path}")
        else:
            print("❌ Failed to generate HTML dashboard.")
        print("\n🎉 ETL PIPELINE COMPLETED SUCCESSFULLY")
        
        # Absolute paths for Streamlit UI
        excel_abs_path = os.path.abspath(excel_path)
        json_abs_path = os.path.abspath(json_path)
        powerbi_abs_path = os.path.abspath(powerbi_path)
        html_abs_path = os.path.abspath(html_path) if html_path else None

        return True, excel_abs_path, json_abs_path, powerbi_abs_path, html_abs_path
    
    except Exception as e:
        print("\n❌ ETL Pipeline Failed")
        print("Error:", str(e))
        return False, None, None, None, None

    finally:
        conn.close()
        print("\n🔌 Database Connection Closed")

# ==========================================================
# CLI ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        source_query = sys.argv[1] if len(sys.argv) > 1 else None
        target_query = sys.argv[2] if len(sys.argv) > 2 else None
        source_type = sys.argv[3] if len(sys.argv) > 3 else 'default'
        target_type = sys.argv[4] if len(sys.argv) > 4 else 'default'
        run_etl(source_query, target_query, source_type, target_type)
    else:
        run_etl()