import React from 'react';
import ProductList from '../components/ProductList';

const ProductsPage: React.FC = () => {
  // In a real app, you would fetch products from API
  const mockProducts = [
    {
      id: '1',
      sku: 'SKU001',
      name: 'Premium Widget',
      currentPrice: 29.99,
      basePrice: 24.99,
      stock: 150,
      category: 'Widgets',
    },
    {
      id: '2',
      sku: 'SKU002',
      name: 'Deluxe Gadget',
      currentPrice: 49.99,
      basePrice: 45.99,
      stock: 75,
      category: 'Gadgets',
    },
    {
      id: '3',
      sku: 'SKU003',
      name: 'Standard Component',
      currentPrice: 19.99,
      basePrice: 19.99,
      stock: 200,
      category: 'Components',
    },
  ];

  return (
    <div className="products-page">
      <ProductList products={mockProducts} />
    </div>
  );
};

export default ProductsPage;