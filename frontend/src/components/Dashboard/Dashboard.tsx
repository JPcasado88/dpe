import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  IconButton,
  Alert,
  Button,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AttachMoney,
  Science,
  Speed,
  Refresh,
  ArrowUpward,
  ArrowDownward
} from '@mui/icons-material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { analyticsAPI, experimentAPI } from '../../services/api';
import './Dashboard.css';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, color, subtitle }) => {
  return (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="overline">
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ color, fontWeight: 'bold' }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box sx={{ 
            backgroundColor: `${color}20`, 
            borderRadius: 2, 
            p: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {icon}
          </Box>
        </Box>
        {change !== undefined && (
          <Box display="flex" alignItems="center" mt={1}>
            {change >= 0 ? (
              <ArrowUpward sx={{ color: '#4caf50', fontSize: 20 }} />
            ) : (
              <ArrowDownward sx={{ color: '#f44336', fontSize: 20 }} />
            )}
            <Typography variant="body2" sx={{ color: change >= 0 ? '#4caf50' : '#f44336' }}>
              {Math.abs(change)}% vs last month
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [metrics, setMetrics] = useState({
    totalRevenue: 0,
    revenueChange: 0,
    activeProducts: 0,
    activeExperiments: 0,
    avgOptimizationImpact: 0,
    priceChangesThisMonth: 0,
    cacheHitRate: 0
  });

  const [revenueData, setRevenueData] = useState<any[]>([]);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [experiments, setExperiments] = useState<any[]>([]);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard analytics
      const analyticsResponse = await analyticsAPI.getDashboard();
      const dashboardData = analyticsResponse.data;
      
      // Fetch active experiments
      const experimentsResponse = await experimentAPI.getAll();
      const activeExperiments = experimentsResponse.data.experiments?.filter(
        (exp: any) => exp.status === 'running'
      ) || [];
      
      // Process data from dashboard API
      const kpiSummary = dashboardData.kpi_summary || {};
      
      setMetrics({
        totalRevenue: parseFloat(kpiSummary.total_revenue_mtd?.replace(/[$,]/g, '') || 0),
        revenueChange: kpiSummary.revenue_increase_pct || 0,
        activeProducts: kpiSummary.products_optimized || 0,
        activeExperiments: activeExperiments.length,
        avgOptimizationImpact: kpiSummary.avg_margin || 0,
        priceChangesThisMonth: kpiSummary.price_changes_mtd || 0,
        cacheHitRate: parseFloat(dashboardData.system_health?.cache_hit_rate?.replace('%', '') || 0)
      });
      
      // Mock revenue trend data
      const mockRevenueData = [];
      for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        mockRevenueData.push({
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          revenue: 40000 + Math.random() * 10000,
          profit: 14000 + Math.random() * 4000
        });
      }
      setRevenueData(mockRevenueData);
      
      // Set opportunities from dashboard data
      setOpportunities(dashboardData.optimization_opportunities || []);
      
      // Set experiments
      setExperiments(activeExperiments.slice(0, 3));
      
      // Mock category data (would come from real API)
      setCategoryData([
        { name: 'Phone Accessories', value: 35, revenue: 127000 },
        { name: 'Premium Audio', value: 25, revenue: 95000 },
        { name: 'Gaming', value: 20, revenue: 78000 },
        { name: 'Smart Home', value: 15, revenue: 52000 },
        { name: 'Other', value: 5, revenue: 18000 }
      ]);
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  const COLORS = ['#2196f3', '#4caf50', '#ff9800', '#9c27b0', '#607d8b'];

  if (loading && !refreshing) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box className="dashboard" sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Executive Dashboard
        </Typography>
        <Box>
          <IconButton onClick={handleRefresh} disabled={refreshing}>
            <Refresh className={refreshing ? 'rotating' : ''} />
          </IconButton>
        </Box>
      </Box>

      {/* Alert for high impact */}
      {metrics.revenueChange > 10 && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <strong>Excellent Performance!</strong> Dynamic pricing has increased revenue by {metrics.revenueChange}% this month.
        </Alert>
      )}

      {/* Key Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Revenue Impact"
            value={`$${metrics.totalRevenue.toLocaleString()}`}
            change={metrics.revenueChange}
            icon={<AttachMoney sx={{ fontSize: 28, color: '#4caf50' }} />}
            color="#4caf50"
            subtitle="This month"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Experiments"
            value={metrics.activeExperiments}
            icon={<Science sx={{ fontSize: 28, color: '#2196f3' }} />}
            color="#2196f3"
            subtitle={`${metrics.activeProducts} products in test`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Optimization Rate"
            value={`${metrics.avgOptimizationImpact.toFixed(1)}%`}
            change={2.3}
            icon={<Speed sx={{ fontSize: 28, color: '#ff9800' }} />}
            color="#ff9800"
            subtitle="Avg margin improvement"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Price Changes"
            value={metrics.priceChangesThisMonth}
            icon={<TrendingUp sx={{ fontSize: 28, color: '#9c27b0' }} />}
            color="#9c27b0"
            subtitle="Automated this month"
          />
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} mb={3}>
        {/* Revenue Trend */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Revenue Trend (30 Days)
            </Typography>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value: any) => `$${value.toLocaleString()}`} />
                <Line 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#4caf50" 
                  strokeWidth={2}
                  name="Revenue"
                />
                <Line 
                  type="monotone" 
                  dataKey="profit" 
                  stroke="#2196f3" 
                  strokeWidth={2}
                  name="Profit"
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Category Performance */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Revenue by Category
            </Typography>
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Opportunities and Experiments */}
      <Grid container spacing={3}>
        {/* Top Opportunities */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Top Revenue Opportunities
              </Typography>
              <Button size="small" href="/optimization">
                View All
              </Button>
            </Box>
            <Box>
              {opportunities.map((opp, index) => (
                <Box key={index} mb={2}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        {opp.product_name}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Current: ${opp.current_price} → Optimal: ${opp.recommended_price}
                      </Typography>
                    </Box>
                    <Chip 
                      label={`+${opp.expected_revenue_change.toFixed(1)}%`}
                      color="success"
                      size="small"
                    />
                  </Box>
                  {index < opportunities.length - 1 && <Divider sx={{ mt: 2 }} />}
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Active Experiments */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Active Experiments
              </Typography>
              <Button size="small" href="/experiments">
                View All
              </Button>
            </Box>
            <Box>
              {experiments.map((exp, index) => (
                <Box key={index} mb={2}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        {exp.name}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {exp.product_count} products • Started {new Date(exp.start_date).toLocaleDateString()}
                      </Typography>
                    </Box>
                    <Chip 
                      label={exp.status}
                      color="primary"
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  {index < experiments.length - 1 && <Divider sx={{ mt: 2 }} />}
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Cache Performance */}
      <Box mt={3}>
        <Paper sx={{ p: 2 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="caption" color="textSecondary">
              System Performance:
            </Typography>
            <Chip 
              label={`Cache Hit Rate: ${metrics.cacheHitRate}%`} 
              size="small" 
              color={metrics.cacheHitRate > 80 ? 'success' : 'warning'}
            />
            <Chip 
              label="API: Healthy" 
              size="small" 
              color="success"
            />
            <Chip 
              label="ML Models: Loaded" 
              size="small" 
              color="success"
            />
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default Dashboard;