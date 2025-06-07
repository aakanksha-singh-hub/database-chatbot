import React, { useState } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Button,
  Box,
  Typography,
  Menu,
  MenuItem,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  FileDownload as DownloadIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  ShowChart as LineChartIcon,
  Calculate as StatsIcon
} from '@mui/icons-material';

function ResultsTable({ data, onVisualize }) {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [anchorEl, setAnchorEl] = useState(null);
  const [statsAnchorEl, setStatsAnchorEl] = useState(null);

  if (!Array.isArray(data) || data.length === 0) {
    return null;
  }

  const columns = Object.keys(data[0]);

  const handleExport = async (format) => {
    try {
      const response = await fetch(`/api/export?format=${format}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ data }),
      });
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `query-results.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export error:', error);
    }
    setAnchorEl(null);
  };

  const calculateStats = (column) => {
    const values = data.map(row => row[column]);
    const numericValues = values.filter(v => typeof v === 'number');
    
    if (numericValues.length === 0) return null;

    return {
      count: numericValues.length,
      mean: numericValues.reduce((a, b) => a + b, 0) / numericValues.length,
      min: Math.min(...numericValues),
      max: Math.max(...numericValues),
      std: Math.sqrt(
        numericValues.reduce((a, b) => a + Math.pow(b - (numericValues.reduce((c, d) => c + d, 0) / numericValues.length), 2), 0) / numericValues.length
      )
    };
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Query Results</Typography>
        <Box>
          <Tooltip title="Statistics">
            <IconButton onClick={(e) => setStatsAnchorEl(e.currentTarget)}>
              <StatsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Visualize">
            <IconButton onClick={() => onVisualize(data)}>
              <BarChartIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Export">
            <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <TableContainer sx={{ maxHeight: 440 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell key={column}>{column}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((row, index) => (
                <TableRow hover key={index}>
                  {columns.map((column) => (
                    <TableCell key={column}>{row[column]}</TableCell>
                  ))}
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[10, 25, 100]}
        component="div"
        count={data.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => handleExport('csv')}>CSV</MenuItem>
        <MenuItem onClick={() => handleExport('xlsx')}>Excel</MenuItem>
        <MenuItem onClick={() => handleExport('json')}>JSON</MenuItem>
        <MenuItem onClick={() => handleExport('sql')}>SQL</MenuItem>
      </Menu>

      <Menu
        anchorEl={statsAnchorEl}
        open={Boolean(statsAnchorEl)}
        onClose={() => setStatsAnchorEl(null)}
      >
        {columns.map((column) => {
          const stats = calculateStats(column);
          if (!stats) return null;
          
          return (
            <MenuItem key={column} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
              <Typography variant="subtitle2">{column}</Typography>
              <Typography variant="body2">
                Count: {stats.count}<br />
                Mean: {stats.mean.toFixed(2)}<br />
                Min: {stats.min}<br />
                Max: {stats.max}<br />
                Std Dev: {stats.std.toFixed(2)}
              </Typography>
            </MenuItem>
          );
        })}
      </Menu>
    </Paper>
  );
}

export default ResultsTable; 