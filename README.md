# Database Chatbot

A powerful chatbot interface that allows users to query databases using natural language. Built with React, FastAPI, and Azure OpenAI.

## Features

### Core Features
- 🧠 Natural Language to SQL Conversion
  - Input box for plain language queries
  - Azure OpenAI-powered query-to-SQL conversion
  - Real-time execution on Azure SQL Database
  - Human-readable results display
  - Shows original query, generated SQL, and results

- 💬 Conversational Follow-up
  - Maintains context of previous queries
  - Supports drill-down and refinement
  - Chat-like interface for multi-turn interaction

- 📊 Dataset Awareness
  - Schema preview
  - Preset query buttons
  - Export functionality (CSV, Excel, JSON)

### Security Features
- SQL Injection Prevention
- Sensitive Data Masking
- Azure Managed Identity Support
- Environment Variable Configuration

## Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- Azure SQL Database
- Azure OpenAI Service

### Backend Setup
1. Create a `.env` file in the root directory with the following variables:
   ```
   AZURE_SQL_CONNECTION_STRING=your_connection_string
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_VERSION=2024-02-15-preview
   AZURE_OPENAI_DEPLOYMENT=your_deployment_name
   AZURE_OPENAI_ENDPOINT=your_endpoint
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the FastAPI backend:
   ```bash
   python backend.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## Usage

1. Open your browser to `http://localhost:3000`
2. View available tables in the schema section
3. Use preset queries or type your own natural language query
4. View results, generated SQL, and analysis
5. Export results in various formats

## Example Queries

- "Show all employees"
- "Top 5 products by sales"
- "Sales by month"
- "List low-stock products"
- "How many employees joined last year?"
- "Break down sales by department"

## Security Considerations

- All database credentials are stored in environment variables
- SQL queries are validated before execution
- Sensitive data is masked in results
- CORS is configured for security

## Development

### Project Structure
```
.
├── backend.py           # FastAPI backend
├── db_chatbot.py       # Core chatbot logic
├── frontend/           # React frontend
│   ├── src/
│   │   ├── App.js     # Main React component
│   │   └── ...
│   └── package.json
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

### Adding New Features
1. Backend: Add new endpoints in `backend.py`
2. Frontend: Create new components in `frontend/src`
3. Core Logic: Extend `DatabaseChatbot` class in `db_chatbot.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Azure OpenAI Service
- Azure SQL Database
- Python Data Science Stack (pandas, numpy, matplotlib, seaborn) 