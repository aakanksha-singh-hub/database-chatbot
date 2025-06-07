import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { format } from 'date-fns';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const MessageBubble = ({ message }) => {
  const isUser = message.type === 'user';
  const timestamp = message.timestamp ? format(new Date(message.timestamp), 'HH:mm') : '';

  const renderContent = () => {
    switch (message.type) {
      case 'sql':
        return (
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Generated SQL:</Typography>
            <SyntaxHighlighter language="sql" style={docco}>
              {message.content}
            </SyntaxHighlighter>
          </Box>
        );
      case 'results':
        return (
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Results:</Typography>
            <Paper sx={{ p: 2, overflowX: 'auto' }}>
              <pre>{JSON.stringify(message.content, null, 2)}</pre>
            </Paper>
          </Box>
        );
      case 'analysis':
        return (
          <Box>
            <Typography variant="subtitle2" color="text.secondary">Analysis:</Typography>
            <Paper sx={{ p: 2 }}>
              <Typography>{message.content}</Typography>
            </Paper>
          </Box>
        );
      case 'error':
        return (
          <Paper sx={{ p: 2, bgcolor: '#ffebee' }}>
            <Typography color="error">{message.content}</Typography>
          </Paper>
        );
      default:
        return <Typography>{message.content}</Typography>;
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Box
        sx={{
          maxWidth: '70%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Paper
          sx={{
            p: 2,
            bgcolor: isUser ? '#e3f2fd' : '#f5f5f5',
            borderRadius: 2,
          }}
        >
          {renderContent()}
        </Paper>
        {timestamp && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mt: 0.5, alignSelf: isUser ? 'flex-end' : 'flex-start' }}
          >
            {timestamp}
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default MessageBubble; 