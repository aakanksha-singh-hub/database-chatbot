import pyodbc

# Replace these with your actual Azure SQL Database values
server = 'aakan-sql-server.database.windows.net'
database = 'chatdb'
username = 'aakanadmin'
password = 'B@BnH$ShDK6&Tq8X'  # 👈 replace with your real password

# Connection string using ODBC Driver 18
conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=aakan-sql-server.database.windows.net,1433;'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

try:
    # Attempt to connect
    conn = pyodbc.connect(conn_str)
    print("✅ Connected to Azure SQL Database!")

    # Example query
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 5 * FROM employees")  # 👈 change table name as needed
    rows = cursor.fetchall()

    # Print the results
    for row in rows:
        print(row)

    # Close connections
    cursor.close()
    conn.close()

except Exception as e:
    print("❌ Connection failed:")
    print(e)
