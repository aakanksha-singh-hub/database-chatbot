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
from sqlalchemy import create_engine, text
import urllib.parse
import warnings
import time
from advanced_queries import NATURAL_LANGUAGE_EXAMPLES

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
        """Initialize the chatbot with database and OpenAI connections."""
        self.connection_string = connection_string
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        self.deployment_name = deployment_name
        self.chat_memory = ChatMemory()
        
        # Create SQLAlchemy engine
        connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
        self.engine = create_engine(connection_url)
        
        # Test connection
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database Chatbot initialized successfully!\n")
        except Exception as e:
            raise Exception(f"Failed to connect to database: {str(e)}")

    def get_schema_info(self) -> str:
        """Get database schema information."""
        try:
            with self.engine.connect() as conn:
                # Get table information
                tables_query = text("""
                SELECT 
                    t.name AS table_name,
                    c.name AS column_name,
                    ty.name AS data_type,
                    c.max_length,
                    c.precision,
                    c.scale,
                    c.is_nullable
                FROM sys.tables t
                INNER JOIN sys.columns c ON t.object_id = c.object_id
                INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
                ORDER BY t.name, c.column_id;
                """)
                tables_df = pd.read_sql(tables_query, conn)
                
                # Format schema information
                schema_info = []
                for table in tables_df['table_name'].unique():
                    table_cols = tables_df[tables_df['table_name'] == table]
                    cols_info = []
                    for _, row in table_cols.iterrows():
                        col_info = f"{row['column_name']} ({row['data_type']})"
                        if row['is_nullable']:
                            col_info += " NULL"
                        cols_info.append(col_info)
                    schema_info.append(f"Table: {table}\nColumns: {', '.join(cols_info)}")
                
                return "\n\n".join(schema_info)
                
        except Exception as e:
            raise Exception(f"Error getting schema info: {str(e)}")

    def generate_sql_query(self, query: str) -> str:
        """Generate SQL query from natural language using Azure OpenAI."""
        # Check if query matches any predefined advanced queries
        for nl_query, sql_query in NATURAL_LANGUAGE_EXAMPLES.items():
            if nl_query.lower() in query.lower():
                return sql_query

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

                Database Schema:
                {self.get_schema_info()}

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
            return pd.read_sql(text(query), self.engine)
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")

    def process_query(self, query: str) -> str:
        """Process a natural language query and return results."""
        try:
            # Generate SQL query
            sql_query = self.generate_sql_query(query)
            
            # Execute query
            df = self.execute_query(sql_query)
            
            # Add to chat memory
            self.chat_memory.add_message("user", query)
            self.chat_memory.add_message("assistant", f"Query executed successfully. Found {len(df)} results.")
            
            # Analyze data
            analysis = self.analyze_data(df)
            
            # Create visualizations
            viz_message = self.visualize_data(df, query)
            
            # Return results
            return f"Query Results:\n{df}\n\nAnalysis:\n{analysis}\n\n{viz_message}"
            
        except Exception as e:
            error_message = f"Error processing query: {str(e)}"
            self.chat_memory.add_message("assistant", error_message)
            return error_message

    def analyze_data(self, df: pd.DataFrame) -> str:
        """Analyze data and return insights."""
        try:
            analysis = []
            
            # Basic statistics
            analysis.append("Basic Statistics:")
            analysis.append(str(df.describe()))
            
            # Data types and missing values
            analysis.append("\nData Types and Missing Values:")
            for col in df.columns:
                missing = df[col].isnull().sum()
                analysis.append(f"{col}: {df[col].dtype} - {missing} missing values")
            
            # Categorical analysis
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                analysis.append("\nCategorical Column Analysis:")
                for col in categorical_cols:
                    value_counts = df[col].value_counts()
                    analysis.append(f"{col}: {len(value_counts)} unique values")
                    analysis.append("Top 5 values:")
                    analysis.append(str(value_counts.head()))
            
            # Numeric analysis
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                analysis.append("\nNumeric Column Analysis:")
                for col in numeric_cols:
                    skewness = df[col].skew()
                    kurtosis = df[col].kurtosis()
                    analysis.append(f"\n{col}:")
                    analysis.append(f"Skewness: {skewness:.2f} (0 is normal, >0 is right-skewed, <0 is left-skewed)")
                    analysis.append(f"Kurtosis: {kurtosis:.2f} (0 is normal, >0 is heavy-tailed, <0 is light-tailed)")
                    
                    # Outlier detection
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))][col]
                    analysis.append(f"Potential outliers: {len(outliers)} values")
            
            # Correlation analysis
            if len(numeric_cols) > 1:
                correlation_matrix = df[numeric_cols].corr()
                strong_correlations = []
                for i in range(len(numeric_cols)):
                    for j in range(i+1, len(numeric_cols)):
                        corr = correlation_matrix.iloc[i,j]
                        if abs(corr) > 0.5:
                            strong_correlations.append(f"{numeric_cols[i]} and {numeric_cols[j]}: {corr:.2f}")
                
                if strong_correlations:
                    analysis.append("\nStrong Correlations:")
                    analysis.extend(strong_correlations)
                else:
                    analysis.append("\nNo strong correlations found between numeric columns")
            
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
        """Export data in various formats with enhanced metadata."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == 'csv':
                filename = f'query_results_{timestamp}.csv'
                # Add metadata as comments
                with open(filename, 'w') as f:
                    f.write(f"# Generated: {datetime.now()}\n")
                    f.write(f"# Total Rows: {len(df)}\n")
                    f.write(f"# Columns: {', '.join(df.columns)}\n\n")
                df.to_csv(filename, mode='a', index=False)
                return f"Data exported to {filename}"
                
            elif format.lower() == 'sql':
                filename = f'query_results_{timestamp}.sql'
                with open(filename, 'w') as f:
                    f.write(f"-- Generated: {datetime.now()}\n")
                    f.write(f"-- Total Rows: {len(df)}\n")
                    f.write(f"-- Columns: {', '.join(df.columns)}\n\n")
                    f.write("INSERT INTO query_results (")
                    f.write(", ".join(df.columns))
                    f.write(") VALUES\n")
                    
                    for i, row in df.iterrows():
                        values = []
                        for val in row:
                            if pd.isna(val):
                                values.append("NULL")
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            else:
                                values.append(f"'{str(val)}'")
                        f.write("(" + ", ".join(values) + ")")
                        if i < len(df) - 1:
                            f.write(",\n")
                        else:
                            f.write(";\n")
                return f"Data exported to {filename}"
                
            elif format.lower() == 'excel':
                filename = f'query_results_{timestamp}.xlsx'
                with pd.ExcelWriter(filename) as writer:
                    # Main data sheet
                    df.to_excel(writer, sheet_name='Data', index=False)
                    
                    # Summary sheet
                    summary_df = pd.DataFrame({
                        'Metric': ['Total Rows', 'Columns', 'Generated'],
                        'Value': [len(df), len(df.columns), datetime.now()]
                    })
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Statistics sheet for numeric columns
                    if len(df.select_dtypes(include=[np.number]).columns) > 0:
                        df.describe().to_excel(writer, sheet_name='Statistics')
                return f"Data exported to {filename}"
                
            elif format.lower() == 'json':
                filename = f'query_results_{timestamp}.json'
                export_data = {
                    'metadata': {
                        'generated': str(datetime.now()),
                        'total_rows': len(df),
                        'columns': list(df.columns)
                    },
                    'data': df.to_dict(orient='records')
                }
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                return f"Data exported to {filename}"
                
            else:
                return "Unsupported export format. Please use 'csv', 'sql', 'excel', or 'json'."
                
        except Exception as e:
            return f"Error exporting data: {str(e)}"

def main():
    """Main function to run the chatbot."""
    # Load environment variables
    load_dotenv()
    
    # Get Azure credentials from environment variables
    connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    api_version = os.getenv('AZURE_OPENAI_VERSION')
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    
    if not all([connection_string, api_key, api_version, deployment_name, endpoint]):
        raise ValueError("Missing required environment variables")
    
    # Initialize chatbot
    chatbot = DatabaseChatbot(connection_string, api_key, api_version, deployment_name, endpoint)
    
    print("Available commands:")
    print("- 'export <format> <query>': Export results")
    print("  Formats: csv, sql, excel, json")
    print("- 'quit': Exit the program\n")
    
    print("Example queries:")
    print("- show me all employees")
    print("- what are the top 5 highest paid employees?")
    print("- how many employees are in each department?")
    print("- group the results by department")
    print("- show me project performance metrics")
    print("- analyze employee performance and contributions")
    print("- give me department analysis")
    print("- show me time-based trends")
    print("- analyze employee skills")
    print("- show me project success metrics\n")
    
    print("The chatbot will automatically:")
    print("- Generate appropriate SQL queries")
    print("- Provide data analysis and insights")
    print("- Create relevant visualizations")
    print("- Maintain conversation context\n")
    
    # Main interaction loop
    while True:
        query = input("Enter your question (or 'quit' to exit): ").strip()
        
        if query.lower() == 'quit':
            break
            
        if query.lower().startswith('export '):
            parts = query.split(' ', 2)
            if len(parts) == 3:
                format_type = parts[1]
                actual_query = parts[2]
                try:
                    sql_query = chatbot.generate_sql_query(actual_query)
                    df = chatbot.execute_query(sql_query)
                    result = chatbot.export_data(df, format_type)
                    print(result)
                except Exception as e:
                    print(f"Error processing export: {str(e)}")
            else:
                print("Invalid export command. Use: export <format> <query>")
        else:
            result = chatbot.process_query(query)
            print(result)

if __name__ == "__main__":
    main() 