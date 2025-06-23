"""
Dynamic Pricing ML Engine
Multi-factor optimization for price recommendations
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OptimizationObjective(Enum):
    MAXIMIZE_REVENUE = "maximize_revenue"
    MAXIMIZE_PROFIT = "maximize_profit"
    MAXIMIZE_VOLUME = "maximize_volume"
    BALANCED = "balanced"

@dataclass
class ProductFeatures:
    """Features for a single product"""
    product_id: str
    current_price: float
    cost: float
    min_price: float
    max_price: float
    stock_quantity: int
    stock_velocity: float
    elasticity: float
    competitor_avg_price: float
    competitor_min_price: float
    market_position: float  # Our price / market avg
    days_since_last_change: int
    category: str
    seasonality_factor: float
    conversion_rate: float
    return_rate: float

@dataclass
class OptimizationResult:
    """Result from price optimization"""
    product_id: str
    current_price: float
    optimal_price: float
    expected_revenue_change: float
    expected_profit_change: float
    expected_volume_change: float
    confidence_score: float
    factors: Dict[str, float]
    constraints_applied: List[str]

class DynamicPricingEngine:
    def __init__(self):
        self.elasticity_model = Ridge(alpha=1.0)
        self.demand_forecast_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.poly_features = PolynomialFeatures(degree=2, include_bias=False)
        
    def calculate_optimal_price(
        self, 
        product: ProductFeatures,
        objective: OptimizationObjective = OptimizationObjective.BALANCED,
        constraints: Optional[Dict] = None
    ) -> OptimizationResult:
        """
        Calculate optimal price considering multiple factors
        """
        
        # Start with base calculations
        factors = {}
        
        # 1. Elasticity-based optimal price
        elasticity_price = self._calculate_elasticity_optimal(product)
        factors['elasticity'] = elasticity_price
        
        # 2. Competition-based adjustment
        competitive_price = self._calculate_competitive_price(product)
        factors['competition'] = competitive_price
        
        # 3. Inventory pressure adjustment
        inventory_price = self._calculate_inventory_price(product)
        factors['inventory'] = inventory_price
        
        # 4. Seasonality adjustment
        seasonal_price = self._apply_seasonality(product.current_price, product.seasonality_factor)
        factors['seasonality'] = seasonal_price
        
        # 5. Margin constraints
        margin_price = self._apply_margin_constraint(product)
        factors['margin'] = margin_price
        
        # Combine factors based on objective
        optimal_price = self._combine_factors(factors, product, objective)
        
        # Apply constraints
        optimal_price, constraints_applied = self._apply_constraints(
            optimal_price, product, constraints
        )
        
        # Calculate expected impacts
        revenue_change, profit_change, volume_change = self._calculate_impacts(
            product, optimal_price
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(product, factors)
        
        return OptimizationResult(
            product_id=product.product_id,
            current_price=product.current_price,
            optimal_price=round(optimal_price, 2),
            expected_revenue_change=round(revenue_change, 2),
            expected_profit_change=round(profit_change, 2),
            expected_volume_change=round(volume_change, 2),
            confidence_score=round(confidence, 2),
            factors={k: round(v, 2) for k, v in factors.items()},
            constraints_applied=constraints_applied
        )
    
    def _calculate_elasticity_optimal(self, product: ProductFeatures) -> float:
        """Calculate price based on elasticity"""
        if product.elasticity >= -1:
            # Inelastic: can increase price
            return product.current_price * 1.1
        else:
            # Elastic: optimize for revenue
            # Optimal price = cost * (elasticity / (1 + elasticity))
            if product.elasticity < -1:
                optimal_multiplier = product.elasticity / (1 + product.elasticity)
                return product.cost / optimal_multiplier
            else:
                return product.current_price
    
    def _calculate_competitive_price(self, product: ProductFeatures) -> float:
        """Adjust price based on competition"""
        if product.market_position > 1.1:
            # We're above market
            if product.elasticity < -2:
                # High elasticity: match market
                return product.competitor_avg_price * 0.98
            else:
                # Low elasticity: small adjustment
                return product.current_price * 0.95
        elif product.market_position < 0.9:
            # We're below market
            if product.elasticity > -1.5:
                # Low elasticity: can increase
                return product.competitor_avg_price * 0.95
            else:
                # High elasticity: stay competitive
                return product.current_price * 1.02
        else:
            # At market price
            return product.current_price
    
    def _calculate_inventory_price(self, product: ProductFeatures) -> float:
        """Adjust price based on inventory levels"""
        days_of_stock = product.stock_quantity / max(product.stock_velocity, 0.1)
        
        if days_of_stock > 60:
            # Excess inventory: reduce price
            reduction_factor = min(0.2, (days_of_stock - 60) / 100)
            return product.current_price * (1 - reduction_factor)
        elif days_of_stock < 7:
            # Low inventory: increase price
            increase_factor = min(0.15, (7 - days_of_stock) / 10)
            return product.current_price * (1 + increase_factor)
        else:
            # Normal inventory
            return product.current_price
    
    def _apply_seasonality(self, base_price: float, seasonality_factor: float) -> float:
        """Apply seasonal adjustments"""
        return base_price * seasonality_factor
    
    def _apply_margin_constraint(self, product: ProductFeatures) -> float:
        """Ensure minimum margin requirements"""
        min_margin_price = product.cost * 1.15  # 15% minimum margin
        return max(min_margin_price, product.min_price)
    
    def _combine_factors(
        self, 
        factors: Dict[str, float], 
        product: ProductFeatures,
        objective: OptimizationObjective
    ) -> float:
        """Combine different pricing factors based on objective"""
        
        weights = self._get_weights(objective, product)
        
        weighted_price = sum(
            factors[factor] * weights.get(factor, 0) 
            for factor in factors
        )
        
        return weighted_price
    
    def _get_weights(
        self, 
        objective: OptimizationObjective,
        product: ProductFeatures
    ) -> Dict[str, float]:
        """Get factor weights based on optimization objective"""
        
        if objective == OptimizationObjective.MAXIMIZE_REVENUE:
            return {
                'elasticity': 0.4,
                'competition': 0.3,
                'inventory': 0.1,
                'seasonality': 0.1,
                'margin': 0.1
            }
        elif objective == OptimizationObjective.MAXIMIZE_PROFIT:
            return {
                'elasticity': 0.2,
                'competition': 0.2,
                'inventory': 0.1,
                'seasonality': 0.1,
                'margin': 0.4
            }
        elif objective == OptimizationObjective.MAXIMIZE_VOLUME:
            return {
                'elasticity': 0.3,
                'competition': 0.4,
                'inventory': 0.2,
                'seasonality': 0.1,
                'margin': 0.0
            }
        else:  # BALANCED
            # Dynamic weights based on product characteristics
            weights = {
                'elasticity': 0.25,
                'competition': 0.25,
                'inventory': 0.2,
                'seasonality': 0.15,
                'margin': 0.15
            }
            
            # Adjust based on elasticity
            if abs(product.elasticity) > 2:
                weights['elasticity'] = 0.35
                weights['competition'] = 0.3
            
            # Adjust based on inventory
            days_of_stock = product.stock_quantity / max(product.stock_velocity, 0.1)
            if days_of_stock > 45 or days_of_stock < 14:
                weights['inventory'] = 0.3
                weights['seasonality'] = 0.1
            
            return weights
    
    def _apply_constraints(
        self, 
        price: float, 
        product: ProductFeatures,
        constraints: Optional[Dict] = None
    ) -> Tuple[float, List[str]]:
        """Apply business constraints to price"""
        
        applied = []
        
        # Hard constraints
        if price < product.min_price:
            price = product.min_price
            applied.append(f"min_price_constraint: ${product.min_price}")
        
        if price > product.max_price:
            price = product.max_price
            applied.append(f"max_price_constraint: ${product.max_price}")
        
        # Custom constraints
        if constraints:
            # Maximum price change per update
            if 'max_change_pct' in constraints:
                max_change = constraints['max_change_pct']
                price_change_pct = abs(price - product.current_price) / product.current_price
                
                if price_change_pct > max_change:
                    if price > product.current_price:
                        price = product.current_price * (1 + max_change)
                    else:
                        price = product.current_price * (1 - max_change)
                    applied.append(f"max_change_constraint: {max_change*100}%")
            
            # Competitive positioning constraint
            if 'max_above_market' in constraints:
                max_above = constraints['max_above_market']
                if price > product.competitor_avg_price * (1 + max_above):
                    price = product.competitor_avg_price * (1 + max_above)
                    applied.append(f"competitive_constraint: max {max_above*100}% above market")
            
            # Minimum margin constraint
            if 'min_margin' in constraints:
                min_margin = constraints['min_margin']
                min_price_for_margin = product.cost / (1 - min_margin)
                if price < min_price_for_margin:
                    price = min_price_for_margin
                    applied.append(f"margin_constraint: min {min_margin*100}% margin")
        
        return price, applied
    
    def _calculate_impacts(
        self, 
        product: ProductFeatures, 
        new_price: float
    ) -> Tuple[float, float, float]:
        """Calculate expected revenue, profit, and volume changes"""
        
        price_change_pct = (new_price - product.current_price) / product.current_price
        
        # Volume change based on elasticity
        volume_change_pct = price_change_pct * product.elasticity
        
        # Current metrics (baseline)
        current_volume = 100  # Normalized baseline
        current_revenue = current_volume * product.current_price
        current_profit = current_volume * (product.current_price - product.cost)
        
        # New metrics
        new_volume = current_volume * (1 + volume_change_pct)
        new_revenue = new_volume * new_price
        new_profit = new_volume * (new_price - product.cost)
        
        # Calculate changes
        revenue_change = ((new_revenue - current_revenue) / current_revenue) * 100
        profit_change = ((new_profit - current_profit) / current_profit) * 100
        volume_change = volume_change_pct * 100
        
        return revenue_change, profit_change, volume_change
    
    def _calculate_confidence(
        self, 
        product: ProductFeatures, 
        factors: Dict[str, float]
    ) -> float:
        """Calculate confidence score for the recommendation"""
        
        confidence = 1.0
        
        # Reduce confidence for extreme elasticity values
        if abs(product.elasticity) > 3:
            confidence *= 0.8
        
        # Reduce confidence for old price changes
        if product.days_since_last_change < 7:
            confidence *= 0.9
        
        # Reduce confidence for high price variance in factors
        prices = list(factors.values())
        if prices:
            cv = np.std(prices) / np.mean(prices)  # Coefficient of variation
            if cv > 0.2:
                confidence *= 0.85
        
        # Reduce confidence for extreme inventory situations
        days_of_stock = product.stock_quantity / max(product.stock_velocity, 0.1)
        if days_of_stock > 90 or days_of_stock < 3:
            confidence *= 0.85
        
        # Boost confidence for stable competitive environment
        if 0.95 <= product.market_position <= 1.05:
            confidence *= 1.1
        
        return min(confidence, 1.0)

    def batch_optimize(
        self,
        products: List[ProductFeatures],
        objective: OptimizationObjective = OptimizationObjective.BALANCED,
        constraints: Optional[Dict] = None
    ) -> List[OptimizationResult]:
        """Optimize prices for multiple products"""
        
        results = []
        
        # Group by category for better optimization
        category_groups = {}
        for product in products:
            if product.category not in category_groups:
                category_groups[product.category] = []
            category_groups[product.category].append(product)
        
        # Optimize within categories
        for category, category_products in category_groups.items():
            # Consider category-level dynamics
            category_avg_elasticity = np.mean([p.elasticity for p in category_products])
            
            for product in category_products:
                # Adjust optimization based on category dynamics
                result = self.calculate_optimal_price(product, objective, constraints)
                results.append(result)
        
        return results

class MLPricePredictor:
    """Machine learning model for demand prediction"""
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train(self, historical_data: pd.DataFrame):
        """Train the demand prediction model"""
        
        # Feature engineering
        features = self._prepare_features(historical_data)
        target = historical_data['units_sold']
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.model.fit(features_scaled, target)
        self.is_trained = True
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': features.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"Model trained. Top features: {feature_importance.head()}")
    
    def predict_demand(
        self, 
        price: float, 
        product_features: Dict,
        temporal_features: Dict
    ) -> float:
        """Predict demand at a given price point"""
        
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        # Prepare features
        features = pd.DataFrame([{
            'price': price,
            'price_relative_to_avg': price / product_features.get('avg_market_price', price),
            'elasticity': product_features.get('elasticity', -1.5),
            'stock_level': product_features.get('stock_quantity', 100),
            'days_since_launch': product_features.get('days_since_launch', 180),
            'competitor_min_price': product_features.get('competitor_min_price', price * 0.9),
            'day_of_week': temporal_features.get('day_of_week', 3),
            'month': temporal_features.get('month', 6),
            'is_holiday': temporal_features.get('is_holiday', 0),
            'seasonality_index': temporal_features.get('seasonality_index', 1.0)
        }])
        
        # Scale and predict
        features_scaled = self.scaler.transform(features)
        predicted_demand = self.model.predict(features_scaled)[0]
        
        return max(0, predicted_demand)
    
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for training"""
        
        features = pd.DataFrame()
        
        # Price features
        features['price'] = df['price']
        features['price_relative_to_avg'] = df['price'] / df.groupby('product_id')['price'].transform('mean')
        
        # Product features
        features['elasticity'] = df['elasticity']
        features['stock_level'] = df['stock_quantity']
        features['days_since_launch'] = (df['date'] - df.groupby('product_id')['date'].transform('min')).dt.days
        
        # Competition features
        features['competitor_min_price'] = df['competitor_min_price']
        features['price_vs_competition'] = df['price'] / df['competitor_min_price']
        
        # Temporal features
        features['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        features['month'] = pd.to_datetime(df['date']).dt.month
        features['is_holiday'] = df['is_holiday'].astype(int)
        features['seasonality_index'] = df['seasonality_index']
        
        return features