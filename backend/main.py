from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd
from io import StringIO
import json
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import urllib.parse
from datetime import datetime
import warnings
import time
from openai import AzureOpenAI
import math
import numpy as np
from db_chatbot import DatabaseChatbot
import uvicorn
import httpx

# Load environment variables
load_dotenv()

app = FastAPI(title="Database Chatbot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Create SQLAlchemy engine
connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(AZURE_SQL_CONNECTION_STRING)}"
engine = create_engine(connection_url)

# Initialize chatbot
chatbot = DatabaseChatbot()

# Models
class QueryRequest(BaseModel):
    query: str

class ConnectionRequest(BaseModel):
    server: str
    database: str
    username: str
    password: str

class QueryResponse(BaseModel):
    sql: str
    results: Any
    analysis: str

# Helper functions
def get_schema_info() -> str:
    """Get database schema information."""
    try:
        with engine.connect() as conn:
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

def generate_sql_query(query: str) -> str:
    """Generate SQL query from natural language using Azure OpenAI."""
    max_retries = 3
    retry_delay = 60  # seconds
    
    for attempt in range(max_retries):
        try:
            # Create a prompt that includes schema information and specific rules
            prompt = f"""Given the following user query, generate a SQL query for Azure SQL Database.
            Follow these rules:
            1. Use square brackets for identifiers
            2. Use DISTINCT to avoid duplicates
            3. Include error handling with BEGIN TRY/END TRY
            4. Do not include backticks or markdown formatting
            5. Use proper SQL Server syntax

            Database Schema:
            {get_schema_info()}

            User Query: {query}

            Generate only the SQL query without any additional text or formatting."""

            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
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

def sanitize(obj):
    """Recursively sanitize objects to be JSON serializable."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize(item) for item in obj]
    elif pd.isna(obj):  # Handle pandas NA values
        return None
    return obj

def analyze_data(df: pd.DataFrame) -> str:
    """Analyze the data and provide insights."""
    try:
        # Basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            stats = df[numeric_cols].describe()
            analysis = "Basic Statistics:\n"
            for col in numeric_cols:
                analysis += f"\n{col}:\n"
                # Handle NaN values in statistics
                mean_val = stats[col]['mean']
                min_val = stats[col]['min']
                max_val = stats[col]['max']
                
                analysis += f"  Mean: {mean_val if pd.notnull(mean_val) else 'N/A'}\n"
                analysis += f"  Min: {min_val if pd.notnull(min_val) else 'N/A'}\n"
                analysis += f"  Max: {max_val if pd.notnull(max_val) else 'N/A'}\n"
        else:
            analysis = "No numeric columns found for statistical analysis.\n"
        
        # Row count
        analysis += f"\nTotal rows: {len(df)}"
        
        return analysis
    except Exception as e:
        return f"Error analyzing data: {str(e)}"

# Routes
@app.get("/schema")
async def get_schema():
    """Get database schema information."""
    try:
        schema_info = get_schema_info()
        return {"schema": schema_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process natural language query and return SQL results and analysis."""
    try:
        # Process the query using the chatbot
        sql_query = chatbot.generate_sql_query(request.query)
        results = chatbot.execute_query(sql_query)
        
        if results is None or results.empty:
            raise HTTPException(status_code=404, detail="No results found")
        
        # Generate analysis
        analysis = chatbot.analyze_data(results)
        
        return QueryResponse(
            sql=sql_query,
            results=results.to_dict('records'),
            analysis=analysis
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/connect")
async def connect_database(request: ConnectionRequest):
    """Connect to a database."""
    try:
        # Create connection string
        connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={request.server};DATABASE={request.database};UID={request.username};PWD={request.password}"
        
        # Test connection
        test_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}")
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # If successful, update the global engine
        global engine
        engine = test_engine
        
        # Get schema info
        schema_info = get_schema_info()
        
        return {
            "message": "Successfully connected to database",
            "schema": schema_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sample/{table_name}")
async def get_sample_data(table_name: str):
    """Get sample data from a table."""
    try:
        with engine.connect() as conn:
            query = f"SELECT TOP 10 * FROM [{table_name}]"
            results_df = pd.read_sql(query, conn)
            return {"sample": results_df.to_dict(orient='records')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/{format}")
async def export_data(format: str):
    """Export the last query results in the specified format."""
    try:
        # Get the last query results
        last_results = chatbot.get_last_results()
        if not last_results:
            raise HTTPException(status_code=404, detail="No results available for export")
        
        # Export based on format
        if format == 'csv':
            return Response(
                content=last_results.to_csv(index=False),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=query-results.csv"}
            )
        elif format == 'json':
            return Response(
                content=last_results.to_json(orient='records'),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=query-results.json"}
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 