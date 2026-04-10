def extract_data(cursor, table_name):
    query = f"SELECT * FROM {table_name}"
    cursor.execute(query)# Execute the query to fetch all data from the specified table
    columns = [desc[0] for desc in cursor.description]# Get column names from cursor description
    data = cursor.fetchall() # Fetch all rows of the query result
    return columns, data
