import os
import pandas as pd
import pyodbc
from openai import AzureOpenAI
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
from typing import List, Dict, Any, Optional
import numpy as np
from io import StringIO
from dotenv import load_dotenv
from sqlalchemy import create_engine
import urllib.parse
import warnings
import time

# Load environment variables from .env file
load_dotenv()

# Database connection settings
AZURE_SQL_CONNECTION_STRING = os.getenv('AZURE_SQL_CONNECTION_STRING')
if not AZURE_SQL_CONNECTION_STRING:
    raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is not set")

# Azure OpenAI settings
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
if not AZURE_OPENAI_API_KEY:
    raise ValueError("AZURE_OPENAI_API_KEY environment variable is not set")

AZURE_OPENAI_VERSION = os.getenv('AZURE_OPENAI_VERSION', '2024-02-15-preview')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')
if not AZURE_OPENAI_DEPLOYMENT:
    raise ValueError("AZURE_OPENAI_DEPLOYMENT environment variable is not set")

AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set")

# Suppress specific FutureWarning
warnings.filterwarnings('ignore', category=FutureWarning, module='seaborn.categorical')

class ChatMemory:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.conversation_history: List[Dict[str, Any]] = []
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        if len(self.conversation_history) > self.max_turns * 2:  # *2 because each turn has user and assistant messages
            self.conversation_history = self.conversation_history[-self.max_turns*2:]
    
    def get_context(self) -> List[Dict[str, Any]]:
        return self.conversation_history
    
    def clear(self):
        self.conversation_history = []

    def get_formatted_history(self) -> str:
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history
        ])

class DatabaseChatbot:
    def __init__(self, connection_string: str, api_key: str, api_version: str, deployment_name: str, endpoint: str):
        self.connection_string = connection_string
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        self.deployment_name = deployment_name
        self.chat_memory = ChatMemory()
        
    def get_schema_info(self) -> str:
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            tables = cursor.fetchall()
            
            schema_info = []
            for table in tables:
                table_name = table[0]
                
                # Get columns for each table
                cursor.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = '{table_name}'
                    ORDER BY ORDINAL_POSITION
                """)
                columns = cursor.fetchall()
                
                # Format column information
                column_info = []
                for col in columns:
                    col_name, data_type, max_length = col
                    if max_length:
                        col_info = f"{col_name} ({data_type}({max_length}))"
                    else:
                        col_info = f"{col_name} ({data_type})"
                    column_info.append(col_info)
                
                # Add table information to schema
                schema_info.append(f"Table: {table_name}")
                schema_info.append("Columns:")
                schema_info.extend([f"  - {col}" for col in column_info])
                schema_info.append("")
            
            return "\n".join(schema_info)
            
        except Exception as e:
            return f"Error getting schema: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()

    def generate_sql_query(self, query: str) -> str:
        """Generate SQL query from natural language using Azure OpenAI."""
        max_retries = 3
        retry_delay = 60  # seconds
        
        for attempt in range(max_retries):
            try:
                # Create a prompt that includes conversation history and specific rules
                prompt = f"""Given the following conversation history and user query, generate a SQL query for Azure SQL Database.
                Follow these rules:
                1. Use square brackets for identifiers
                2. Use DISTINCT to avoid duplicates
                3. Include error handling with BEGIN TRY/END TRY
                4. Do not include backticks or markdown formatting
                5. Use proper SQL Server syntax

                Conversation History:
                {self.chat_memory.get_formatted_history()}

                User Query: {query}

                Generate only the SQL query without any additional text or formatting."""

                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {"role": "system", "content": "You are a SQL expert that generates SQL queries for Azure SQL Database."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )

                # Extract the SQL query from the response
                sql_query = response.choices[0].message.content.strip()
                
                # Remove any markdown formatting or backticks
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                
                # Add error handling
                sql_query = f"""BEGIN TRY
    {sql_query}
