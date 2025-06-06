import React, { useState, useEffect, useRef } from 'react';
import { 
  Container, 
  Paper, 
  TextField, 
  Button, 
  Typography, 
  Box,
  CircularProgress,
  IconButton,
  Menu,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import { Send as SendIcon, History as HistoryIcon, Save as SaveIcon } from '@mui/icons-material';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [schemaInfo, setSchemaInfo] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const messagesEndRef = useRef(null);

  const presetQueries = [
    "Show all employees",
    "Top 5 products by sales",
    "Sales by month",
    "List low-stock products"
  ];

  useEffect(() => {
    // Fetch schema information on component mount
    fetchSchemaInfo();
  }, []);

  const fetchSchemaInfo = async () => {
    try {
      const response = await axios.get(`${API_URL}/schema`);
      setSchemaInfo(response.data.schema); // Access the schema property
    } catch (error) {
      console.error('Error fetching schema:', error);
      setSchemaInfo('Error loading schema information');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    const userMessage = { type: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await axios.post(`${API_URL}/query`, { query });
      const { sql, results, analysis } = response.data;
      
      setMessages(prev => [
        ...prev,
        { type: 'sql', content: sql },
        { type: 'results', content: results },
        { type: 'analysis', content: analysis }
      ]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        { type: 'error', content: error.response?.data?.error || 'An error occurred' }
      ]);
    }

    setLoading(false);
    setQuery('');
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`${API_URL}/export`, {
        params: { format },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `query-results.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export error:', error);
    }
  };

  const renderMessage = (message) => {
    switch (message.type) {
      case 'user':
        return (
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Paper sx={{ p: 2, maxWidth: '70%', bgcolor: '#e3f2fd' }}>
              <Typography>{message.content}</Typography>
            </Paper>
          </Box>
        );
      case 'sql':
        return (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">Generated SQL:</Typography>
            <SyntaxHighlighter language="sql" style={docco}>
              {message.content}
            </SyntaxHighlighter>
          </Box>
        );
      case 'results':
        return (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">Results:</Typography>
            <Paper sx={{ p: 2, overflowX: 'auto' }}>
              <pre>{JSON.stringify(message.content, null, 2)}</pre>
            </Paper>
          </Box>
        );
      case 'analysis':
        return (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">Analysis:</Typography>
            <Paper sx={{ p: 2 }}>
              <Typography>{message.content}</Typography>
            </Paper>
          </Box>
        );
      case 'error':
        return (
          <Box sx={{ mb: 2 }}>
            <Paper sx={{ p: 2, bgcolor: '#ffebee' }}>
              <Typography color="error">{message.content}</Typography>
            </Paper>
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Database Chatbot
      </Typography>

      {/* Schema Information */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Available Tables
        </Typography>
        {schemaInfo ? (
          <Typography component="pre" sx={{ 
            overflowX: 'auto', 
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
            fontFamily: 'monospace'
          }}>
            {schemaInfo}
          </Typography>
        ) : (
          <CircularProgress size={20} />
        )}
      </Paper>

      {/* Preset Queries */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Quick Queries
        </Typography>
        <List>
          {presetQueries.map((preset, index) => (
            <ListItem key={index} button onClick={() => setQuery(preset)}>
              <ListItemText primary={preset} />
            </ListItem>
          ))}
        </List>
      </Paper>

      {/* Chat Interface */}
      <Paper sx={{ p: 2, mb: 2, height: '60vh', overflow: 'auto' }}>
        {messages.map((message, index) => (
          <div key={index}>{renderMessage(message)}</div>
        ))}
        <div ref={messagesEndRef} />
      </Paper>

      {/* Input Area */}
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Ask a question about your data..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
          disabled={loading}
        />
        <IconButton 
          color="primary" 
          onClick={handleQuery}
          disabled={loading || !query.trim()}
        >
          {loading ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
        <IconButton
          color="primary"
          onClick={(e) => setAnchorEl(e.currentTarget)}
        >
          <SaveIcon />
        </IconButton>
      </Box>

      {/* Export Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => { handleExport('csv'); setAnchorEl(null); }}>
          Export as CSV
        </MenuItem>
        <MenuItem onClick={() => { handleExport('json'); setAnchorEl(null); }}>
          Export as JSON
        </MenuItem>
        <MenuItem onClick={() => { handleExport('excel'); setAnchorEl(null); }}>
          Export as Excel
        </MenuItem>
      </Menu>
    </Container>
  );
}

export default App; 