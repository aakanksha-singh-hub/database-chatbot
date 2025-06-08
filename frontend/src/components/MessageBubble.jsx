// Create or replace with this content

import React from 'react';
import { Box, Typography, Paper, Avatar, Chip, Fade } from '@mui/material';
import { format } from 'date-fns';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { 
  Code as CodeIcon, 
  Storage as StorageIcon,
  Analytics as AnalyticsIcon,
  Error as ErrorIcon,
  Android as UserIcon,
  SmartToy as BotIcon
} from '@mui/icons-material';
import ResultsTable from './ResultsTable';

const MessageBubble = ({ message }) => {
  const isUser = message.type === 'user';
  const timestamp = message.timestamp ? format(new Date(message.timestamp), 'HH:mm') : '';

  const renderContent = () => {
    switch (message.type) {
      case 'user':
        return (
          <Typography variant="body1">{message.content}</Typography>
        );
      case 'sql':
        return (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <CodeIcon fontSize="small" sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="subtitle2" color="text.secondary" fontWeight={600}>
                Generated SQL
              </Typography>
            </Box>
            <Fade in={true} timeout={500}>
              <Box sx={{ borderRadius: 2, overflow: 'hidden' }}>
                <SyntaxHighlighter 
                  language="sql" 
                  style={vs2015}
                  customStyle={{ 
                    borderRadius: '12px',
                    margin: 0,
                    fontSize: '14px'
                  }}
                >
                  {message.content}
                </SyntaxHighlighter>
              </Box>
            </Fade>
          </Box>
        );
      case 'results':
        return (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <StorageIcon fontSize="small" sx={{ mr: 1, color: 'info.main' }} />
              <Typography variant="subtitle2" color="text.secondary" fontWeight={600}>
                Results
              </Typography>
              <Chip 
                size="small" 
                label={`${Array.isArray(message.content) ? message.content.length : 0} rows`}
                sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
              />
            </Box>
            <Paper 
              sx={{ 
                p: 2, 
                overflowX: 'auto', 
                bgcolor: '#f8fafc',
                borderRadius: 2,
                transition: 'all 0.3s ease',
                '&:hover': {
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                },
              }}
            >
              <Fade in={true} timeout={600}>
                <Box>
                  <ResultsTable data={message.content} />
                </Box>
              </Fade>
            </Paper>
          </Box>
        );
      case 'analysis':
        return (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <AnalyticsIcon fontSize="small" sx={{ mr: 1, color: 'success.main' }} />
              <Typography variant="subtitle2" color="text.secondary" fontWeight={600}>
                Analysis
              </Typography>
            </Box>
            <Fade in={true} timeout={700}>
              <Paper 
                sx={{ 
                  p: 2,
                  bgcolor: '#f8fafc',
                  borderRadius: 2,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                  },
                }}
              >
                <Typography 
                  sx={{ 
                    whiteSpace: 'pre-line',
                    fontSize: '14px',
                    lineHeight: 1.6 
                  }}
                >
                  {message.content}
                </Typography>
              </Paper>
            </Fade>
          </Box>
        );
      case 'error':
        return (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <ErrorIcon fontSize="small" sx={{ mr: 1, color: 'error.main' }} />
              <Typography variant="subtitle2" color="error" fontWeight={600}>
                Error
              </Typography>
            </Box>
            <Fade in={true} timeout={500}>
              <Paper 
                sx={{ 
                  p: 2, 
                  bgcolor: '#fff5f5',
                  borderRadius: 2,
                  border: '1px solid #fee2e2',
                }}
              >
                <Typography color="error.main">{message.content}</Typography>
              </Paper>
            </Fade>
          </Box>
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
        mb: 3,
        position: 'relative',
      }}
    >
      {!isUser && message.type !== 'sql' && message.type !== 'results' && message.type !== 'analysis' && message.type !== 'error' && (
        <Avatar
          sx={{
            bgcolor: 'primary.main',
            width: 36,
            height: 36,
            mr: 1.5,
            boxShadow: '0 2px 8px rgba(67, 97, 238, 0.2)',
          }}
        >
          <BotIcon fontSize="small" />
        </Avatar>
      )}
      
      <Box
        sx={{
          maxWidth: message.type === 'results' || message.type === 'analysis' ? '85%' : '70%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Fade in={true} timeout={400}>
          <Paper
            elevation={0}
            sx={{
              p: message.type === 'user' ? 2 : (message.type === 'sql' || message.type === 'results' || message.type === 'analysis' || message.type === 'error') ? 2 : 2,
              bgcolor: isUser ? 'primary.main' : 'background.paper',
              color: isUser ? 'white' : 'text.primary',
              borderRadius: 3,
              position: 'relative',
              ...(message.type === 'sql' || message.type === 'results' || message.type === 'analysis' || message.type === 'error' ? {
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
                borderRadius: 3,
              } : {})
            }}
          >
            {renderContent()}
          </Paper>
        </Fade>
        
        {timestamp && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ 
              mt: 0.5, 
              alignSelf: isUser ? 'flex-end' : 'flex-start',
              fontSize: '0.7rem',
              opacity: 0.8
            }}
          >
            {timestamp}
          </Typography>
        )}
      </Box>
      
      {isUser && (
        <Avatar
          sx={{
            bgcolor: 'secondary.main',
            width: 36,
            height: 36,
            ml: 1.5,
            boxShadow: '0 2px 8px rgba(247, 37, 133, 0.2)',
          }}
        >
          <UserIcon fontSize="small" />
        </Avatar>
      )}
    </Box>
  );
};

export default MessageBubble;