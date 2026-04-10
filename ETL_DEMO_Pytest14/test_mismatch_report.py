"""Test script to verify mismatch report generation with sample data"""
import os
import sys

# Add DataValidation to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'DataValidation'))

from src.report_generator import generate_excel_report

# Create sample mismatch data for testing
os.makedirs("DataValidation/logs", exist_ok=True)

sample_mismatch_data = """Only in Source: {'src_employee_id': 207, 'src_first_name': 'Divya', 'src_last_name': 'Sharma', 'src_email': 'divya.sharma@company.org', 'src_phone_number': '922.000.0002', 'src_hire_date': '2012-04-20', 'src_job_id': 5, 'src_salary': 17500, 'src_manager_id': 11}
Only in Target: {'tgt_employee_id': 207, 'tgt_first_name': 'Divya', 'tgt_last_name': 'Sharma', 'tgt_email': 'divya.sharma@company.org', 'tgt_phone_number': '922.000.0002', 'tgt_hire_date': '2012-04-20', 'tgt_job_id': 5, 'tgt_salary': 18000, 'tgt_manager_id': 11}
Only in Source: {'src_employee_id': 209, 'src_first_name': 'Sneha', 'src_last_name': 'Iyer', 'src_email': 'sneha.iyer@company.org', 'src_phone_number': '944.000.0004', 'src_hire_date': '2016-10-01', 'src_job_id': 7, 'src_salary': 11000, 'src_manager_id': 15}
Only in Target: {'tgt_employee_id': 209, 'tgt_first_name': 'Sneha', 'tgt_last_name': 'Iyer', 'tgt_email': 'sneha.iyer@company.org', 'tgt_phone_number': '944.000.0004', 'tgt_hire_date': '2016-10-01', 'tgt_job_id': 7, 'tgt_salary': 11500, 'tgt_manager_id': 15}
Only in Source: {'src_employee_id': 203, 'src_first_name': 'Amit', 'src_last_name': 'Sharma', 'src_email': 'amit.sharma@company.org', 'src_phone_number': '777.123.4569', 'src_hire_date': '2015-08-19', 'src_job_id': 6, 'src_salary': 9500, 'src_manager_id': 12}
Only in Target: {'tgt_employee_id': 203, 'tgt_first_name': 'Amit', 'tgt_last_name': 'Sharma', 'tgt_email': 'amit.sharma@company.org', 'tgt_phone_number': '777.123.4569', 'tgt_hire_date': '2015-08-19', 'tgt_job_id': 6, 'tgt_salary': 10000, 'tgt_manager_id': 12}
Only in Source: {'src_employee_id': 121, 'src_first_name': 'Neena', 'src_last_name': 'Pandey', 'src_email': 'neena.Pandey@sqltutorial.org', 'src_phone_number': '515.123.4599', 'src_hire_date': '1989-09-21', 'src_job_id': 5, 'src_salary': 17000, 'src_manager_id': None}
Only in Target: {'tgt_employee_id': 121, 'tgt_first_name': 'Neena', 'tgt_last_name': 'Pandey', 'tgt_email': 'neena.Pandey@sqltutorial.org', 'tgt_phone_number': '515.123.4599', 'tgt_hire_date': '1989-09-21', 'tgt_job_id': 5, 'tgt_salary': 17000, 'tgt_manager_id': 10}
Only in Source: {'src_employee_id': 999, 'src_first_name': 'Test', 'src_last_name': 'User', 'src_email': 'test.user@company.org', 'src_phone_number': '111.222.3333', 'src_hire_date': '2020-01-01', 'src_job_id': 1, 'src_salary': 50000, 'src_manager_id': 5}
"""

# Write sample data
with open("DataValidation/logs/row_data_mismatch_log.txt", "w", encoding="utf-8") as f:
    f.write(sample_mismatch_data)

# Create sample validation results
validation_results = {
    "Structure Validation": {"passed": True, "output": "Structures match"},
    "Record Count Check": {"passed": False, "output": "Source: 150, Target: 145"},
    "Row-wise Data Validation": {"passed": False, "output": "Matched: 145, Mismatched: 5"}
}

# Generate report
print("Generating Excel report with sample mismatch data...")
os.makedirs("DataValidation/reports", exist_ok=True)

# Create sample configurations
source_config = {
    'type': 'sqlserver',
    'server': 'DESKTOP-NILANCH\\SQLEXPRESS',
    'database': 'ETL_TRAINING',
    'authType': 'windows'
}

target_config = {
    'type': 'sqlserver',
    'server': 'DESKTOP-NILANCH\\SQLEXPRESS',
    'database': 'ETL_TRAINING',
    'authType': 'windows'
}

report_file = generate_excel_report(
    validation_results,
    output_file="DataValidation/reports/test_mismatch_report.xlsx",
    source_table="dbo.user_country",
    target_table="dbo.user_country_test",
    sample_size=1000,
    source_db_config=source_config,
    target_db_config=target_config
)

print(f"\n✅ Report generated: {report_file}")
print("\nOpening Excel file to verify...")
os.system(f'start excel "{os.path.abspath(report_file)}"')

print("\n" + "="*80)
print("VERIFICATION CHECKLIST:")
print("="*80)
print("1. ✓ Check if 'Mismatch Records' sheet shows 'SOURCE VS TARGET COMPARISON'")
print("2. ✓ Verify columns are paired: src_employee_id, tgt_employee_id, src_first_name, tgt_first_name, etc.")
print("3. ✓ Check if source columns have BLUE headers")
print("4. ✓ Check if target columns have PURPLE headers")
print("5. ✓ Verify different values are highlighted in YELLOW")
print("6. ✓ Verify N/A values are highlighted in RED")
print("7. ✓ Check Row # column has gradient background")
print("8. ✓ Verify all rows and columns are visible (employee_id, first_name, last_name, email, phone_number, hire_date, job_id, salary, manager_id)")
print("="*80)
