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
from datetime import datetime, timedelta
import warnings
import time
from openai import AzureOpenAI
import math
import numpy as np
from db_chatbot import DatabaseChatbot
import uvicorn
import httpx
import io
import sqlite3

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
class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    query: str
    context: Optional[List[Message]] = []

class ConnectionRequest(BaseModel):
    server: str
    database: str
    username: str
    password: str

class QueryResponse(BaseModel):
    sql: str
    results: Any
    analysis: str

class ExportRequest(BaseModel):
    data: List[Dict[str, Any]]
    format: str

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

def generate_suggestions(query: str, results: List[Dict[str, Any]]) -> List[str]:
    """Generate relevant follow-up questions based on the current query and results."""
    try:
        prompt = f"""
        Based on the following query and its results, generate 3-4 relevant follow-up questions.
        The questions should be natural and help explore the data further.

        Query: {query}
        Results: {json.dumps(results, indent=2)}

        Generate follow-up questions that:
        1. Explore related data
        2. Ask for more specific details
        3. Request different analysis or visualization
        4. Compare or contrast with other data

        Return only the questions as a JSON array of strings.
        """

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful database assistant that generates relevant follow-up questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )

        try:
            suggestions = json.loads(response.choices[0].message.content)
            if not isinstance(suggestions, list):
                suggestions = [suggestions]
            return suggestions
        except json.JSONDecodeError:
            content = response.choices[0].message.content.strip()
            suggestions = [line.strip() for line in content.split('\n') if line.strip()]
            return suggestions

    except Exception as e:
        print(f"Error generating suggestions: {str(e)}")
        return []

def get_employee_data():
    """Get the sample employee data."""
    return [
        {
            "id": 1,
            "name": "John Doe",
            "department": "Finance",
            "salary": 75000,
            "hire_date": "2020-01-15",
            "position": "Senior Financial Analyst",
            "years_experience": 8,
            "education": "MBA",
            "performance_rating": 4.5
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "department": "Human Resources",
            "salary": 65000,
            "hire_date": "2019-05-20",
            "position": "HR Manager",
            "years_experience": 6,
            "education": "Master's in HR",
            "performance_rating": 4.8
        },
        {
            "id": 3,
            "name": "Alice Johnson",
            "department": "IT",
            "salary": 85000,
            "hire_date": "2021-03-10",
            "position": "Senior Developer",
            "years_experience": 10,
            "education": "MS in Computer Science",
            "performance_rating": 4.7
        },
        {
            "id": 4,
            "name": "Bob Brown",
            "department": "Marketing",
            "salary": 70000,
            "hire_date": "2020-11-05",
            "position": "Marketing Specialist",
            "years_experience": 5,
            "education": "Bachelor's in Marketing",
            "performance_rating": 4.2
        },
        {
            "id": 5,
            "name": "Carol White",
            "department": "Finance",
            "salary": 78000,
            "hire_date": "2019-08-15",
            "position": "Financial Controller",
            "years_experience": 12,
            "education": "CPA",
            "performance_rating": 4.9
        }
    ]

