def transform_data(columns, data):
    transformed = [] # Initialize an empty list to hold transformed data
    
    # Column mapping from source (CSV) to target (Database)
    column_mapping = {
        'employee_id': 'Emp_id',
        'first_name': 'FirstName', 
        'last_name': 'LastName',
        'email': 'Email',
        'phone_number': 'PhoneNumber',
        'hire_date': 'Hired_Date',
        'job_id': 'Job_Id',
        'salary': 'Salary',
        'manager_id': 'Manager_id',
        'department_id': 'Department_id'
    }

    for row in data:
        row_dict = dict(zip(columns, row)) # Convert each row to a dictionary using the column names
        
        # Apply column mapping - rename columns to match target table
        mapped_row = {}
        for source_col, value in row_dict.items():
            target_col = column_mapping.get(source_col, source_col)  # Use mapping or keep original name
            mapped_row[target_col] = value

        # ✅ Safe capitalization: Only if value is not None
        if "FirstName" in mapped_row and mapped_row["FirstName"]:
            mapped_row["FirstName"] = mapped_row["FirstName"].capitalize()

        if "LastName" in mapped_row and mapped_row["LastName"]:
            mapped_row["LastName"] = mapped_row["LastName"].capitalize()

        # You can add more transformations here if needed

        transformed.append(mapped_row) # Append the transformed row to the list

    return transformed
