import React, { useState, useEffect, useRef } from 'react';
import { 
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
  Grid,
  Card,
  CardContent
} from '@mui/material';
import { 
  Send as SendIcon, 
  Save as SaveIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  ShowChart as LineChartIcon
} from '@mui/icons-material';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import axios from 'axios';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Chat() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [schemaInfo, setSchemaInfo] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [visualizationType, setVisualizationType] = useState(null);
  const messagesEndRef = useRef(null);

  const presetQueries = [
    "Show all employees",
    "Top 5 products by sales",
    "Sales by month",
    "List low-stock products"
  ];

  useEffect(() => {
    fetchSchemaInfo();
  }, []);

  const fetchSchemaInfo = async () => {
    try {
      const response = await axios.get(`${API_URL}/schema`);
      setSchemaInfo(response.data.schema);
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

      // Auto-detect visualization type based on results
      if (Array.isArray(results) && results.length > 0) {
        const firstRow = results[0];
        const numericColumns = Object.entries(firstRow)
          .filter(([_, value]) => typeof value === 'number')
          .map(([key]) => key);

        if (numericColumns.length >= 2) {
          setVisualizationType('bar');
        }
      }
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

  const renderVisualization = (data) => {
    if (!Array.isArray(data) || data.length === 0) return null;

    const firstRow = data[0];
    const numericColumns = Object.entries(firstRow)
      .filter(([_, value]) => typeof value === 'number')
      .map(([key]) => key);

    if (numericColumns.length < 2) return null;

    const chartData = data.map(row => ({
      name: row[numericColumns[0]],
      value: row[numericColumns[1]]
    }));

    switch (visualizationType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        );
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                label
              />
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        );
      default:
        return null;
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
              {renderVisualization(message.content)}
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
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Chat with Your Database
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

      {/* Quick Queries */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Quick Queries
        </Typography>
        <Grid container spacing={2}>
          {presetQueries.map((preset, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary">
                    {preset}
                  </Typography>
                  <Button 
                    size="small" 
                    onClick={() => setQuery(preset)}
                    sx={{ mt: 1 }}
                  >
                    Try it
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
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

      {/* Visualization Controls */}
      {messages.some(m => m.type === 'results') && (
        <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
          <IconButton 
            color={visualizationType === 'bar' ? 'primary' : 'default'}
            onClick={() => setVisualizationType('bar')}
          >
            <BarChartIcon />
          </IconButton>
          <IconButton 
            color={visualizationType === 'pie' ? 'primary' : 'default'}
            onClick={() => setVisualizationType('pie')}
          >
            <PieChartIcon />
          </IconButton>
          <IconButton 
            color={visualizationType === 'line' ? 'primary' : 'default'}
            onClick={() => setVisualizationType('line')}
          >
            <LineChartIcon />
          </IconButton>
        </Box>
      )}
    </Box>
  );
}

export default Chat; 