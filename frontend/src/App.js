import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import * as XLSX from 'xlsx';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const NATURAL_SUGGESTIONS = [
  "How many employees work in each department?",
  "Who are the top 5 highest paid employees?",
  "Show me the average salary by department.",
  "What are the most common skills among employees?",
  "Show me recent hiring trends.",
  "Which department has the best performance ratings?",
  "List all employees who joined in the last year.",
  "Show me the gender distribution in the company.",
  "What is the average years of experience by department?",
  "Show me a breakdown of employees by education level."
];

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [visualizationType, setVisualizationType] = useState(null);
  const messagesEndRef = useRef(null);
  const [error, setError] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          context: messages,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from server');
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, 
        { role: 'user', content: input },
        { 
          role: 'assistant', 
          content: data.response, 
          results: data.results, 
          visualizationType: data.visualizationType,
          suggestions: data.suggestions || []
        }
      ]);
      setInput('');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const exportToExcel = (data) => {
    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Data");
    XLSX.writeFile(workbook, "database_results.xlsx");
  };

  const prepareChartData = (results, type) => {
    if (!results || results.length === 0) return null;

    switch (type) {
      case 'department':
        if (results[0].hasOwnProperty('count')) {
          // Department distribution data
          return {
            labels: results.map(r => r.department),
            datasets: [{
              data: results.map(r => r.count),
              backgroundColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF'
              ]
            }]
          };
        } else {
          // Department employee data
          const departmentData = results.reduce((acc, emp) => {
            acc[emp.department] = (acc[emp.department] || 0) + 1;
            return acc;
          }, {});
          return {
            labels: Object.keys(departmentData),
            datasets: [{
              data: Object.values(departmentData),
              backgroundColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF'
              ]
            }]
          };
        }

      case 'salary':
        const salaryRanges = {
          '0-50k': 0,
          '50k-75k': 0,
          '75k-100k': 0,
          '100k+': 0
        };
        results.forEach(emp => {
          const salary = emp.salary;
          if (salary <= 50000) salaryRanges['0-50k']++;
          else if (salary <= 75000) salaryRanges['50k-75k']++;
          else if (salary <= 100000) salaryRanges['75k-100k']++;
          else salaryRanges['100k+']++;
        });
        return {
          labels: Object.keys(salaryRanges),
          datasets: [{
            label: 'Number of Employees',
            data: Object.values(salaryRanges),
            backgroundColor: '#36A2EB'
          }]
        };

      case 'performance':
        const performanceRanges = {
          '4.5-5.0': 0,
          '4.0-4.4': 0,
          '3.5-3.9': 0,
          '3.0-3.4': 0
        };
        results.forEach(emp => {
          const rating = emp.performance_rating;
          if (rating >= 4.5) performanceRanges['4.5-5.0']++;
          else if (rating >= 4.0) performanceRanges['4.0-4.4']++;
          else if (rating >= 3.5) performanceRanges['3.5-3.9']++;
          else performanceRanges['3.0-3.4']++;
        });
        return {
          labels: Object.keys(performanceRanges),
          datasets: [{
            label: 'Number of Employees',
            data: Object.values(performanceRanges),
            backgroundColor: '#4BC0C0'
          }]
        };

      case 'experience':
        const experienceRanges = {
          '10+ years': 0,
          '7-9 years': 0,
          '4-6 years': 0,
          '0-3 years': 0
        };
        results.forEach(emp => {
          const exp = emp.years_experience;
          if (exp >= 10) experienceRanges['10+ years']++;
          else if (exp >= 7) experienceRanges['7-9 years']++;
          else if (exp >= 4) experienceRanges['4-6 years']++;
          else experienceRanges['0-3 years']++;
        });
        return {
          labels: Object.keys(experienceRanges),
          datasets: [{
            label: 'Number of Employees',
            data: Object.values(experienceRanges),
            backgroundColor: '#FFCE56'
          }]
        };

      default:
        return null;
    }
  };

  const renderResults = (results, type) => {
    if (!results || results.length === 0) return null;

    const chartData = prepareChartData(results, type);

  return (
      <div className="results-container">
        <div className="results-header">
          <h3>Results ({results.length} records)</h3>
          <button 
            className="export-button"
            onClick={() => exportToExcel(results)}
          >
            Export to Excel
          </button>
        </div>
        
        {chartData && (
          <div className="visualization-container">
            <div className="chart">
              <h4>{type.charAt(0).toUpperCase() + type.slice(1)} Distribution</h4>
              {type === 'department' ? (
                <Pie data={chartData} />
              ) : (
                <Bar 
                  data={chartData}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: {
                        display: false
                      },
                      title: {
                        display: true,
                        text: `${type.charAt(0).toUpperCase() + type.slice(1)} Distribution`
                      }
                    }
                  }}
                />
              )}
            </div>
          </div>
        )}

        <div className="table-container">
          <table className="results-table">
            <thead>
              <tr>
                {Object.keys(results[0]).map(column => (
                  <th key={column}>{column.charAt(0).toUpperCase() + column.slice(1)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.map((row, index) => (
                <tr key={index}>
                  {Object.keys(row).map(column => (
                    <td key={`${index}-${column}`}>
                      {column === 'salary' ? `$${row[column].toLocaleString()}` : 
                       column === 'performance_rating' ? row[column].toFixed(1) :
                       row[column]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderSuggestions = (suggestions) => {
    if (!suggestions || suggestions.length === 0) return null;
    
    return (
      <div className="suggestions-container">
        <div className="suggestions-header">
          <span>Suggested Questions:</span>
        </div>
        <div className="suggestions-list">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="suggestion-button"
              onClick={() => {
                setInput(suggestion);
                handleSubmit({ preventDefault: () => {} });
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="App">
      <div className="chat-container">
        <div className="messages-container">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-content">
                {message.content}
                {message.results && renderResults(message.results, message.visualizationType)}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="loading">Thinking...</div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your data..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Thinking...' : 'Send'}
          </button>
        </form>
        <button
          className="suggestions-toggle"
          onClick={() => setShowSuggestions((prev) => !prev)}
          style={{ marginTop: '0.5rem', marginBottom: '1rem' }}
        >
          Suggestions
        </button>
        {showSuggestions && (
          <div className="suggestions-modal">
            <div className="suggestions-modal-content">
              <h4>Example Questions</h4>
              <ul>
                {NATURAL_SUGGESTIONS.map((suggestion, idx) => (
                  <li key={idx}>
                    <button
                      className="suggestion-button"
                      onClick={() => {
                        setInput(suggestion);
                        setShowSuggestions(false);
                        handleSubmit({ preventDefault: () => {} });
                      }}
                    >
                      {suggestion}
                    </button>
                  </li>
                ))}
              </ul>
              <button
                className="close-suggestions"
                onClick={() => setShowSuggestions(false)}
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App; 