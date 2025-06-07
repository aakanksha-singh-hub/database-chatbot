import React from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Paper,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { 
  Storage as StorageIcon,
  Chat as ChatIcon,
  Code as CodeIcon,
  Cloud as CloudIcon
} from '@mui/icons-material';

function Home() {
  const navigate = useNavigate();

  const features = [
    {
      icon: <ChatIcon sx={{ fontSize: 40 }} />,
      title: "Natural Language Queries",
      description: "Ask questions in plain English, no SQL knowledge required"
    },
    {
      icon: <StorageIcon sx={{ fontSize: 40 }} />,
      title: "Azure SQL Integration",
      description: "Seamlessly connect with your Azure SQL database"
    },
    {
      icon: <CodeIcon sx={{ fontSize: 40 }} />,
      title: "Smart SQL Generation",
      description: "Powered by Azure OpenAI for accurate query generation"
    },
    {
      icon: <CloudIcon sx={{ fontSize: 40 }} />,
      title: "Data Visualization",
      description: "Interactive charts and graphs for your data insights"
    }
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Box sx={{ 
        textAlign: 'center', 
        py: 8,
        background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
        color: 'white',
        borderRadius: 2,
        mb: 6
      }}>
        <Typography variant="h2" component="h1" gutterBottom>
          Database Chatbot
        </Typography>
        <Typography variant="h5" gutterBottom>
          Query your structured data using natural language
        </Typography>
        <Button 
          variant="contained" 
          size="large"
          sx={{ 
            mt: 4,
            backgroundColor: 'white',
            color: '#2196F3',
            '&:hover': {
              backgroundColor: '#f5f5f5'
            }
          }}
          onClick={() => navigate('/chat')}
        >
          Start Exploring
        </Button>
      </Box>

      {/* Features Grid */}
      <Grid container spacing={4} sx={{ mb: 6 }}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Box sx={{ color: 'primary.main', mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h6" gutterBottom>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Technologies Section */}
      <Paper sx={{ p: 4, mb: 6 }}>
        <Typography variant="h5" gutterBottom>
          Built with Modern Technologies
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Typography variant="subtitle1" color="primary">Frontend</Typography>
            <Typography variant="body2">React, Material-UI</Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="subtitle1" color="primary">Backend</Typography>
            <Typography variant="body2">Flask, Azure OpenAI</Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="subtitle1" color="primary">Database</Typography>
            <Typography variant="body2">Azure SQL</Typography>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}

export default Home; 