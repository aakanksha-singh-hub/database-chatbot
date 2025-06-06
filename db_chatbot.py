import os
from openai import AzureOpenAI
import pyodbc
from config import (
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_VERSION
)

# Database connection settings
DB_CONFIG = {
    'server': 'aakan-sql-server.database.windows.net',
    'database': 'chatdb',
    'username': 'aakanadmin',
    'password': 'B@BnH$ShDK6&Tq8X',
    'driver': '{ODBC Driver 18 for SQL Server}'
}

class DatabaseChatbot:
    def __init__(self):
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            api_version=AZURE_OPENAI_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        
        # Database connection string
        self.conn_str = (
            f'DRIVER={DB_CONFIG["driver"]};'
            f'SERVER={DB_CONFIG["server"]},1433;'
            f'DATABASE={DB_CONFIG["database"]};'
            f'UID={DB_CONFIG["username"]};'
            f'PWD={DB_CONFIG["password"]};'
            'Encrypt=yes;'
            'TrustServerCertificate=no;'
            'Connection Timeout=30;'
        )

    def get_database_schema(self):
        """Get the database schema information"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("""
                SELECT 
                    t.name AS table_name,
                    c.name AS column_name,
                    ty.name AS data_type
                FROM sys.tables t
                INNER JOIN sys.columns c ON t.object_id = c.object_id
                INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
                ORDER BY t.name, c.column_id
            """)
            
            schema_info = {}
            for row in cursor.fetchall():
                table_name, column_name, data_type = row
                if table_name not in schema_info:
                    schema_info[table_name] = []
                schema_info[table_name].append(f"{column_name} ({data_type})")
            
            cursor.close()
            conn.close()
            return schema_info
        except Exception as e:
            print(f"Error getting schema: {e}")
            return {}

    def natural_language_to_sql(self, query):
        """Convert natural language query to SQL using Azure OpenAI"""
        schema_info = self.get_database_schema()
        
        # Create a prompt that includes the database schema
        schema_prompt = "Database Schema:\n"
        for table, columns in schema_info.items():
            schema_prompt += f"\nTable: {table}\nColumns: {', '.join(columns)}\n"

        messages = [
            {"role": "system", "content": f"""You are a SQL expert that converts natural language queries to SQL.
            Use the following database schema to generate accurate SQL queries:
            {schema_prompt}
            
            Rules:
            1. Only generate SQL queries, no explanations
            2. Use proper SQL Server syntax (not MySQL):
               - Use square brackets [] for identifiers, not backticks
               - Use TOP instead of LIMIT
               - Use proper SQL Server date functions
            3. Include error handling in the query
            4. Format the output as a single SQL query
            5. Always use proper SQL Server syntax for Azure SQL Database
            6. Example correct syntax:
               - SELECT [column_name] FROM [table_name]
               - SELECT TOP 10 [column_name] FROM [table_name]
               - SELECT [column_name] FROM [table_name] WHERE [column_name] = 'value'
            7. DO NOT include any markdown formatting or code block markers
            """},
            {"role": "user", "content": query}
        ]

        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the SQL query
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            
            # Debug: Print the generated SQL query
            print("\nDebug - Generated SQL Query:")
            print(sql_query)
            
            # Ensure no backticks are present
            if '`' in sql_query:
                sql_query = sql_query.replace('`', '')
            
            return sql_query
        except Exception as e:
            return f"Error generating SQL: {str(e)}"

    def execute_query(self, sql_query):
        """Execute the SQL query and return results"""
        try:
            # Debug: Print the SQL query before execution
            print("\nDebug - Executing SQL Query:")
            print(sql_query)
            
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(sql_query)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch results
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                "columns": columns,
                "results": results
            }
        except Exception as e:
            print(f"\nDebug - SQL Error: {str(e)}")
            return {
                "error": str(e)
            }

    def chat(self, user_query):
        """Main chat function that processes user queries"""
        # Convert natural language to SQL
        sql_query = self.natural_language_to_sql(user_query)
        
        if sql_query.startswith("Error"):
            return {
                "error": sql_query,
                "sql_query": None,
                "results": None
            }
        
        # Execute the SQL query
        results = self.execute_query(sql_query)
        
        if "error" in results:
            return {
                "error": results["error"],
                "sql_query": sql_query,
                "results": None
            }
        
        return {
            "error": None,
            "sql_query": sql_query,
            "results": results
        }

def main():
    chatbot = DatabaseChatbot()
    print("Welcome to the Database Chatbot!")
    print("Type 'exit' to quit")
    
    while True:
        user_input = input("\nEnter your question: ")
        if user_input.lower() == 'exit':
            break
            
        response = chatbot.chat(user_input)
        
        if response["error"]:
            print(f"\nError: {response['error']}")
        else:
            print("\nGenerated SQL Query:")
            print(response["sql_query"])
            
            if response["results"]:
                print("\nResults:")
                # Print column headers
                print(" | ".join(response["results"]["columns"]))
                print("-" * 50)
                # Print results
                for row in response["results"]["results"]:
                    print(" | ".join(str(value) for value in row))

if __name__ == "__main__":
    main() 