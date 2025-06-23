// Price calculations
export const calculateMargin = (price: number, cost: number): number => {
  if (price === 0) return 0;
  return ((price - cost) / price) * 100;
};

export const calculateMarkup = (price: number, cost: number): number => {
  if (cost === 0) return 0;
  return ((price - cost) / cost) * 100;
};

export const calculatePriceFromMargin = (cost: number, marginPercent: number): number => {
  return cost / (1 - marginPercent / 100);
};

export const calculatePriceFromMarkup = (cost: number, markupPercent: number): number => {
  return cost * (1 + markupPercent / 100);
};

// Price elasticity calculations
export const calculatePriceElasticity = (
  oldPrice: number,
  newPrice: number,
  oldQuantity: number,
  newQuantity: number
): number => {
  if (oldPrice === 0 || oldQuantity === 0) return 0;
  
  const percentChangeQuantity = ((newQuantity - oldQuantity) / oldQuantity) * 100;
  const percentChangePrice = ((newPrice - oldPrice) / oldPrice) * 100;
  
  if (percentChangePrice === 0) return 0;
  
  return percentChangeQuantity / percentChangePrice;
};

// Revenue calculations
export const calculateRevenue = (price: number, quantity: number): number => {
  return price * quantity;
};

export const calculateProfit = (revenue: number, cost: number, quantity: number): number => {
  return revenue - (cost * quantity);
};

export const calculateROI = (profit: number, investment: number): number => {
  if (investment === 0) return 0;
  return (profit / investment) * 100;
};

// Statistical calculations
export const calculateAverage = (values: number[]): number => {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
};

export const calculateMedian = (values: number[]): number => {
  if (values.length === 0) return 0;
  
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  
  if (sorted.length % 2 === 0) {
    return (sorted[middle - 1] + sorted[middle]) / 2;
  }
  
  return sorted[middle];
};

export const calculateStandardDeviation = (values: number[]): number => {
  if (values.length === 0) return 0;
  
  const mean = calculateAverage(values);
  const squaredDifferences = values.map(val => Math.pow(val - mean, 2));
  const variance = calculateAverage(squaredDifferences);
  
  return Math.sqrt(variance);
};

// Percentage calculations
export const calculatePercentageChange = (oldValue: number, newValue: number): number => {
  if (oldValue === 0) return newValue === 0 ? 0 : 100;
  return ((newValue - oldValue) / oldValue) * 100;
};

export const calculatePercentageOfTotal = (value: number, total: number): number => {
  if (total === 0) return 0;
  return (value / total) * 100;
};

// Competitive pricing calculations
export const calculateCompetitivePrice = (
  competitorPrices: number[],
  strategy: 'match' | 'beat' | 'premium',
  adjustment: number = 0
): number => {
  if (competitorPrices.length === 0) return 0;
  
  const avgCompetitorPrice = calculateAverage(competitorPrices);
  
  switch (strategy) {
    case 'match':
      return avgCompetitorPrice;
    case 'beat':
      return avgCompetitorPrice * (1 - adjustment / 100);
    case 'premium':
      return avgCompetitorPrice * (1 + adjustment / 100);
    default:
      return avgCompetitorPrice;
  }
};

// Optimization calculations
export const calculateOptimalPrice = (
  baseCost: number,
  targetMargin: number,
  competitorPrice: number,
  competitorWeight: number,
  minPrice: number,
  maxPrice: number
): number => {
  const marginBasedPrice = calculatePriceFromMargin(baseCost, targetMargin);
  const weightedPrice = marginBasedPrice * (1 - competitorWeight) + competitorPrice * competitorWeight;
  
  // Ensure price is within bounds
  return Math.max(minPrice, Math.min(maxPrice, weightedPrice));
};

// Conversion calculations
export const calculateConversionRate = (conversions: number, visitors: number): number => {
  if (visitors === 0) return 0;
  return (conversions / visitors) * 100;
};

export const calculateAbandonmentRate = (started: number, completed: number): number => {
  if (started === 0) return 0;
  return ((started - completed) / started) * 100;
};

// Forecasting calculations
export const calculateLinearTrend = (data: { x: number; y: number }[]): { slope: number; intercept: number } => {
  if (data.length < 2) return { slope: 0, intercept: 0 };
  
  const n = data.length;
  const sumX = data.reduce((sum, point) => sum + point.x, 0);
  const sumY = data.reduce((sum, point) => sum + point.y, 0);
  const sumXY = data.reduce((sum, point) => sum + point.x * point.y, 0);
  const sumX2 = data.reduce((sum, point) => sum + point.x * point.x, 0);
  
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  
  return { slope, intercept };
};

export const forecastValue = (slope: number, intercept: number, x: number): number => {
  return slope * x + intercept;
};

// Experiment calculations
export const calculateStatisticalSignificance = (
  controlConversions: number,
  controlVisitors: number,
  variantConversions: number,
  variantVisitors: number,
  confidenceLevel: number = 0.95
): { isSignificant: boolean; pValue: number } => {
  // Simplified z-test for proportions
  const p1 = controlConversions / controlVisitors;
  const p2 = variantConversions / variantVisitors;
  const p = (controlConversions + variantConversions) / (controlVisitors + variantVisitors);
  
  const se = Math.sqrt(p * (1 - p) * (1 / controlVisitors + 1 / variantVisitors));
  const z = Math.abs(p1 - p2) / se;
  
  // Approximate p-value (two-tailed)
  const pValue = 2 * (1 - normalCDF(z));
  
  return {
    isSignificant: pValue < (1 - confidenceLevel),
    pValue,
  };
};

// Helper function for normal CDF approximation
const normalCDF = (z: number): number => {
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;
  
  const sign = z < 0 ? -1 : 1;
  z = Math.abs(z) / Math.sqrt(2);
  
  const t = 1 / (1 + p * z);
  const y = 1 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-z * z);
  
  return 0.5 * (1 + sign * y);
};