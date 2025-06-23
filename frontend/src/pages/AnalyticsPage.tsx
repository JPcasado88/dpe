import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  InfoOutlined,
  TrendingUp,
  TrendingDown,
  Download
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine
} from 'recharts';
import { format, subDays } from 'date-fns';
import api from '../services/api';
import './AnalyticsPage.css';

interface MetricData {
  date: string;
  revenue: number;
  profit: number;
  volume: number;
  conversion: number;
}

interface ElasticityPoint {
  price: number;
  demand: number;
}

interface ExperimentResult {
  id: number;
  name: string;
  products: number;
  duration: number;
  revenue_impact: number;
  conversion_change: number;
  status: string;
  confidence: number;
}

const AnalyticsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState(30);
  const [metricType, setMetricType] = useState<'revenue' | 'profit' | 'volume' | 'conversion'>('revenue');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
  // Data states
  const [metricsData, setMetricsData] = useState<MetricData[]>([]);
  const [elasticityData, setElasticityData] = useState<ElasticityPoint[]>([]);
  const [experiments, setExperiments] = useState<ExperimentResult[]>([]);
  const [summary, setSummary] = useState({
    totalRevenue: 0,
    totalProfit: 0,
    avgConversion: 0,
    optimizationImpact: 0
  });

  useEffect(() => {
    fetchAnalyticsData();
  }, [dateRange, selectedCategory]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      const endDate = new Date();
      const startDate = subDays(endDate, dateRange);
      
      // Fetch metrics data
      const metricsResponse = await api.post('/analytics/dashboard', {
        metrics: ['revenue', 'profit', 'volume', 'conversion'],
        start_date: format(startDate, 'yyyy-MM-dd'),
        end_date: format(endDate, 'yyyy-MM-dd'),
        granularity: dateRange > 90 ? 'weekly' : 'daily',
        categories: selectedCategory !== 'all' ? [selectedCategory] : undefined
      });
      
      // Process metrics data
      if (metricsResponse.data.data_points) {
        setMetricsData(metricsResponse.data.data_points.map((point: any) => ({
          date: format(new Date(point.date), 'MMM dd'),
          revenue: point.metrics.revenue || 0,
          profit: point.metrics.profit || 0,
          volume: point.metrics.volume || 0,
          conversion: (point.metrics.conversion || 0) * 100
        })));
        
        setSummary({
          totalRevenue: metricsResponse.data.summary.total_revenue || 0,
          totalProfit: metricsResponse.data.summary.total_profit || 0,
          avgConversion: (metricsResponse.data.summary.avg_conversion || 0) * 100,
          optimizationImpact: 12.7 // This would come from the API
        });
      }
      
      // Mock elasticity data (would come from real API)
      const mockElasticityData = [];
      for (let i = 50; i <= 150; i += 5) {
        const price = i;
        const basedemand = 100;
        const elasticity = -2.1; // Example elasticity
        const priceChange = (price - 100) / 100;
        const demandChange = priceChange * elasticity;
        const demand = basedemand * (1 + demandChange);
        mockElasticityData.push({ price, demand: Math.max(0, demand) });
      }
      setElasticityData(mockElasticityData);
      
      // Fetch experiments
      const experimentsResponse = await api.get('/experiments?status=completed');
      if (experimentsResponse.data) {
        setExperiments(experimentsResponse.data.slice(0, 5).map((exp: any) => ({
          id: exp.id,
          name: exp.name,
          products: exp.product_count || 0,
          duration: 14, // Would calculate from dates
          revenue_impact: Math.random() * 10000 - 2000, // Mock data
          conversion_change: Math.random() * 2 - 0.5, // Mock data
          status: exp.status,
          confidence: 0.95 // Mock data
        })));
      }
      
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMetricValue = (data: MetricData) => {
    switch (metricType) {
      case 'revenue': return data.revenue;
      case 'profit': return data.profit;
      case 'volume': return data.volume;
      case 'conversion': return data.conversion;
      default: return data.revenue;
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box className="analytics-page" sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Analytics & Insights
        </Typography>
        
        <Box display="flex" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Date Range</InputLabel>
            <Select
              value={dateRange}
              label="Date Range"
              onChange={(e) => setDateRange(e.target.value as number)}
            >
              <MenuItem value={7}>Last 7 days</MenuItem>
              <MenuItem value={30}>Last 30 days</MenuItem>
              <MenuItem value={90}>Last 90 days</MenuItem>
              <MenuItem value={365}>Last year</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={selectedCategory}
              label="Category"
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <MenuItem value="all">All Categories</MenuItem>
              <MenuItem value="Phone Accessories">Phone Accessories</MenuItem>
              <MenuItem value="Premium Audio">Premium Audio</MenuItem>
              <MenuItem value="Gaming Accessories">Gaming Accessories</MenuItem>
              <MenuItem value="Smart Home">Smart Home</MenuItem>
            </Select>
          </FormControl>
          
          <IconButton>
            <Download />
          </IconButton>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="overline">
                Total Revenue
              </Typography>
              <Typography variant="h5" component="div" fontWeight="bold">
                {formatCurrency(summary.totalRevenue)}
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                <TrendingUp sx={{ color: '#4caf50', fontSize: 20, mr: 0.5 }} />
                <Typography variant="body2" color="success.main">
                  +{summary.optimizationImpact}% from optimization
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="overline">
                Total Profit
              </Typography>
              <Typography variant="h5" component="div" fontWeight="bold">
                {formatCurrency(summary.totalProfit)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {((summary.totalProfit / summary.totalRevenue) * 100).toFixed(1)}% margin
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="overline">
                Avg Conversion Rate
              </Typography>
              <Typography variant="h5" component="div" fontWeight="bold">
                {summary.avgConversion.toFixed(2)}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Industry avg: 2.5%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="overline">
                Active Optimizations
              </Typography>
              <Typography variant="h5" component="div" fontWeight="bold">
                247
              </Typography>
              <Typography variant="body2" color="primary">
                Across all products
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Chart */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Performance Trends
          </Typography>
          
          <ToggleButtonGroup
            value={metricType}
            exclusive
            onChange={(e, value) => value && setMetricType(value)}
            size="small"
          >
            <ToggleButton value="revenue">Revenue</ToggleButton>
            <ToggleButton value="profit">Profit</ToggleButton>
            <ToggleButton value="volume">Volume</ToggleButton>
            <ToggleButton value="conversion">Conversion</ToggleButton>
          </ToggleButtonGroup>
        </Box>
        
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={metricsData}>
            <defs>
              <linearGradient id="colorMetric" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2196f3" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#2196f3" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <RechartsTooltip />
            <Area
              type="monotone"
              dataKey={(data) => getMetricValue(data)}
              stroke="#2196f3"
              fillOpacity={1}
              fill="url(#colorMetric)"
              name={metricType.charAt(0).toUpperCase() + metricType.slice(1)}
            />
          </AreaChart>
        </ResponsiveContainer>
      </Paper>

      <Grid container spacing={3}>
        {/* Price Elasticity Chart */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                Price Elasticity Curve
              </Typography>
              <Tooltip title="Shows how demand changes with price">
                <IconButton size="small">
                  <InfoOutlined fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            
            <ResponsiveContainer width="100%" height={320}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="price" 
                  name="Price" 
                  unit="$"
                  domain={['dataMin - 10', 'dataMax + 10']}
                />
                <YAxis 
                  dataKey="demand" 
                  name="Demand" 
                  unit=" units"
                />
                <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter 
                  name="Price vs Demand" 
                  data={elasticityData} 
                  fill="#ff9800"
                  line={{ stroke: '#ff9800', strokeWidth: 2 }}
                />
                <ReferenceLine x={100} stroke="#666" strokeDasharray="5 5" label="Current Price" />
              </ScatterChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Experiment Results */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 400, overflow: 'auto' }}>
            <Typography variant="h6" mb={2}>
              Recent Experiment Results
            </Typography>
            
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Experiment</TableCell>
                    <TableCell align="right">Revenue Impact</TableCell>
                    <TableCell align="right">Confidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {experiments.map((exp) => (
                    <TableRow key={exp.id}>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {exp.name}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {exp.products} products • {exp.duration} days
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={formatCurrency(exp.revenue_impact)}
                          color={exp.revenue_impact > 0 ? 'success' : 'error'}
                          size="small"
                          icon={exp.revenue_impact > 0 ? <TrendingUp /> : <TrendingDown />}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" color="textSecondary">
                          {(exp.confidence * 100).toFixed(0)}%
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AnalyticsPage;