import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 
  (window.location.hostname === 'dpe-fe-production.up.railway.app' 
    ? 'https://web-production-343d.up.railway.app' 
    : window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://web-production-343d.up.railway.app');

console.log('API_BASE_URL:', API_BASE_URL);
console.log('REACT_APP_API_URL:', process.env.REACT_APP_API_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    console.log('Making request to:', config.url);
    console.log('Full URL:', (config.baseURL || '') + (config.url || ''));
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data);
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Product APIs
export const productAPI = {
  getAll: () => api.get('/api/v1/products'),
  getById: (id: string) => api.get(`/api/v1/products/${id}`),
  create: (data: any) => api.post('/api/v1/products', data),
  update: (id: string, data: any) => api.put(`/api/v1/products/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/products/${id}`),
  updatePrice: (id: string, price: number) => api.patch(`/api/v1/products/${id}/price`, { price }),
};

// Pricing APIs
export const pricingAPI = {
  optimize: (productIds: string[], strategy: string) => 
    api.post('/api/v1/pricing/optimize', { productIds, strategy }),
  getHistory: (productId: string) => api.get(`/api/v1/pricing/history/${productId}`),
  getCurrentPrices: () => api.get('/api/v1/pricing/current'),
};

// Competitor APIs
export const competitorAPI = {
  getAll: () => api.get('/api/v1/competitors'),
  getById: (id: string) => api.get(`/api/v1/competitors/${id}`),
  create: (data: any) => api.post('/api/v1/competitors', data),
  update: (id: string, data: any) => api.put(`/api/v1/competitors/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/competitors/${id}`),
  scrape: (id: string) => api.post(`/api/v1/competitors/${id}/scrape`),
  getPrices: (competitorId: string) => api.get(`/api/v1/competitors/${competitorId}/prices`),
};

// Experiment APIs
export const experimentAPI = {
  getAll: () => api.get('/api/v1/experiments'),
  getById: (id: string) => api.get(`/api/v1/experiments/${id}`),
  create: (data: any) => api.post('/api/v1/experiments', data),
  update: (id: string, data: any) => api.put(`/api/v1/experiments/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/experiments/${id}`),
  start: (id: string) => api.post(`/api/v1/experiments/${id}/start`),
  pause: (id: string) => api.post(`/api/v1/experiments/${id}/pause`),
  stop: (id: string) => api.post(`/api/v1/experiments/${id}/stop`),
  getResults: (id: string) => api.get(`/api/v1/experiments/${id}/results`),
};

// Analytics APIs
export const analyticsAPI = {
  getDashboard: () => api.get('/api/v1/analytics/dashboard'),
  getRevenue: (startDate: string, endDate: string) => 
    api.get('/api/v1/analytics/revenue', { params: { startDate, endDate } }),
  getPricePerformance: (productId?: string) => 
    api.get('/api/v1/analytics/price-performance', { params: { productId } }),
  getExperimentSummary: () => api.get('/api/v1/analytics/experiments'),
};

// Utility function to handle API errors
export const handleAPIError = (error: any): string => {
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export default api;