END TRY
BEGIN CATCH
    SELECT ERROR_NUMBER() AS ErrorNumber, ERROR_MESSAGE() AS ErrorMessage;
END CATCH"""

                return sql_query

            except Exception as e:
                error_message = str(e)
                if "429" in error_message and attempt < max_retries - 1:
                    print(f"\nRate limit exceeded. Waiting {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(f"Error generating SQL query: {error_message}")

        raise Exception("Failed to generate SQL query after maximum retries")

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame."""
        try:
            # Create SQLAlchemy engine
            params = urllib.parse.parse_qs(self.connection_string)
            connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(self.connection_string)}"
            engine = create_engine(connection_url)
            
            # Execute query using SQLAlchemy
            return pd.read_sql(query, engine)
            
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    def analyze_data(self, df: pd.DataFrame) -> str:
        """Analyze the data and provide comprehensive insights"""
        try:
            analysis = []
            
            # Basic statistics
            analysis.append("Basic Statistics:")
            analysis.append(df.describe().to_string())
            
            # Data types and missing values
            analysis.append("\nData Types and Missing Values:")
            for col in df.columns:
                missing = df[col].isnull().sum()
                dtype = df[col].dtype
                analysis.append(f"{col}: {dtype} - {missing} missing values")
            
            # Unique values for categorical columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                analysis.append("\nCategorical Column Analysis:")
                for col in categorical_cols:
                    unique_vals = df[col].nunique()
                    value_counts = df[col].value_counts().head(5)
                    analysis.append(f"{col}: {unique_vals} unique values")
                    analysis.append("Top 5 values:")
                    analysis.append(value_counts.to_string())
            
            # Numeric column analysis
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) > 0:
                analysis.append("\nNumeric Column Analysis:")
                for col in numeric_cols:
                    # Skewness and kurtosis
                    skew = df[col].skew()
                    kurt = df[col].kurtosis()
                    analysis.append(f"\n{col}:")
                    analysis.append(f"Skewness: {skew:.2f} (0 is normal, >0 is right-skewed, <0 is left-skewed)")
                    analysis.append(f"Kurtosis: {kurt:.2f} (0 is normal, >0 is heavy-tailed, <0 is light-tailed)")
                    
                    # Outliers using IQR method
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))][col]
                    analysis.append(f"Potential outliers: {len(outliers)} values")
            
            # Time series analysis
            date_cols = df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                analysis.append("\nTime Series Analysis:")
                for col in date_cols:
                    analysis.append(f"\n{col}:")
                    analysis.append(f"Date range: {df[col].min()} to {df[col].max()}")
                    analysis.append(f"Total days: {(df[col].max() - df[col].min()).days}")
            
            # Correlation analysis
            if len(numeric_cols) > 1:
                analysis.append("\nCorrelation Analysis:")
                corr_matrix = df[numeric_cols].corr()
                # Find strong correlations
                strong_correlations = []
                for i in range(len(numeric_cols)):
                    for j in range(i+1, len(numeric_cols)):
                        corr = corr_matrix.iloc[i,j]
                        if abs(corr) > 0.5:  # Only show strong correlations
                            strong_correlations.append(f"{numeric_cols[i]} and {numeric_cols[j]}: {corr:.2f}")
                if strong_correlations:
                    analysis.append("Strong correlations found:")
                    analysis.extend(strong_correlations)
                else:
                    analysis.append("No strong correlations found between numeric columns")
            
            return "\n".join(analysis)
            
        except Exception as e:
            return f"Error analyzing data: {str(e)}"

    def visualize_data(self, df: pd.DataFrame, query: str) -> str:
        """Create enhanced visualizations based on data and query."""
        try:
            # Set a valid seaborn style
            sns.set_theme(style="whitegrid")
            
            # Create timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"visualization_{timestamp}"
            
            # Get numeric and categorical columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            date_cols = df.select_dtypes(include=['datetime64']).columns
            
            # Create visualizations directory if it doesn't exist
            os.makedirs('visualizations', exist_ok=True)
            
            # 1. Time Series Analysis
            if len(date_cols) > 0 and len(numeric_cols) > 0:
                for date_col in date_cols:
                    for num_col in numeric_cols:
                        plt.figure(figsize=(12, 6))
                        # Use pandas plot instead of seaborn for time series
                        df.plot(x=date_col, y=num_col, kind='line', ax=plt.gca())
                        plt.title(f'{num_col} Over Time')
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        plt.savefig(f'visualizations/{base_filename}_timeseries_{num_col}.png')
                        plt.close()
            
            # 2. Distribution Analysis
            for col in numeric_cols:
                # Histogram with KDE
                plt.figure(figsize=(10, 6))
                # Use pandas plot instead of seaborn for histogram
                df[col].plot(kind='hist', density=True, bins=30)
                df[col].plot(kind='kde')
                plt.title(f'Distribution of {col}')
                plt.xlabel(col)
                plt.ylabel('Density')
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(f'visualizations/{base_filename}_hist_{col}.png')
                plt.close()
                
                # Box plot
                plt.figure(figsize=(10, 6))
                # Use pandas plot instead of seaborn for box plot
                df.boxplot(column=col)
                plt.title(f'Box Plot of {col}')
                plt.ylabel(col)
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(f'visualizations/{base_filename}_box_{col}.png')
                plt.close()
            
            # 3. Correlation Analysis
            if len(numeric_cols) > 1:
                correlation_matrix = df[numeric_cols].corr()
                plt.figure(figsize=(10, 8))
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
                plt.title('Correlation Matrix')
                plt.tight_layout()
                plt.savefig(f'visualizations/{base_filename}_correlation.png')
                plt.close()
            
            # 4. Categorical Analysis
            for cat_col in categorical_cols:
                # Bar plot
                plt.figure(figsize=(10, 6))
                # Use pandas plot instead of seaborn for bar plot
                df[cat_col].value_counts().plot(kind='bar')
                plt.title(f'Distribution of {cat_col}')
                plt.xlabel(cat_col)
                plt.ylabel('Count')
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(f'visualizations/{base_filename}_bar_{cat_col}.png')
                plt.close()
                
                # If we have numeric columns, create grouped box plots
                if len(numeric_cols) > 0:
                    for num_col in numeric_cols:
                        plt.figure(figsize=(12, 6))
                        # Use pandas plot instead of seaborn for grouped box plot
                        df.boxplot(column=num_col, by=cat_col)
                        plt.title(f'{num_col} by {cat_col}')
                        plt.suptitle('')  # Remove default suptitle
                        plt.grid(True)
                        plt.tight_layout()
                        plt.savefig(f'visualizations/{base_filename}_box_{num_col}_by_{cat_col}.png')
                        plt.close()
            
            return f"Visualizations saved in 'visualizations' directory"
            
        except Exception as e:
            print(f"Error creating visualizations: {str(e)}")
            return "Error creating visualizations"

    def export_data(self, df: pd.DataFrame, format: str = 'csv') -> str:
        """Export data to various formats with enhanced formatting"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == 'csv':
                filename = f"query_results_{timestamp}.csv"
                # Add metadata as comments
                with open(filename, 'w', newline='') as f:
                    f.write(f"# Query Results Export\n")
                    f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Total Rows: {len(df)}\n")
                    f.write(f"# Columns: {', '.join(df.columns)}\n\n")
                    df.to_csv(f, index=False)
                return f"Data exported to {filename}"
                
            elif format.lower() == 'sql':
                filename = f"query_{timestamp}.sql"
                with open(filename, 'w') as f:
                    f.write("-- Generated SQL Query\n")
                    f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"-- Total Rows: {len(df)}\n")
                    f.write(f"-- Columns: {', '.join(df.columns)}\n\n")
                    f.write(query)
                return f"SQL query exported to {filename}"
                
            elif format.lower() == 'excel':
                filename = f"query_results_{timestamp}.xlsx"
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    # Main data sheet
                    df.to_excel(writer, sheet_name='Data', index=False)
                    
                    # Summary sheet
                    summary_df = pd.DataFrame({
                        'Metric': ['Total Rows', 'Columns', 'Generated At'],
                        'Value': [
                            len(df),
                            ', '.join(df.columns),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ]
                    })
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Statistics sheet for numeric columns
                    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                    if len(numeric_cols) > 0:
                        stats_df = df[numeric_cols].describe()
                        stats_df.to_excel(writer, sheet_name='Statistics')
                return f"Data exported to {filename}"
                
            elif format.lower() == 'json':
                filename = f"query_results_{timestamp}.json"
                # Convert DataFrame to dict with metadata
                export_data = {
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "total_rows": len(df),
                        "columns": list(df.columns)
                    },
                    "data": df.to_dict(orient='records')
                }
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                return f"Data exported to {filename}"
                
            else:
                return "Unsupported export format. Please use 'csv', 'sql', 'excel', or 'json'."
                
        except Exception as e:
            return f"Error exporting data: {str(e)}"

    def process_query(self, user_input: str, export_format: Optional[str] = None) -> str:
        """Process user query with improved error handling and context management"""
        try:
            # Add user message to chat memory
            self.chat_memory.add_message("user", user_input)
            
            # Generate and execute query
            query = self.generate_sql_query(user_input)
            df = self.execute_query(query)
            
            if df.empty:
                response = "No data found for your query."
            else:
                # Generate analysis and visualization
                analysis = self.analyze_data(df)
                visualization = self.visualize_data(df, query)
                
                # Format response with query context
                response = f"Query Results:\n{df.to_string()}\n\nAnalysis:\n{analysis}"
                if visualization:
                    response += f"\n\nVisualization saved as: {visualization}"
                
                # Export if requested
                if export_format:
                    export_result = self.export_data(df, export_format)
                    response += f"\n\n{export_result}"
            
            # Add assistant response to chat memory with metadata
            self.chat_memory.add_message("assistant", response, {
                "query": query,
                "row_count": len(df),
                "columns": list(df.columns),
                "has_visualization": bool(visualization),
                "export_format": export_format
            })
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            self.chat_memory.add_message("assistant", error_msg, {"error": str(e)})
            return error_msg

def main():
    try:
        # Initialize the chatbot
        chatbot = DatabaseChatbot(
            connection_string=AZURE_SQL_CONNECTION_STRING,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_VERSION,
            deployment_name=AZURE_OPENAI_DEPLOYMENT,
            endpoint=AZURE_OPENAI_ENDPOINT
        )
        
        print("Database Chatbot initialized successfully!")
        print("\nAvailable commands:")
        print("- 'export <format> <query>': Export results")
        print("  Formats: csv, sql, excel, json")
        print("- 'quit': Exit the program")
        print("\nExample queries:")
        print("- show me all employees")
        print("- what are the top 5 highest paid employees?")
        print("- how many employees are in each department?")
        print("- group the results by department")
        print("\nThe chatbot will automatically:")
        print("- Generate appropriate SQL queries")
        print("- Provide data analysis and insights")
        print("- Create relevant visualizations")
        print("- Maintain conversation context")
        
        while True:
            try:
                user_input = input("\nEnter your question (or 'quit' to exit): ")
                
                if user_input.lower() == 'quit':
                    break
                
                # Handle export command
                export_format = None
                if user_input.lower().startswith('export '):
                    parts = user_input.split()
                    if len(parts) > 1:
                        export_format = parts[1].lower()
                        user_input = ' '.join(parts[2:])
                
                response = chatbot.process_query(user_input, export_format)
                print("\n" + response)
            
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                continue
            
            except Exception as e:
                print(f"\nError: {str(e)}")
                continue
    
    except Exception as e:
        print(f"Error initializing chatbot: {str(e)}")

if __name__ == "__main__":
    main() 