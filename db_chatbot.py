import os
from openai import AzureOpenAI
import pyodbc
import pandas as pd
from datetime import datetime
import csv
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
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Initialize query history for refinement
        self.query_history = []
        
        # Store last query results for context
        self.last_query_results = None
        self.last_sql_query = None

    def get_database_schema(self):
        """Get the database schema information"""
        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()
            
            # Get table information with a simpler query
            cursor.execute("""
                SELECT 
                    t.name AS table_name,
                    c.name AS column_name,
                    ty.name AS data_type,
                    c.is_nullable,
                    c.is_identity
                FROM sys.tables t
                INNER JOIN sys.columns c ON t.object_id = c.object_id
                INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
                ORDER BY t.name, c.column_id
            """)
            
            schema_info = {}
            for row in cursor.fetchall():
                table_name, column_name, data_type, is_nullable, is_identity = row
                if table_name not in schema_info:
                    schema_info[table_name] = []
                
                column_info = {
                    'name': column_name,
                    'type': data_type,
                    'nullable': is_nullable,
                    'identity': is_identity
                }
                schema_info[table_name].append(column_info)
            
            cursor.close()
            conn.close()
            return schema_info
        except Exception as e:
            print(f"Error getting schema: {e}")
            return {}

    def mask_sensitive_data(self, data, columns):
        """Mask sensitive data in the results"""
        sensitive_patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
        }
        
        masked_data = []
        for row in data:
            masked_row = list(row)
            for i, col in enumerate(columns):
                if any(pattern in col.lower() for pattern in ['email', 'phone', 'ssn', 'password', 'credit']):
                    masked_row[i] = '********'
            masked_data.append(masked_row)
        
        return masked_data

    def generate_summary(self, query, results):
        """Generate a natural language summary of the query results"""
        if not results or not results.get('results'):
            return "No results found."

        # Convert results to a more readable format
        data_str = str(results['results'][:5])  # Limit to first 5 rows for summary
        
        # Create a more detailed prompt for better insights
        messages = [
            {"role": "system", "content": """You are a data analyst that provides clear, concise summaries of database query results.
            Focus on key insights, patterns, and notable findings.
            Format your response with emojis and bullet points for important insights.
            Include specific numbers and dates when relevant.
            Highlight the most significant findings first."""},
            {"role": "user", "content": f"Query: {query}\nResults: {data_str}\n\nProvide a brief summary of these results, highlighting key insights with emojis."}
        ]

        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def export_to_csv(self, results, filename=None):
        """Export results to CSV file"""
        if not results or not results.get('results'):
            return "No results to export."

        if filename is None:
            filename = f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        try:
            df = pd.DataFrame(results['results'], columns=results['columns'])
            df.to_csv(filename, index=False)
            return f"Results exported to {filename}"
        except Exception as e:
            return f"Error exporting to CSV: {str(e)}"

    def natural_language_to_sql(self, query):
        """Convert natural language query to SQL using Azure OpenAI"""
        schema_info = self.get_database_schema()
        
        # Create a prompt that includes the database schema
        schema_prompt = "Database Schema:\n"
        for table, columns in schema_info.items():
            schema_prompt += f"\nTable: {table}\n"
            for col in columns:
                schema_prompt += f"- {col['name']} ({col['type']})"
                if col['nullable']:
                    schema_prompt += " [nullable]"
                if col['identity']:
                    schema_prompt += " [identity]"
                schema_prompt += "\n"

        # Add conversation context if available
        context = ""
        if self.conversation_history:
            context = "\nPrevious conversation context:\n" + "\n".join(self.conversation_history[-3:])
            
            # Add specific context for grouping queries
            if any(word in query.lower() for word in ['group', 'by department', 'per department']):
                context += "\n\nFor grouping queries, include:\n"
                context += "1. COUNT of employees\n"
                context += "2. AVG salary\n"
                context += "3. MIN and MAX salary\n"
                context += "4. Total employees per department\n"
                context += "Example: SELECT department, COUNT(*) as employee_count, AVG(salary) as avg_salary, MIN(salary) as min_salary, MAX(salary) as max_salary FROM employees GROUP BY department"

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
            3. Format the output as a single SQL query
            4. Always use proper SQL Server syntax for Azure SQL Database
            5. Example correct syntax:
               - SELECT DISTINCT [column_name] FROM [table_name]
               - SELECT DISTINCT TOP 10 [column_name] FROM [table_name]
               - SELECT DISTINCT [column_name] FROM [table_name] WHERE [column_name] = 'value'
               - For grouping: SELECT [department], COUNT(*) as employee_count, AVG([salary]) as avg_salary FROM [employees] GROUP BY [department]
            6. DO NOT include any markdown formatting or code block markers
            7. Ensure proper security by:
               - Using parameterized queries where possible
               - Avoiding SQL injection vulnerabilities
               - Limiting result sets to reasonable sizes
            8. Always use DISTINCT to prevent duplicate rows
            9. For grouping queries, always include:
               - COUNT of records
               - AVG of numeric columns
               - MIN and MAX of numeric columns
            {context}
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
            
            # Ensure DISTINCT is used
            if "SELECT" in sql_query.upper() and "DISTINCT" not in sql_query.upper():
                sql_query = sql_query.replace("SELECT", "SELECT DISTINCT", 1)
            
            # Add error handling
            if "BEGIN TRY" not in sql_query.upper():
                sql_query = f"""BEGIN TRY
    {sql_query}
END TRY
BEGIN CATCH
    SELECT ERROR_NUMBER() AS ErrorNumber, ERROR_MESSAGE() AS ErrorMessage;
END CATCH"""
            
            # Debug: Print the generated SQL query
            print("\nDebug - Generated SQL Query:")
            print(sql_query)
            
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
            
            # Mask sensitive data
            masked_results = self.mask_sensitive_data(results, columns)
            
            return {
                "columns": columns,
                "results": masked_results
            }
        except Exception as e:
            print(f"\nDebug - SQL Error: {str(e)}")
            return {
                "error": str(e)
            }

    def format_results(self, results, show_sql=False):
        """Format the results in a readable way"""
        if not results or not results.get('results'):
            return "No results found."

        # Convert to pandas DataFrame for better formatting
        df = pd.DataFrame(results['results'], columns=results['columns'])
        
        # Format the output
        output = []
        
        if show_sql and self.last_sql_query:
            output.append("\nGenerated SQL Query:")
            output.append("=" * 80)
            output.append(self.last_sql_query)
            output.append("=" * 80)
        
        output.append("\nResults:")
        output.append("=" * 80)
        output.append(df.to_string(index=False))
        output.append("=" * 80)
        output.append(f"\nTotal rows: {len(df)}")
        
        return "\n".join(output)

    def chat(self, user_query):
        """Main chat function that processes user queries"""
        # Add query to history
        self.query_history.append(user_query)
        
        # Check for context-based queries
        if self.last_query_results and any(word in user_query.lower() for word in ['group', 'sort', 'filter', 'where']):
            # Add context to the query
            if 'group' in user_query.lower():
                user_query = f"Show me the department-wise summary of employees including count, average salary, and salary range"
            elif 'sort' in user_query.lower():
                user_query = f"Sort the previous results by {user_query.split('by')[-1].strip()}"
            elif 'filter' in user_query.lower() or 'where' in user_query.lower():
                user_query = f"Filter the previous results where {user_query.split('where')[-1].strip()}"
        
        # Convert natural language to SQL
        sql_query = self.natural_language_to_sql(user_query)
        self.last_sql_query = sql_query
        
        if sql_query.startswith("Error"):
            return {
                "error": sql_query,
                "sql_query": None,
                "results": None,
                "summary": None
            }
        
        # Execute the SQL query
        results = self.execute_query(sql_query)
        self.last_query_results = results
        
        if "error" in results:
            return {
                "error": results["error"],
                "sql_query": sql_query,
                "results": None,
                "summary": None
            }
        
        # Generate summary
        summary = self.generate_summary(user_query, results)
        
        # Add to conversation history
        self.conversation_history.append(f"User: {user_query}")
        self.conversation_history.append(f"Assistant: {summary}")
        
        return {
            "error": None,
            "sql_query": sql_query,
            "results": results,
            "summary": summary
        }

