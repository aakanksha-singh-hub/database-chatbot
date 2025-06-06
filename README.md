# Database Chatbot with Azure OpenAI

A natural language interface for querying Azure SQL Database using Azure OpenAI. This project demonstrates how to build a conversational interface that allows users to interact with a database using plain English.

## Features

- Natural language to SQL conversion using Azure OpenAI
- Secure connection to Azure SQL Database
- Automatic schema detection and query generation
- Error handling and result formatting
- Command-line interface for easy interaction

## Prerequisites

- Python 3.8 or higher
- Azure SQL Database
- Azure OpenAI Service
- ODBC Driver 18 for SQL Server

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/database-chatbot.git
cd database-chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your environment:
   - Create a `config.py` file with your Azure OpenAI and database credentials
   - Ensure you have ODBC Driver 18 for SQL Server installed

## Usage

Run the chatbot:
```bash
python db_chatbot.py
```

Example queries:
- "Show me all employees"
- "What are the top 5 highest paid employees?"
- "How many employees are in each department?"

## Security

- Database credentials are stored in `config.py` (not tracked in git)
- Azure OpenAI API key is stored securely
- SQL injection prevention through proper query handling

## Project Structure

- `db_chatbot.py`: Main chatbot implementation
- `config.py`: Configuration and credentials (not tracked in git)
- `requirements.txt`: Python dependencies
- `.gitignore`: Git ignore rules

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 