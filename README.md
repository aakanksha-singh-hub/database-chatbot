# Database Chatbot

A natural language to SQL chatbot that allows users to query Azure SQL Database using conversational language. The chatbot provides data analysis, visualizations, and export capabilities.

## Features

- Natural language to SQL query conversion
- Data analysis and insights
- Automatic visualization generation
- Multiple export formats (CSV, SQL, Excel, JSON)
- Conversation context memory
- Rate limit handling
- Error recovery

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

3. Create a `.env` file with your Azure credentials:
```env
# Azure SQL Database
AZURE_SQL_CONNECTION_STRING=your_connection_string

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_ENDPOINT=your_endpoint
```

## Usage

Run the chatbot:
```bash
python db_chatbot.py
```

### Available Commands

- `export <format> <query>`: Export results
  - Formats: csv, sql, excel, json
- `quit`: Exit the program

### Example Queries

- `show me all employees`
- `what are the top 5 highest paid employees?`
- `how many employees are in each department?`
- `group the results by department`

## Features in Detail

### Natural Language Processing
- Converts natural language queries to SQL
- Maintains conversation context
- Handles complex queries and aggregations

### Data Analysis
- Basic statistics
- Data type analysis
- Missing value detection
- Correlation analysis
- Outlier detection

### Visualizations
- Time series analysis
- Distribution plots
- Correlation heatmaps
- Categorical analysis
- Box plots

### Export Capabilities
- CSV export with metadata
- SQL query export
- Excel export with multiple sheets
- JSON export with metadata

## Error Handling

The chatbot includes comprehensive error handling for:
- Rate limiting
- SQL syntax errors
- Connection issues
- Data processing errors

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Azure OpenAI Service
- Azure SQL Database
- Python Data Science Stack (pandas, numpy, matplotlib, seaborn) 