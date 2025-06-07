import React from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import {
  Help as HelpIcon,
  Code as CodeIcon,
  BarChart as BarChartIcon,
  Save as SaveIcon,
  Warning as WarningIcon,
  Lightbulb as LightbulbIcon
} from '@mui/icons-material';

function Help() {
  const examples = [
    {
      question: "Show me all employees in the Sales department",
      explanation: "This will generate a SELECT query to fetch all employees from the Sales department"
    },
    {
      question: "What are the top 5 products by revenue?",
      explanation: "This will create a query to sort products by revenue and limit to top 5"
    },
    {
      question: "Compare monthly sales for the last 6 months",
      explanation: "This will generate a query to aggregate sales by month and create a time series"
    },
    {
      question: "List all customers who haven't made a purchase in 3 months",
      explanation: "This will create a query to find inactive customers using date comparison"
    }
  ];

  const tips = [
    "Be specific in your questions to get more accurate results",
    "Use natural language - no need to know SQL syntax",
    "You can ask follow-up questions to refine your results",
    "The system will automatically suggest visualizations for numeric data",
    "Export your results in various formats (CSV, Excel, JSON) for further analysis"
  ];

  const limitations = [
    "Complex queries might take longer to process",
    "Very vague questions may not yield precise results",
    "Some advanced SQL features might not be supported",
    "Large result sets may be truncated for performance",
    "Sensitive data should be handled with care"
  ];

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Help & Instructions
      </Typography>

      {/* Getting Started */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Getting Started
        </Typography>
        <List>
          <ListItem>
            <ListItemIcon>
              <HelpIcon color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="Connect Your Database"
              secondary="First, connect your Azure SQL database using the Connect page. You'll need your server name, database name, and credentials."
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CodeIcon color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="Ask Questions"
              secondary="Use natural language to ask questions about your data. The system will automatically generate the appropriate SQL query."
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <BarChartIcon color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="View Results"
              secondary="Results are displayed in a table format with automatic visualization options for numeric data."
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <SaveIcon color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="Export Data"
              secondary="Export your results in various formats for further analysis or reporting."
            />
          </ListItem>
        </List>
      </Paper>

      {/* Example Queries */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Example Queries
        </Typography>
        <Grid container spacing={2}>
          {examples.map((example, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" color="primary" gutterBottom>
                    {example.question}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {example.explanation}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Tips */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Tips for Better Results
        </Typography>
        <List>
          {tips.map((tip, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                <LightbulbIcon color="primary" />
              </ListItemIcon>
              <ListItemText primary={tip} />
            </ListItem>
          ))}
        </List>
      </Paper>

      {/* Limitations */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Limitations & Considerations
        </Typography>
        <List>
          {limitations.map((limitation, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                <WarningIcon color="warning" />
              </ListItemIcon>
              <ListItemText primary={limitation} />
            </ListItem>
          ))}
        </List>
      </Paper>

      {/* Best Practices */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Best Practices
        </Typography>
        <Typography variant="body2">
          • Start with simple questions and gradually make them more complex
          <br />
          • Use specific column names when you know them
          <br />
          • Break down complex questions into smaller parts
          <br />
          • Review the generated SQL to understand how your question was interpreted
        </Typography>
      </Alert>
    </Box>
  );
}

export default Help; 