def main():
    try:
        chatbot = DatabaseChatbot()
        print("Welcome to the Database Chatbot!")
        print("Type 'exit' to quit")
        print("Type 'help' for available commands")
        
        show_sql = False  # Flag to control SQL display
        
        while True:
            try:
                user_input = input("\nEnter your question: ")
                
                if user_input.lower() == 'exit':
                    print("\nThank you for using the Database Chatbot. Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("- exit: Quit the chatbot")
                    print("- help: Show this help message")
                    print("- history: Show query history")
                    print("- sql: Toggle SQL query display")
                    print("- export: Export last results to CSV")
                    print("\nExample queries:")
                    print("- Show me all employees")
                    print("- What are the top 5 highest paid employees?")
                    print("- How many employees are in each department?")
                    print("- Group the results by department")
                    continue
                elif user_input.lower() == 'history':
                    print("\nQuery History:")
                    for i, query in enumerate(chatbot.query_history, 1):
                        print(f"{i}. {query}")
                    continue
                elif user_input.lower() == 'sql':
                    show_sql = not show_sql
                    print(f"\nSQL display {'enabled' if show_sql else 'disabled'}")
                    continue
                elif user_input.lower() == 'export':
                    if chatbot.last_query_results:
                        result = chatbot.export_to_csv(chatbot.last_query_results)
                        print(f"\n{result}")
                    else:
                        print("\nNo results to export")
                    continue
                    
                response = chatbot.chat(user_input)
                
                if response["error"]:
                    print(f"\nError: {response['error']}")
                else:
                    print(chatbot.format_results(response["results"], show_sql))
                    
                    print("\nSummary:")
                    print(response["summary"])
            
            except KeyboardInterrupt:
                print("\n\nTo exit the chatbot, please type 'exit'")
                continue
            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")
                continue
    
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
    finally:
        print("\nThank you for using the Database Chatbot. Goodbye!")

if __name__ == "__main__":
    main() 