def get_database():
    """Get the expanded sample database."""
    # Departments
    departments = [
        {"id": 1, "name": "Finance", "budget": 1500000, "location": "Floor 1", "manager_id": 1},
        {"id": 2, "name": "Human Resources", "budget": 800000, "location": "Floor 2", "manager_id": 2},
        {"id": 3, "name": "IT", "budget": 2000000, "location": "Floor 3", "manager_id": 3},
        {"id": 4, "name": "Marketing", "budget": 1200000, "location": "Floor 1", "manager_id": 4},
        {"id": 5, "name": "Sales", "budget": 2500000, "location": "Floor 4", "manager_id": 5},
        {"id": 6, "name": "Research", "budget": 1800000, "location": "Floor 5", "manager_id": 6}
    ]

    # Employees
    employees = [
        {
            "id": 1,
            "name": "John Doe",
            "department_id": 1,
            "position": "Senior Financial Analyst",
            "salary": 75000,
            "hire_date": "2020-01-15",
            "years_experience": 8,
            "education": "MBA",
            "performance_rating": 4.5,
            "manager_id": None,
            "email": "john.doe@company.com",
            "phone": "555-0101"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "department_id": 2,
            "position": "HR Manager",
            "salary": 65000,
            "hire_date": "2019-05-20",
            "years_experience": 6,
            "education": "Master's in HR",
            "performance_rating": 4.8,
            "manager_id": None,
            "email": "jane.smith@company.com",
            "phone": "555-0102"
        },
        {
            "id": 3,
            "name": "Alice Johnson",
            "department_id": 3,
            "position": "Senior Developer",
            "salary": 85000,
            "hire_date": "2021-03-10",
            "years_experience": 10,
            "education": "MS in Computer Science",
            "performance_rating": 4.7,
            "manager_id": None,
            "email": "alice.johnson@company.com",
            "phone": "555-0103"
        },
        {
            "id": 4,
            "name": "Bob Brown",
            "department_id": 4,
            "position": "Marketing Specialist",
            "salary": 70000,
            "hire_date": "2020-11-05",
            "years_experience": 5,
            "education": "Bachelor's in Marketing",
            "performance_rating": 4.2,
            "manager_id": None,
            "email": "bob.brown@company.com",
            "phone": "555-0104"
        },
        {
            "id": 5,
            "name": "Carol White",
            "department_id": 1,
            "position": "Financial Controller",
            "salary": 78000,
            "hire_date": "2019-08-15",
            "years_experience": 12,
            "education": "CPA",
            "performance_rating": 4.9,
            "manager_id": 1,
            "email": "carol.white@company.com",
            "phone": "555-0105"
        },
        {
            "id": 6,
            "name": "David Wilson",
            "department_id": 5,
            "position": "Sales Manager",
            "salary": 95000,
            "hire_date": "2018-06-01",
            "years_experience": 15,
            "education": "MBA",
            "performance_rating": 4.6,
            "manager_id": None,
            "email": "david.wilson@company.com",
            "phone": "555-0106"
        },
        {
            "id": 7,
            "name": "Eva Martinez",
            "department_id": 6,
            "position": "Research Scientist",
            "salary": 82000,
            "hire_date": "2022-01-10",
            "years_experience": 7,
            "education": "PhD in Physics",
            "performance_rating": 4.4,
            "manager_id": 6,
            "email": "eva.martinez@company.com",
            "phone": "555-0107"
        }
    ]

    # Projects
    projects = [
        {
            "id": 1,
            "name": "Digital Transformation",
            "department_id": 3,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "budget": 500000,
            "status": "In Progress",
            "manager_id": 3
        },
        {
            "id": 2,
            "name": "Employee Wellness Program",
            "department_id": 2,
            "start_date": "2023-03-01",
            "end_date": "2023-08-31",
            "budget": 100000,
            "status": "Planning",
            "manager_id": 2
        },
        {
            "id": 3,
            "name": "Market Expansion",
            "department_id": 4,
            "start_date": "2023-02-01",
            "end_date": "2024-01-31",
            "budget": 750000,
            "status": "In Progress",
            "manager_id": 4
        }
    ]

    # Project Assignments
    project_assignments = [
        {"id": 1, "project_id": 1, "employee_id": 3, "role": "Lead Developer", "hours_per_week": 30},
        {"id": 2, "project_id": 1, "employee_id": 7, "role": "Technical Consultant", "hours_per_week": 20},
        {"id": 3, "project_id": 2, "employee_id": 2, "role": "Project Manager", "hours_per_week": 25},
        {"id": 4, "project_id": 3, "employee_id": 4, "role": "Marketing Lead", "hours_per_week": 35}
    ]

    # Training Programs
    training_programs = [
        {
            "id": 1,
            "name": "Leadership Development",
            "type": "Management",
            "duration_weeks": 12,
            "cost_per_participant": 5000,
            "start_date": "2023-04-01",
            "end_date": "2023-06-30"
        },
        {
            "id": 2,
            "name": "Technical Skills Enhancement",
            "type": "Technical",
            "duration_weeks": 8,
            "cost_per_participant": 3000,
            "start_date": "2023-05-01",
            "end_date": "2023-06-30"
        }
    ]

    # Training Participants
    training_participants = [
        {"id": 1, "training_id": 1, "employee_id": 5, "completion_status": "In Progress", "score": None},
        {"id": 2, "training_id": 1, "employee_id": 6, "completion_status": "Completed", "score": 95},
        {"id": 3, "training_id": 2, "employee_id": 3, "completion_status": "Completed", "score": 98},
        {"id": 4, "training_id": 2, "employee_id": 7, "completion_status": "In Progress", "score": None}
    ]

    return {
        "departments": departments,
        "employees": employees,
        "projects": projects,
        "project_assignments": project_assignments,
        "training_programs": training_programs,
        "training_participants": training_participants
    }

