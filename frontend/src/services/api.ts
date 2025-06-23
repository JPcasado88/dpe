import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth token
api.interceptors.request.use(
  (config) => {
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
  getAll: () => api.get('/api/products'),
  getById: (id: string) => api.get(`/api/products/${id}`),
  create: (data: any) => api.post('/api/products', data),
  update: (id: string, data: any) => api.put(`/api/products/${id}`, data),
  delete: (id: string) => api.delete(`/api/products/${id}`),
  updatePrice: (id: string, price: number) => api.patch(`/api/products/${id}/price`, { price }),
};

// Pricing APIs
export const pricingAPI = {
  optimize: (productIds: string[], strategy: string) => 
    api.post('/api/pricing/optimize', { productIds, strategy }),
  getHistory: (productId: string) => api.get(`/api/pricing/history/${productId}`),
  getCurrentPrices: () => api.get('/api/pricing/current'),
};

// Competitor APIs
export const competitorAPI = {
  getAll: () => api.get('/api/competitors'),
  getById: (id: string) => api.get(`/api/competitors/${id}`),
  create: (data: any) => api.post('/api/competitors', data),
  update: (id: string, data: any) => api.put(`/api/competitors/${id}`, data),
  delete: (id: string) => api.delete(`/api/competitors/${id}`),
  scrape: (id: string) => api.post(`/api/competitors/${id}/scrape`),
  getPrices: (competitorId: string) => api.get(`/api/competitors/${competitorId}/prices`),
};

// Experiment APIs
export const experimentAPI = {
  getAll: () => api.get('/api/experiments'),
  getById: (id: string) => api.get(`/api/experiments/${id}`),
  create: (data: any) => api.post('/api/experiments', data),
  update: (id: string, data: any) => api.put(`/api/experiments/${id}`, data),
  delete: (id: string) => api.delete(`/api/experiments/${id}`),
  start: (id: string) => api.post(`/api/experiments/${id}/start`),
  pause: (id: string) => api.post(`/api/experiments/${id}/pause`),
  stop: (id: string) => api.post(`/api/experiments/${id}/stop`),
  getResults: (id: string) => api.get(`/api/experiments/${id}/results`),
};

// Analytics APIs
export const analyticsAPI = {
  getDashboard: () => api.get('/api/analytics/dashboard'),
  getRevenue: (startDate: string, endDate: string) => 
    api.get('/api/analytics/revenue', { params: { startDate, endDate } }),
  getPricePerformance: (productId?: string) => 
    api.get('/api/analytics/price-performance', { params: { productId } }),
  getExperimentSummary: () => api.get('/api/analytics/experiments'),
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