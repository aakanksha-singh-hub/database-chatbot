// Create or replace with this content

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  IconButton, 
  CircularProgress, 
  Paper,
  Tooltip,
  Zoom,
  Fade
} from '@mui/material';
import { 
  Send as SendIcon
} from '@mui/icons-material';

const MessageInput = ({ onSend, loading }) => {
  const [message, setMessage] = useState('');
  const [scale, setScale] = useState(false);

  // Animation effect when loading state changes
  useEffect(() => {
    if (loading) {
      setScale(false);
    }
  }, [loading]);

  const handleChange = (e) => {
    setMessage(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !loading) {
      onSend(message);
      setMessage('');
      setScale(true);
      setTimeout(() => setScale(false), 300);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <Fade in={true} timeout={800}>
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderTop: '1px solid rgba(0, 0, 0, 0.05)',
          borderRadius: '0 0 24px 24px',
          background: 'white',
        }}
      >
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px' }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Ask about your database..."
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={loading}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '16px',
                backgroundColor: '#f8fafc',
                transition: 'all 0.3s ease',
                '&:hover': {
                  backgroundColor: '#f1f5f9',
                },
                '&.Mui-focused': {
                  backgroundColor: 'white',
                  boxShadow: '0 0 0 3px rgba(67, 97, 238, 0.15)',
                },
              },
            }}
            InputProps={{
              sx: { padding: '12px 16px' }
            }}
          />
          <Tooltip title={loading ? "Processing..." : "Send message"} placement="top" TransitionComponent={Zoom}>
            <Box sx={{ position: 'relative' }}>
              <IconButton
                type="submit"
                color="primary"
                disabled={!message.trim() || loading}
                sx={{
                  bgcolor: 'primary.main',
                  color: 'white',
                  borderRadius: '16px',
                  p: '12px',
                  minWidth: '48px',
                  height: '48px',
                  transition: 'all 0.3s ease',
                  transform: scale ? 'scale(0.9)' : 'scale(1)',
                  boxShadow: '0 4px 12px rgba(67, 97, 238, 0.2)',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 6px 16px rgba(67, 97, 238, 0.3)',
                  },
                  '&:disabled': {
                    bgcolor: 'action.disabledBackground',
                    color: 'action.disabled',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
              </IconButton>
            </Box>
          </Tooltip>
        </form>
      </Paper>
    </Fade>
  );
};

export default MessageInput;