def format_response(query: str) -> Dict[str, Any]:
    query = query.lower()
    db = get_database()

    # Helper: map department_id to name
    dept_id_to_name = {d['id']: d['name'] for d in db['departments']}
    employees_with_dept = []
    for emp in db['employees']:
        emp_copy = emp.copy()
        emp_copy['department'] = dept_id_to_name.get(emp['department_id'], 'Unknown')
        employees_with_dept.append(emp_copy)

    # Synonym/keyword sets for robust detection
    department_keywords = ["department", "departments", "division", "divisions", "unit", "units"]
    employee_keywords = ["employee", "employees", "staff", "personnel", "worker", "workers", "people"]
    salary_keywords = ["salary", "salaries", "pay", "compensation", "wage", "wages", "income"]
    performance_keywords = ["performance", "rating", "ratings", "score", "scores", "review", "reviews"]
    experience_keywords = ["experience", "years", "tenure", "seniority"]
    education_keywords = ["education", "degree", "degrees", "qualification", "qualifications", "mba", "phd", "master", "bachelor"]
    project_keywords = ["project", "projects", "initiative", "initiatives", "assignment", "assignments"]
    training_keywords = ["training", "trainings", "course", "courses", "program", "programs", "learning", "development"]
    budget_keywords = ["budget", "budgets", "funding", "allocation", "allocations"]
    status_keywords = ["status", "statuses", "state", "states", "progress"]
    participant_keywords = ["participant", "participants", "attendee", "attendees", "enrollment", "enrollments"]

    def contains_any(keywords):
        return any(word in query for word in keywords)

    response = ""
    results = []
    visualization_type = None

    # Special case: average salary by department
    if ("average salary" in query or "avg salary" in query) and contains_any(department_keywords):
        # Calculate average salary per department
        dept_salaries = {}
        for emp in employees_with_dept:
            dept = emp['department']
            dept_salaries.setdefault(dept, []).append(emp['salary'])
        avg_salaries = [
            {"department": dept, "average_salary": round(sum(sals)/len(sals), 2)}
            for dept, sals in dept_salaries.items()
        ]
        # Find the highest
        if avg_salaries:
            max_avg = max(avg_salaries, key=lambda x: x['average_salary'])['average_salary']
            top_departments = [d for d in avg_salaries if d['average_salary'] == max_avg]
            if len(top_departments) == 1:
                response = f"The highest average salary is in the {top_departments[0]['department']} department (${max_avg:,.2f})."
            else:
                names = ', '.join(d['department'] for d in top_departments)
                response = f"The highest average salary (${max_avg:,.2f}) is shared by these departments: {names}."
        else:
            response = "No salary data available."
        results = sorted(avg_salaries, key=lambda x: x['average_salary'], reverse=True)
        visualization_type = "salary"
    # --- original logic follows ---
    elif contains_any(department_keywords):
        if contains_any(budget_keywords):
            results = sorted(db["departments"], key=lambda x: x["budget"], reverse=True)
            response = "Departments sorted by budget (highest to lowest):"
            visualization_type = "budget"
        else:
            dept_counts = {}
            for emp in employees_with_dept:
                dept_name = emp["department"]
                dept_counts[dept_name] = dept_counts.get(dept_name, 0) + 1
            results = [{"department": dept, "count": count} for dept, count in dept_counts.items()]
            response = "Department-wise employee distribution:"
            visualization_type = "department"
    elif contains_any(employee_keywords):
        if contains_any(salary_keywords):
            if "highest" in query:
                results = sorted(employees_with_dept, key=lambda x: x["salary"], reverse=True)[:3]
                response = "Top 3 highest paid employees:"
            elif "lowest" in query:
                results = sorted(employees_with_dept, key=lambda x: x["salary"])[:3]
                response = "Top 3 lowest paid employees:"
            else:
                results = sorted(employees_with_dept, key=lambda x: x["salary"], reverse=True)
                response = "All employees sorted by salary:"
            visualization_type = "salary"
        elif contains_any(performance_keywords):
            if "highest" in query:
                results = sorted(employees_with_dept, key=lambda x: x["performance_rating"], reverse=True)[:3]
                response = "Top 3 highest performing employees:"
            else:
                results = sorted(employees_with_dept, key=lambda x: x["performance_rating"], reverse=True)
                response = "All employees sorted by performance rating:"
            visualization_type = "performance"
        elif contains_any(experience_keywords):
            if "most" in query:
                results = sorted(employees_with_dept, key=lambda x: x["years_experience"], reverse=True)[:3]
                response = "Top 3 most experienced employees:"
            else:
                results = sorted(employees_with_dept, key=lambda x: x["years_experience"], reverse=True)
                response = "All employees sorted by years of experience:"
            visualization_type = "experience"
        elif contains_any(education_keywords):
            if "mba" in query:
                results = [emp for emp in employees_with_dept if "mba" in emp["education"].lower()]
                response = f"Found {len(results)} employees with MBA:"
            elif "phd" in query:
                results = [emp for emp in employees_with_dept if "phd" in emp["education"].lower()]
                response = f"Found {len(results)} employees with PhD:"
            elif "master" in query:
                results = [emp for emp in employees_with_dept if "master" in emp["education"].lower()]
                response = f"Found {len(results)} employees with Master's degrees:"
            elif "bachelor" in query:
                results = [emp for emp in employees_with_dept if "bachelor" in emp["education"].lower()]
                response = f"Found {len(results)} employees with Bachelor's degrees:"
            else:
                results = employees_with_dept
                response = "All employees with their education details:"
            visualization_type = "education"
        else:
            results = employees_with_dept
            response = "All employees:"
            visualization_type = "department"
    elif contains_any(project_keywords):
        if contains_any(budget_keywords):
            results = sorted(db["projects"], key=lambda x: x["budget"], reverse=True)
            response = "Projects sorted by budget:"
            visualization_type = "budget"
        elif contains_any(status_keywords):
            status_counts = {}
            for project in db["projects"]:
                status_counts[project["status"]] = status_counts.get(project["status"], 0) + 1
            results = [{"status": status, "count": count} for status, count in status_counts.items()]
            response = "Project status distribution:"
            visualization_type = "status"
        else:
            results = db["projects"]
            response = "All projects:"
            visualization_type = "project"
    elif contains_any(training_keywords):
        if contains_any(budget_keywords) or contains_any(["cost"]):
            results = sorted(db["training_programs"], key=lambda x: x["cost_per_participant"], reverse=True)
            response = "Training programs sorted by cost:"
            visualization_type = "cost"
        elif contains_any(participant_keywords):
            results = []
            for program in db["training_programs"]:
                participants = [p for p in db["training_participants"] if p["training_id"] == program["id"]]
                results.append({
                    "program": program["name"],
                    "participants": len(participants),
                    "completed": len([p for p in participants if p["completion_status"] == "Completed"])
                })
            response = "Training program participation:"
            visualization_type = "participation"
        else:
            results = db["training_programs"]
            response = "All training programs:"
            visualization_type = "training"
    else:
        results = employees_with_dept
        response = "All employees:"
        visualization_type = "department"

    # Generate suggestions based on the query type
    suggestions = []
    if ("average salary" in query or "avg salary" in query) and contains_any(department_keywords):
        suggestions = [
            "Show highest paid employees",
            "Show department budgets",
            "Show department distribution"
        ]
    elif contains_any(department_keywords):
        suggestions = [
            "Show departments by budget",
            "Show department locations",
            "Show employee distribution by department"
        ]
    elif contains_any(employee_keywords):
        suggestions = [
            "Show highest paid employees",
            "Show performance ratings",
            "Show experience levels",
            "Show education distribution"
        ]
    elif contains_any(project_keywords):
        suggestions = [
            "Show projects by budget",
            "Show project status",
            "Show project timelines"
        ]
    elif contains_any(training_keywords):
        suggestions = [
            "Show training programs by cost",
            "Show training participation",
            "Show completion rates"
        ]
    else:
        suggestions = [
            "Show department distribution",
            "Show employee salaries",
            "Show project status",
            "Show training programs"
        ]

    return {
        "response": response,
        "results": results,
        "suggestions": suggestions,
        "visualizationType": visualization_type
    }

