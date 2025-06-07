import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Code as CodeIcon,
  Cloud as CloudIcon,
  Psychology as PsychologyIcon,
  Build as BuildIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';

function About() {
  const learnings = [
    {
      title: "Natural Language Processing",
      description: "Understanding how to effectively convert natural language queries into SQL using Azure OpenAI's capabilities"
    },
    {
      title: "Database Integration",
      description: "Learning to securely connect and interact with Azure SQL databases while maintaining data integrity"
    },
    {
      title: "User Experience",
      description: "Creating an intuitive interface that makes database querying accessible to non-technical users"
    }
  ];

  const challenges = [
    {
      title: "Query Accuracy",
      description: "Ensuring the generated SQL queries accurately reflect user intent while handling edge cases"
    },
    {
      title: "Performance Optimization",
      description: "Balancing response time with query complexity and result set size"
    },
    {
      title: "Error Handling",
      description: "Providing meaningful feedback when queries fail or return unexpected results"
    }
  ];

  const futureIdeas = [
    {
      title: "Enhanced Grounding",
      description: "Improve query accuracy by incorporating more context about the database schema and relationships"
    },
    {
      title: "SQL Validation",
      description: "Add validation and optimization of generated SQL queries before execution"
    },
    {
      title: "Multi-user Support",
      description: "Implement user authentication and role-based access control"
    },
    {
      title: "Advanced Analytics",
      description: "Add more sophisticated data analysis and visualization capabilities"
    }
  ];

  const technologies = [
    {
      category: "Frontend",
      items: ["React", "Material-UI", "Recharts"]
    },
    {
      category: "Backend",
      items: ["Flask", "Azure OpenAI", "SQLAlchemy"]
    },
    {
      category: "Database",
      items: ["Azure SQL", "Azure Key Vault"]
    }
  ];

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        About the Project
      </Typography>

      {/* Project Overview */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Project Overview
        </Typography>
        <Typography paragraph>
          This project aims to bridge the gap between natural language and database querying,
          making data analysis accessible to users without SQL knowledge. By leveraging
          Azure OpenAI's capabilities, we've created an intuitive interface that converts
          natural language questions into SQL queries and presents the results in a
          user-friendly format.
        </Typography>
      </Paper>

      {/* Key Learnings */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Key Learnings
        </Typography>
        <Grid container spacing={3}>
          {learnings.map((learning, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {learning.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {learning.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Challenges & Solutions */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Challenges & Solutions
        </Typography>
        <Grid container spacing={3}>
          {challenges.map((challenge, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {challenge.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {challenge.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Technologies Used */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Technologies Used
        </Typography>
        <Grid container spacing={3}>
          {technologies.map((tech, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {tech.category}
                  </Typography>
                  <List dense>
                    {tech.items.map((item, i) => (
                      <ListItem key={i}>
                        <ListItemIcon>
                          {tech.category === "Frontend" ? <CodeIcon /> :
                           tech.category === "Backend" ? <CloudIcon /> :
                           <BuildIcon />}
                        </ListItemIcon>
                        <ListItemText primary={item} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Future Ideas */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Future Ideas
        </Typography>
        <Grid container spacing={3}>
          {futureIdeas.map((idea, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {idea.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {idea.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Project Goals */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Project Goals
        </Typography>
        <List>
          <ListItem>
            <ListItemIcon>
              <PsychologyIcon color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="Democratize Data Access"
              secondary="Make database querying accessible to users without technical background"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <SecurityIcon color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="Ensure Data Security"
              secondary="Maintain data integrity and security while providing easy access"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <SpeedIcon color="primary" />
            </ListItemIcon>
            <ListItemText 
              primary="Optimize Performance"
              secondary="Provide fast and accurate responses to natural language queries"
            />
          </ListItem>
        </List>
      </Paper>
    </Box>
  );
}

export default About; 