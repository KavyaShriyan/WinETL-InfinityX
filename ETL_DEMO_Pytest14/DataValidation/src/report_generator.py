import os
import ast
import re
import json
import glob
import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime

# Global variables to store table names
SOURCE_TABLE = "Source Table"
TARGET_TABLE = "Target Table"

def set_table_names(source, target):
    """Set the source and target table names for reports"""
    global SOURCE_TABLE, TARGET_TABLE
    SOURCE_TABLE = source
    TARGET_TABLE = target

def parse_and_display_structure_details(ws, output_text, source_table, target_table):
    """Parse structure validation output and display it in Excel with proper formatting"""
    # Extract column information using regex
    
    # Section 1: Source Table Structure
    ws.append(["SOURCE TABLE STRUCTURE"])
    # Style this header
    header_row = ws.max_row
    ws.cell(header_row, 1).font = Font(bold=True, size=12, color="FFFFFF")
    ws.cell(header_row, 1).fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    ws.merge_cells(f'A{header_row}:C{header_row}')
    ws.append([""])
    
    # Try to extract source table column information
    source_match = re.search(r'Source table name:\s*(.+?)\n.*?Number of columns:\s*(\d+)', output_text, re.DOTALL)
    if source_match:
        num_cols_src = source_match.group(2)
        ws.append(["Table Name:", source_table])
        ws.cell(ws.max_row, 1).font = Font(bold=True, color="1E3A8A")
        ws.cell(ws.max_row, 1).fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
        
        ws.append(["Number of Columns:", num_cols_src])
        ws.cell(ws.max_row, 1).font = Font(bold=True, color="1E3A8A")
        ws.cell(ws.max_row, 1).fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
        ws.append([""])
    
    # Extract column details for source
    column_details_pattern = r'Column Details:\s*\n((?:\s+-\s+.*?\n)+)'
    source_section = re.search(r'Source table name:.*?(?=Target table name:|Structure Comparison Issues:|$)', output_text, re.DOTALL)
    
    if source_section:
        source_text = source_section.group(0)
        col_details = re.search(column_details_pattern, source_text, re.DOTALL)
        
        if col_details:
            # Parse column details
            ws.append(["Column Name", "Data Type", "Nullable"])
            # Style column headers
            header_row = ws.max_row
            for col_idx in range(1, 4):
                ws.cell(header_row, col_idx).font = Font(bold=True, color="FFFFFF")
                ws.cell(header_row, col_idx).fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
                ws.cell(header_row, col_idx).alignment = Alignment(horizontal='center', vertical='center')
            
            column_lines = col_details.group(1).strip().split('\n')
            for line in column_lines:
                # Parse line like: "Name (varchar, NULLABLE)" or "🔴 Name (varchar, NULLABLE)"
                line = line.strip().lstrip('-').strip()
                if '(' in line and ')' in line:
                    # Check if this column has a mismatch (red circle emoji)
                    has_mismatch = '🔴' in line
                    # Remove red circle emoji if present
                    line = line.replace('🔴', '').strip()
                    
                    # Extract column name and details
                    col_name = line.split('(')[0].strip()
                    details = line.split('(')[1].split(')')[0]
                    
                    # Split details by comma
                    parts = [p.strip() for p in details.split(',')]
                    data_type = parts[0] if len(parts) > 0 else 'N/A'
                    nullable = parts[1] if len(parts) > 1 else 'N/A'
                    
                    ws.append([col_name, data_type, nullable])
                    # Highlight mismatched columns in red/yellow, otherwise alternate row colors
                    row_num = ws.max_row
                    if has_mismatch:
                        # Red/yellow highlight for mismatched columns
                        fill_color = "FEF3C7"  # Light yellow for warnings
                        for col_idx in range(1, 4):
                            ws.cell(row_num, col_idx).fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                            ws.cell(row_num, col_idx).font = Font(color="92400E")  # Dark yellow text
                    else:
                        # Alternate row colors for better readability
                        fill_color = "EFF6FF" if row_num % 2 == 0 else "FFFFFF"
                        for col_idx in range(1, 4):
                            ws.cell(row_num, col_idx).fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    
    ws.append([""])
    
    # Section 2: Target Table Structure
    ws.append(["TARGET TABLE STRUCTURE"])
    # Style this header
    header_row = ws.max_row
    ws.cell(header_row, 1).font = Font(bold=True, size=12, color="FFFFFF")
    ws.cell(header_row, 1).fill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")
    ws.merge_cells(f'A{header_row}:C{header_row}')
    ws.append([""])
    
    # Try to extract target table column information
    target_match = re.search(r'Target table name:\s*(.+?)\n.*?Number of columns:\s*(\d+)', output_text, re.DOTALL)
    if target_match:
        num_cols_tgt = target_match.group(2)
        ws.append(["Table Name:", target_table])
        ws.cell(ws.max_row, 1).font = Font(bold=True, color="6B21A8")
        ws.cell(ws.max_row, 1).fill = PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid")
        
        ws.append(["Number of Columns:", num_cols_tgt])
        ws.cell(ws.max_row, 1).font = Font(bold=True, color="6B21A8")
        ws.cell(ws.max_row, 1).fill = PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid")
        ws.append([""])
    
    # Extract column details for target
    target_section = re.search(r'Target table name:.*?(?=Structure Comparison Issues:|$)', output_text, re.DOTALL)
    
    if target_section:
        target_text = target_section.group(0)
        col_details = re.search(column_details_pattern, target_text, re.DOTALL)
        
        if col_details:
            # Parse column details
            ws.append(["Column Name", "Data Type", "Nullable"])
            # Style column headers
            header_row = ws.max_row
            for col_idx in range(1, 4):
                ws.cell(header_row, col_idx).font = Font(bold=True, color="FFFFFF")
                ws.cell(header_row, col_idx).fill = PatternFill(start_color="8B5CF6", end_color="8B5CF6", fill_type="solid")
                ws.cell(header_row, col_idx).alignment = Alignment(horizontal='center', vertical='center')
            
            column_lines = col_details.group(1).strip().split('\n')
            for line in column_lines:
                # Parse line like: "Name (varchar, NULLABLE)" or "🔴 Name (varchar, NULLABLE)"
                line = line.strip().lstrip('-').strip()
                if '(' in line and ')' in line:
                    # Check if this column has a mismatch (red circle emoji)
                    has_mismatch = '🔴' in line
                    # Remove red circle emoji if present
                    line = line.replace('🔴', '').strip()
                    
                    # Extract column name and details
                    col_name = line.split('(')[0].strip()
                    details = line.split('(')[1].split(')')[0]
                    
                    # Split details by comma
                    parts = [p.strip() for p in details.split(',')]
                    data_type = parts[0] if len(parts) > 0 else 'N/A'
                    nullable = parts[1] if len(parts) > 1 else 'N/A'
                    
                    ws.append([col_name, data_type, nullable])
                    # Highlight mismatched columns in red/yellow, otherwise alternate row colors
                    row_num = ws.max_row
                    if has_mismatch:
                        # Red/yellow highlight for mismatched columns
                        fill_color = "FEF3C7"  # Light yellow for warnings
                        for col_idx in range(1, 4):
                            ws.cell(row_num, col_idx).fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                            ws.cell(row_num, col_idx).font = Font(color="92400E")  # Dark yellow text
                    else:
                        # Alternate row colors for better readability
                        fill_color = "F5F3FF" if row_num % 2 == 0 else "FFFFFF"
                        for col_idx in range(1, 4):
                            ws.cell(row_num, col_idx).fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    
    ws.append([""])
    
    # Section 3: Structure Comparison Issues (if any)
    if "Structure Comparison Issues:" in output_text:
        ws.append(["STRUCTURE COMPARISON ISSUES"])
        # Style this header with warning color
        header_row = ws.max_row
        ws.cell(header_row, 1).font = Font(bold=True, size=12, color="FFFFFF")
        ws.cell(header_row, 1).fill = PatternFill(start_color="DC2626", end_color="DC2626", fill_type="solid")
        ws.merge_cells(f'A{header_row}:C{header_row}')
        ws.append([""])
        
        # Extract columns only in source
        source_only_pattern = r'Columns in SOURCE but NOT in TARGET:\s*\n((?:\s+🔴.*?\n)+)'
        source_only_match = re.search(source_only_pattern, output_text, re.DOTALL)
        
        if source_only_match:
            ws.append(["Columns in SOURCE but NOT in TARGET"])
            # Style subsection header
            header_row = ws.max_row
            ws.cell(header_row, 1).font = Font(bold=True, color="FFFFFF")
            ws.cell(header_row, 1).fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
            ws.merge_cells(f'A{header_row}:C{header_row}')
            
            ws.append(["Column Name", "Data Type", "Nullable"])
            # Style column headers
            header_row = ws.max_row
            for col_idx in range(1, 4):
                ws.cell(header_row, col_idx).font = Font(bold=True, color="FFFFFF")
                ws.cell(header_row, col_idx).fill = PatternFill(start_color="FBBF24", end_color="FBBF24", fill_type="solid")
                ws.cell(header_row, col_idx).alignment = Alignment(horizontal='center', vertical='center')
            
            lines = source_only_match.group(1).strip().split('\n')
            for line in lines:
                line = line.strip().replace('🔴', '').strip()
                if '(' in line and ')' in line:
                    col_name = line.split('(')[0].strip()
                    details = line.split('(')[1].split(')')[0]
                    parts = [p.strip() for p in details.split(',')]
                    data_type = parts[0] if len(parts) > 0 else 'N/A'
                    nullable = parts[1] if len(parts) > 1 else 'N/A'
                    ws.append([col_name, data_type, nullable])
                    # Highlight missing columns
                    row_num = ws.max_row
                    for col_idx in range(1, 4):
                        ws.cell(row_num, col_idx).fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
            ws.append([""])
        
        # Extract columns only in target
        target_only_pattern = r'Columns in TARGET but NOT in SOURCE:\s*\n((?:\s+🔴.*?\n)+)'
        target_only_match = re.search(target_only_pattern, output_text, re.DOTALL)
        
        if target_only_match:
            ws.append(["Columns in TARGET but NOT in SOURCE"])
            # Style subsection header
            header_row = ws.max_row
            ws.cell(header_row, 1).font = Font(bold=True, color="FFFFFF")
            ws.cell(header_row, 1).fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
            ws.merge_cells(f'A{header_row}:C{header_row}')
            
            ws.append(["Column Name", "Data Type", "Nullable"])
            # Style column headers
            header_row = ws.max_row
            for col_idx in range(1, 4):
                ws.cell(header_row, col_idx).font = Font(bold=True, color="FFFFFF")
                ws.cell(header_row, col_idx).fill = PatternFill(start_color="FBBF24", end_color="FBBF24", fill_type="solid")
                ws.cell(header_row, col_idx).alignment = Alignment(horizontal='center', vertical='center')
            
            lines = target_only_match.group(1).strip().split('\n')
            for line in lines:
                line = line.strip().replace('🔴', '').strip()
                if '(' in line and ')' in line:
                    col_name = line.split('(')[0].strip()
                    details = line.split('(')[1].split(')')[0]
                    parts = [p.strip() for p in details.split(',')]
                    data_type = parts[0] if len(parts) > 0 else 'N/A'
                    nullable = parts[1] if len(parts) > 1 else 'N/A'
                    ws.append([col_name, data_type, nullable])
                    # Highlight missing columns
                    row_num = ws.max_row
                    for col_idx in range(1, 4):
                        ws.cell(row_num, col_idx).fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
            ws.append([""])
        
        # Extract type mismatches
        type_mismatch_pattern = r'Columns with DIFFERENT DATA TYPES or NULLABILITY:\s*\n((?:\s+🔴.*?\n)+)'
        type_mismatch_match = re.search(type_mismatch_pattern, output_text, re.DOTALL)
        
        if type_mismatch_match:
            ws.append(["Columns with DIFFERENT DATA TYPES or NULLABILITY"])
            # Style subsection header
            header_row = ws.max_row
            ws.cell(header_row, 1).font = Font(bold=True, color="FFFFFF")
            ws.cell(header_row, 1).fill = PatternFill(start_color="EF4444", end_color="EF4444", fill_type="solid")
            ws.merge_cells(f'A{header_row}:C{header_row}')
            
            ws.append(["Column Name", "Source Type", "Target Type"])
            # Style column headers
            header_row = ws.max_row
            for col_idx in range(1, 4):
                ws.cell(header_row, col_idx).font = Font(bold=True, color="FFFFFF")
                ws.cell(header_row, col_idx).fill = PatternFill(start_color="F87171", end_color="F87171", fill_type="solid")
                ws.cell(header_row, col_idx).alignment = Alignment(horizontal='center', vertical='center')
            
            lines = type_mismatch_match.group(1).strip().split('\n')
            for line in lines:
                line = line.strip().replace('🔴', '').strip()
                # Parse lines like "ActiveStatus: (varchar,  NULLABLE) vs (varchar, NOT NULL)"
                if ':' in line and ' vs ' in line:
                    col_name = line.split(':')[0].strip()
                    types = line.split(':')[1].strip()
                    source_type = types.split(' vs ')[0].strip()
                    target_type = types.split(' vs ')[1].strip() if ' vs ' in types else 'N/A'
                    ws.append([col_name, source_type, target_type])
                    # Highlight type mismatches
                    row_num = ws.max_row
                    for col_idx in range(1, 4):
                        ws.cell(row_num, col_idx).fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
            ws.append([""])

