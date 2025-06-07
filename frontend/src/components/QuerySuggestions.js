import React from 'react';
import { Paper, Box, Typography, Button } from '@mui/material';

function QuerySuggestions({ suggestions, onSuggestionClick }) {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Typography variant="subtitle1" gutterBottom>
        Suggested Questions:
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {suggestions.map((suggestion, index) => (
          <Button
            key={index}
            variant="outlined"
            size="small"
            onClick={() => onSuggestionClick(suggestion)}
            sx={{
              textTransform: 'none',
              borderRadius: 2,
              '&:hover': {
                backgroundColor: 'primary.light',
                color: 'white'
              }
            }}
          >
            {suggestion}
          </Button>
        ))}
      </Box>
    </Paper>
  );
}

export default QuerySuggestions; 