# Routes
@app.get("/schema")
async def get_schema():
    """Get database schema information."""
    try:
        schema_info = get_schema_info()
        return {"schema": schema_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def execute_query(request: QueryRequest):
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Format the response based on the query
        response_data = format_response(request.query)
        
        # Generate suggestions based on the query and results
        suggestions = generate_suggestions(request.query, response_data["results"])

        return {
            "response": response_data["response"],
            "results": response_data["results"],
            "suggestions": suggestions,
            "visualizationType": response_data["visualizationType"]
        }

    except Exception as e:
        print(f"Error in execute_query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your query: {str(e)}"
        )

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

@app.post("/api/export")
async def export_data(request: ExportRequest):
    try:
        df = pd.DataFrame(request.data)
        
        if request.format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=export.csv"}
            )
        
        elif request.format == "xlsx":
            output = io.BytesIO()
            df.to_excel(output, index=False)
            return Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=export.xlsx"}
            )
        
        elif request.format == "json":
            return Response(
                content=json.dumps(request.data),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=export.json"}
            )
        
        elif request.format == "sql":
            # Generate SQL insert statements
            sql_output = []
            for row in request.data:
                columns = ", ".join(row.keys())
                values = ", ".join([f"'{str(v)}'" for v in row.values()])
                sql_output.append(f"INSERT INTO table_name ({columns}) VALUES ({values});")
            
            return Response(
                content="\n".join(sql_output),
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename=export.sql"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
    
    except Exception as e:
        print(f"Error in export_data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while exporting data: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 