import { useState, useEffect, useCallback } from 'react';
import { PriceHistory, PricingStrategy, CompetitorPrice } from '../types';
import { pricingAPI, competitorAPI, handleAPIError } from '../services/api';

interface UsePricingResult {
  priceHistory: PriceHistory[];
  loading: boolean;
  error: string | null;
  optimizePrices: (productIds: string[], strategy: string) => Promise<void>;
  getCurrentPrices: () => Promise<{ [productId: string]: number }>;
  refresh: () => void;
}

export const usePricing = (productId?: string): UsePricingResult => {
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPriceHistory = useCallback(async () => {
    if (!productId) return;
    
    try {
      setLoading(true);
      setError(null);
      const response = await pricingAPI.getHistory(productId);
      setPriceHistory(response.data);
    } catch (err) {
      setError(handleAPIError(err));
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    if (productId) {
      fetchPriceHistory();
    }
  }, [fetchPriceHistory, productId]);

  const optimizePrices = async (productIds: string[], strategy: string) => {
    try {
      setError(null);
      await pricingAPI.optimize(productIds, strategy);
      // Refresh price history if we're tracking a specific product
      if (productId && productIds.includes(productId)) {
        await fetchPriceHistory();
      }
    } catch (err) {
      setError(handleAPIError(err));
      throw err;
    }
  };

  const getCurrentPrices = async () => {
    try {
      const response = await pricingAPI.getCurrentPrices();
      return response.data;
    } catch (err) {
      setError(handleAPIError(err));
      throw err;
    }
  };

  return {
    priceHistory,
    loading,
    error,
    optimizePrices,
    getCurrentPrices,
    refresh: fetchPriceHistory,
  };
};

// Hook for competitor prices
interface UseCompetitorPricesResult {
  competitorPrices: CompetitorPrice[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export const useCompetitorPrices = (competitorId?: string): UseCompetitorPricesResult => {
  const [competitorPrices, setCompetitorPrices] = useState<CompetitorPrice[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCompetitorPrices = useCallback(async () => {
    if (!competitorId) return;
    
    try {
      setLoading(true);
      setError(null);
      const response = await competitorAPI.getPrices(competitorId);
      setCompetitorPrices(response.data);
    } catch (err) {
      setError(handleAPIError(err));
    } finally {
      setLoading(false);
    }
  }, [competitorId]);

  useEffect(() => {
    if (competitorId) {
      fetchCompetitorPrices();
    }
  }, [fetchCompetitorPrices, competitorId]);

  return {
    competitorPrices,
    loading,
    error,
    refresh: fetchCompetitorPrices,
  };
};

// Hook for pricing strategies
interface UsePricingStrategiesResult {
  strategies: PricingStrategy[];
  loading: boolean;
  error: string | null;
  applyStrategy: (strategyId: string, productIds: string[]) => Promise<void>;
}

export const usePricingStrategies = (): UsePricingStrategiesResult => {
  const [strategies, setStrategies] = useState<PricingStrategy[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock strategies for now
  useEffect(() => {
    setStrategies([
      {
        id: '1',
        name: 'Competitive Pricing',
        type: 'competitive',
        parameters: {
          competitorWeight: 0.7,
          minMargin: 15,
        },
      },
      {
        id: '2',
        name: 'Profit Maximization',
        type: 'profit',
        parameters: {
          minMargin: 30,
          maxMargin: 50,
          demandElasticity: 1.2,
        },
      },
      {
        id: '3',
        name: 'Volume Optimization',
        type: 'volume',
        parameters: {
          minMargin: 10,
          competitorWeight: 0.9,
        },
      },
    ]);
  }, []);

  const applyStrategy = async (strategyId: string, productIds: string[]) => {
    try {
      setError(null);
      const strategy = strategies.find(s => s.id === strategyId);
      if (!strategy) throw new Error('Strategy not found');
      
      await pricingAPI.optimize(productIds, strategy.type);
    } catch (err) {
      setError(handleAPIError(err));
      throw err;
    }
  };

  return {
    strategies,
    loading,
    error,
    applyStrategy,
  };
};