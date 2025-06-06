import pyodbc

server = 'aakan-sql-server.database.windows.net,1433'
database = 'chatdb'
username = 'aakanadmin'
password = 'B@BnH$ShDK6&Tq8X'  # replace with your actual password

conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Create table if not exists
    create_table_sql = """
    IF OBJECT_ID('employees', 'U') IS NULL
    CREATE TABLE employees (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100),
        department NVARCHAR(100),
        salary FLOAT,
        doj DATE
    );
    """
    cursor.execute(create_table_sql)
    conn.commit()
    print("✅ Table 'employees' created or already exists.")

    # Insert sample data
    insert_data_sql = """
    INSERT INTO employees (name, department, salary, doj) VALUES
    ('Alice', 'Marketing', 70000, '2021-03-15'),
    ('Bob', 'Sales', 65000, '2019-06-20'),
    ('Charlie', 'Marketing', 72000, '2022-01-10'),
    ('David', 'HR', 60000, '2018-11-05'),
    ('Eva', 'Marketing', 68000, '2020-09-23');
    """
    cursor.execute(insert_data_sql)
    conn.commit()
    print("✅ Sample data inserted.")

    # Query to verify
    cursor.execute("SELECT * FROM employees;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    cursor.close()
    conn.close()

except Exception as e:
    print("❌ Error:")
    print(e)
