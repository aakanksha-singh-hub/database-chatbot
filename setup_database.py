import os
import pyodbc
from dotenv import load_dotenv

def setup_database():
    """Set up the database with tables and sample data."""
    # Load environment variables
    load_dotenv()
    
    # Get connection string from environment variable
    connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')
    if not connection_string:
        raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is not set")
    
    try:
        # Connect to the database
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Read and execute the SQL script
        with open('setup_database.sql', 'r') as file:
            sql_script = file.read()
            
            # Split the script into individual statements
            statements = sql_script.split(';')
            
            # Execute each statement
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            
            # Commit the changes
            conn.commit()
            
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    setup_database() 