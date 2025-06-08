import React, { useState } from 'react';
import { Container, Box, Typography, TextField, Button, Paper, Alert, Snackbar, InputAdornment, IconButton } from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';

const ConnectPage = () => {
  const [form, setForm] = useState({ server: '', database: '', username: '', password: '' });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const validate = () => {
    const newErrors = {};
    if (!form.server.trim()) newErrors.server = 'Server name is required.';
    if (!form.database.trim()) newErrors.database = 'Database name is required.';
    if (!form.username.trim()) newErrors.username = 'Username is required.';
    if (!form.password) newErrors.password = 'Password is required.';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: undefined });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrorMsg('');
    setSuccess(false);
    try {
      // Call backend to test connection (replace with your backend route)
      const response = await fetch('/api/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Connection failed');
      }
      // Simulate session storage (replace with secure session logic)
      sessionStorage.setItem('db_connected', 'true');
      sessionStorage.setItem('db_name', form.database);
      setSuccess(true);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Paper elevation={4} sx={{ p: { xs: 2, md: 4 }, borderRadius: 3, boxShadow: 3 }}>
        <Typography variant="h4" fontWeight={700} color="primary" gutterBottom>
          Connect to Your Azure SQL Database
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Enter your database credentials below. All fields are required.
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            label="Server Name"
            name="server"
            value={form.server}
            onChange={handleChange}
            error={!!errors.server}
            helperText={errors.server}
            fullWidth
            autoComplete="off"
            variant="outlined"
            InputProps={{ sx: { borderRadius: 2 } }}
          />
          <TextField
            label="Database Name"
            name="database"
            value={form.database}
            onChange={handleChange}
            error={!!errors.database}
            helperText={errors.database}
            fullWidth
            autoComplete="off"
            variant="outlined"
            InputProps={{ sx: { borderRadius: 2 } }}
          />
          <TextField
            label="Username"
            name="username"
            value={form.username}
            onChange={handleChange}
            error={!!errors.username}
            helperText={errors.username}
            fullWidth
            autoComplete="off"
            variant="outlined"
            InputProps={{ sx: { borderRadius: 2 } }}
          />
          <TextField
            label="Password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            value={form.password}
            onChange={handleChange}
            error={!!errors.password}
            helperText={errors.password}
            fullWidth
            autoComplete="off"
            variant="outlined"
            InputProps={{
              sx: { borderRadius: 2 },
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowPassword((v) => !v)} edge="end" tabIndex={-1}>
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            size="large"
            sx={{ borderRadius: 2, fontWeight: 700, mt: 1 }}
            disabled={loading}
          >
            {loading ? 'Connecting...' : 'Explore Dataset'}
          </Button>
        </Box>
        <Snackbar
          open={!!errorMsg}
          autoHideDuration={6000}
          onClose={() => setErrorMsg('')}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert severity="error" onClose={() => setErrorMsg('')} sx={{ width: '100%' }}>
            {errorMsg}
          </Alert>
        </Snackbar>
        <Snackbar
          open={success}
          autoHideDuration={4000}
          onClose={() => setSuccess(false)}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert severity="success" sx={{ width: '100%' }}>
            Connected successfully! You can now explore your dataset.
          </Alert>
        </Snackbar>
      </Paper>
    </Container>
  );
};

export default ConnectPage; 