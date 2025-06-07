import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Divider
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Connect() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    server: '',
    database: '',
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [schema, setSchema] = useState(null);
  const [selectedTable, setSelectedTable] = useState(null);
  const [sampleData, setSampleData] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleConnect = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_URL}/connect`, formData);
      setSchema(response.data.schema);
      // Store connection info in session storage
      sessionStorage.setItem('dbConnection', JSON.stringify(formData));
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to connect to database');
    } finally {
      setLoading(false);
    }
  };

  const handleTableSelect = async (tableName) => {
    setSelectedTable(tableName);
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/sample/${tableName}`);
      setSampleData(response.data.sample);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to fetch sample data');
    } finally {
      setLoading(false);
    }
  };

  const handleStartChat = () => {
    navigate('/chat');
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Connect Your Database
      </Typography>

      {!schema ? (
        <Paper sx={{ p: 3, mb: 3 }}>
          <form onSubmit={handleConnect}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Server Name"
                  name="server"
                  value={formData.server}
                  onChange={handleInputChange}
                  required
                  placeholder="e.g., your-server.database.windows.net"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Database Name"
                  name="database"
                  value={formData.database}
                  onChange={handleInputChange}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Username"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={loading}
                  sx={{ mt: 2 }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Connect'}
                </Button>
              </Grid>
            </Grid>
          </form>
        </Paper>
      ) : (
        <>
          <Alert severity="success" sx={{ mb: 3 }}>
            Successfully connected to the database!
          </Alert>

          <Grid container spacing={3}>
            {/* Schema Explorer */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Available Tables
                </Typography>
                <Box sx={{ maxHeight: '60vh', overflow: 'auto' }}>
                  {Object.entries(schema).map(([tableName, columns]) => (
                    <Card 
                      key={tableName} 
                      sx={{ 
                        mb: 1, 
                        cursor: 'pointer',
                        bgcolor: selectedTable === tableName ? '#e3f2fd' : 'inherit'
                      }}
                      onClick={() => handleTableSelect(tableName)}
                    >
                      <CardContent>
                        <Typography variant="subtitle1">{tableName}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {Object.keys(columns).length} columns
                        </Typography>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              </Paper>
            </Grid>

            {/* Table Details */}
            <Grid item xs={12} md={8}>
              {selectedTable && (
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    {selectedTable} Details
                  </Typography>
                  
                  {/* Column Information */}
                  <Typography variant="subtitle1" gutterBottom>
                    Columns
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Column Name</TableCell>
                          <TableCell>Data Type</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(schema[selectedTable]).map(([column, type]) => (
                          <TableRow key={column}>
                            <TableCell>{column}</TableCell>
                            <TableCell>{type}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  <Divider sx={{ my: 3 }} />

                  {/* Sample Data */}
                  <Typography variant="subtitle1" gutterBottom>
                    Sample Data
                  </Typography>
                  {loading ? (
                    <CircularProgress />
                  ) : sampleData ? (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            {Object.keys(sampleData[0] || {}).map(header => (
                              <TableCell key={header}>{header}</TableCell>
                            ))}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {sampleData.map((row, index) => (
                            <TableRow key={index}>
                              {Object.values(row).map((value, i) => (
                                <TableCell key={i}>{value}</TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Typography color="text.secondary">
                      No sample data available
                    </Typography>
                  )}
                </Paper>
              )}
            </Grid>
          </Grid>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              size="large"
              onClick={handleStartChat}
            >
              Start Chatting with Your Data
            </Button>
          </Box>
        </>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}

export default Connect; 