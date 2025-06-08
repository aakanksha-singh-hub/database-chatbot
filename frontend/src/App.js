import React, { useState, useRef, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import './App.css';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import * as XLSX from 'xlsx';
import { AppBar, Toolbar, Typography, Button, Container, Grid, Card, CardContent, Box, CssBaseline, IconButton, useTheme } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import '@fontsource/inter/400.css';
import '@fontsource/inter/700.css';
import Chat from './components/Chat';
import AboutPage from './components/AboutPage';
import ConnectPage from './components/ConnectPage';

// This comment is added to force GitHub to re-index the frontend directory.
// It can be removed later if desired.

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const getDesignTokens = (mode) => ({
  palette: {
    mode,
    ...(mode === 'light'
      ? {
          primary: { main: '#eab308', contrastText: '#fff' },
          secondary: { main: '#facc15', contrastText: '#fff' },
          background: {
            default: '#fdf6ec',
            paper: '#fff8e1',
            navbar: 'linear-gradient(90deg, #fffbe6 0%, #fdf6ec 100%)',
            hero: 'linear-gradient(135deg, #fffbe6 0%, #fdf6ec 100%)',
            section: '#fdf6ec',
            card: '#fff8e1',
          },
          text: {
            primary: '#7c5e2a',
            secondary: '#bfa76a',
          },
        }
      : {
          primary: { main: '#a084ee', contrastText: '#fff' },
          secondary: { main: '#6a8dff', contrastText: '#fff' },
          background: {
            default: '#18192a',
            paper: '#23283a',
            navbar: '#23283a',
            hero: '#23283a',
            section: '#18192a',
            card: '#23283a',
          },
          text: {
            primary: '#f8fafc',
            secondary: '#bdbdbd',
          },
        }),
  },
  typography: {
    fontFamily: 'Inter, Poppins, Lato, Arial, sans-serif',
  },
});

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

const NavigationBar = ({ mode, toggleMode }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  return (
    <AppBar
      position="sticky"
      elevation={6}
      sx={{
        mb: 6,
        background: theme.palette.background.navbar,
        color: theme.palette.text.primary,
        boxShadow: theme.palette.mode === 'light'
          ? '0 4px 24px 0 rgba(106, 141, 255, 0.10)'
          : '0 2px 12px 0 rgba(35, 40, 58, 0.7)',
        borderBottom: theme.palette.mode === 'light' ? '1.5px solid #d1d5db' : '1.5px solid #23283a',
      }}
    >
      <Toolbar sx={{ minHeight: 72, display: 'flex', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #6a8dff 0%, #a084ee 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(106, 141, 255, 0.15)',
              mr: 1.5,
            }}
          >
            <span role="img" aria-label="logo" style={{ fontSize: 28 }}>🤖</span>
          </Box>
          <Typography variant="h6" sx={{ fontWeight: 800, letterSpacing: 1, color: theme.palette.primary.main, fontSize: '1.5rem' }}>
            QueryBot
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button color="inherit" onClick={() => navigate('/')} sx={{ fontWeight: 700, fontSize: '1.15rem' }}>Home</Button>
          <Button color="inherit" onClick={() => navigate('/connect')} sx={{ fontWeight: 700, fontSize: '1.15rem' }}>Connect</Button>
          <Button color="inherit" onClick={() => navigate('/chat')} sx={{ fontWeight: 700, fontSize: '1.15rem' }}>Chat</Button>
          <Button color="inherit" onClick={() => navigate('/about')} sx={{ fontWeight: 700, fontSize: '1.15rem' }}>About</Button>
          <IconButton onClick={toggleMode} sx={{ ml: 2 }} color="primary">
            {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

const HeroSection = () => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const navigate = useNavigate();
  return (
    <Box sx={{ bgcolor: theme.palette.background.hero, py: 8 }}>
      <Container maxWidth="md">
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={7}>
            <Typography variant="h3" fontWeight={800} color="primary" gutterBottom>
              QueryBot: Natural Language SQL Chatbot
            </Typography>
            <Typography variant="h5" fontWeight={500} color="text.secondary" gutterBottom>
              Query your Azure SQL database effortlessly — just ask in plain English.
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Welcome to the future of data interaction. Whether you're a data analyst, product manager, or developer, this tool empowers you to interact with structured data without writing a single line of SQL. Powered by Azure OpenAI and Azure SQL Database, this GenAI chatbot bridges the gap between natural language and database queries.
            </Typography>
            <Button variant="contained" size="large" color="primary" sx={{ fontWeight: 700 }} onClick={() => navigate('/chat')}>
              Start Exploring
            </Button>
          </Grid>
          <Grid item xs={12} md={5}>
            <Card elevation={4} sx={{ bgcolor: theme.palette.background.card, borderRadius: 3 }}>
              <CardContent>
                <Typography variant="subtitle2" color="primary" fontWeight={700} gutterBottom>
                  Show me the top 5 customers by revenue
                </Typography>
                <Box sx={{
                  bgcolor: isDark ? '#23283a' : '#eceff1',
                  borderRadius: 2,
                  p: 1,
                  fontFamily: 'monospace',
                  fontSize: 14,
                  mb: 1,
                  color: isDark ? '#e0e0e0' : undefined,
                }}>
                  SELECT TOP 5 customer_name, SUM(revenue) as total_revenue...
                </Box>
                <Typography variant="body2" color="success.main" fontWeight={600}>
                  Results displayed in a beautiful table...
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

const benefits = [
  {
    icon: '✅',
    title: 'No SQL Expertise Required',
    desc: 'Ask questions in plain English and get instant results',
  },
  {
    icon: '⚡',
    title: 'Real-time Insights',
    desc: 'Get immediate answers to your data questions',
  },
  {
    icon: '🔒',
    title: 'Secure Integration',
    desc: 'Connect your own Azure SQL database safely',
  },
  {
    icon: '📊',
    title: 'Visualize & Export',
    desc: 'View results in charts and export in multiple formats',
  },
];

const cardContentSx = {
  minHeight: 200,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  px: 2,
  py: 3,
};

const BenefitsSection = () => {
  const theme = useTheme();
  return (
    <Box sx={{ bgcolor: theme.palette.background.section, py: 8 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" align="center" fontWeight={700} color="primary" gutterBottom>
          Key Benefits
        </Typography>
        <Grid container spacing={4} justifyContent="center">
          {benefits.map((b, i) => (
            <Grid item xs={12} sm={6} md={3} key={i} sx={{ display: 'flex' }}>
              <Card elevation={2} sx={{ borderRadius: 3, textAlign: 'center', py: 0, height: '100%', display: 'flex', flex: 1, bgcolor: theme.palette.background.card }}>
                <CardContent sx={cardContentSx}>
                  <Typography variant="h2" component="div" gutterBottom>{b.icon}</Typography>
                  <Typography variant="h6" fontWeight={700} gutterBottom>{b.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{b.desc}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
};

const techStack = [
  { icon: '🗄️', title: 'Azure SQL Database', desc: 'Enterprise-grade database management' },
  { icon: '🤖', title: 'Azure OpenAI (GPT-4)', desc: 'State-of-the-art language model' },
  { icon: '🐍', title: 'Python + FastAPI', desc: 'High-performance backend framework' },
  { icon: '⚡', title: 'React + MUI', desc: 'Modern, fast, and beautiful UI' },
];

const TechStackSection = () => {
  const theme = useTheme();
  return (
    <Box sx={{ bgcolor: theme.palette.background.section, py: 8 }}>
      <Container maxWidth="lg">
        <Typography variant="h4" align="center" fontWeight={700} color="primary" gutterBottom>
          Powered By
        </Typography>
        <Grid container spacing={4} justifyContent="center">
          {techStack.map((t, i) => (
            <Grid item xs={12} sm={6} md={3} key={i} sx={{ display: 'flex' }}>
              <Card elevation={2} sx={{ borderRadius: 3, textAlign: 'center', py: 0, height: '100%', display: 'flex', flex: 1, bgcolor: theme.palette.background.card }}>
                <CardContent sx={cardContentSx}>
                  <Typography variant="h2" component="div" gutterBottom>{t.icon}</Typography>
                  <Typography variant="h6" fontWeight={700} gutterBottom>{t.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{t.desc}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
};

const CTASection = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  return (
    <Box sx={{ bgcolor: theme.palette.background.default, py: 8, textAlign: 'center' }}>
      <Container maxWidth="sm">
        <Typography variant="h4" fontWeight={700} color="primary" gutterBottom>
          Ready to Transform Your Data Experience?
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Start exploring your data in a whole new way.
        </Typography>
        <Button variant="contained" size="large" color="primary" sx={{ fontWeight: 700 }} onClick={() => navigate('/chat')}>
          Start Exploring
        </Button>
      </Container>
    </Box>
  );
};

function App() {
  const [mode, setMode] = useState('light');
  const theme = createTheme(getDesignTokens(mode));
  const toggleMode = () => setMode((prev) => (prev === 'light' ? 'dark' : 'light'));

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              <Box sx={{ minHeight: '100vh', bgcolor: theme.palette.background.default }}>
                <NavigationBar mode={mode} toggleMode={toggleMode} />
                <HeroSection />
                <BenefitsSection />
                <TechStackSection />
                <CTASection />
              </Box>
            }
          />
          <Route
            path="/chat"
            element={
              <Box sx={{ minHeight: '100vh', bgcolor: theme.palette.background.default }}>
                <NavigationBar mode={mode} toggleMode={toggleMode} />
                <Chat />
              </Box>
            }
          />
          <Route
            path="/about"
            element={
              <Box sx={{ minHeight: '100vh', bgcolor: theme.palette.background.default }}>
                <NavigationBar mode={mode} toggleMode={toggleMode} />
                <AboutPage />
              </Box>
            }
          />
          <Route
            path="/connect"
            element={
              <Box sx={{ minHeight: '100vh', bgcolor: theme.palette.background.default }}>
                <NavigationBar mode={mode} toggleMode={toggleMode} />
                <ConnectPage />
              </Box>
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App; 