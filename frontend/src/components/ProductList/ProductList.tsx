import React, { useState } from 'react';
import './ProductList.css';

interface Product {
  id: string;
  sku: string;
  name: string;
  currentPrice: number;
  basePrice: number;
  stock: number;
  category: string;
}

interface ProductListProps {
  products?: Product[];
}

const ProductList: React.FC<ProductListProps> = ({ products = [] }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<keyof Product>('name');

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedProducts = [...filteredProducts].sort((a, b) => {
    if (sortBy === 'currentPrice' || sortBy === 'basePrice' || sortBy === 'stock') {
      return Number(a[sortBy]) - Number(b[sortBy]);
    }
    return String(a[sortBy]).localeCompare(String(b[sortBy]));
  });

  return (
    <div className="product-list">
      <div className="product-list-header">
        <h2>Products</h2>
        <div className="product-list-controls">
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as keyof Product)}
            className="sort-select"
          >
            <option value="name">Sort by Name</option>
            <option value="currentPrice">Sort by Price</option>
            <option value="stock">Sort by Stock</option>
            <option value="category">Sort by Category</option>
          </select>
        </div>
      </div>

      <div className="product-table-container">
        <table className="product-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Category</th>
              <th>Base Price</th>
              <th>Current Price</th>
              <th>Stock</th>
              <th>Price Change</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedProducts.map(product => {
              const priceChange = ((product.currentPrice - product.basePrice) / product.basePrice * 100).toFixed(2);
              return (
                <tr key={product.id}>
                  <td>{product.sku}</td>
                  <td>{product.name}</td>
                  <td>{product.category}</td>
                  <td>${product.basePrice.toFixed(2)}</td>
                  <td>${product.currentPrice.toFixed(2)}</td>
                  <td>{product.stock}</td>
                  <td className={Number(priceChange) > 0 ? 'positive' : Number(priceChange) < 0 ? 'negative' : ''}>
                    {Number(priceChange) > 0 ? '+' : ''}{priceChange}%
                  </td>
                  <td>
                    <button className="action-btn">View Details</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sortedProducts.length === 0 && (
          <div className="no-products">
            No products found. Try adjusting your search criteria.
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductList;