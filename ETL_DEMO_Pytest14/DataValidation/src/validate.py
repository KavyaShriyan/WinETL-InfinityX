import os
from datetime import datetime, date
from decimal import Decimal

def format_value(val):
    if isinstance(val, (datetime, date)):
        return val.strftime('%Y-%m-%d')
    elif isinstance(val, Decimal):
        return float(val)
    elif isinstance(val, str):
        return val.strip()
    elif val is None:
        return "NULL"
    return val

def format_table_output(columns, rows, max_width=30):
    """
    Format data in a table format similar to SSMS output.
    """
    if not rows:
        return "No data to display."
    
    # Convert values to strings and limit width
    def truncate(val, width=max_width):
        val_str = str(val)
        return val_str if len(val_str) <= width else val_str[:width-3] + "..."
    
    # Calculate column widths
    col_widths = {}
    for col in columns:
        col_widths[col] = len(col)
    
    for row in rows:
        for i, val in enumerate(row):
            col = columns[i]
            val_len = len(truncate(val))
            if val_len > col_widths[col]:
                col_widths[col] = min(val_len, max_width)
    
    # Build table header
    header_line = "| " + " | ".join(col.ljust(col_widths[col]) for col in columns) + " |"
    separator = "|-" + "-|-".join("-" * col_widths[col] for col in columns) + "-|"
    
    result = separator + "\n" + header_line + "\n" + separator
    
    # Build table rows
    for row in rows:
        row_line = "| " + " | ".join(
            truncate(val).ljust(col_widths[columns[i]]) 
            for i, val in enumerate(row)
        ) + " |"
        result += "\n" + row_line
    
    result += "\n" + separator
    result += f"\n({len(rows)} row{'s' if len(rows) != 1 else ''} affected)"
    
    return result

def create_html_table(columns, rows):
    """
    Create a simple HTML table for displaying matched records.
    """
    if not rows:
        return "<p>No data to display.</p>"
    
    def format_html_value(val):
        if val is None:
            return "NULL"
        return str(val).strip()
    
    html = ['<table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 12px; margin: 0; display: block;">']
    
    # Table header
    html.append('<thead>')
    html.append('<tr style="background-color: #4CAF50; color: white;">')
    for col in columns:
        html.append(f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left; font-weight: bold; white-space: nowrap;">{col}</th>')
    html.append('</tr>')
    html.append('</thead>')
    
    # Table body
    html.append('<tbody>')
    for idx, row in enumerate(rows):
        row_bg = '#ffffff' if idx % 2 == 0 else '#f9f9f9'
        html.append(f'<tr style="background-color: {row_bg};">')
        for val in row:
            cell_value = format_html_value(val)
            html.append(f'<td style="border: 1px solid #ddd; padding: 8px; white-space: nowrap; color: #1f2937;">{cell_value}</td>')
        html.append('</tr>')
    
    html.append('</tbody>')
    html.append('</table>')
    html.append(f'<p style="margin: 5px 0 0 0; font-style: italic; color: #666;">({len(rows)} row{"s" if len(rows) != 1 else ""} affected)</p>')
    
    return ''.join(html)

def create_html_side_by_side_table(source_cols, target_cols, source_rows, target_rows):
    """
    Create an HTML table with alternating source/target columns (src_col1, tgt_col1, src_col2, tgt_col2...)
    showing source columns (blue) and target columns (purple), with yellow highlighting for different values.
    """
    if not source_rows and not target_rows:
        return "<p>No data to compare.</p>"
    
    def format_html_value(val):
        if val is None:
            return "NULL"
        return str(val).strip()
    
    def values_are_equal(v1, v2):
        """Compare two values for equality, handling different data types and null values"""
        # Both None or both "NULL" string or both empty
        if (v1 is None or v1 == "NULL" or v1 == "") and (v2 is None or v2 == "NULL" or v2 == ""):
            return True
        # Direct equality check (works for strings, numbers, etc.)
        if v1 == v2:
            return True
        # Try numeric comparison if both can be converted to numbers
        try:
            # Handle string representations of numbers
            num1 = float(v1) if v1 not in (None, "NULL", "") else None
            num2 = float(v2) if v2 not in (None, "NULL", "") else None
            if num1 is not None and num2 is not None:
                return abs(num1 - num2) < 1e-10  # Use epsilon for float comparison
        except (ValueError, TypeError):
            pass
        # String comparison (case-insensitive, stripped)
        try:
            str1 = str(v1).strip().lower() if v1 not in (None, "NULL") else ""
            str2 = str(v2).strip().lower() if v2 not in (None, "NULL") else ""
            return str1 == str2
        except:
            pass
        return False
    
    # Start building HTML table - output directly without wrapper
    html = ['<table style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; display: block; overflow-x: auto; max-width: 100%; margin: 0;">']
    
    # Table header - interleave source and target columns
    html.append('<thead>')
    html.append('<tr style="background-color: #f0f0f0;">')
    html.append('<th style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold; position: sticky; left: 0; background-color: #f0f0f0; z-index: 10;">#</th>')
    
    # Interleave source and target column headers
    for i, col in enumerate(source_cols):
        # Source column header (blue)
        html.append(f'<th style="border: 1px solid #ddd; padding: 8px; background-color: #d4e3fc; color: #000; text-align: left; font-weight: bold; white-space: nowrap;">🔵 src_{col}</th>')
        # Target column header (purple) - right after corresponding source column
        if i < len(target_cols):
            html.append(f'<th style="border: 1px solid #ddd; padding: 8px; background-color: #e4d4fc; color: #000; text-align: left; font-weight: bold; white-space: nowrap;">🟣 tgt_{target_cols[i]}</th>')
    
    html.append('</tr>')
    html.append('</thead>')
    
    # Table body
    html.append('<tbody>')
    max_rows = max(len(source_rows), len(target_rows))
    
    for idx in range(max_rows):
        # Alternate row colors for better readability
        row_bg = '#ffffff' if idx % 2 == 0 else '#f9f9f9'
        html.append(f'<tr style="background-color: {row_bg};">')
        
        # Row number (sticky)
        html.append(f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold; position: sticky; left: 0; background-color: {row_bg}; z-index: 5; color: #1f2937;">{idx}</td>')
        
        # Get source and target rows
        source_row = source_rows[idx] if idx < len(source_rows) else [None] * len(source_cols)
        target_row = target_rows[idx] if idx < len(target_rows) else [None] * len(target_cols)
        
        # Debug: Track differences for first few rows
        if idx < 3:
            diff_cols = []
        
        # Interleave source and target columns
        for i in range(len(source_cols)):
            # Source column value
            src_val = source_row[i] if i < len(source_row) else None
            src_cell_value = format_html_value(src_val)
            
            # Check if different from target
            tgt_val = target_row[i] if i < len(target_row) else None
            
            # Compare using the function defined at the top of this function
            is_different = not values_are_equal(src_val, tgt_val)
            
            # Debug logging for first few rows
            if idx < 3 and is_different:
                diff_cols.append(f"{source_cols[i]}(src='{src_val}' vs tgt='{tgt_val}')")
            
            src_bg_color = '#fff9c4' if is_different else row_bg
            html.append(f'<td style="border: 1px solid #ddd; padding: 8px; background-color: {src_bg_color}; white-space: nowrap; color: #1f2937;">{src_cell_value}</td>')
            
            # Target column value (right after source)
            if i < len(target_cols):
                tgt_cell_value = format_html_value(tgt_val)
                tgt_bg_color = '#fff9c4' if is_different else row_bg
                html.append(f'<td style="border: 1px solid #ddd; padding: 8px; background-color: {tgt_bg_color}; white-space: nowrap; color: #1f2937;">{tgt_cell_value}</td>')
        
        # Log differences for debugging
        if idx < 3 and diff_cols:
            print(f"[DEBUG HTML] Row {idx} - Columns marked as different: {', '.join(diff_cols[:5])}... ({len(diff_cols)} total)")
        
        html.append('</tr>')
    
    html.append('</tbody>')
    html.append('</table>')
    html.append('<p style="margin: 5px 0 0 0; font-style: italic; color: #666;">Showing {0} row{1}</p>'.format(max_rows, "s" if max_rows != 1 else ""))
    html.append('<p style="margin: 3px 0 0 0; font-size: 11px; color: #666;"><span style="color: #1e88e5;">🔵 = Source columns</span> | <span style="color: #7e57c2;">🟣 = Target columns</span> | <span style="background-color: #fff9c4; padding: 2px 6px;">Yellow highlight</span> = different values</p>')
    
    return ''.join(html)

def create_side_by_side_table(source_cols, target_cols, source_rows, target_rows, max_width=20):
    """
    Create a side-by-side comparison table with source columns on left (blue background)
    and target columns on right (purple background), highlighting differences in yellow.
    """
    if not source_rows and not target_rows:
        return "No data to compare."
    
    def truncate(val, width=max_width):
        if val is None:
            return "NULL"
        val_str = str(val).strip()
        return val_str if len(val_str) <= width else val_str[:width-3] + "..."
    
    # Build header with visual separators
    header_parts = []
    header_parts.append("#")
    
    # Source columns (blue background indicator)
    for col in source_cols:
        header_parts.append(f"🔵 src_{col}")
    
    # Target columns (purple background indicator)  
    for col in target_cols:
        header_parts.append(f"🟣 tgt_{col}")
    
    # Calculate column widths
    col_widths = [3]  # Row number column
    for col in source_cols:
        col_widths.append(min(max(len(f"src_{col}"), 12), max_width))
    for col in target_cols:
        col_widths.append(min(max(len(f"tgt_{col}"), 12), max_width))
    
    # Build table header
    header_line = "| " + " | ".join(
        str(header_parts[i]).ljust(col_widths[i]) 
        for i in range(len(header_parts))
    ) + " |"
    separator = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"
    
    result = separator + "\n" + header_line + "\n" + separator
    
    # Build table rows
    max_rows = max(len(source_rows), len(target_rows))
    for idx in range(max_rows):
        row_parts = [str(idx)]
        
        # Get source and target rows
        source_row = source_rows[idx] if idx < len(source_rows) else [None] * len(source_cols)
        target_row = target_rows[idx] if idx < len(target_rows) else [None] * len(target_cols)
        
        # Source columns
        for i, val in enumerate(source_row):
            truncated = truncate(val, col_widths[i + 1])
            # Highlight if different from target (same position comparison)
            if i < len(target_row):
                src_val = val
                tgt_val = target_row[i] if i < len(target_row) else None
                # Normalize for comparison
                src_normalized = str(src_val).strip() if src_val is not None else None
                tgt_normalized = str(tgt_val).strip() if tgt_val is not None else None
                
                if src_normalized != tgt_normalized:
                    # Mark source value with yellow highlight if different
                    truncated = f"🟡{truncated}"
            row_parts.append(truncated.ljust(col_widths[i + 1] + (2 if "🟡" in truncated else 0)))
        
        # Target columns
        for i, val in enumerate(target_row):
            truncated = truncate(val, col_widths[len(source_cols) + i + 1])
            # Highlight if different from source (same position comparison)
            if i < len(source_row):
                src_val = source_row[i] if i < len(source_row) else None
                tgt_val = val
                # Normalize for comparison
                src_normalized = str(src_val).strip() if src_val is not None else None
                tgt_normalized = str(tgt_val).strip() if tgt_val is not None else None
                
                if src_normalized != tgt_normalized:
                    # Mark target value with yellow highlight if different
                    truncated = f"🟡{truncated}"
            row_parts.append(truncated.ljust(col_widths[len(source_cols) + i + 1] + (2 if "🟡" in truncated else 0)))
        
        row_line = "| " + " | ".join(row_parts) + " |"
        result += "\n" + row_line
    
    result += "\n" + separator
    result += f"\n(Showing {max_rows} row{'s' if max_rows != 1 else ''})"
    result += "\n🔵 = Source columns  |  🟣 = Target columns  |  🟡 = Different value"
    
    return result

def get_table_structure(cursor, table):
    # Handle temp tables/views differently
    # SQL Server temp tables start with ## or #
    # Databricks temp views don't have special prefix, so we detect by pattern temp_source_* or temp_target_*
    # SQLite temp tables use TempSource_ or TempTarget_ prefix
    table_lower = table.lower()
    is_temp_table = table.startswith('##') or table.startswith('#') or table_lower.startswith('temp_source_') or table_lower.startswith('temp_target_') or table_lower.startswith('tempsource_') or table_lower.startswith('temptarget_')
    
    if is_temp_table:
        # For temp tables/views, query directly to get structure from cursor metadata
        try:
            # SQL Server temp tables
            if table.startswith('##') or table.startswith('#'):
                # First try: Standard SQL Server approach using sys.columns
                try:
                    cursor.execute(f"""
                        SELECT 
                            c.name AS COLUMN_NAME,
                            t.name AS DATA_TYPE,
                            CASE WHEN c.is_nullable = 1 THEN 'YES' ELSE 'NO' END AS IS_NULLABLE
                        FROM tempdb.sys.columns c
                        INNER JOIN tempdb.sys.types t ON c.user_type_id = t.user_type_id
                        WHERE c.object_id = OBJECT_ID('tempdb..{table}')
                        ORDER BY c.column_id
                    """)
                    result = cursor.fetchall()
                    if result:
                        return result
                except:
                    pass  # Fall through to generic approach
            
            # Generic approach for both SQL Server fallback and Databricks temp views
            # Use LIMIT 0 for Databricks, TOP 0 for SQL Server
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 0")
            except:
                cursor.execute(f"SELECT TOP 0 * FROM {table}")
            
            columns = cursor.description
            result = []
            for col in columns:
                # col[0] = name, col[1] = type_code, col[6] = nullable
                col_name = col[0]
                # Map type codes to SQL type names (works for both pyodbc and databricks-sql-connector)
                type_map = {
                    -7: 'bit', -6: 'tinyint', -5: 'bigint', -4: 'image',
                    -3: 'varbinary', -2: 'binary', -1: 'text', 1: 'char',
                    2: 'numeric', 3: 'decimal', 4: 'int', 5: 'smallint',
                    6: 'float', 7: 'real', 8: 'double', 12: 'varchar',
                    91: 'date', 92: 'time', 93: 'datetime'
                }
                # Get type name from type_code, or use the type name directly if available
                if hasattr(col, 'type_code'):
                    col_type = type_map.get(col.type_code, str(col.type_code))
                elif len(col) > 1:
                    col_type = type_map.get(col[1], 'varchar')
                else:
                    col_type = 'varchar'
                
                # Nullable info - different position depending on connector
                if hasattr(col, 'null_ok'):
                    col_nullable = 'YES' if col.null_ok else 'NO'
                elif len(col) > 6:
                    col_nullable = 'NO' if col[6] == False or col[6] == 0 else 'YES'
                else:
                    col_nullable = 'YES'  # Default to nullable if unknown
                
                result.append((col_name, col_type, col_nullable))
            return result
        except Exception as e:
            print(f"[ERROR] Failed to get temp table/view structure: {e}")
            return []
    else:
        # Regular tables - use INFORMATION_SCHEMA (SQL Server/Synapse only)
        if '.' in table:
            schema, table_name = table.split(".")
        else:
            schema = 'dbo'
            table_name = table
        try:
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{schema}'
            """)
            result = cursor.fetchall()
            return result
        except:
            # Fallback: query directly (works for Databricks regular tables)
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 0")
            except:
                cursor.execute(f"SELECT TOP 0 * FROM {table}")
            
            columns = cursor.description
            result = []
            for col in columns:
                col_name = col[0]
                col_type = 'varchar'  # Generic type
                col_nullable = 'YES'  # Default
                result.append((col_name, col_type, col_nullable))
            return result

def get_primary_keys(cursor, table):
    # Temp tables/views typically don't have primary keys unless explicitly created
    # SQL Server temp tables start with ## or #
    # Databricks temp views start with temp_source_ or temp_target_
    # SQLite temp tables use TempSource_ or TempTarget_ prefix
    table_lower = table.lower()
    is_temp = table.startswith('##') or table.startswith('#') or table_lower.startswith('temp_source_') or table_lower.startswith('temp_target_') or table_lower.startswith('tempsource_') or table_lower.startswith('temptarget_')
    
    if is_temp:
        return []
    
    # Try SQL Server approach first
    try:
        if '.' in table:
            schema, table_name = table.split(".")
        else:
            schema = 'dbo'
            table_name = table
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE OBJECTPROPERTY(
                OBJECT_ID(CONSTRAINT_SCHEMA + '.' + QUOTENAME(CONSTRAINT_NAME)), 
                'IsPrimaryKey'
            ) = 1 
            AND TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{schema}'
        """)
        return [row[0] for row in cursor.fetchall()]
    except:
        # Databricks doesn't support INFORMATION_SCHEMA for primary keys
        # Return empty list for Databricks tables
        return []

def structure_validation(cursor, table1, table2, return_output=False, source_name=None, target_name=None, source_cursor=None, target_cursor=None):
    # Use separate cursors if provided, otherwise use the same cursor for both
    cursor1 = source_cursor if source_cursor else cursor
    cursor2 = target_cursor if target_cursor else cursor
    
    struct1 = get_table_structure(cursor1, table1)
    struct2 = get_table_structure(cursor2, table2)
    pk1 = get_primary_keys(cursor1, table1)
    pk2 = get_primary_keys(cursor2, table2)
    
    # Use original names if provided, otherwise use table names
    display_name1 = source_name if source_name else table1
    display_name2 = target_name if target_name else table2
    
    output = []
    output.append("\n📐 Structure Validation:\n")

    if not struct1:
        output.append(f"⚠️ Warning: Table '{display_name1}' structure is empty or not found.")
    if not struct2:
        output.append(f"⚠️ Warning: Table '{display_name2}' structure is empty or not found.")

    # Create dictionaries for easy lookup: column_name -> (data_type, is_nullable)
    struct1_dict = {col[0]: (col[1], col[2]) for col in struct1}
    struct2_dict = {col[0]: (col[1], col[2]) for col in struct2}
    
    # Identify issues
    source_only_cols = set(struct1_dict.keys()) - set(struct2_dict.keys())
    target_only_cols = set(struct2_dict.keys()) - set(struct1_dict.keys())
    common_cols = set(struct1_dict.keys()) & set(struct2_dict.keys())
    
    # Check for data type or nullability mismatches in common columns
    type_mismatch_cols = set()
    for col in common_cols:
        if struct1_dict[col] != struct2_dict[col]:
            type_mismatch_cols.add(col)
    
    # Check primary key differences
    pk_source_only = set(pk1) - set(pk2)
    pk_target_only = set(pk2) - set(pk1)

    def format_structure(struct, pk_list, table_display_name, is_source=True, problem_cols=None):
        """Format structure with highlighting for problematic columns"""
        if problem_cols is None:
            problem_cols = set()
        
        col_names = []
        for col in struct:
            col_name = col[0]
            if col_name in problem_cols:
                col_names.append(f"🔴 {col_name}")  # Highlight problematic columns
            else:
                col_names.append(col_name)
        
        data_types = []
        for col in struct:
            col_name = col[0]
            col_type = col[1]
            col_nullable = 'NULLABLE' if col[2] == 'YES' else 'NOT NULL'
            
            if col_name in problem_cols:
                data_types.append(f"🔴 {col_name} ({col_type}, {col_nullable})")
            else:
                data_types.append(f"{col_name} ({col_type}, {col_nullable})")
        
        # Highlight primary keys that are different
        pk_display = []
        for pk in pk_list:
            if is_source and pk in pk_source_only:
                pk_display.append(f"🔴 {pk}")
            elif not is_source and pk in pk_target_only:
                pk_display.append(f"🔴 {pk}")
            else:
                pk_display.append(pk)
        
        label = "Source table name" if is_source else "Target table name"
        return (
            f"🗂 {label}: {table_display_name}\n"
            f"🔢 Number of columns: {len(struct)}\n"
            f"📋 Column Names: {', '.join(col_names)}\n"
            f"🧾 Column Details:\n  - " + "\n  - ".join(data_types) + "\n"
            f"🔑 Primary Keys: {', '.join(pk_display) if pk_list else 'None'}\n"
        )

    # Identify all problematic columns for source and target
    source_problem_cols = source_only_cols | type_mismatch_cols
    target_problem_cols = target_only_cols | type_mismatch_cols

    output.append(format_structure(struct1, pk1, display_name1, is_source=True, problem_cols=source_problem_cols))
    output.append(format_structure(struct2, pk2, display_name2, is_source=False, problem_cols=target_problem_cols))
    
    # Check if structures match based on actual differences found (not order-dependent)
    has_column_differences = bool(source_only_cols or target_only_cols)
    has_type_mismatches = bool(type_mismatch_cols)
    has_pk_differences = bool(pk_source_only or pk_target_only)
    result = not (has_column_differences or has_type_mismatches or has_pk_differences)
    
    if not result:
        output.append("\n🔍 Structure Comparison Issues:\n")
        
        if source_only_cols:
            output.append(f"❌ Columns in SOURCE but NOT in TARGET:")
            for col in sorted(source_only_cols):
                col_info = struct1_dict[col]
                output.append(f"   🔴 {col} ({col_info[0]}, {'NULLABLE' if col_info[1] == 'YES' else 'NOT NULL'})")
        
        if target_only_cols:
            output.append(f"\n❌ Columns in TARGET but NOT in SOURCE:")
            for col in sorted(target_only_cols):
                col_info = struct2_dict[col]
                output.append(f"   🔴 {col} ({col_info[0]}, {'NULLABLE' if col_info[1] == 'YES' else 'NOT NULL'})")
        
        if type_mismatch_cols:
            output.append(f"\n❌ Columns with DIFFERENT DATA TYPES or NULLABILITY:")
            for col in sorted(type_mismatch_cols):
                src_info = struct1_dict[col]
                tgt_info = struct2_dict[col]
                output.append(f"   🔴 {col}:")
                output.append(f"      Source: ({src_info[0]}, {'NULLABLE' if src_info[1] == 'YES' else 'NOT NULL'})")
                output.append(f"      Target: ({tgt_info[0]}, {'NULLABLE' if tgt_info[1] == 'YES' else 'NOT NULL'})")
        
        if pk_source_only or pk_target_only:
            output.append(f"\n❌ PRIMARY KEY Differences:")
            if pk_source_only:
                output.append(f"   In SOURCE only: {', '.join(sorted(pk_source_only))}")
            if pk_target_only:
                output.append(f"   In TARGET only: {', '.join(sorted(pk_target_only))}")
        
        output.append("\n❌ Source and Target Table Structure and DataTypes are mismatched.")
        output.append("\n🔴 = Column with issue/mismatch")
    else:
        output.append("✅ Source and Target Table Structure and DataTypes are matched.")
    
    return ("\n".join(output), result) if return_output else result

def count_validation(cursor, table1, table2, source_name=None, target_name=None, return_output=False, source_cursor=None, target_cursor=None):
    # Use separate cursors if provided, otherwise use the same cursor for both
    cursor1 = source_cursor if source_cursor else cursor
    cursor2 = target_cursor if target_cursor else cursor
    
    cursor1.execute(f"SELECT COUNT(*) FROM {table1}")
    source_count = cursor1.fetchone()[0]
    cursor2.execute(f"SELECT COUNT(*) FROM {table2}")
    target_count = cursor2.fetchone()[0]

    # Use original names if provided
    display_name1 = source_name if source_name else table1
    display_name2 = target_name if target_name else table2

    warnings = []
    if source_count == 0:
        warnings.append(f"⚠️ Warning: Source table is empty.")
    if target_count == 0:
        warnings.append(f"⚠️ Warning: Target table is empty.")

    result = source_count == target_count
    output = f"🔢 Record Count Check:\n"
    if warnings:
        output += "\n".join(warnings) + "\n"
    output += f" - Source table ({display_name1}): {source_count} rows\n"
    output += f" - Target table ({display_name2}): {target_count} rows\n"
    output += "✅ Source and Target Record counts are matched." if result else "❌ Source and Target Record counts are mismatched."
    return (result, output) if return_output else result

def null_check(cursor, table, return_output=False, source_name=None):
    # OPTIMIZATION: Use COUNT(*) instead of fetching all rows
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    
    display_name = source_name if source_name else table
    
    if count == 0:
        warning = f"⚠️ Warning: Table '{display_name}' is empty. Skipping null check."
        return warning if return_output else print(warning)

    # OPTIMIZATION: Get column names without fetching data using LIMIT/TOP 0
    try:
        cursor.execute(f"SELECT * FROM {table} LIMIT 0")
    except:
        cursor.execute(f"SELECT TOP 0 * FROM {table}")
    columns = [desc[0] for desc in cursor.description]
    
    struct = get_table_structure(cursor, table)
    nullability = {col[0]: col[2] for col in struct}
    pk_columns = get_primary_keys(cursor, table)
    
    # Check if there are any NOT NULL constraints or primary keys to validate
    has_constraints = any(nullability.get(col) == "NO" for col in columns) or len(pk_columns) > 0
    
    if not has_constraints:
        skip_msg = f"ℹ️ Null Check skipped for '{display_name}': No NOT NULL constraints or Primary Keys defined."
        return skip_msg if return_output else print(skip_msg)
    
    # OPTIMIZATION: Count nulls efficiently with individual queries instead of fetching all data
    print(f"[PERFORMANCE] Checking NULL values for {len(columns)} columns in {display_name}...")
    null_counts = {}
    violations = []
    for col in columns:
        try:
            # Use backticks for Databricks temp views, brackets for SQL Server
            col_identifier = f"`{col}`" if table.startswith('temp_') else f"[{col}]"
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_identifier} IS NULL")
            count = cursor.fetchone()[0]
        except Exception as e:
            # Fallback: try without column identifier decorators
            print(f"[DEBUG] Column identifier failed for {col}, using plain name: {e}")
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
                count = cursor.fetchone()[0]
            except:
                # If still fails, skip this column
                print(f"[WARNING] Could not check NULL for column {col}")
                count = 0
        
        null_counts[col] = count
        if nullability.get(col) == "NO" and count > 0:
            violations.append(f"❌ NOT NULL violation in '{col}': {count} NULLs")
        if col in pk_columns and count > 0:
            violations.append(f"❌ PRIMARY KEY violation in '{col}': {count} NULLs")
    
    output = [f"\n🚫 NULL Validation Report for: {display_name}"]
    
    # Add column details with highlighting for constraints
    for col, count in null_counts.items():
        col_label = col
        constraints = []
        
        # Check if column is primary key
        if col in pk_columns:
            constraints.append("🔑 PRIMARY KEY")
        
        # Check if column has NOT NULL constraint
        if nullability.get(col) == "NO":
            constraints.append("🔒 NOT NULL")
        
        # Build the output line with constraint badges
        if constraints:
            constraint_badges = " " + " ".join(constraints)
            output.append(f" - {col}{constraint_badges}: {count} NULLs")
        else:
            output.append(f" - {col}: {count} NULLs")
    
    if violations:
        output.append("\n🚨 Constraint Violations:")
        output.extend(violations)
    else:
        output.append("✅ Nullable, Not Null and Primary Key Constraints are verified.")
    return "\n".join(output) if return_output else null_counts

def duplicate_check(cursor, table, columns=None, use_primary_key=False, use_all_columns=False, return_output=False, label="", log_file=None, log_records=None):
    def get_primary_keys_internal(cursor, table):
        # Try SQL Server approach
        try:
            cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE OBJECTPROPERTY(
                    OBJECT_ID(CONSTRAINT_SCHEMA + '.' + QUOTENAME(CONSTRAINT_NAME)), 
                    'IsPrimaryKey'
                ) = 1
                AND TABLE_NAME = '{table.split('.')[-1]}'
            """)
            return [row[0] for row in cursor.fetchall()]
        except:
            # Databricks doesn't support this query
            return []

    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    if count == 0:
        msg = f"⚠️ Warning: Table '{table}' is empty. Skipping duplicate check."
        return msg if return_output else print(msg)

    if use_primary_key:
        columns = get_primary_keys_internal(cursor, table)
        if not columns:
            # If no primary key, use all columns
            # Try LIMIT 1 for Databricks, TOP 1 for SQL Server
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            except:
                cursor.execute(f"SELECT TOP 1 * FROM {table}")
            columns = [desc[0] for desc in cursor.description]
            check_type = "All Columns (no primary key found)"
        else:
            check_type = "Primary Key Columns"
    elif use_all_columns:
        # Try LIMIT 1 for Databricks, TOP 1 for SQL Server
        try:
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
        except:
            cursor.execute(f"SELECT TOP 1 * FROM {table}")
        columns = [desc[0] for desc in cursor.description]
        check_type = "All Columns"
    elif not columns:
        msg = "⚠️ No columns specified for duplicate check."
        return msg if return_output else print(msg)
    else:
        check_type = "Specified Columns"

    # Use backticks for Databricks, brackets for SQL Server with fallback
    try:
        if table.startswith('temp_'):
            col_str = ", ".join(f"`{col}`" for col in columns)
        else:
            col_str = ", ".join(f"[{col}]" for col in columns)
        
        cursor.execute(f"""
            SELECT {col_str}, COUNT(*) 
            FROM {table} 
            GROUP BY {col_str}
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
    except Exception as e:
        # Fallback: try without column decorators
        print(f"[DEBUG] Duplicate check with column identifiers failed, using plain names: {e}")
        try:
            col_str = ", ".join(columns)
            cursor.execute(f"""
                SELECT {col_str}, COUNT(*) 
                FROM {table} 
                GROUP BY {col_str}
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
        except Exception as e2:
            # If still fails, return error message
            error_msg = f"⚠️ Could not perform duplicate check on {table}: {str(e2)}"
            return error_msg if return_output else print(error_msg)
    
    table_display = label if label else table
    
    if not duplicates:
        msg = f"✅ No duplicate records found in {table_display} table\n"
        msg += f"   Check performed on: {check_type}\n"
        msg += f"   Columns checked: {', '.join(columns)}"
        return msg if return_output else print(msg)

    msg = f"❌ Duplicates found in {table_display} table\n"
    msg += f"   Check performed on: {check_type}\n"
    msg += f"   Columns checked: {', '.join(columns)}\n\n"
    for row in duplicates:
        msg += f"🔁 Duplicate Key: {row}\n"

    where_clauses = []
    params = []
    is_databricks = table.startswith('temp_')
    
    for dup in duplicates:
        if is_databricks:
            # Databricks: Use backticks and direct value substitution (doesn't support ? params in WHERE)
            clause_parts = []
            for col, val in zip(columns, dup[:len(columns)]):
                if val is None:
                    clause_parts.append(f"`{col}` IS NULL")
                elif isinstance(val, str):
                    # Escape single quotes
                    escaped_val = val.replace("'", "''")
                    clause_parts.append(f"`{col}` = '{escaped_val}'")
                else:
                    clause_parts.append(f"`{col}` = {val}")
            where_clauses.append(f"({' AND '.join(clause_parts)})")
        else:
            # SQL Server: Use brackets and parameterized queries
            clause = " AND ".join([f"[{col}] = ?" for col in columns])
            where_clauses.append(f"({clause})")
            params.extend(dup[:len(columns)])
    
    query = f"SELECT * FROM {table} WHERE " + " OR ".join(where_clauses)
    
    try:
        if is_databricks:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
        
        duplicate_records = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
    except Exception as e:
        # If fetching duplicate records fails, just show the count
        print(f"[DEBUG] Could not fetch duplicate records: {e}")
        msg += f"\n⚠️ Found {len(duplicates)} duplicate key(s) but could not fetch full records\n"
        return msg if return_output else print(msg)
    msg += f"\n📄 Duplicate Records in {table_display} table:\n"
    formatted_records = []
    for record in duplicate_records:
        formatted_row = {col: format_value(val) for col, val in zip(col_names, record)}
        msg += str(formatted_row) + "\n"
        formatted_records.append(formatted_row)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            for record in formatted_records:
                f.write(str(record) + "\n")
        msg += f"\n📝 Duplicate log saved to: {os.path.abspath(log_file)}"
    if log_records is not None:
        log_records.extend(formatted_records)
    return msg if return_output else print(msg)

import os
from datetime import datetime, date
from decimal import Decimal

def format_value(val):
    """Normalize values for consistent comparison across different data types"""
    # Handle NULL/None/Empty as consistent "NULL" string
    if val is None or val == "" or (isinstance(val, str) and val.strip() == ""):
        return "NULL"
    
    # Handle datetime/date types
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    
    # Handle Decimal types
    if isinstance(val, Decimal):
        return str(float(val))
    
    # Handle numeric types - convert to string to ensure consistent comparison
    # This prevents issues like 5 != 5.0 != "5"
    if isinstance(val, (int, float)):
        # Remove trailing zeros and decimal point if not needed
        num_str = str(float(val))
        # Clean up: "5.0" -> "5", but "5.5" stays "5.5"
        if '.' in num_str and num_str.endswith('0'):
            num_str = num_str.rstrip('0').rstrip('.')
        return num_str
    
    # Handle strings - strip whitespace and convert to uppercase for case-insensitive comparison
    if isinstance(val, str):
        stripped = val.strip()
        # Try to parse as number for consistency
        try:
            num = float(stripped)
            num_str = str(num)
            if '.' in num_str and num_str.endswith('0'):
                num_str = num_str.rstrip('0').rstrip('.')
            return num_str
        except (ValueError, TypeError):
            # Not a number - return as uppercase string for case-insensitive comparison
            return stripped.upper() if stripped else "NULL"
    
    # For any other type, convert to string
    return str(val).strip().upper()

def row_data_validation(cursor, table1, table2, return_output=False, mismatch_log_file=None, source_name=None, target_name=None, source_cursor=None, target_cursor=None, sample_size=0):
    # Use separate cursors if provided, otherwise use the same cursor for both
    cursor1 = source_cursor if source_cursor else cursor
    cursor2 = target_cursor if target_cursor else cursor
    
    # OPTIMIZATION: First get column names without fetching data
    # Use LIMIT/TOP 0 to get structure without data transfer
    try:
        cursor1.execute(f"SELECT * FROM {table1} LIMIT 0")
    except:
        cursor1.execute(f"SELECT TOP 0 * FROM {table1}")
    cols1 = [desc[0] for desc in cursor1.description]
    
    try:
        cursor2.execute(f"SELECT * FROM {table2} LIMIT 0")
    except:
        cursor2.execute(f"SELECT TOP 0 * FROM {table2}")
    cols2 = [desc[0] for desc in cursor2.description]
    
    # OPTIMIZATION: Get row counts efficiently without fetching all data
    cursor1.execute(f"SELECT COUNT(*) FROM {table1}")
    count1 = cursor1.fetchone()[0]
    cursor2.execute(f"SELECT COUNT(*) FROM {table2}")
    count2 = cursor2.fetchone()[0]
    
    # Use display names for CSV files
    source_display = source_name if source_name else table1
    target_display = target_name if target_name else table2

    # Enhanced logic to handle column name differences
    if len(cols1) != len(cols2):
        msg = "❌ Different number of columns between tables. Cannot compare row-level data accurately."
        return msg if return_output else print(msg)
    
    # Check if column names match (even if in different order)
    column_mapping_info = ""
    target_reorder_indices = None  # Initialize reordering mapping
    cols1_set = set(cols1)
    cols2_set = set(cols2)
    
    # Check if columns are exactly the same but potentially in different order
    if cols1_set == cols2_set and cols1 != cols2:
        # Columns match but order is different - we need to reorder
        column_mapping_info = f"\n🔄 Column order difference detected - reordering for accurate comparison:\n"
        col_order_map = {col: idx for idx, col in enumerate(cols1)}
        target_reorder_indices = [col_order_map[col] for col in cols2]
        column_mapping_info += f"   Source order: {', '.join(cols1)}\n"
        column_mapping_info += f"   Target order: {', '.join(cols2)}\n"
        column_mapping_info += "   ✅ Reordering target data to match source column order...\n"
        print(f"[DEBUG] Column reordering map: {list(zip(cols2, target_reorder_indices))}")
    elif cols1 != cols2:
        # Columns have different names at same positions - position-based comparison
        column_mapping_info = f"\n🔄 Column name mapping detected:\n"
        for i, (col1, col2) in enumerate(zip(cols1, cols2)):
            column_mapping_info += f"   Source[{i}]: {col1} ↔ Target[{i}]: {col2}\n"
        column_mapping_info += "📋 Performing position-based comparison...\n"
        target_reorder_indices = None
    else:
        # Columns match perfectly
        target_reorder_indices = None

    msg = f"\n📊 Row-wise Data Validation (All Columns):"
    
    # Add column mapping info if columns were different
    if column_mapping_info:
        msg += column_mapping_info
    
    # Add info if sampling is used
    if sample_size > 0:
        msg += f"\n📊 Row-wise comparison uses {sample_size} sampled records (structure/count/null/duplicate checks use full dataset).\n"
    else:
        msg += f"\n📊 Comparing all records for row-wise validation.\n"

    if count1 == 0 and count2 == 0:
        msg += "\n✅ Both source and target tables are empty."
        return msg if return_output else print(msg)

    if count2 == 0:
        msg += f"\n⚠️ Target table '{table2}' is empty."
        msg += f"\n❌ Rows present only in Source: {count1}"
        msg += f"\n✅ Matched Rows: 0"
        return msg if return_output else print(msg)

    if count1 == 0:
        msg += f"\n⚠️ Source table '{table1}' is empty."
        msg += f"\n❌ Rows present only in Target: {count2}"
        msg += f"\n✅ Matched Rows: 0"
        return msg if return_output else print(msg)
    
    # OPTIMIZATION: Fetch data with fallback for compatibility
    # CRITICAL: Add ORDER BY to ensure deterministic ordering and prevent false mismatches
    # when duplicate records exist (they must be in same order in both source and target)
    # SMART SAMPLING: If sample_size > 0, only fetch that many rows for row-wise comparison
    print(f"[PERFORMANCE] Fetching rows from source table (sample_size={sample_size if sample_size > 0 else 'all'})...")
    try:
        # Build ORDER BY clause using all columns for deterministic ordering
        order_by_cols1 = ", ".join([f"[{col}]" for col in cols1])
        
        # Add LIMIT/TOP clause if sampling is requested
        limit_clause = ""
        if sample_size > 0:
            # Try to detect if this is SQL Server or Databricks based on table name pattern
            # SQL Server temp tables typically start with #temp_ or temp_
            # Databricks temp views also use temp_ prefix, so we need to try both syntaxes
            pass  # Will use TOP/LIMIT in queries below
        
        # Try optimized query with NOLOCK hint for SQL Server
        if not table1.startswith('temp_'):
            # SQL Server - use brackets and NOLOCK with ORDER BY
            col_list1 = ", ".join([f"[{col}]" for col in cols1])
            if sample_size > 0:
                cursor1.execute(f"SELECT TOP {sample_size} {col_list1} FROM {table1} WITH (NOLOCK) ORDER BY {order_by_cols1}")
            else:
                cursor1.execute(f"SELECT {col_list1} FROM {table1} WITH (NOLOCK) ORDER BY {order_by_cols1}")
        else:
            # Databricks - use ORDER BY for deterministic results with LIMIT for sampling
            order_by_cols1_db = ", ".join([f"`{col}`" for col in cols1])
            if sample_size > 0:
                cursor1.execute(f"SELECT * FROM {table1} ORDER BY {order_by_cols1_db} LIMIT {sample_size}")
            else:
                cursor1.execute(f"SELECT * FROM {table1} ORDER BY {order_by_cols1_db}")
        rows1 = cursor1.fetchall()
        print(f"[DEBUG] Source rows fetched with ORDER BY for deterministic ordering")
    except Exception as e:
        # Fallback to simple SELECT * with ORDER BY if optimized query fails
        print(f"[DEBUG] Optimized query failed, trying alternative syntax: {e}")
        try:
            # Try with backticks for Databricks compatibility
            order_by_cols1_db = ", ".join([f"`{col}`" for col in cols1])
            if sample_size > 0:
                # Try LIMIT first (Databricks), then TOP (SQL Server)
                try:
                    cursor1.execute(f"SELECT * FROM {table1} ORDER BY {order_by_cols1_db} LIMIT {sample_size}")
                except:
                    # SQL Server doesn't support LIMIT, try TOP
                    order_by_cols1 = ", ".join([f"[{col}]" for col in cols1])
                    cursor1.execute(f"SELECT TOP {sample_size} * FROM {table1} ORDER BY {order_by_cols1}")
            else:
                cursor1.execute(f"SELECT * FROM {table1} ORDER BY {order_by_cols1_db}")
        except:
            # Last resort: no ORDER BY (may cause false mismatches)
            print(f"[WARNING] Could not apply ORDER BY - results may have false mismatches for duplicate records")
            if sample_size > 0:
                try:
                    cursor1.execute(f"SELECT * FROM {table1} LIMIT {sample_size}")
                except:
                    cursor1.execute(f"SELECT TOP {sample_size} * FROM {table1}")
            else:
                cursor1.execute(f"SELECT * FROM {table1}")
        rows1 = cursor1.fetchall()
    
    print(f"[PERFORMANCE] Fetching rows from target table (sample_size={sample_size if sample_size > 0 else 'all'})...")
    try:
        # Build ORDER BY clause using all columns for deterministic ordering
        order_by_cols2 = ", ".join([f"[{col}]" for col in cols2])
        
        # Try optimized query with NOLOCK hint for SQL Server
        if not table2.startswith('temp_'):
            # SQL Server - use brackets and NOLOCK with ORDER BY
            col_list2 = ", ".join([f"[{col}]" for col in cols2])
            if sample_size > 0:
                cursor2.execute(f"SELECT TOP {sample_size} {col_list2} FROM {table2} WITH (NOLOCK) ORDER BY {order_by_cols2}")
            else:
                cursor2.execute(f"SELECT {col_list2} FROM {table2} WITH (NOLOCK) ORDER BY {order_by_cols2}")
        else:
            # Databricks - use ORDER BY for deterministic results with LIMIT for sampling
            order_by_cols2_db = ", ".join([f"`{col}`" for col in cols2])
            if sample_size > 0:
                cursor2.execute(f"SELECT * FROM {table2} ORDER BY {order_by_cols2_db} LIMIT {sample_size}")
            else:
                cursor2.execute(f"SELECT * FROM {table2} ORDER BY {order_by_cols2_db}")
        rows2 = cursor2.fetchall()
        print(f"[DEBUG] Target rows fetched with ORDER BY for deterministic ordering")
    except Exception as e:
        # Fallback to simple SELECT * with ORDER BY if optimized query fails
        print(f"[DEBUG] Optimized query failed, trying alternative syntax: {e}")
        try:
            # Try with backticks for Databricks compatibility
            order_by_cols2_db = ", ".join([f"`{col}`" for col in cols2])
            if sample_size > 0:
                # Try LIMIT first (Databricks), then TOP (SQL Server)
                try:
                    cursor2.execute(f"SELECT * FROM {table2} ORDER BY {order_by_cols2_db} LIMIT {sample_size}")
                except:
                    # SQL Server doesn't support LIMIT, try TOP
                    order_by_cols2 = ", ".join([f"[{col}]" for col in cols2])
                    cursor2.execute(f"SELECT TOP {sample_size} * FROM {table2} ORDER BY {order_by_cols2}")
            else:
                cursor2.execute(f"SELECT * FROM {table2} ORDER BY {order_by_cols2_db}")
        except:
            # Last resort: no ORDER BY (may cause false mismatches)
            print(f"[WARNING] Could not apply ORDER BY - results may have false mismatches for duplicate records")
            if sample_size > 0:
                try:
                    cursor2.execute(f"SELECT * FROM {table2} LIMIT {sample_size}")
                except:
                    cursor2.execute(f"SELECT TOP {sample_size} * FROM {table2}")
            else:
                cursor2.execute(f"SELECT * FROM {table2}")
        rows2 = cursor2.fetchall()

    # Reorder target rows if needed to match source column order
    if target_reorder_indices is not None:
        print(f"[DEBUG] Reordering target rows to match source column order...")
        # Reorder each target row according to the mapping
        reordered_rows2 = []
        for row in rows2:
            # Create a new tuple with values reordered to match source
            reordered_row = tuple(row[i] for i in target_reorder_indices)
            reordered_rows2.append(reordered_row)
        rows2 = reordered_rows2
        # After reordering, use source column names for target as well
        cols2 = cols1.copy()
        print(f"[DEBUG] Target rows reordered successfully")

    row_tuples_1 = [tuple(format_value(v) for v in row) for row in rows1]
    row_tuples_2 = [tuple(format_value(v) for v in row) for row in rows2]

    # Debug: Show detailed comparison information for troubleshooting
    print(f"\n{'='*80}")
    print(f"[DEBUG] DETAILED ROW COMPARISON ANALYSIS")
    print(f"{'='*80}")
    print(f"[DEBUG] Source table: {table1}")
    print(f"[DEBUG] Target table: {table2}")
    print(f"[DEBUG] Number of columns: {len(cols1)}")
    print(f"[DEBUG] Column names: {cols1}")
    print(f"[DEBUG] Total source rows: {len(row_tuples_1)}")
    print(f"[DEBUG] Total target rows: {len(row_tuples_2)}")
    
    if row_tuples_1 and row_tuples_2:
        print(f"\n[DEBUG] Sample rows (first 3 from each):")
        print(f"\n[DEBUG] SOURCE ROWS:")
        for i, row in enumerate(row_tuples_1[:3]):
            print(f"  [{i}] {row}")
        
        print(f"\n[DEBUG] TARGET ROWS:")
        for i, row in enumerate(row_tuples_2[:3]):
            print(f"  [{i}] {row}")
        
        # Check if first source row exists anywhere in target
        first_src = row_tuples_1[0]
        if first_src in row_tuples_2:
            target_pos = row_tuples_2.index(first_src)
            print(f"\n[DEBUG] ✅ First source row FOUND in target at position {target_pos}")
        else:
            print(f"\n[DEBUG] ❌ First source row NOT FOUND in target")
            # Find the closest match
            if row_tuples_2:
                first_tgt = row_tuples_2[0]
                mismatches = sum(1 for a, b in zip(first_src, first_tgt) if a != b)
                print(f"[DEBUG] Comparing with first target row:")
                print(f"[DEBUG]   Mismatched columns: {mismatches}/{len(cols1)}")
                for idx, (col, src_val, tgt_val) in enumerate(zip(cols1, first_src, first_tgt)):
                    if src_val != tgt_val:
                        print(f"[DEBUG]     Column {idx} ({col}): '{src_val}' vs '{tgt_val}'")

    print(f"{'='*80}\n")

    print(f"[PERFORMANCE] Comparing {len(row_tuples_1)} source rows with {len(row_tuples_2)} target rows...")
    set1 = set(row_tuples_1)
    set2 = set(row_tuples_2)

    only_in_source = set1 - set2
    only_in_target = set2 - set1
    matched = set1 & set2
    
    # Debug: Log set comparison results
    print(f"[DEBUG] Set comparison results:")
    print(f"[DEBUG]   Matched rows: {len(matched)}")
    print(f"[DEBUG]   Only in source: {len(only_in_source)}")
    print(f"[DEBUG]   Only in target: {len(only_in_target)}")
    total_after_comparison = len(matched) + len(only_in_source) + len(only_in_target)
    print(f"[DEBUG]   Total: {len(matched)} + {len(only_in_source)} + {len(only_in_target)} = {total_after_comparison}")
    print(f"[DEBUG]   Expected total: {len(row_tuples_1)}")
    
    # Validate the math makes sense
    if total_after_comparison != len(row_tuples_1):
        print(f"[WARNING] ⚠️ MATH ERROR: Total after comparison ({total_after_comparison}) != Original row count ({len(row_tuples_1)})")
        print(f"[WARNING] This indicates duplicate rows or format_value normalization issues")
        # Check for duplicates in source
        unique_source = len(set1)
        if unique_source != len(row_tuples_1):
            print(f"[WARNING] Source has {len(row_tuples_1) - unique_source} duplicate rows after normalization")
        # Check for duplicates in target
        unique_target = len(set2)
        if unique_target != len(row_tuples_2):
            print(f"[WARNING] Target has {len(row_tuples_2) - unique_target} duplicate rows after normalization")
    
    if only_in_source and len(only_in_source) <= 5:
        print(f"[DEBUG] Rows only in source (first 2 column values):")
        for row in list(only_in_source)[:5]:
            print(f"[DEBUG]   {row[0] if row else 'NULL'} | {row[1] if len(row) > 1 else 'NULL'}")
    
    if only_in_target and len(only_in_target) <= 5:
        print(f"[DEBUG] Rows only in target (first 2 column values):")
        for row in list(only_in_target)[:5]:
            print(f"[DEBUG]   {row[0] if row else 'NULL'} | {row[1] if len(row) > 1 else 'NULL'}")

    msg += f"\n✅ Matched Rows: {len(matched)}"
    
    # Add clarification if sampling was used
    if sample_size > 0:
        msg += f" (from sampled {sample_size} records)"
        msg += f"\n💡 Note: Counts above reflect the sampled dataset. Structure/Count/Null/Duplicate validations use the full dataset."

    # Determine base directory for CSV files
    if mismatch_log_file:
        base_dir = os.path.dirname(mismatch_log_file)
    else:
        base_dir = "logs"
    os.makedirs(base_dir, exist_ok=True)
    
    # Display matched records - HTML table format (source data)
    # OPTIMIZATION: Limit display to first 10 records to reduce HTML size
    if matched:
        msg += "<h3 style='color: #4CAF50; margin: 0; padding: 0; display: block; line-height: 1.2;'>✅ MATCHED RECORDS (Sample - First 10):</h3>"
        msg += create_html_table(cols1, list(matched)[:10])
        if len(matched) > 10:
            msg += f"<p style='font-style: italic; color: #666; margin-top: 5px;'>... and {len(matched) - 10} more matched rows</p>"
        
        # Create CSV file for matched rows with timestamp and table name
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Clean table name for filename (remove special chars)
        clean_target = target_display.replace(' ', '_').replace(',', '').replace('.', '_')
        matched_csv = os.path.join(base_dir, f"{clean_target}_matched_rows_{timestamp}.csv")
        import csv
        print(f"[PERFORMANCE] Writing {len(matched)} matched rows to CSV...")
        with open(matched_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols1)  # Header
            writer.writerows(matched)
        msg += f"<p style='margin-top: 10px;'>📥 All {len(matched)} matched rows exported to: {os.path.abspath(matched_csv)}</p>"
    
    # Display mismatched records - use POSITION-BASED comparison
    # This works for ANY table without guessing column names
    # Compare row[0] from source to row[0] from target, row[1] to row[1], etc.
    if only_in_source or only_in_target:
        msg += "<div style='margin: 20px 0; padding: 10px; background-color: #ffebee; border: 2px solid #d32f2f; border-radius: 8px;'>"
        msg += "<div style='padding: 10px; background-color: #fff3e0; border-left: 4px solid #ff9800; margin-bottom: 8px;'>"
        msg += "<h4 style='margin: 0 0 5px 0; color: #e65100; font-size: 16px;'>🚨 MISMATCHED RECORDS - Source vs Target Comparison</h4>"
        msg += "<p style='margin: 0; font-size: 13px; line-height: 1.6;'>"
        msg += "<span style='display: inline-block; margin-right: 15px;'><strong style='color: #1e88e5;'>🔵 Source columns</strong> on the left</span>"
        msg += "<span style='display: inline-block; margin-right: 15px;'><strong style='color: #7e57c2;'>🟣 Target columns</strong> on the right</span>"
        msg += "<span style='display: inline-block;'><strong style='background-color: #fff9c4; padding: 3px 8px; border-radius: 3px;'>Yellow highlight</strong> = different values</span>"
        msg += "</p>"
        msg += "</div>"
        
        # POSITION-BASED DISPLAY: Compare rows by their position in the result set
        # This is table-agnostic and doesn't require guessing column names
        print(f"[DEBUG] Using position-based comparison for mismatch display")
        
        # Find mismatched rows by iterating through both lists by position
        all_source_rows = []
        all_target_rows = []
        
        # Compare each position - if ORDER BY is correct, matching entities should be at same position
        max_len = max(len(rows1), len(rows2))
        for i in range(max_len):
            src_row = row_tuples_1[i] if i < len(row_tuples_1) else None
            tgt_row = row_tuples_2[i] if i < len(row_tuples_2) else None
            
            # Only include rows that don't match
            if src_row != tgt_row:
                all_source_rows.append(src_row if src_row else tuple(['NULL'] * len(cols1)))
                all_target_rows.append(tgt_row if tgt_row else tuple(['NULL'] * len(cols2)))
        
        print(f"[DEBUG] Found {len(all_source_rows)} mismatched positions out of {max_len} total rows")
        
        total_mismatches = len(all_source_rows)
        actual_mismatch_count = len(only_in_source) + len(only_in_target)
        
        msg += f"<h3 style='margin: 0; padding: 0; color: #d32f2f; font-size: 18px; display: block; line-height: 1.2;'>❌ Total Mismatched Positions: {total_mismatches}</h3>"
        
        # Add clarification about position-based comparison
        msg += f"<p style='margin: 5px 0; font-size: 13px; color: #666;'><i>(Comparing row positions: {total_mismatches} positions where source and target differ)</i></p>"
        msg += f"<p style='margin: 5px 0; font-size: 13px; color: #666;'><i>Set comparison found: {len(only_in_source)} unique rows only in source, {len(only_in_target)} unique rows only in target</i></p>"
        
        # Add sampling clarification if applicable
        if sample_size > 0:
            msg += f"<p style='margin: 5px 0; font-size: 13px; color: #ff9800; background-color: #fff3e0; padding: 5px; border-radius: 4px;'><strong>💡 Sampling Note:</strong> These row-wise mismatches are from the sampled {sample_size} records. Full dataset was validated for structure, counts, nulls, and duplicates.</p>"
        
        # Display first 10 mismatches
        display_limit = min(10, len(all_source_rows))
        msg += create_html_side_by_side_table(
            cols1, cols2, 
            all_source_rows[:display_limit], 
            all_target_rows[:display_limit]
        )
        
        if len(all_source_rows) > 10:
            msg += f"<p style='font-style: italic; color: #666;'>... and {len(all_source_rows) - 10} more mismatched rows</p>"
        
        # Export to CSV files with timestamp and table names
        from datetime import datetime
        import hashlib
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean and truncate table names for safe filenames (Windows MAX_PATH limit)
        def safe_filename(name, max_length=50):
            clean = name.replace(' ', '_').replace(',', '').replace('.', '_')
            if len(clean) <= max_length:
                return clean
            # For very long names, use first 40 chars + hash
            name_hash = hashlib.md5(clean.encode()).hexdigest()[:8]
            return f"{clean[:40]}_{name_hash}"
        
        clean_source = safe_filename(source_display)
        clean_target = safe_filename(target_display)
        
        if only_in_source:
            source_only_csv = os.path.join(base_dir, f"{clean_source}_source_only_rows_{timestamp}.csv")
            import csv
            with open(source_only_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols1)
                writer.writerows(only_in_source)
            msg += f"<p style='margin-top: 10px;'>📥 Source-only rows exported to: {os.path.abspath(source_only_csv)}</p>"
        
        if only_in_target:
            target_only_csv = os.path.join(base_dir, f"{clean_target}_target_only_rows_{timestamp}.csv")
            import csv
            with open(target_only_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols2)
                writer.writerows(only_in_target)
            msg += f"<p style='margin-top: 10px;'>📥 Target-only rows exported to: {os.path.abspath(target_only_csv)}</p>"
        
        msg += "</div>"  # Close the wrapper div

        # Also save text log for compatibility
        if not mismatch_log_file:
            mismatch_log_file = os.path.join(base_dir, "row_data_mismatch_log.txt")

        with open(mismatch_log_file, "w", encoding="utf-8") as f:
            for row in only_in_source:
                formatted = {col: val for col, val in zip(cols1, row)}
                f.write(f"Only in Source: {formatted}\n")
            for row in only_in_target:
                formatted = {col: val for col, val in zip(cols2, row)}
                f.write(f"Only in Target: {formatted}\n")

    return msg if return_output else print(msg)