def parse_and_display_null_details(ws, output_text, table_type):
    """Parse null check output and display all column details in Excel"""
    print(f"[DEBUG parse_and_display_null_details] Called for {table_type}")
    print(f"[DEBUG parse_and_display_null_details] Output text length: {len(output_text) if output_text else 0}")
    print(f"[DEBUG parse_and_display_null_details] Output preview (first 400 chars): {output_text[:400] if output_text else 'None'}")
    
    if not output_text or output_text.strip() == "":
        ws.append(["No null check data available."])
        return
    
    # Check if this is a skip message (no actual null check was performed)
    if "Null Check skipped" in output_text or "No NOT NULL constraints" in output_text:
        # Display the skip message directly
        ws.append([output_text.strip()])
        # Merge cells for better display
        ws.merge_cells(f'A{ws.max_row}:C{ws.max_row}')
        ws.cell(ws.max_row, 1).font = Font(italic=True, color="0369A1")
        ws.cell(ws.max_row, 1).fill = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid")
        ws.cell(ws.max_row, 1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        return
    
    # Parse the null check report
    lines = output_text.strip().split('\n')
    
    # Extract column information
    ws.append(["Column Name", "NULL Count", "Constraints"])
    # Style column headers based on table type
    header_row = ws.max_row
    header_color = "2563EB" if table_type == "Source" else "8B5CF6"
    for col_idx in range(1, 4):
        ws.cell(header_row, col_idx).font = Font(bold=True, color="FFFFFF")
        ws.cell(header_row, col_idx).fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")
        ws.cell(header_row, col_idx).alignment = Alignment(horizontal='center', vertical='center')
    
    for line in lines:
        line = line.strip()
        
        # Skip header lines and summary lines
        if not line or line.startswith('🚫') or line.startswith('✅') or line.startswith('🚨') or line.startswith('Nullable') or line.startswith('❌') or line.startswith('ℹ️') or line.startswith('⚠️'):
            continue
        
        # Parse lines like: " - EmployeeID 🔑 PRIMARY KEY 🔒 NOT NULL: 0 NULLs"
        # or " - Name 🔒 NOT NULL: 5 NULLs"
        # or " - VendorSAPCode: 0 NULLs"
        if line.startswith('-') or ':' in line:
            # Remove leading dash if present
            if line.startswith('-'):
                line = line.lstrip('-').strip()
            
            # Extract column name and null count
            if ':' in line:
                parts = line.split(':', 1)  # Split only on first colon
                col_part = parts[0].strip()
                null_part = parts[1].strip() if len(parts) > 1 else "0 NULLs"
                
                # Extract constraints from column part
                constraints = []
                col_name = col_part
                
                # Check for PRIMARY KEY (with or without emoji)
                if '🔑 PRIMARY KEY' in col_part or 'PRIMARY KEY' in col_part:
                    constraints.append('PRIMARY KEY')
                    col_name = col_name.replace('🔑 PRIMARY KEY', '').replace('PRIMARY KEY', '').strip()
                
                # Check for NOT NULL (with or without emoji)
                if '🔒 NOT NULL' in col_part or 'NOT NULL' in col_part:
                    constraints.append('NOT NULL')
                    col_name = col_name.replace('🔒 NOT NULL', '').replace('NOT NULL', '').strip()
                
                # Clean up any remaining emojis from column name
                col_name = col_name.replace('🔑', '').replace('🔒', '').strip()
                
                # Extract null count using regex to handle both "NULL" and "NULLs"
                null_count = "0"
                if 'NULL' in null_part:
                    try:
                        import re
                        # Match patterns like "0 NULLs" or "15 NULL" or just "0"
                        match = re.search(r'(\d+)\s*NULL', null_part)
                        if match:
                            null_count = match.group(1)
                        else:
                            # Try to extract just a number
                            match = re.search(r'(\d+)', null_part)
                            if match:
                                null_count = match.group(1)
                    except:
                        null_count = "0"
                
                # Only add if we have a valid column name (not a duplicate header or status line)
                if col_name and col_name not in ['Column Name', 'Status', 'Check']:
                    # Add to worksheet
                    constraint_text = ", ".join(constraints) if constraints else "None"
                    ws.append([col_name, null_count, constraint_text])
                    
                    # Style the row based on null count and constraints
                    row_num = ws.max_row
                    try:
                        null_count_int = int(null_count)
                        has_violations = null_count_int > 0 and len(constraints) > 0
                        
                        if has_violations:
                            # Red highlight for constraint violations
                            for col_idx in range(1, 4):
                                ws.cell(row_num, col_idx).fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                            ws.cell(row_num, 2).font = Font(bold=True, color="991B1B")
                        elif len(constraints) > 0:
                            # Light blue/purple for columns with constraints (no violations)
                            bg_color = "DBEAFE" if table_type == "Source" else "EDE9FE"
                            for col_idx in range(1, 4):
                                ws.cell(row_num, col_idx).fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
                            ws.cell(row_num, 3).font = Font(bold=True, color="1E40AF" if table_type == "Source" else "6B21A8")
                        else:
                            # Alternate colors for regular columns
                            fill_color = "EFF6FF" if table_type == "Source" else "F5F3FF"
                            alt_color = "FFFFFF"
                            bg_color = fill_color if row_num % 2 == 0 else alt_color
                            for col_idx in range(1, 4):
                                ws.cell(row_num, col_idx).fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
                    except ValueError:
                        # If null_count is not a valid integer, just apply default styling
                        fill_color = "EFF6FF" if table_type == "Source" else "F5F3FF"
                        alt_color = "FFFFFF"
                        bg_color = fill_color if row_num % 2 == 0 else alt_color
                        for col_idx in range(1, 4):
                            ws.cell(row_num, col_idx).fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
    
    # Add summary line
    ws.append([""])
    ws.append(["Status:"])
    status_row = ws.max_row
    ws.cell(status_row, 1).font = Font(bold=True, size=11)
    
    if "Constraint Violations:" in output_text or "violation" in output_text.lower():
        ws.cell(status_row, 2).value = "⚠️ CONSTRAINT VIOLATIONS DETECTED"
        ws.cell(status_row, 2).font = Font(bold=True, color="FFFFFF")
        ws.cell(status_row, 2).fill = PatternFill(start_color="DC2626", end_color="DC2626", fill_type="solid")
    elif "verified" in output_text.lower() or "✅" in output_text:
        ws.cell(status_row, 2).value = "✅ All constraints verified successfully"
        ws.cell(status_row, 2).font = Font(bold=True, color="FFFFFF")
        ws.cell(status_row, 2).fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
    else:
        ws.cell(status_row, 2).value = "Checked"
        ws.cell(status_row, 2).font = Font(bold=True, color="475569")

def generate_excel_report(results, output_file="reports/etl_validation_report.xlsx", source_table=None, target_table=None, sample_size=0, source_db_config=None, target_db_config=None):
    """Generate comprehensive Excel report with tabular data for duplicates and mismatches"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Force fresh file - delete if exists to prevent caching
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
            print(f"[DEBUG] Deleted old Excel file to force fresh generation")
        except:
            pass
    
    # Set table names if provided (treat empty strings as None)
    print(f"[DEBUG] generate_excel_report called with source_table='{source_table}', target_table='{target_table}', sample_size={sample_size}")
    src_table = source_table if source_table and source_table.strip() else SOURCE_TABLE
    tgt_table = target_table if target_table and target_table.strip() else TARGET_TABLE
    print(f"[DEBUG] Using src_table='{src_table}', tgt_table='{tgt_table}'")
    
    wb = Workbook()
    
    # ===== Sheet 1: Executive Summary =====
    ws_summary = wb.active
    ws_summary.title = "Executive Summary"
    
    # Header
    ws_summary.append(["ETL Validation Report"])
    ws_summary.append([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ws_summary.append([""])
    
    # SOURCE CONFIGURATION
    ws_summary.append(["SOURCE CONFIGURATION"])
    if source_db_config:
        db_type = source_db_config.get('type', 'SQL Server')
        
        # Map database types to display names
        db_type_mapping = {
            'sqlserver': 'SQL Server',
            'default': 'SQL Server',
            'databricks': 'Databricks',
            'databricks_example': 'Databricks',
            'azuresynapse': 'Azure Synapse',
            'fabric': 'Microsoft Fabric',
            'mysql': 'MySQL',
            'postgresql': 'PostgreSQL',
            'oracle': 'Oracle Database',
            'mongodb': 'MongoDB',
            's3': 'AWS S3',
            'azureblob': 'Azure Blob Storage',
            'gcs': 'Google Cloud Storage',
            'powerbi': 'Power BI'
        }
        
        db_type_display = db_type_mapping.get(db_type, db_type)
        is_databricks = db_type in ('databricks', 'databricks_example')
        
        ws_summary.append(["Source Database Type:", db_type_display])
        
        # Extract appropriate fields based on database type
        if is_databricks:
            # Databricks specific fields
            workspace_url = source_db_config.get('workspace_url', 'N/A')
            catalog = source_db_config.get('catalog', 'N/A')
            schema = source_db_config.get('schema', 'N/A')
            
            ws_summary.append(["Server/Host:", workspace_url])
            ws_summary.append(["Database:", f"{catalog}.{schema}" if catalog != 'N/A' and schema != 'N/A' else catalog])
            
            # Databricks authentication
            databricks_auth = source_db_config.get('databricks_auth_type', source_db_config.get('auth_type', 'token'))
            if databricks_auth == 'token':
                auth_display = 'Access Token'
            elif databricks_auth == 'azure_ad':
                auth_display = 'Azure AD Service Principal'
            else:
                auth_display = databricks_auth
            ws_summary.append(["Authentication:", auth_display])
        else:
            # RDBMS and other types - use standard fields
            ws_summary.append(["Server/Host:", source_db_config.get('server', source_db_config.get('host', 'N/A'))])
            ws_summary.append(["Database:", source_db_config.get('database', 'N/A')])
            
            auth_type = source_db_config.get('authType', source_db_config.get('auth_type', 'Windows'))
            if auth_type == 'windows' or auth_type == 'yes':
                auth_type = 'Windows Authentication'
            elif auth_type == 'ActiveDirectoryMfa':
                auth_type = 'Azure AD MFA'
            elif source_db_config.get('username'):
                auth_type = 'Username/Password'
            ws_summary.append(["Authentication:", auth_type])
    else:
        ws_summary.append(["Source Database Type:", "SQL Server"])
        ws_summary.append(["Server/Host:", "Default Connection"])
        ws_summary.append(["Database:", "N/A"])
        ws_summary.append(["Authentication:", "Windows"])
    ws_summary.append(["Table/Query:", src_table])
    ws_summary.append([""])
    
    # TARGET CONFIGURATION
    ws_summary.append(["TARGET CONFIGURATION"])
    if target_db_config:
        db_type = target_db_config.get('type', 'SQL Server')
        
        # Map database types to display names
        db_type_mapping = {
            'sqlserver': 'SQL Server',
            'default': 'SQL Server',
            'databricks': 'Databricks',
            'databricks_example': 'Databricks',
            'azuresynapse': 'Azure Synapse',
            'fabric': 'Microsoft Fabric',
            'mysql': 'MySQL',
            'postgresql': 'PostgreSQL',
            'oracle': 'Oracle Database',
            'mongodb': 'MongoDB',
            's3': 'AWS S3',
            'azureblob': 'Azure Blob Storage',
            'gcs': 'Google Cloud Storage',
            'powerbi': 'Power BI'
        }
        
        db_type_display = db_type_mapping.get(db_type, db_type)
        is_databricks = db_type in ('databricks', 'databricks_example')
        
        ws_summary.append(["Target Database Type:", db_type_display])
        
        # Extract appropriate fields based on database type
        if is_databricks:
            # Databricks specific fields
            workspace_url = target_db_config.get('workspace_url', 'N/A')
            catalog = target_db_config.get('catalog', 'N/A')
            schema = target_db_config.get('schema', 'N/A')
            
            ws_summary.append(["Server/Host:", workspace_url])
            ws_summary.append(["Database:", f"{catalog}.{schema}" if catalog != 'N/A' and schema != 'N/A' else catalog])
            
            # Databricks authentication
            databricks_auth = target_db_config.get('databricks_auth_type', target_db_config.get('auth_type', 'token'))
            if databricks_auth == 'token':
                auth_display = 'Access Token'
            elif databricks_auth == 'azure_ad':
                auth_display = 'Azure AD Service Principal'
            else:
                auth_display = databricks_auth
            ws_summary.append(["Authentication:", auth_display])
        else:
            # RDBMS and other types - use standard fields
            ws_summary.append(["Server/Host:", target_db_config.get('server', target_db_config.get('host', 'N/A'))])
            ws_summary.append(["Database:", target_db_config.get('database', 'N/A')])
            
            auth_type = target_db_config.get('authType', target_db_config.get('auth_type', 'Windows'))
            if auth_type == 'windows' or auth_type == 'yes':
                auth_type = 'Windows Authentication'
            elif auth_type == 'ActiveDirectoryMfa':
                auth_type = 'Azure AD MFA'
            elif target_db_config.get('username'):
                auth_type = 'Username/Password'
            ws_summary.append(["Authentication:", auth_type])
    else:
        ws_summary.append(["Target Database Type:", "SQL Server"])
        ws_summary.append(["Server/Host:", "Default Connection"])
        ws_summary.append(["Database:", "N/A"])
        ws_summary.append(["Authentication:", "Windows"])
    ws_summary.append(["Table/Query:", tgt_table])
    ws_summary.append([""])
    
    if sample_size > 0:
        ws_summary.append(["Sampling:", f"TOP {sample_size} records (for performance optimization)"])
        ws_summary.append([""])
    
    # Summary Statistics
    ws_summary.append(["VALIDATION SUMMARY"])
    ws_summary.append(["Check", "Status", "Details"])
    
    # Define checks - combine Null Check and Duplicate Check
    individual_checks = [
        ("Structure Validation", "Structure Validation"),
        ("Record Count Check", "Record Count Check"),
        ("Null Check", ["Null Check (Source Table)", "Null Check (Target Table)"]),
        ("Duplicate Check", ["Duplicate Check (Source Table)", "Duplicate Check (Target Table)"]),
        ("Row-wise Data Validation", "Row-wise Data Validation")
    ]
    
    total_validations = 5  # Fixed: 5 main validation types
    pass_count = 0
    fail_count = 0
    
    for display_name, keys in individual_checks:
        # Handle combined checks (Null and Duplicate)
        if isinstance(keys, list):
            combined_status = "PASS"
            combined_details = []
            
            for key in keys:
                result = results.get(key, {})
                if isinstance(result, dict):
                    if not result.get("passed", False):
                        combined_status = "FAIL"
                    output = result.get("output", "")
                    detail = get_summary_details(key, output)
                    # Extract table type (Source/Target)
                    table_type = "Source" if "Source" in key else "Target"
                    combined_details.append(f"{table_type}: {detail}")
            
            # Join details
            final_details = ", ".join(combined_details) if combined_details else "Checked"
            ws_summary.append([display_name, combined_status, final_details])
            
            if combined_status == "PASS":
                pass_count += 1
            else:
                fail_count += 1
        else:
            # Single check
            result = results.get(keys, {})
            
            if isinstance(result, dict):
                status = "PASS" if result.get("passed", False) else "FAIL"
                output = result.get("output", "")
            else:
                status = "INFO"
                output = str(result)
            
            if status == "PASS":
                pass_count += 1
            elif status == "FAIL":
                fail_count += 1
            
            details = get_summary_details(keys, output if isinstance(result, dict) else result)
            ws_summary.append([display_name, status, details])
    
    ws_summary.append([""])
    ws_summary.append(["Total Validations", total_validations])
    ws_summary.append(["Passed", pass_count])
    ws_summary.append(["Failed", fail_count])
    ws_summary.append([""])
    ws_summary.append(["OVERALL RESULT", f"Passed: {pass_count}, Failed: {fail_count}"])
    
    # Style summary sheet
    style_summary_sheet(ws_summary)
    
    # ===== Sheet 2: Mismatch Records (Source vs Target Comparison) =====
    ws_mismatch = wb.create_sheet("Mismatch Records")
    # Ensure we're using the LATEST mismatch log from current run
    mismatch_log_path = os.path.join("logs", "row_data_mismatch_log.txt")
    if not os.path.exists(mismatch_log_path):
        # Try project-specific path
        mismatch_log_path = os.path.join("..", "etl_project_two_tables", "logs", "row_data_mismatch_log.txt")
    
    mismatch_data = parse_mismatch_log(mismatch_log_path)
    
    # Parse all source and target records
    source_records = []
    target_records = []
    
    for record in mismatch_data['source']:
        try:
            if record.startswith('{'):
                record_dict = ast.literal_eval(record)
                source_records.append(record_dict)
        except:
            pass
    
    for record in mismatch_data['target']:
        try:
            if record.startswith('{'):
                record_dict = ast.literal_eval(record)
                target_records.append(record_dict)
        except:
            pass
    
    print(f"[DEBUG] Mismatch log parsing results:")
    print(f"[DEBUG]   Source records found: {len(source_records)}")
    print(f"[DEBUG]   Target records found: {len(target_records)}")
    print(f"[DEBUG]   Total from log: {len(source_records) + len(target_records)}")
    
    total_mismatches = len(source_records) + len(target_records)
    
    ws_mismatch.append(["ROW DATA MISMATCH SUMMARY"])
    ws_mismatch.append(["Source Table:", src_table])
    ws_mismatch.append(["Target Table:", tgt_table])
    ws_mismatch.append([""])
    ws_mismatch.append(["Category", "Count"])
    ws_mismatch.append(["Records only in Source", len(source_records)])
    ws_mismatch.append(["Records only in Target", len(target_records)])
    ws_mismatch.append(["Total Mismatched Records", total_mismatches])
    ws_mismatch.append([""])
    ws_mismatch.append(["HOW TO READ THIS REPORT:"])
    ws_mismatch.append(["• Blue columns (src_*) = Source table values"])
    ws_mismatch.append(["• Purple columns (tgt_*) = Target table values"])
    ws_mismatch.append(["• Yellow highlighting = Values differ between source & target"])
    ws_mismatch.append(["• Records are paired using composite key (all columns) with similarity matching"])
    ws_mismatch.append(["• Each row shows the best match between source and target records"])
    ws_mismatch.append([""])
    
    # Create source vs target comparison table
    # IMPORTANT: "Only in Source" means NO match in target (display source with empty target)
    # IMPORTANT: "Only in Target" means NO match in source (display target with empty source)
    if total_mismatches > 0:
        ws_mismatch.append(["SOURCE VS TARGET COMPARISON"])
        ws_mismatch.append([""])
        
# Get column names and handle mapping when source/target have different naming or ordering
    # This matches the logic in validate.py for consistent behavior
    source_columns = []
    target_columns = []
    
    if source_records:
        source_columns = list(source_records[0].keys())
    if target_records:
        target_columns = list(target_records[0].keys())
    
    # Check if columns need mapping or reordering
    src_set = set(source_columns)
    tgt_set = set(target_columns)
    
    # Create column mapping: source_col_name -> target_col_name
    column_mapping = {}
    
    if src_set == tgt_set and source_columns != target_columns:
        # Case 1: Same column names but DIFFERENT ORDER
        # Example: Source=['A','B','C'], Target=['B','A','C']
        # Create identity mapping (column name stays same, but we know order differs)
        for col in source_columns:
            column_mapping[col] = col
        print(f"[DEBUG] Column order difference detected - same names, different positions")
        print(f"[DEBUG] Source order: {source_columns[:5]}...")
        print(f"[DEBUG] Target order: {target_columns[:5]}...")
        
    elif len(source_columns) == len(target_columns) and src_set != tgt_set:
        # Case 2: DIFFERENT column names at same positions (position-based mapping)
        # Example: Source=['FileName'], Target=['file_name']
        for src_col, tgt_col in zip(source_columns, target_columns):
            column_mapping[src_col] = tgt_col
        print(f"[DEBUG] Position-based column mapping created: {len(column_mapping)} mappings")
        print(f"[DEBUG] Example mappings: {list(column_mapping.items())[:5]}")
        
    else:
        # Case 3: Columns match perfectly (same names, same order)
        for col in source_columns:
            column_mapping[col] = col
        print(f"[DEBUG] Columns match perfectly - no mapping needed")
    
    # Use source column names as the canonical column list
    columns = source_columns
    
    print(f"[DEBUG] Total columns found: {len(columns)}")
    print(f"[DEBUG] All columns: {columns}")
    if source_records:
        print(f"[DEBUG] Sample source record keys: {list(source_records[0].keys())}")
    if target_records:
        print(f"[DEBUG] Sample target record keys: {list(target_records[0].keys())}")
    
    # Initialize variables that will be used later
    mismatch_cells = []
    data_start_row = 0
    
    if columns:
        # Create header row with interleaved source and target columns
        header_row = ["Row #"]
        for col in columns:
            header_row.append(f"src_{col}")
            header_row.append(f"tgt_{col}")
        ws_mismatch.append(header_row)
        print(f"[DEBUG] Created header row with {len(columns)} column pairs")
        
        # Use COMPOSITE KEY approach (all columns as tuple) to find similar records
        # This matches how the dashboard validation works with tuple comparison
        print(f"[DEBUG] Using composite key (all columns) for intelligent pairing")
        
        # Create tuple-based keys for each record (like validate.py does)
        import re
        
        def make_tuple_key(record, cols):
            """Create a tuple of all column values for comparison, with date normalization"""
            normalized_values = []
            for col in cols:
                val = record.get(col, '')
                if val is None:
                    normalized_values.append('')
                else:
                    val_str = str(val).strip()
                    # Normalize dates: remove timezone and fractional seconds
                    # '2025-10-17T14:24:15+00:00' -> '2025-10-17T14:24:15'
                    # '2025-10-17T15:31:07.310000' -> '2025-10-17T15:31:07'
                    val_str = re.sub(r'[+-]\d{2}:\d{2}$', '', val_str)  # Remove +00:00, -05:00
                    val_str = re.sub(r'Z$', '', val_str)  # Remove Z
                    val_str = re.sub(r'\.\d+', '', val_str)  # Remove .310000
                    normalized_values.append(val_str)
            return tuple(normalized_values)
        
        # Build mappings: tuple -> record
        source_tuples = {}
        target_tuples = {}
        
        for rec in source_records:
            key = make_tuple_key(rec, columns)
            source_tuples[key] = rec
        
        for rec in target_records:
            key = make_tuple_key(rec, columns)
            target_tuples[key] = rec
        
        print(f"[DEBUG] Source records: {len(source_tuples)}")
        print(f"[DEBUG] Target records: {len(target_tuples)}")
        
        # Find best matches: for each source record, find closest target record
        # Use similarity scoring based on matching column values
        def calculate_similarity(src_rec, tgt_rec, cols):
            """Calculate how many columns match between two records"""
            matches = sum(1 for col in cols if str(src_rec.get(col, '')).strip() == str(tgt_rec.get(col, '')).strip())
            return matches
        
        # Create paired comparisons with intelligent matching
        paired_records = []
        used_target_keys = set()
        
        for src_key, src_rec in source_tuples.items():
            best_match = None
            best_score = -1
            best_tgt_key = None
            
            # Find the target record with highest similarity
            for tgt_key, tgt_rec in target_tuples.items():
                if tgt_key not in used_target_keys:
                    score = calculate_similarity(src_rec, tgt_rec, columns)
                    if score > best_score:
                        best_score = score
                        best_match = tgt_rec
                        best_tgt_key = tgt_key
            
            if best_match:
                paired_records.append((src_rec, best_match))
                used_target_keys.add(best_tgt_key)
            else:
                # No good match found, pair with empty target
                paired_records.append((src_rec, {}))
        
        # Add remaining unmatched target records
        for tgt_key, tgt_rec in target_tuples.items():
            if tgt_key not in used_target_keys:
                paired_records.append(({}, tgt_rec))
        
        print(f"[DEBUG] Created {len(paired_records)} paired comparisons")
        print(f"[DEBUG] Pairs with both sides: {sum(1 for src, tgt in paired_records if src and tgt)}")
        print(f"[DEBUG] Source-only records: {sum(1 for src, tgt in paired_records if src and not tgt)}")
        print(f"[DEBUG] Target-only records: {sum(1 for src, tgt in paired_records if not src and tgt)}")
        print(f"[DEBUG] Target-only records: {sum(1 for src, tgt in paired_records if not src and tgt)}")
        
        # Store cell positions for highlighting
        mismatch_cells = []
        data_start_row = ws_mismatch.max_row + 1
        
        # Display paired comparisons (limit to 1000 for performance)
        display_limit = min(len(paired_records), 1000)
        for idx, (src_record, tgt_record) in enumerate(paired_records[:display_limit]):
            comparison_row = [idx + 1]  # Row number
            col_idx = 0  # Track column position (0-indexed)
            
            for col in columns:
                src_val = src_record.get(col, '') if src_record else ''
                
                # Map source column name to target column name if they differ
                tgt_col = column_mapping.get(col, col)
                tgt_val = tgt_record.get(tgt_col, '') if tgt_record else ''
                
                # Convert to string, handling None and keeping falsy values like 0, False
                if src_val is None:
                    src_str = ''
                elif src_val == '':
                    src_str = ''
                else:
                    src_str = str(src_val).strip()
                
                if tgt_val is None:
                    tgt_str = ''
                elif tgt_val == '':
                    tgt_str = ''
                else:
                    tgt_str = str(tgt_val).strip()
                
                comparison_row.append(src_str)
                comparison_row.append(tgt_str)
                
                # Debug first row to verify data extraction
                if idx == 0 and col in ['FileName', 'file_name', 'BatchID', 'LoadDateTime']:
                    print(f"[DEBUG] Row 0, Col '{col}' (target:'{tgt_col}'): src_raw={repr(src_val)}, tgt_raw={repr(tgt_val)}, src_str='{src_str}', tgt_str='{tgt_str}'")
                
                # Highlight ONLY if BOTH sides have values AND they differ
                if src_str and tgt_str and src_str != tgt_str:
                    excel_row = data_start_row + idx
                    src_col = col_idx * 2 + 2  # Source column position in Excel
                    tgt_col = col_idx * 2 + 3  # Target column position in Excel
                    mismatch_cells.append((excel_row, src_col))
                    mismatch_cells.append((excel_row, tgt_col))
                    
                    # Debug first 10 mismatches
                    if len(mismatch_cells) <= 20:
                        print(f"[DEBUG] Highlight: row={excel_row}, col='{col}', src='{src_str[:20]}...', tgt='{tgt_str[:20]}...', src_excel_col={src_col}, tgt_excel_col={tgt_col}")
                
                col_idx += 1
            
            ws_mismatch.append(comparison_row)
        
        print(f"[DEBUG] Displayed {display_limit} comparison rows")
        print(f"[DEBUG] Collected {len(mismatch_cells)} cells for yellow highlighting")
    else:
        # No mismatches found - display message
        ws_mismatch.append(["No mismatches found."])
        ws_mismatch.append(["All records match between source and target tables."])
        mismatch_cells = []  # No cells to highlight
    
    # CRITICAL: Apply highlighting FIRST before styling
    if mismatch_cells:
        from openpyxl.styles import PatternFill
        highlight_fill = PatternFill(start_color="FFEB3B", end_color="FFEB3B", fill_type="solid")
        
        print(f"[DEBUG] ========================================")
        print(f"[DEBUG] Applying yellow highlighting to {len(mismatch_cells)} cells")
        print(f"[DEBUG] Data starts at row {data_start_row}")
        print(f"[DEBUG] Sheet has {ws_mismatch.max_row} rows and {ws_mismatch.max_column} columns")
        
        highlighted_count = 0
        for row_idx, col_idx in mismatch_cells[:20]:  # Show first 20 for debugging
            try:
                cell = ws_mismatch.cell(row=row_idx, column=col_idx)
                old_fill = cell.fill.start_color.index if cell.fill else 'NONE'
                cell.fill = highlight_fill
                highlighted_count += 1
                if highlighted_count <= 5:  # Detailed output for first 5
                    print(f"[DEBUG] Highlighted cell row={row_idx}, col={col_idx}, value={cell.value}, old_fill={old_fill}")
            except Exception as e:
                print(f"[ERROR] Failed to highlight cell at row={row_idx}, col={col_idx}: {e}")
        
        # Apply all remaining cells without debug output
        for row_idx, col_idx in mismatch_cells[20:]:
            try:
                cell = ws_mismatch.cell(row=row_idx, column=col_idx)
                cell.fill = highlight_fill
                highlighted_count += 1
            except:
                pass
        
        print(f"[DEBUG] Successfully highlighted {highlighted_count} cells")
        print(f"[DEBUG] ========================================")
    else:
        print(f"[DEBUG] No mismatch cells to highlight")
    
    # Now apply styling - pass mismatch_cells so styling skips them
    style_mismatch_sheet_comparison(ws_mismatch, mismatch_cells)
    
    # ===== Sheet 3: Matched Records =====
    ws_matched = wb.create_sheet("Matched Records")
    
    # IMPORTANT: Get matched count from CURRENT validation results, NOT from old CSV files
    matched_count = 0
    row_validation = results.get("Row-wise Data Validation", {})
    
    print(f"[DEBUG] ========================================")
    print(f"[DEBUG] MATCHED RECORDS DETECTION")
    print(f"[DEBUG] Results keys: {list(results.keys())}")
    
    if row_validation:
        output_html = row_validation.get('output', '')
        print(f"[DEBUG] Row validation output length: {len(output_html)} chars")
        print(f"[DEBUG] Searching for matched count in output...")
        
        # Parse matched count from HTML output (format: "✅ Matched Rows: 123")
        import re
        match = re.search(r'✅\s*Matched\s*Rows?:\s*(\d+)', output_html)
        if match:
            matched_count = int(match.group(1))
            print(f"[DEBUG] ✅ Found matched count from validation results: {matched_count}")
        else:
            print(f"[DEBUG] ❌ Could not find matched count pattern in output")
            print(f"[DEBUG] Output snippet: {output_html[:500]}")
            # Force to 0 if we can't find the count
            matched_count = 0
    else:
        print(f"[DEBUG] ❌ No Row-wise Data Validation result found")
    
    ws_matched.append(["MATCHED RECORDS SUMMARY"])
    ws_matched.append(["Source Table:", src_table])
    ws_matched.append(["Target Table:", tgt_table])
    ws_matched.append([""])
    ws_matched.append(["Total Matched Records", matched_count])
    ws_matched.append([""])
    ws_matched.append(["NOTE: These records have identical values across ALL columns in both source and target tables."])
    ws_matched.append([""])
    
    print(f"[DEBUG] Writing matched count to sheet: {matched_count}")
    
    # CRITICAL: Only load and display CSV data if current validation has matches
    matched_data = []
    if matched_count > 0:
        print(f"[DEBUG] Matched count > 0, loading CSV data...")
        logs_abs_path = os.path.dirname(os.path.abspath(mismatch_log_path))
        
        print(f"[DEBUG] Looking for matched CSV in: {logs_abs_path}")
        
        matched_data = parse_matched_csv(logs_abs_path)
        
        csv_files = glob.glob(os.path.join(logs_abs_path, "*_matched_rows_*.csv"))
        if csv_files:
            latest = max(csv_files, key=os.path.getmtime)
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest))
            print(f"[DEBUG] Latest matched CSV: {os.path.basename(latest)}")
            print(f"[DEBUG] Modified: {mod_time}")
            print(f"[DEBUG] Loaded {len(matched_data)} rows from CSV")
        else:
            print(f"[DEBUG] ❌ No matched CSV files found")
            matched_data = []
    else:
        print(f"[DEBUG] ✅ Matched count is 0 - NOT loading any CSV data")
        print(f"[DEBUG] This ensures we don't show old data from previous validations")
    
    print(f"[DEBUG] ========================================")
    
    if matched_data and len(matched_data) > 1:
        ws_matched.append(["MATCHED RECORD DETAILS (Sample - Up to 1000 rows)"])
        ws_matched.append([""])
        
        # Get columns from first record
        if matched_data and len(matched_data[0]) > 0:
            columns = matched_data[0]  # First row is header
            ws_matched.append(columns)
            
            print(f"[DEBUG] Adding {min(len(matched_data)-1, 1000)} matched records to Excel...")
            
            # Add data rows (limit to 1000 for performance as requested)
            for row_data in matched_data[1:1001]:
                ws_matched.append(row_data)
            
            if len(matched_data) > 1001:
                ws_matched.append([""])
                ws_matched.append([f"... and {len(matched_data) - 1001} more matched rows"])
            
            print(f"[DEBUG] ✅ Successfully added {min(len(matched_data)-1, 1000)} matched records to sheet")
    else:
        print(f"[DEBUG] ❌ matched_data is empty or has only header row")
        print(f"[DEBUG] matched_data length: {len(matched_data) if matched_data else 0}")
        ws_matched.append(["No matched records found."])
        ws_matched.append(["This indicates that all records are either only in source or only in target."])
    
    style_matched_sheet(ws_matched)
    
    # ===== Add Individual Validation Sheets (Remove Duplicate Records and Record Counts sheets) =====
    # Only create: Structure Validation, Record Count Validation, Null Check, Duplicate Check
    
    # Structure Validation Sheet
    ws_struct = wb.create_sheet("Structure Validation")
    ws_struct.append(["STRUCTURE VALIDATION"])
    ws_struct.append([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ws_struct.append([""])
    ws_struct.append(["Source Table:", src_table])
    ws_struct.append(["Target Table:", tgt_table])
    ws_struct.append([""])
    ws_struct.append(["Summary Statistics"])
    ws_struct.append(["Total Validations:", total_validations])
    ws_struct.append(["Passed:", pass_count])
    ws_struct.append(["Failed:", fail_count])
    ws_struct.append([""])
    ws_struct.append(["Validation Details"])
    ws_struct.append(["Check", "Status", "Output"])
    
    # Add Structure Validation with detailed parsing
    result = results.get("Structure Validation", {})
    if isinstance(result, dict):
        status = "PASS" if result.get("passed", False) else "FAIL"
        output = strip_html_tags(str(result.get("output", "")))
    else:
        status = "INFO"
        output = str(result)
    ws_struct.append(["Structure Validation", status, "See detailed breakdown below"])
    ws_struct.append([""])
    
    # Parse and display detailed structure information
    parse_and_display_structure_details(ws_struct, output, src_table, tgt_table)
    
    style_validation_detail_sheet(ws_struct)
    
    # Record Count Validation Sheet
    ws_count = wb.create_sheet("Record Count Validation")
    ws_count.append(["RECORD COUNT VALIDATION"])
    ws_count.append([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ws_count.append([""])
    ws_count.append(["Source Table:", src_table])
    ws_count.append(["Target Table:", tgt_table])
    ws_count.append([""])
    ws_count.append(["Summary Statistics"])
    ws_count.append(["Total Validations:", total_validations])
    ws_count.append(["Passed:", pass_count])
    ws_count.append(["Failed:", fail_count])
    ws_count.append([""])
    ws_count.append(["Validation Details"])
    ws_count.append(["Check", "Status", "Output"])
    
    # Add only Record Count Check
    result = results.get("Record Count Check", {})
    if isinstance(result, dict):
        status = "PASS" if result.get("passed", False) else "FAIL"
        output = strip_html_tags(str(result.get("output", "")))
    else:
        status = "INFO"
        output = str(result)
    ws_count.append(["Record Count Check", status, output[:1000]])
    style_validation_detail_sheet(ws_count)
    
    # Null Check Sheet - Enhanced to show all column details
    ws_null = wb.create_sheet("Null Check")
    ws_null.append(["NULL CHECK VALIDATION"])
    ws_null.append([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ws_null.append([""])
    ws_null.append(["Source Table:", src_table])
    ws_null.append(["Target Table:", tgt_table])
    ws_null.append([""])
    ws_null.append(["Summary Statistics"])
    ws_null.append(["Total Validations:", total_validations])
    ws_null.append(["Passed:", pass_count])
    ws_null.append(["Failed:", fail_count])
    ws_null.append([""])
    
    # Add Null Check for Source Table with detailed column breakdown
    ws_null.append(["SOURCE TABLE NULL CHECK DETAILS"])
    ws_null.append([""])
    source_null_result = results.get("Null Check (Source Table)", {})
    print(f"[DEBUG REPORT] Source null result type: {type(source_null_result)}")
    
    # NEW APPROACH: If we have combined data (both source and target in one), split it here
    if isinstance(source_null_result, dict):
        source_output = strip_html_tags(str(source_null_result.get("output", "")))
        
        # Check if this contains BOTH source AND target (separator present)
        separator = "\n" + "="*80 + "\n"
        if separator in source_output:
            print(f"[DEBUG REPORT] FOUND COMBINED DATA - Splitting now in Excel generator")
            parts = source_output.split(separator)
            source_only = parts[0].strip() if len(parts) > 0 else source_output
            target_only = parts[1].strip() if len(parts) > 1 else ""
            
            # Use only source part
            print(f"[DEBUG REPORT] After split - Source length: {len(source_only)}, Target length: {len(target_only)}")
            parse_and_display_null_details(ws_null, source_only, "Source")
            
            # Store target for later use
            _extracted_target_output = target_only
        else:
            print(f"[DEBUG REPORT] Source output (first 300 chars): {source_output[:300]}")
            parse_and_display_null_details(ws_null, source_output, "Source")
            _extracted_target_output = None
    else:
        ws_null.append([str(source_null_result)])
        _extracted_target_output = None
    
    ws_null.append([""])
    ws_null.append([""])
    
    # Add Null Check for Target Table with detailed column breakdown
    ws_null.append(["TARGET TABLE NULL CHECK DETAILS"])
    ws_null.append([""])
    target_null_result = results.get("Null Check (Target Table)", {})
    print(f"[DEBUG REPORT] Target null result type: {type(target_null_result)}")
    
    # NEW APPROACH: Use extracted target if we split combined data above
    if _extracted_target_output:
        print(f"[DEBUG REPORT] Using extracted target data: {len(_extracted_target_output)} chars")
        parse_and_display_null_details(ws_null, _extracted_target_output, "Target")
    elif isinstance(target_null_result, dict):
        target_output = strip_html_tags(str(target_null_result.get("output", "")))
        print(f"[DEBUG REPORT] Target output (first 300 chars): {target_output[:300]}")
        parse_and_display_null_details(ws_null, target_output, "Target")
    else:
        ws_null.append([str(target_null_result)])
    
    style_validation_detail_sheet(ws_null)
    
    # Duplicate Check Sheet
    ws_dup = wb.create_sheet("Duplicate Check")
    ws_dup.append(["DUPLICATE CHECK VALIDATION"])
    ws_dup.append([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    ws_dup.append([""])
    ws_dup.append(["Source Table:", src_table])
    ws_dup.append(["Target Table:", tgt_table])
    ws_dup.append([""])
    ws_dup.append(["Summary Statistics"])
    ws_dup.append(["Total Validations:", total_validations])
    ws_dup.append(["Passed:", pass_count])
    ws_dup.append(["Failed:", fail_count])
    ws_dup.append([""])
    ws_dup.append(["Validation Details"])
    ws_dup.append(["Check", "Status", "Output"])
    
    # Add Duplicate Check for Source and Target
    for dup_key in ["Duplicate Check (Source Table)", "Duplicate Check (Target Table)"]:
        result = results.get(dup_key, {})
        if isinstance(result, dict):
            status = "PASS" if result.get("passed", False) else "FAIL"
            output = strip_html_tags(str(result.get("output", "")))
        else:
            status = "INFO"
            output = str(result)
        table_type = "Source" if "Source" in dup_key else "Target"
        ws_dup.append([f"Duplicate Check ({table_type})", status, output[:500]])
    style_validation_detail_sheet(ws_dup)
    
    # Auto-size columns for all sheets
    auto_size_columns(wb)
    
    print(f"[DEBUG] ========================================")
    print(f"[DEBUG] Saving Excel report to: {output_file}")
    print(f"[DEBUG] Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    wb.save(output_file)
    print(f"[DEBUG] Excel file saved successfully!")
    print(f"[DEBUG] File size: {os.path.getsize(output_file) / 1024:.2f} KB")
    print(f"[DEBUG] ========================================")
    return output_file


def generate_mismatch_preview_section(mismatch_data):
    """Generate a preview section showing sample mismatched records"""
    total_mismatches = len(mismatch_data['source']) + len(mismatch_data['target'])
    
    if total_mismatches == 0:
        return ""
    
    # Combine source and target records for preview (limit to 10 total)
    preview_records = []
    
    # Add source records with indicator
    for record in mismatch_data['source'][:5]:
        preview_records.append(('SOURCE', record))
    
    # Add target records with indicator
    for record in mismatch_data['target'][:5]:
        preview_records.append(('TARGET', record))
    
    if not preview_records:
        return ""
    
    # Get columns from first record
    columns = None
    first_record = preview_records[0][1]
    if first_record.startswith('{'):
        try:
            record_dict = ast.literal_eval(first_record)
            columns = list(record_dict.keys())
        except:
            pass
    
    if not columns:
        return ""
    
    # Generate HTML table
    html = '''
        <div class="section">
            <h2>📋 Sample Mismatched Records</h2>
            <table class="mismatch-table">
                <thead>
                    <tr>
                        <th style="width: 60px; background: #2c3e50;">#</th>
    '''
    
    for col in columns:
        html += f'<th>{col}</th>'
    
    html += '''
                    </tr>
                </thead>
                <tbody>
    '''
    
    for idx, (location, record) in enumerate(preview_records[:10]):
        try:
            record_dict = ast.literal_eval(record)
            row_class = 'odd-row' if idx % 2 == 0 else 'even-row'
            
            html += f'<tr class="{row_class}"><td class="row-number">{idx}</td>'
            for col in columns:
                value = record_dict.get(col, '')
                html += f'<td>{value}</td>'
            html += '</tr>'
        except:
            pass
    
    html += '''
                </tbody>
            </table>
            <p style="margin-top: 1rem; color: #666; font-style: italic;">
                Showing sample of mismatched records. View full details in sections below.
            </p>
        </div>
    '''
    
    return html


def generate_html_dashboard(results, output_file="reports/etl_dashboard.html", source_table=None, target_table=None):
    """Generate comprehensive HTML dashboard with high-level summary and detailed tables"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    src_table = source_table or SOURCE_TABLE
    tgt_table = target_table or TARGET_TABLE
    
    # Parse log files
    mismatch_data = parse_mismatch_log("logs/row_data_mismatch_log.txt")
    duplicate_data = parse_duplicate_log("logs/duplicate_combined_log.txt")
    
    # Extract counts
    count_result = results.get("Record Count Check", "")
    source_count = extract_count(count_result, 'source')
    target_count = extract_count(count_result, 'target')
    
    # Calculate validation stats
    checks = [
        ("Structure Validation", "Structure Validation"),
        ("Record Count Check", "Record Count Check"),
        ("Null Check (Source)", "Null Check (Source Table)"),
        ("Null Check (Target)", "Null Check (Target Table)"),
        ("Duplicate Check (Source)", "Duplicate Check (Source Table)"),
        ("Duplicate Check (Target)", "Duplicate Check (Target Table)"),
        ("Row-wise Data Validation", "Row-wise Data Validation")
    ]
    
    pass_count = 0
    fail_count = 0
    validation_rows = ""
    
    for display_name, key in checks:
        result = results.get(key, {})
        
        # Handle both structured (dict) and legacy (string) formats
        if isinstance(result, dict):
            status = "PASS" if result.get("passed", False) else "FAIL"
            status_class = "status-pass" if status == "PASS" else "status-fail"
            output = result.get("output", "")
        else:
            # Legacy string format
            result_str = str(result).lower()
            if "[success]" in result_str or "matched" in result_str or "no duplicates" in result_str or "✅" in str(result):
                status = "PASS"
                status_class = "status-pass"
            elif "[error]" in result_str or "mismatch" in result_str or "❌" in str(result):
                status = "FAIL"
                status_class = "status-fail"
            else:
                status = "INFO"
                status_class = "status-info"
            output = result
        
        if status == "PASS":
            pass_count += 1
        elif status == "FAIL":
            fail_count += 1
        
        details = get_summary_details(key, output if isinstance(result, dict) else result)
        validation_rows += f"""
            <tr>
                <td>{display_name}</td>
                <td class="{status_class}">{status}</td>
                <td>{details}</td>
            </tr>
        """
    
    # Generate mismatch table HTML
    mismatch_source_table = generate_html_table(mismatch_data['source'], "Source Only Records")
    mismatch_target_table = generate_html_table(mismatch_data['target'], "Target Only Records")
    
    # Generate duplicate table HTML
    duplicate_table = generate_html_table(duplicate_data, "Duplicate Records")
    
    # Generate detailed validation sections
    detail_sections = ""
    for check_name, result in results.items():
        result_str = str(result).lower()
        # Special handling for Row-wise Data Validation
        if "row-wise" in check_name.lower():
            has_source_only = "only in source" in result_str or "rows present only in source" in result_str
            has_target_only = "only in target" in result_str or "rows present only in target" in result_str
            if has_source_only or has_target_only:
                status_class = "fail"
            else:
                status_class = "pass"
        elif "[SUCCESS]" in str(result) or "matched" in result_str or "✅" in str(result):
            status_class = "pass"
        elif "[ERROR]" in str(result) or "mismatch" in result_str or "❌" in str(result):
            status_class = "fail"
        else:
            status_class = "info"
            
        detail_sections += f"""
        <div class="detail-card {status_class}">
            <h4>{check_name}</h4>
            <pre>{str(result)}</pre>
        </div>
        """
    # Debug: ensure detail_sections is not empty
    if not detail_sections:
        detail_sections = '<div class="detail-card info"><h4>Debug</h4><div class="result-content">No detailed results available</div></div>'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ETL Validation Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ height: 100%; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f5f7fa; 
            color: #333; 
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 3rem; text-align: center; flex-shrink: 0; }}
        .header h1 {{ font-size: 3rem; margin-bottom: 1rem; font-weight: 700; letter-spacing: -0.5px; }}
        .header .subtitle {{ opacity: 0.95; font-size: 1.25rem; margin-bottom: 1rem; }}
        .header .tables {{ margin-top: 1.5rem; font-size: 1.2rem; background: rgba(255,255,255,0.15); padding: 1rem 2rem; border-radius: 10px; display: inline-block; }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 3rem; flex: 1 0 auto; }}
        
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .summary-card {{ background: white; border-radius: 12px; padding: 2rem; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .summary-card h3 {{ font-size: 1.1rem; color: #666; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }}
        .summary-card .value {{ font-size: 3.5rem; font-weight: 700; }}
        .summary-card.source .value {{ color: #3498db; }}
        .summary-card.target .value {{ color: #9b59b6; }}
        .summary-card.pass .value {{ color: #27ae60; }}
        .summary-card.fail .value {{ color: #e74c3c; }}
        .summary-card.mismatch .value {{ color: #f39c12; }}
        
        .section {{ background: white; border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .section h2 {{ font-size: 1.75rem; margin-bottom: 1.25rem; padding-bottom: 0.75rem; border-bottom: 2px solid #eee; color: #444; font-weight: 600; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 1.1rem; }}
        th {{ background: #667eea; color: white; padding: 16px 18px; text-align: left; font-weight: 600; font-size: 1.1rem; }}
        td {{ padding: 14px 18px; border-bottom: 1px solid #eee; font-size: 1.1rem; }}
        tr:hover {{ background: #f8f9fa; }}
        
        .status-pass {{ background: #d4edda; color: #155724; font-weight: 600; padding: 8px 16px; border-radius: 6px; font-size: 1rem; }}
        .status-fail {{ background: #f8d7da; color: #721c24; font-weight: 600; padding: 8px 16px; border-radius: 6px; font-size: 1rem; }}
        .status-info {{ background: #fff3cd; color: #856404; font-weight: 600; padding: 8px 16px; border-radius: 6px; font-size: 1rem; }}
        
        .detail-card {{ border-radius: 10px; padding: 1.5rem; margin-bottom: 1rem; }}
        .detail-card.pass {{ background: #f0fff4; border-left: 5px solid #27ae60; }}
        .detail-card.fail {{ background: #fff5f5; border-left: 5px solid #e74c3c; }}
        .detail-card.info {{ background: #fffbeb; border-left: 5px solid #f39c12; }}
        .detail-card h4 {{ margin-bottom: 0.75rem; color: #333; font-size: 1.25rem; font-weight: 600; }}
        .result-content {{ padding: 1rem; background: #f8f9fa; border-radius: 6px; word-wrap: break-word; overflow-wrap: break-word; font-size: 1.05rem; }}
        .result-content pre {{ margin: 0; white-space: pre-wrap; word-wrap: break-word; font-size: 1.05rem; }}

        .count-display {{ text-align: center; font-size: 1.3rem; }}
        .count-label {{ font-weight: 600; color: #555; }}
        .count-value {{ font-size: 1.5rem; font-weight: 700; color: #27ae60; }}

        .data-validation-display {{ display: flex; justify-content: space-around; flex-wrap: wrap; }}
        .validation-stat {{ text-align: center; margin: 0.75rem; }}
        .stat-label {{ display: block; font-weight: 600; color: #555; margin-bottom: 0.5rem; font-size: 1.1rem; }}
        .stat-value {{ font-size: 1.75rem; font-weight: 700; }}

        .structure-display, .null-display, .duplicate-display {{ text-align: center; font-size: 1.3rem; font-weight: 600; }}
        .success-icon {{ color: #27ae60; margin-right: 0.5rem; }}
        .error-icon {{ color: #e74c3c; margin-right: 0.5rem; }}
        
        .data-table {{ font-size: 1.05rem; }}
        .data-table th {{ background: #34495e; font-size: 1rem; }}
        .data-table td {{ font-size: 1rem; }}
        
        /* Mismatch Table Styles */
        .mismatch-section-title {{ 
            font-size: 1.3rem; 
            font-weight: 600; 
            color: #2c3e50; 
            margin-bottom: 1rem; 
            padding: 0.5rem; 
            background: #e8f4f8;
            border-left: 4px solid #3498db;
        }}
        
        .mismatch-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 0.5rem; 
            font-size: 0.95rem; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .mismatch-table th {{ 
            background: #4a90e2; 
            color: white; 
            padding: 12px 14px; 
            text-align: left; 
            font-weight: 600; 
            font-size: 0.95rem; 
            border: 1px solid #3498db;
        }}
        
        .mismatch-table td {{ 
            padding: 10px 14px; 
            font-size: 0.9rem; 
            border: 1px solid #ddd;
        }}
        
        .mismatch-table .row-number {{ 
            background: #4a90e2; 
            color: white; 
            font-weight: 600; 
            text-align: center; 
            width: 60px;
        }}
        
        .mismatch-table .odd-row {{ 
            background: #fce8e8; 
        }}
        
        .mismatch-table .even-row {{ 
            background: #ffffff; 
        }}
        
        .mismatch-table tr:hover {{ 
            background: #e3f2fd !important; 
        }}
        
        .tabs {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; }}
        .tab-btn {{ padding: 0.85rem 1.75rem; border: none; background: #e9ecef; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 1.1rem; }}
        .tab-btn.active {{ background: #667eea; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        .no-data {{ text-align: center; padding: 2rem; color: #666; font-style: italic; font-size: 1.2rem; }}
        
        .footer {{ 
            text-align: center; 
            padding: 1.5rem; 
            background: #2c3e50;
            color: #ecf0f1; 
            font-size: 1.1rem;
            flex-shrink: 0;
            margin-top: auto;
            border-top: 3px solid #667eea;
        }}
        .footer strong {{ color: #667eea; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ETL Validation Dashboard</h1>
        <div class="subtitle">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <div class="tables">
            <strong>Source:</strong> {src_table} &nbsp;|&nbsp; <strong>Target:</strong> {tgt_table}
        </div>
    </div>
    
    <div class="container">
        <!-- Summary Cards -->
        <div class="summary-cards">
            <div class="summary-card source">
                <h3>Source Records</h3>
                <div class="value">{source_count}</div>
            </div>
            <div class="summary-card target">
                <h3>Target Records</h3>
                <div class="value">{target_count}</div>
            </div>
            <div class="summary-card pass">
                <h3>Validations Passed</h3>
                <div class="value">{pass_count}</div>
            </div>
            <div class="summary-card fail">
                <h3>Validations Failed</h3>
                <div class="value">{fail_count}</div>
            </div>
            <div class="summary-card mismatch">
                <h3>Mismatched Records</h3>
                <div class="value">{len(mismatch_data['source']) + len(mismatch_data['target'])}</div>
            </div>
        </div>
        
        <!-- Validation Summary -->
        <div class="section">
            <h2>Validation Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Validation Check</th>
                        <th>Status</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {validation_rows}
                </tbody>
            </table>
        </div>
        
        <!-- Sample Mismatched Records Preview -->
        {generate_mismatch_preview_section(mismatch_data)}
        
        <!-- Mismatch Records -->
        <div class="section">
            <h2>Mismatch Records</h2>
            <div class="tabs">
                <button class="tab-btn active" onclick="showTab('source-mismatch')">Only in Source ({len(mismatch_data['source'])})</button>
                <button class="tab-btn" onclick="showTab('target-mismatch')">Only in Target ({len(mismatch_data['target'])})</button>
            </div>
            <div id="source-mismatch" class="tab-content active">
                {mismatch_source_table}
            </div>
            <div id="target-mismatch" class="tab-content">
                {mismatch_target_table}
            </div>
        </div>
        
        <!-- Duplicate Records -->
        <div class="section">
            <h2>Duplicate Records ({len(duplicate_data)} found)</h2>
            {duplicate_table}
        </div>
        
        <!-- Detailed Validation Results -->
        <div class="section">
            <h2>Detailed Validation Results</h2>
            {detail_sections}
        </div>
    </div>
    
    <div class="footer">
        <strong>WinWire</strong> InfinityX - Enterprise ETL Validation & Data Reconciliation Engine © 2026 | Powered by PyTest & FastAPI
    </div>
    
    <script>
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file


# ===== Helper Functions =====

def get_summary_details(key, result):
    """Get summary details for a validation check"""
    if not result:
        return "No data"
    
    result_str = str(result)
    
    if "Structure" in key:
        if "Number of columns:" in result_str:
            cols = result_str.split("Number of columns:")[1].split("\n")[0].strip()
            return f"Columns: {cols}"
        return "Structure compared"
    
    elif "Count" in key:
        source = extract_count(result_str, 'source')
        target = extract_count(result_str, 'target')
        return f"Source: {source}, Target: {target}"
    
    elif "Null" in key:
        return extract_null_summary(result_str)
    
    elif "Duplicate" in key:
        if "No duplicates" in result_str:
            return "No duplicates found"
        elif "Duplicates found" in result_str:
            return "Duplicates detected"
        return "Checked"
    
    elif "Row-wise" in key:
        matched = extract_matched_count(result_str)
        mismatched = extract_mismatched_count(result_str)
        return f"Matched: {matched}, Mismatched: {mismatched}"
    
    return "Completed"


def extract_count(result_text, table_type):
    """Extract count from result text"""
    if not result_text:
        return "0"
    lines = str(result_text).split('\n')
    for line in lines:
        if table_type.lower() in line.lower() and ':' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                count = parts[-1].strip().split()[0]
                if count.isdigit():
                    return count
    return "0"


def extract_null_summary(result_text):
    """Extract null check summary"""
    if not result_text:
        return "No NULLs"
    
    if "violation" in result_text.lower():
        return "Constraint violations found"
    elif "NULLs" in result_text:
        return "NULL values checked"
    return "Checked"


def extract_matched_count(result_text):
    """Extract matched count from row-wise validation"""
    if not result_text:
        return 0
    result_str = str(result_text)
    
    # Try different patterns
    patterns = [
        r"Matched Rows:\s*(\d+)",
        r"(\d+)\s*row.*matched",
        r"MATCHED RECORDS.*?\((\d+)\s*row"
    ]
    
    for pattern in patterns:
        import re
        match = re.search(pattern, result_str, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    return 0


def extract_mismatched_count(result_text):
    """Extract mismatched count from row-wise validation"""
    if not result_text:
        return 0
    
    source_only = 0
    target_only = 0
    result_str = str(result_text)
    
    # Extract from different patterns
    import re
    
    # Try to find "Total Mismatched Positions: N" (newer format with HTML)
    mismatch_pattern = r"Total Mismatched Positions:\s*(\d+)"
    match = re.search(mismatch_pattern, result_str, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except:
            pass
    
    # Try to find "Total Mismatched Records: N" (legacy format)
    mismatch_pattern = r"Total Mismatched Records:\s*(\d+)"
    match = re.search(mismatch_pattern, result_str, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except:
            pass
    
    # Alternative: Extract from "Set comparison found: X unique rows only in source, Y unique rows only in target"
    set_comparison_pattern = r"Set comparison found:\s*(\d+)\s*unique rows only in source,\s*(\d+)\s*unique rows only in target"
    match = re.search(set_comparison_pattern, result_str, re.IGNORECASE)
    if match:
        try:
            source_only = int(match.group(1))
            target_only = int(match.group(2))
            return source_only + target_only
        except:
            pass
    
    # Fallback: Look for individual counts
    if "Rows present only in Source:" in result_str or "rows only in source" in result_str.lower():
        try:
            # Try pattern with "unique rows only in source"
            match = re.search(r"(\d+)\s*unique rows only in source", result_str, re.IGNORECASE)
            if match:
                source_only = int(match.group(1))
            else:
                # Try pattern with "Rows present only in Source:"
                source_only = int(result_str.split("Rows present only in Source:")[1].split("\n")[0].strip().split()[0])
        except:
            pass
    
    if "Rows present only in Target:" in result_str or "rows only in target" in result_str.lower():
        try:
            # Try pattern with "unique rows only in target"
            match = re.search(r"(\d+)\s*unique rows only in target", result_str, re.IGNORECASE)
            if match:
                target_only = int(match.group(1))
            else:
                # Try pattern with "Rows present only in Target:"
                target_only = int(result_str.split("Rows present only in Target:")[1].split("\n")[0].strip().split()[0])
        except:
            pass
    
    return source_only + target_only


def parse_matched_csv(log_dir):
    """Parse the most recent matched records CSV file"""
    
    print(f"[DEBUG] Looking for matched CSV files in: {log_dir}")
    
    # Find the most recent matched_rows CSV file
    pattern = os.path.join(log_dir, "*_matched_rows_*.csv")
    csv_files = glob.glob(pattern)
    
    if not csv_files:
        # Try without prefix
        pattern = os.path.join(log_dir, "matched_rows*.csv")
        csv_files = glob.glob(pattern)
    
    if not csv_files:
        print(f"[DEBUG] ❌ No matched CSV files found in {log_dir}")
        return []
    
    # Get the most recent file
    latest_file = max(csv_files, key=os.path.getmtime)
    print(f"[DEBUG] Found latest matched CSV: {os.path.basename(latest_file)}")
    print(f"[DEBUG] File size: {os.path.getsize(latest_file)} bytes")
    
    try:
        with open(latest_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            data = list(reader)
            print(f"[DEBUG] ✅ Loaded {len(data)} rows from matched CSV (including header)")
            if data:
                print(f"[DEBUG] Header has {len(data[0])} columns")
                print(f"[DEBUG] Sample columns: {data[0][:5]}...")
            return data
    except Exception as e:
        print(f"[ERROR] Failed to parse matched CSV: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_mismatch_log(log_path):
    """Parse the mismatch log file into source and target records"""
    result = {'source': [], 'target': []}
    
    if not os.path.exists(log_path):
        return result
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('Only in Source:'):
                    record = line.replace('Only in Source:', '').strip()
                    if record:
                        result['source'].append(record)
                elif line.startswith('Only in Target:'):
                    record = line.replace('Only in Target:', '').strip()
                    if record:
                        result['target'].append(record)
    except Exception as e:
        print(f"Error parsing mismatch log: {e}")
    
    return result


def parse_duplicate_log(log_path):
    """Parse the duplicate log file"""
    records = []
    
    if not os.path.exists(log_path):
        return records
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and line.startswith('{'):
                    records.append(line)
    except Exception as e:
        print(f"Error parsing duplicate log: {e}")
    
    return records


def get_columns_from_records(records):
    """Extract column names from record dictionaries"""
    if not records:
        return []
    
    try:
        # Try to parse the first record as a dictionary
        first_record = records[0]
        if first_record.startswith('{'):
            record_dict = ast.literal_eval(first_record)
            return list(record_dict.keys())
    except:
        pass
    
    return []


def parse_record_to_row(record, columns):
    """Parse a record string to a row of values"""
    try:
        if record.startswith('{'):
            record_dict = ast.literal_eval(record)
            return [record_dict.get(col, '') for col in columns]
    except:
        pass
    return ['' for _ in columns]

def generate_json_report(results, output_file="reports/etl_validation_report.json"):
    """Generate JSON report with detailed results and metrics"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Calculate data quality metrics
    metrics = calculate_data_quality_metrics(results)

    report = {
        "timestamp": datetime.now().isoformat(),
        "validation_results": results,
        "data_quality_metrics": metrics,
        "summary": {
            "total_checks": len(results),
            "passed": sum(1 for r in results.values() if "✅" in str(r) or "matched" in str(r).lower()),
            "failed": sum(1 for r in results.values() if "❌" in str(r) or "mismatch" in str(r).lower()),
            "overall_score": metrics.get("overall_score", 0)
        }
    }

    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    return output_file

def calculate_data_quality_metrics(results):
    """Calculate data quality metrics from validation results"""
    metrics = {
        "completeness": 0,
        "accuracy": 0,
        "consistency": 0,
        "timeliness": 0,
        "overall_score": 0
    }

    # Simple scoring based on results
    total_checks = len(results)
    if total_checks == 0:
        return metrics

    passed = 0
    for key, result in results.items():
        if "✅" in str(result) or ("null" in key.lower() and "❌" not in str(result)) or ("duplicate" in key.lower() and "❌" not in str(result)):
            passed += 1

    score = (passed / total_checks) * 100
    metrics["overall_score"] = score
    metrics["completeness"] = score  # Simplified
    metrics["accuracy"] = score
    metrics["consistency"] = score
    metrics["timeliness"] = score

    return metrics

def generate_powerbi_dashboard(results, output_file="reports/powerbi_validation_dashboard.json"):
    """Generate Power BI compatible dashboard data"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    dashboard_data = {
        "datasets": [],
        "reports": [],
        "validation_metrics": calculate_data_quality_metrics(results)
    }

    # Add sample Power BI data structure
    dashboard_data["datasets"].append({
        "name": "Validation Results",
        "tables": [{
            "name": "Results",
            "columns": [
                {"name": "Check", "dataType": "string"},
                {"name": "Status", "dataType": "string"},
                {"name": "Details", "dataType": "string"}
            ],
            "rows": [[k, "PASS" if "✅" in str(v) else "FAIL", str(v)] for k, v in results.items()]
        }]
    })

    with open(output_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2)

    return output_file


def generate_html_table(records, title):
    """Generate HTML table from records with row numbers and proper styling"""
    if not records:
        return f'<div class="no-data">No {title.lower()} found.</div>'
    
    columns = get_columns_from_records(records)
    
    if not columns:
        # Fallback to simple list
        html = f'<div class="mismatch-section-title">📋 Sample {title}</div>'
        html += f'<table class="mismatch-table"><thead><tr><th style="width: 60px;">#</th><th>Record</th></tr></thead><tbody>'
        for idx, record in enumerate(records[:100]):  # Limit to 100 records
            row_class = 'odd-row' if idx % 2 == 0 else 'even-row'
            html += f'<tr class="{row_class}"><td class="row-number">{idx}</td><td>{record}</td></tr>'
        html += '</tbody></table>'
        return html
    
    # Generate proper table with row numbers
    html = f'<div class="mismatch-section-title">📋 Sample {title}</div>'
    html = '<table class="mismatch-table"><thead><tr><th style="width: 60px; background: #2c3e50;">#</th>'
    for col in columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    
    for idx, record in enumerate(records[:100]):  # Limit to 100 records
        row_data = parse_record_to_row(record, columns)
        row_class = 'odd-row' if idx % 2 == 0 else 'even-row'
        html += f'<tr class="{row_class}"><td class="row-number">{idx}</td>'
        for val in row_data:
            html += f'<td>{val}</td>'
        html += '</tr>'
    
    html += '</tbody></table>'
    
    if len(records) > 100:
        html += f'<p style="color: #666; font-style: italic; margin-top: 1rem;">Showing 100 of {len(records)} records. Download Excel for complete data.</p>'
    
    return html


def format_excel_details(check_name, result, status):
    """Format validation details for Excel display with high-level summaries"""
    result = result.replace("[SUCCESS]", "").replace("[ERROR]", "").strip()

    if "Record Count Check" in check_name:
        import re
        match = re.search(r'Source:\s*(\d+).*?Target:\s*(\d+)', result)
        if match:
            source_count = int(match.group(1))
            target_count = int(match.group(2))
            if source_count == target_count:
                return f"Counts match: {source_count:,} records"
            else:
                diff = abs(source_count - target_count)
                return f"Mismatch: Source {source_count:,}, Target {target_count:,} (Difference: {diff:,})"

    elif "Row-wise Data Validation" in check_name:
        import re
        match = re.search(r'Matched:\s*(\d+).*?Mismatched:\s*(\d+)', result)
        if match:
            matched = int(match.group(1))
            mismatched = int(match.group(2))
            total = matched + mismatched
            if mismatched == 0:
                return f"All {total:,} records matched"
            else:
                match_pct = (matched / total * 100) if total > 0 else 0
                return f"{matched:,} matched, {mismatched:,} mismatched ({match_pct:.1f}% match rate)"

    elif "Structure Validation" in check_name:
        if status == "PASS":
            return "Table structures compatible"
        else:
            return "Structure mismatch detected"

    elif "Null Check" in check_name:
        if status == "PASS":
            return "No NULL values found"
        else:
            return "NULL values detected"

    elif "Duplicate Check" in check_name:
        if status == "PASS":
            return "No duplicate records"
        else:
            return "Duplicate records found"

    # Default formatting
    if not result:
        return "✅ Validation completed successfully"
    return result[:80] + "..." if len(result) > 80 else result


def format_validation_result(check_name, result):
    """Format validation result for better display"""
    if "Record Count Check" in check_name:
        # Parse "Source: 83, Target: 83"
        import re
        match = re.search(r'Source:\s*(\d+).*?Target:\s*(\d+)', result)
        if match:
            source_count = match.group(1)
            target_count = match.group(2)
            if source_count == target_count:
                return f'<div class="count-display"><span class="count-label">Records Match:</span> <span class="count-value">{source_count}</span></div>'
            else:
                return f'<div class="count-display"><span class="count-label">Source:</span> <span class="count-value">{source_count}</span> | <span class="count-label">Target:</span> <span class="count-value">{target_count}</span></div>'
    elif "Row-wise Data Validation" in check_name:
        # Parse "Matched: 47, Mismatched: 4"
        import re
        match = re.search(r'Matched:\s*(\d+).*?Mismatched:\s*(\d+)', result)
        if match:
            matched = match.group(1)
            mismatched = match.group(2)
            return f'<div class="data-validation-display"><div class="validation-stat"><span class="stat-label">✅ Matched Records:</span> <span class="stat-value">{matched}</span></div><div class="validation-stat"><span class="stat-label">❌ Mismatched Records:</span> <span class="stat-value">{mismatched}</span></div></div>'
    elif "Structure Validation" in check_name:
        if "matched" in result.lower():
            return '<div class="structure-display"><span class="success-icon">✅</span> Table structures are compatible</div>'
        else:
            return f'<div class="structure-display"><span class="error-icon">❌</span> {result}</div>'
    elif "Null Check" in check_name:
        if "❌" in result:
            return '<div class="null-display"><span class="error-icon">❌</span> NULL values found</div>'
        else:
            return '<div class="null-display"><span class="success-icon">✅</span> No NULL value issues</div>'
    elif "Duplicate Check" in check_name:
        if "❌" in result:
            return '<div class="duplicate-display"><span class="error-icon">❌</span> Duplicate records found</div>'
        else:
            return '<div class="duplicate-display"><span class="success-icon">✅</span> No duplicate issues</div>'

    # Default formatting
    return f'<pre style="margin: 0; white-space: pre-wrap;">{result}</pre>'


def auto_size_columns(wb):
    """Auto-size columns for all sheets"""
    for sheet in wb:
        for col_idx, column in enumerate(sheet.columns, 1):
            max_length = 0
            column_letter = get_column_letter(col_idx)
            
            for cell in column:
                try:
                    if cell.value and cell.coordinate not in sheet.merged_cells:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = min(cell_length, 50)  # Cap at 50
                except:
                    pass
            
            adjusted_width = (max_length + 2) * 1.2
            sheet.column_dimensions[column_letter].width = max(adjusted_width, 10)


def style_summary_sheet(sheet):
    """Style the summary sheet"""
    # Title - mild purple
    sheet['A1'].font = Font(bold=True, size=16, color="4F46E5")
    sheet['A1'].fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
    
    # Subtitle row - very light purple
    sheet['A2'].fill = PatternFill(start_color="F5F3FF", end_color="F5F3FF", fill_type="solid")
    
    # Find and style SOURCE CONFIGURATION section (blue theme)
    for row_idx in range(1, sheet.max_row + 1):
        cell_value = sheet.cell(row_idx, 1).value
        if cell_value == "SOURCE CONFIGURATION":
            # Header row - blue
            sheet.cell(row_idx, 1).font = Font(bold=True, size=12, color="FFFFFF")
            sheet.cell(row_idx, 1).fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
            sheet.merge_cells(f'A{row_idx}:B{row_idx}')
            # Detail rows - light blue
            for detail_row in range(row_idx + 1, row_idx + 6):
                if detail_row <= sheet.max_row:
                    sheet.cell(detail_row, 1).font = Font(bold=True, color="1E3A8A")
                    sheet.cell(detail_row, 1).fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
                    sheet.cell(detail_row, 2).fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
            break
    
    # Find and style TARGET CONFIGURATION section (purple theme)
    for row_idx in range(1, sheet.max_row + 1):
        cell_value = sheet.cell(row_idx, 1).value
        if cell_value == "TARGET CONFIGURATION":
            # Header row - purple
            sheet.cell(row_idx, 1).font = Font(bold=True, size=12, color="FFFFFF")
            sheet.cell(row_idx, 1).fill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")
            sheet.merge_cells(f'A{row_idx}:B{row_idx}')
            # Detail rows - light purple
            for detail_row in range(row_idx + 1, row_idx + 6):
                if detail_row <= sheet.max_row:
                    sheet.cell(detail_row, 1).font = Font(bold=True, color="6B21A8")
                    sheet.cell(detail_row, 1).fill = PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid")
                    sheet.cell(detail_row, 2).fill = PatternFill(start_color="F5F3FF", end_color="F5F3FF", fill_type="solid")
            break
    
    # Find and style VALIDATION SUMMARY section (green/teal theme)
    for row_idx in range(1, sheet.max_row + 1):
        cell_value = sheet.cell(row_idx, 1).value
        if cell_value == "VALIDATION SUMMARY":
            # Section header "VALIDATION SUMMARY" - teal
            sheet.cell(row_idx, 1).font = Font(bold=True, size=12, color="FFFFFF")
            sheet.cell(row_idx, 1).fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
            sheet.merge_cells(f'A{row_idx}:C{row_idx}')
            
            # Column headers row - mild teal
            header_row = row_idx + 1
            for col_idx in range(1, 4):
                cell = sheet.cell(header_row, col_idx)
                if cell.value:
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="14B8A6", end_color="14B8A6", fill_type="solid")
                    cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Status colors for validation rows
            detail_start_row = header_row + 1
            for detail_row_idx in range(detail_start_row, sheet.max_row + 1):
                status_cell = sheet.cell(detail_row_idx, 2)
                if status_cell.value == "PASS":
                    status_cell.fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
                    status_cell.font = Font(bold=True, color="065F46")
                elif status_cell.value == "FAIL":
                    status_cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                    status_cell.font = Font(bold=True, color="991B1B")
                elif status_cell.value and isinstance(status_cell.value, (int, str)) and str(status_cell.value).isdigit():
                    # This is a count row (Total Validations, Passed, Failed)
                    sheet.cell(detail_row_idx, 1).font = Font(bold=True)
                    sheet.cell(detail_row_idx, 2).font = Font(bold=True)
            break
    
    # Adjust column widths for better readability
    sheet.column_dimensions['A'].width = 35
    sheet.column_dimensions['B'].width = 50
    sheet.column_dimensions['C'].width = 80


def style_mismatch_sheet(sheet):
    """Style the mismatch sheet"""
    # Main title - mild blue
    sheet['A1'].font = Font(bold=True, size=14, color="1E40AF")
    sheet['A1'].fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    
    # Subtitle - light blue
    sheet['A2'].fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    
    # Summary header row "Category, Count" - mild sky blue
    for cell in sheet[4]:
        if cell.value:
            cell.font = Font(bold=True, color="075985")
            cell.fill = PatternFill(start_color="BAE6FD", end_color="BAE6FD", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Section headers and column headers
    for row in sheet.iter_rows():
        for cell in row:
            if cell.value:
                cell_value = str(cell.value)
                # Section headers "RECORDS ONLY IN SOURCE/TARGET" - mild amber
                if "RECORDS ONLY IN" in cell_value:
                    cell.font = Font(bold=True, size=12, color="92400E")
                    cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
                # Column headers (row after section header) - lighter amber
                elif cell.row > 1 and any("RECORDS ONLY IN" in str(sheet.cell(cell.row - 1, c).value or "") for c in range(1, sheet.max_column + 1)):
                    cell.font = Font(bold=True, color="78350F")
                    cell.fill = PatternFill(start_color="FDE68A", end_color="FDE68A", fill_type="solid")
                    cell.alignment = Alignment(horizontal='center', vertical='center')


def style_matched_sheet(sheet):
    """Style the matched records sheet"""
    # Main title - green theme
    sheet['A1'].font = Font(bold=True, size=14, color="065F46")
    sheet['A1'].fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    
    # Subtitle
    if sheet.max_row >= 2:
        sheet['A2'].font = Font(italic=True, size=10, color="374151")
    
    # Summary statistics
    for row_idx in range(3, 7):
        if row_idx <= sheet.max_row:
            for col_idx in range(1, 3):
                cell = sheet.cell(row_idx, col_idx)
                if cell.value:
                    cell.font = Font(bold=True if col_idx == 1 else False)
                    cell.alignment = Alignment(horizontal='left', vertical='center')
    
    # Column headers - find the header row
    for row_idx in range(1, min(sheet.max_row + 1, 20)):
        cell_value = sheet.cell(row_idx, 1).value
        if cell_value and "MATCHED RECORD DETAILS" in str(cell_value):
            # Found the header section
            header_row_idx = row_idx + 1
            if header_row_idx <= sheet.max_row:
                for col_idx in range(1, sheet.max_column + 1):
                    cell = sheet.cell(header_row_idx, col_idx)
                    if cell.value:
                        cell.font = Font(bold=True, color="FFFFFF")
                        cell.fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Style data rows with alternating colors
                for data_row_idx in range(header_row_idx + 1, sheet.max_row + 1):
                    row_color = "F0FDF4" if (data_row_idx - header_row_idx) % 2 == 0 else "FFFFFF"
                    for col_idx in range(1, sheet.max_column + 1):
                        cell = sheet.cell(data_row_idx, col_idx)
                        cell.fill = PatternFill(start_color=row_color, end_color=row_color, fill_type="solid")
                        cell.alignment = Alignment(horizontal='left', vertical='center')
            break


def style_mismatch_sheet_comparison(sheet, skip_cells=None):
    """Style the mismatch sheet with interleaved source/target column format
    
    Args:
        sheet: The worksheet to style
        skip_cells: List of (row, col) tuples to skip styling (already highlighted cells)
    """
    if skip_cells is None:
        skip_cells = []  
    skip_cells_set = set(skip_cells)  # Convert to set for O(1) lookup
    # Main title - mild blue
    sheet['A1'].font = Font(bold=True, size=14, color="1E40AF")
    sheet['A1'].fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    
    # Subtitle - light blue
    sheet['A2'].fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    
    # Summary header row "Category, Count" - mild sky blue
    for cell in sheet[5]:
        if cell.value:
            cell.font = Font(bold=True, color="075985")
            cell.fill = PatternFill(start_color="BAE6FD", end_color="BAE6FD", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Style "HOW TO READ THIS REPORT" section (rows 10-14)
    how_to_read_row = None
    for row_idx, row in enumerate(sheet.iter_rows(), 1):
        for cell in row:
            if cell.value and "HOW TO READ THIS REPORT" in str(cell.value):
                how_to_read_row = row_idx
                break
        if how_to_read_row:
            break
    
    if how_to_read_row:
        # Header of the instruction section
        sheet.cell(how_to_read_row, 1).font = Font(bold=True, size=11, color="065F46")
        sheet.cell(how_to_read_row, 1).fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
        
        # Instruction bullets (next 4 rows)
        for offset in range(1, 5):
            instruction_cell = sheet.cell(how_to_read_row + offset, 1)
            if instruction_cell.value:
                instruction_cell.font = Font(size=10, color="047857")
                instruction_cell.fill = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")
                instruction_cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
                # Make the row taller for readability
                sheet.row_dimensions[how_to_read_row + offset].height = 18
        
        # Merge cells for better layout (optional - makes instructions span multiple columns)
        sheet.merge_cells(start_row=how_to_read_row, start_column=1, end_row=how_to_read_row, end_column=3)
        for offset in range(1, 5):
            try:
                sheet.merge_cells(start_row=how_to_read_row + offset, start_column=1, end_row=how_to_read_row + offset, end_column=5)
            except:
                pass  # Already merged or invalid range
    
    # Find the comparison section header and table
    comparison_header_row = None
    header_row = None
    
    for row_idx, row in enumerate(sheet.iter_rows(), 1):
        for cell in row:
            if cell.value and "SOURCE VS TARGET COMPARISON" in str(cell.value):
                comparison_header_row = row_idx
                header_row = row_idx + 2  # Header is 2 rows after section title
                break
        if comparison_header_row:
            break
    
    # Style section header
    if comparison_header_row:
        sheet.cell(comparison_header_row, 1).font = Font(bold=True, size=12, color="92400E")
        sheet.cell(comparison_header_row, 1).fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    
    # Style column headers with interleaved colors for src/tgt pairs
    if header_row:
        for col_idx, cell in enumerate(sheet[header_row], 1):
            if cell.value:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                sheet.column_dimensions[cell.column_letter].width = 15
                
                # Row # column
                if col_idx == 1:
                    cell.fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
                    sheet.column_dimensions[cell.column_letter].width = 8
                # Source columns (even indices: 2, 4, 6...)
                elif col_idx % 2 == 0:
                    cell.fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")  # Blue
                # Target columns (odd indices: 3, 5, 7...)
                else:
                    cell.fill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")  # Purple
        
        # Style data rows - highlighting is already applied in generation logic
        # Just add alternating row backgrounds for better readability
        data_start_row = header_row + 1
        for row_idx in range(data_start_row, sheet.max_row + 1):
            # Row # column - light blue background
            cell = sheet.cell(row_idx, 1)
            cell.fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
            cell.font = Font(bold=True, color="1E40AF")
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Data columns - apply light backgrounds ONLY if not in skip list
            for col_idx in range(2, sheet.max_column + 1):
                cell = sheet.cell(row_idx, col_idx)
                
                # Skip cells that were already highlighted (yellow)
                if (row_idx, col_idx) not in skip_cells_set:
                    # Light backgrounds for source and target columns
                    if col_idx % 2 == 0:  # Source column
                        cell.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")  # Light blue
                    else:  # Target column
                        cell.fill = PatternFill(start_color="F3E8FF", end_color="F3E8FF", fill_type="solid")  # Light purple
                    cell.font = Font(color="1F2937")
                
                cell.alignment = Alignment(horizontal='left', vertical='center')


def style_duplicate_sheet(sheet):
    """Style the duplicate sheet"""
    # Main title - mild rose
    sheet['A1'].font = Font(bold=True, size=14, color="BE123C")
    sheet['A1'].fill = PatternFill(start_color="FFE4E6", end_color="FFE4E6", fill_type="solid")
    
    # Subtitle - light rose
    sheet['A2'].fill = PatternFill(start_color="FFF1F2", end_color="FFF1F2", fill_type="solid")
    
    # Summary row - mild pink
    sheet['A4'].fill = PatternFill(start_color="FBCFE8", end_color="FBCFE8", fill_type="solid")
    sheet['A4'].font = Font(bold=True)
    
    # Section headers and column headers
    for row in sheet.iter_rows():
        for cell in row:
            if cell.value:
                cell_value = str(cell.value)
                # Section header "DUPLICATE RECORD DETAILS" - mild rose
                if "DUPLICATE RECORD DETAILS" in cell_value:
                    cell.font = Font(bold=True, size=12, color="9F1239")
                    cell.fill = PatternFill(start_color="FECDD3", end_color="FECDD3", fill_type="solid")
                # Column headers (row after section header) - lighter rose
                elif cell.row > 1 and any("DUPLICATE RECORD DETAILS" in str(sheet.cell(cell.row - 1, c).value or "") for c in range(1, sheet.max_column + 1)):
                    cell.font = Font(bold=True, color="881337")
                    cell.fill = PatternFill(start_color="FECACA", end_color="FECACA", fill_type="solid")
                    cell.alignment = Alignment(horizontal='center', vertical='center')


def style_counts_sheet(sheet):
    """Style the record counts sheet"""
    # Main title - mild teal
    sheet['A1'].font = Font(bold=True, size=14, color="115E59")
    sheet['A1'].fill = PatternFill(start_color="CCFBF1", end_color="CCFBF1", fill_type="solid")
    
    # Column headers row - mild cyan
    for cell in sheet[3]:
        if cell.value:
            cell.font = Font(bold=True, color="164E63")
            cell.fill = PatternFill(start_color="A5F3FC", end_color="A5F3FC", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')


def strip_html_tags(text):
    """Remove HTML tags from text"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', str(text))


def style_validation_detail_sheet(sheet):
    """Style individual validation detail sheets"""
    # Main title
    sheet['A1'].font = Font(bold=True, size=14, color="1F2937")
    sheet['A1'].fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    
    # Summary section headers
    if sheet['A4'].value:
        sheet['A4'].font = Font(bold=True, size=11, color="374151")
        sheet['A4'].fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
    
    # Column headers for validation details
    for row_idx in range(1, sheet.max_row + 1):
        cell_value = sheet.cell(row_idx, 1).value
        if cell_value and "Validation Details" in str(cell_value):
            # Found the header row
            for col_idx in range(1, 4):
                cell = sheet.cell(row_idx + 1, col_idx)
                if cell.value:
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
                    cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Style data rows
            for data_row_idx in range(row_idx + 2, sheet.max_row + 1):
                for col_idx in range(1, 4):
                    cell = sheet.cell(data_row_idx, col_idx)
                    if col_idx == 2 and cell.value:  # Status column
                        if cell.value == "PASS":
                            cell.fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
                            cell.font = Font(bold=True, color="065F46")
                        elif cell.value == "FAIL":
                            cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                            cell.font = Font(bold=True, color="991B1B")
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                    else:
                        cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
            break
