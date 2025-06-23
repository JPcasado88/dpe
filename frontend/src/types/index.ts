// Product related types
export interface Product {
  id: string;
  sku: string;
  name: string;
  description?: string;
  category: string;
  basePrice: number;
  currentPrice: number;
  minPrice?: number;
  maxPrice?: number;
  cost: number;
  stock: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Pricing related types
export interface PriceHistory {
  id: string;
  productId: string;
  price: number;
  timestamp: Date;
  source: 'manual' | 'optimization' | 'experiment' | 'competitor_match';
  reason?: string;
}

export interface PricingStrategy {
  id: string;
  name: string;
  type: 'competitive' | 'profit' | 'volume' | 'custom';
  parameters: {
    minMargin?: number;
    maxMargin?: number;
    competitorWeight?: number;
    demandElasticity?: number;
    customRules?: Array<{
      condition: string;
      action: string;
      value: number;
    }>;
  };
}

// Competitor related types
export interface Competitor {
  id: string;
  name: string;
  url: string;
  isActive: boolean;
  lastScraped?: Date;
  scrapeFrequency: 'hourly' | 'daily' | 'weekly';
  createdAt: Date;
  updatedAt: Date;
}

export interface CompetitorPrice {
  id: string;
  competitorId: string;
  productSku: string;
  productName: string;
  price: number;
  availability: 'in_stock' | 'out_of_stock' | 'unknown';
  scrapedAt: Date;
}

// Experiment related types
export interface Experiment {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'running' | 'paused' | 'completed';
  type: 'ab_test' | 'multi_variant' | 'time_based';
  startDate?: Date;
  endDate?: Date;
  products: string[]; // Product IDs
  control: {
    strategy: string;
    parameters: any;
  };
  variants: Array<{
    id: string;
    name: string;
    strategy: string;
    parameters: any;
    allocation: number; // Percentage of traffic
  }>;
  metrics: {
    primaryMetric: 'revenue' | 'conversion' | 'profit' | 'volume';
    secondaryMetrics: string[];
  };
  createdAt: Date;
  updatedAt: Date;
}

export interface ExperimentResult {
  experimentId: string;
  variantId: string;
  metrics: {
    revenue: number;
    conversions: number;
    conversionRate: number;
    averageOrderValue: number;
    profit: number;
    volume: number;
  };
  statistics: {
    confidence: number;
    pValue: number;
    uplift: number;
    isSignificant: boolean;
  };
}

// Analytics related types
export interface DashboardMetrics {
  totalRevenue: number;
  revenueChange: number;
  averageOrderValue: number;
  aovChange: number;
  conversionRate: number;
  conversionChange: number;
  activeProducts: number;
  activeExperiments: number;
  priceOptimizationImpact: number;
}

export interface RevenueData {
  date: Date;
  revenue: number;
  orders: number;
  averagePrice: number;
}

export interface PricePerformance {
  productId: string;
  productName: string;
  priceChanges: number;
  revenueImpact: number;
  volumeImpact: number;
  elasticity: number;
  optimalPrice: number;
  currentPrice: number;
}

// User and authentication types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'analyst' | 'viewer';
  permissions: string[];
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// API response types
export interface APIResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Form and UI types
export interface SelectOption {
  value: string;
  label: string;
}

export interface TableColumn<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  formatter?: (value: any) => string;
}

export interface FilterOptions {
  search?: string;
  category?: string;
  status?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}