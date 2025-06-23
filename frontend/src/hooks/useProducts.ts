import { useState, useEffect, useCallback } from 'react';
import { Product } from '../types';
import { productAPI, handleAPIError } from '../services/api';

interface UseProductsResult {
  products: Product[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
  createProduct: (product: Partial<Product>) => Promise<void>;
  updateProduct: (id: string, updates: Partial<Product>) => Promise<void>;
  deleteProduct: (id: string) => Promise<void>;
  updatePrice: (id: string, price: number) => Promise<void>;
}

export const useProducts = (): UseProductsResult => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await productAPI.getAll();
      setProducts(response.data);
    } catch (err) {
      setError(handleAPIError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const createProduct = async (product: Partial<Product>) => {
    try {
      setError(null);
      const response = await productAPI.create(product);
      setProducts([...products, response.data]);
    } catch (err) {
      setError(handleAPIError(err));
      throw err;
    }
  };

  const updateProduct = async (id: string, updates: Partial<Product>) => {
    try {
      setError(null);
      const response = await productAPI.update(id, updates);
      setProducts(products.map(p => p.id === id ? response.data : p));
    } catch (err) {
      setError(handleAPIError(err));
      throw err;
    }
  };

  const deleteProduct = async (id: string) => {
    try {
      setError(null);
      await productAPI.delete(id);
      setProducts(products.filter(p => p.id !== id));
    } catch (err) {
      setError(handleAPIError(err));
      throw err;
    }
  };

  const updatePrice = async (id: string, price: number) => {
    try {
      setError(null);
      const response = await productAPI.updatePrice(id, price);
      setProducts(products.map(p => p.id === id ? { ...p, currentPrice: price } : p));
    } catch (err) {
      setError(handleAPIError(err));
      throw err;
    }
  };

  return {
    products,
    loading,
    error,
    refresh: fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    updatePrice,
  };
};

// Hook for individual product
export const useProduct = (id: string) => {
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await productAPI.getById(id);
        setProduct(response.data);
      } catch (err) {
        setError(handleAPIError(err));
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchProduct();
    }
  }, [id]);

  return { product, loading, error };
};