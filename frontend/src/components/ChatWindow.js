import React, { useState, useEffect, useRef } from 'react';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
import axios from 'axios';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (message) => {
    setLoading(true);
    const userMessage = {
      type: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await axios.post(`${API_URL}/query`, { query: message });
      const { sql, results, analysis } = response.data;

      // Add SQL query
      setMessages((prev) => [
        ...prev,
        {
          type: 'sql',
          content: sql,
          timestamp: new Date().toISOString(),
        },
      ]);

      // Add results
      setMessages((prev) => [
        ...prev,
        {
          type: 'results',
          content: results,
          timestamp: new Date().toISOString(),
        },
      ]);

      // Add analysis
      setMessages((prev) => [
        ...prev,
        {
          type: 'analysis',
          content: analysis,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          type: 'error',
          content: error.response?.data?.error || 'An error occurred',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      <Paper
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Typography variant="h5" component="h1">
          Database Chatbot
        </Typography>
      </Paper>

      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      <MessageInput onSend={handleSend} loading={loading} />
    </Box>
  );
};

export default ChatWindow; 