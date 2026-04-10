import os

os.makedirs('logs', exist_ok=True)

sample = """Only in Source: {'src_employee_id': 207, 'src_first_name': 'Divya', 'src_last_name': 'Sharma', 'src_email': 'divya.sharma@company.org', 'src_phone_number': '922.000.0002', 'src_hire_date': '2012-04-20', 'src_job_id': 5, 'src_salary': 17500, 'src_manager_id': 11}
Only in Target: {'tgt_employee_id': 207, 'tgt_first_name': 'Divya', 'tgt_last_name': 'Sharma', 'tgt_email': 'divya.sharma@company.org', 'tgt_phone_number': '922.000.0002', 'tgt_hire_date': '2012-04-20', 'tgt_job_id': 5, 'tgt_salary': 18000, 'tgt_manager_id': 11}
Only in Source: {'src_employee_id': 209, 'src_first_name': 'Sneha', 'src_last_name': 'Iyer', 'src_email': 'sneha.iyer@company.org', 'src_phone_number': '944.000.0004', 'src_hire_date': '2016-10-01', 'src_job_id': 7, 'src_salary': 11000, 'src_manager_id': None}
Only in Target: {'tgt_employee_id': 209, 'tgt_first_name': 'Sneha', 'tgt_last_name': 'Iyer', 'tgt_email': 'sneha.iyer@company.org', 'tgt_phone_number': '944.000.0004', 'tgt_hire_date': '2016-10-01', 'tgt_job_id': 7, 'tgt_salary': 11500, 'tgt_manager_id': 15}
Only in Source: {'src_employee_id': 203, 'src_first_name': 'Amit', 'src_last_name': 'Sharma', 'src_email': 'amit.sharma@company.org', 'src_phone_number': '777.123.4569', 'src_hire_date': '2015-08-19', 'src_job_id': 6, 'src_salary': 9500, 'src_manager_id': 12}
Only in Target: {'tgt_employee_id': 203, 'tgt_first_name': 'Amit', 'tgt_last_name': 'Sharma', 'tgt_email': 'amit.sharma@company.org', 'tgt_phone_number': '777.123.4569', 'tgt_hire_date': '2015-08-19', 'tgt_job_id': 6, 'tgt_salary': 10000, 'tgt_manager_id': 12}
"""

with open('logs/row_data_mismatch_log.txt', 'w', encoding='utf-8') as f:
    f.write(sample)

print("Sample mismatch data written to logs/row_data_mismatch_log.txt")

# Generate report
from src.report_generator import generate_excel_report

validation_results = {
    "Structure Validation": {"passed": True, "output": "Structures match"},
    "Record Count Check": {"passed": False, "output": "Source: 150, Target: 147"},
    "Row-wise Data Validation": {"passed": False, "output": "Matched: 147, Mismatched: 3"}
}

os.makedirs('reports', exist_ok=True)
report_file = generate_excel_report(
    validation_results,
    output_file="reports/test_mismatch_verification.xlsx",
    source_table="dbo.emp_source",
    target_table="dbo.employees"
)

print(f"\n✅ Report generated: {report_file}")
print("\nOpening Excel file...")
os.system(f'start excel "{os.path.abspath(report_file)}"')

print("\n" + "="*80)
print("VERIFICATION CHECKLIST:")
print("="*80)
print("1. ✓ Check 'Mismatch Records' sheet for 'SOURCE VS TARGET COMPARISON' header")
print("2. ✓ Verify paired columns: src_employee_id | tgt_employee_id, src_first_name | tgt_first_name, etc.")
print("3. ✓ Blue headers for source columns, Purple for target")
print("4. ✓ Yellow highlighting for different values (salary differences)")
print("5. ✓ All columns visible: employee_id, first_name, last_name, email, phone_number, hire_date, job_id, salary, manager_id")
print("="*80)
