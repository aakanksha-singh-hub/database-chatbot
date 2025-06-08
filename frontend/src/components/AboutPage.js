import React from 'react';
import { Container, Typography, Box, List, ListItem, ListItemText, Divider, useTheme, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';

const sampleQueries = [
  {
    natural: 'List all departments',
    sql: 'SELECT DISTINCT department FROM employees;'
  },
  {
    natural: 'Top 5 products by sales in 2023',
    sql: 'SELECT TOP 5 product_name, SUM(sales) FROM orders WHERE YEAR(order_date) = 2023 GROUP BY product_name ORDER BY SUM(sales) DESC;'
  },
  {
    natural: 'Average salary by department',
    sql: 'SELECT department, AVG(salary) FROM employees GROUP BY department;'
  },
  {
    natural: 'Show total revenue per year',
    sql: 'SELECT YEAR(order_date), SUM(revenue) FROM sales GROUP BY YEAR(order_date);'
  }
];

const challenges = [
  { challenge: 'Mapping vague queries to correct SQL', solution: 'Introduced table-aware prompting and auto-suggestions' },
  { challenge: 'Handling runtime SQL errors', solution: 'Implemented a TRY-CATCH wrapper and safe failure messages' },
  { challenge: 'Connecting to Azure SQL databases securely', solution: 'Used environment-level access configuration with scoped credentials' },
  { challenge: 'Designing an intuitive interface', solution: 'Used Streamlit with Tailwind CSS for minimal, responsive interaction' },
];

const roadmap = [
  'Visualization Engine: Add basic bar/line/pie charts for aggregated data',
  'User Authentication: Optional user login with role-based access',
  'Data Masking & Security: Obfuscate sensitive columns in output',
  'SQL Validator: Pre-execute SQL linting and safety check',
  'Session-based Memory: Enable contextual query history and refinement',
  'Query History & Export: Allow downloading of results and logs',
];

const AboutPage = () => {
  const theme = useTheme();
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: theme.palette.background.default, fontFamily: theme.typography.fontFamily }}>
      <Container maxWidth="md" sx={{ py: 6 }}>
        <Box
          sx={{
            bgcolor: theme.palette.background.paper,
            borderRadius: 3,
            p: { xs: 2, md: 4 },
            boxShadow: 3,
            background: theme.palette.mode === 'dark'
              ? 'linear-gradient(135deg, #23283a 0%, #2d3142 100%)'
              : 'linear-gradient(135deg, #fffbe6 0%, #fdf6ec 100%)',
          }}
        >
          <Typography variant="h3" fontWeight={800} color="primary" gutterBottom>
            About
          </Typography>
          <Typography variant="body1" sx={{ mb: 3, color: theme.palette.text.primary }}>
            Welcome to the QueryBot - Your GenAI SQL Chatbot – a streamlined, production-ready platform that enables users to query structured databases using natural language. This system removes the technical barrier of writing SQL and allows anyone to interact with data conversationally and securely.
          </Typography>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            What This App Does
          </Typography>
          <Typography variant="body1" sx={{ mb: 3, color: theme.palette.text.primary }}>
            This application enables users to query an Azure SQL database using plain English. It translates natural language queries into executable SQL statements, runs them against the connected database, and returns neatly formatted results. In addition to conversational querying, the system also includes a database explorer, schema insights, and intelligent query suggestions.
          </Typography>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            How to Use the App
          </Typography>
          <List sx={{ mb: 3 }}>
            <ListItem>
              <ListItemText
                primary={<b>Connect to Your Database</b>}
                secondary={
                  'Navigate to the "Connect" page and enter the required Azure SQL credentials: server name, database name, username, and password. On successful validation, your session will be initialized for querying.'
                }
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary={<b>Explore Your Dataset</b>}
                secondary={
                  'Once connected, you can browse through available tables, view their schemas (column names and data types), and preview sample rows. This helps you understand the structure of your data before asking questions.'
                }
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary={<b>Ask a Question</b>}
                secondary={
                  'Go to the "Chat" page and type a natural language query such as "List all employees who joined after 2020." The system will automatically convert your input into SQL and display both the SQL query and results in a clear, tabular format.'
                }
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary={<b>Refine or Explore Further</b>}
                secondary={
                  'You may continue the conversation by asking follow-up questions, refining filters, or switching to a different table.'
                }
              />
            </ListItem>
          </List>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            Sample Queries
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><b>Natural Language Input</b></TableCell>
                  <TableCell><b>SQL Translation</b></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sampleQueries.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{row.natural}</TableCell>
                    <TableCell><code>{row.sql}</code></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            Prompting Tips
          </Typography>
          <List sx={{ mb: 3 }}>
            <ListItem><ListItemText primary="Be specific: Include table names or column references where possible." secondary='Example: "Show average salary by department in 2022."' /></ListItem>
            <ListItem><ListItemText primary="Use contextual filters:" secondary='Example: "Employees with salary over 70000 in Marketing."' /></ListItem>
            <ListItem><ListItemText primary="Avoid vague phrasing: General inputs like 'Show me something interesting' may not yield usable results." /></ListItem>
          </List>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            Export and Visualization
          </Typography>
          <Typography variant="body1" sx={{ mb: 3, color: theme.palette.text.primary }}>
            This version focuses on clean tabular outputs. Export features (CSV) and basic chart visualizations are on the roadmap and will be introduced in future iterations.
          </Typography>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            Limitations
          </Typography>
          <List sx={{ mb: 3 }}>
            <ListItem><ListItemText primary="Ambiguity in queries: The system may struggle with overly vague or highly contextual questions." /></ListItem>
            <ListItem><ListItemText primary="Security scope: Only read operations are permitted. The system does not allow updates, deletions, or schema changes." /></ListItem>
            <ListItem><ListItemText primary="Error handling: SQL errors are caught and shown gracefully, but complex nested queries may require refinement." /></ListItem>
            <ListItem><ListItemText primary="Sensitive data: This POC does not yet support masking or encryption of sensitive fields." /></ListItem>
          </List>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            Why We Built This
          </Typography>
          <Typography variant="body1" sx={{ mb: 3, color: theme.palette.text.primary }}>
            Accessing insights from databases still requires technical fluency in SQL. This project was designed to simplify structured data querying using natural language, making enterprise data accessible to non-technical users. By integrating Azure SQL with Azure OpenAI, we showcase how AI can improve workflows and reduce friction in everyday data interaction.
          </Typography>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            What We Learned
          </Typography>
          <List sx={{ mb: 3 }}>
            <ListItem><ListItemText primary="Effective prompt engineering dramatically improves query accuracy." /></ListItem>
            <ListItem><ListItemText primary="Integrating schema-awareness and metadata helps guide meaningful query construction." /></ListItem>
            <ListItem><ListItemText primary="Robust error handling is essential to build trust and reliability in an AI-driven querying experience." /></ListItem>
            <ListItem><ListItemText primary="The user experience must remain clean and responsive, especially for technical tasks like database exploration." /></ListItem>
          </List>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            Challenges and Solutions
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><b>Challenge</b></TableCell>
                  <TableCell><b>Solution</b></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {challenges.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{row.challenge}</TableCell>
                    <TableCell>{row.solution}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Typography variant="h5" fontWeight={700} color="text.secondary" gutterBottom>
            Future Roadmap
          </Typography>
          <List>
            {roadmap.map((item, idx) => (
              <ListItem key={idx}><ListItemText primary={item} /></ListItem>
            ))}
          </List>
        </Box>
      </Container>
    </Box>
  );
};

export default AboutPage; 