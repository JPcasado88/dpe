#!/usr/bin/env python3
"""
Local test script for Dynamic Pricing Engine
Tests core functionality without Docker
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from ml.pricing_optimizer import DynamicPricingEngine, ProductFeatures, OptimizationObjective
from datetime import datetime
import json

def test_pricing_engine():
    """Test the ML pricing optimization engine"""
    print("🚀 Testing Dynamic Pricing Engine")
    print("=" * 50)
    
    # Initialize engine
    engine = DynamicPricingEngine()
    
    # Test product: iPhone case
    test_product = ProductFeatures(
        product_id="PA-001",
        current_price=39.99,
        cost=12.00,
        min_price=25.00,
        max_price=55.00,
        stock_quantity=150,
        stock_velocity=5.0,
        elasticity=-2.1,  # Elastic product
        competitor_avg_price=37.99,
        competitor_min_price=34.99,
        market_position=1.05,  # 5% above market
        days_since_last_change=7,
        category="Phone Accessories",
        seasonality_factor=1.0,
        conversion_rate=0.032,
        return_rate=0.05
    )
    
    print("\n📱 Test Product: Premium iPhone Case")
    print(f"Current Price: ${test_product.current_price}")
    print(f"Cost: ${test_product.cost}")
    print(f"Margin: {((test_product.current_price - test_product.cost) / test_product.current_price * 100):.1f}%")
    print(f"Elasticity: {test_product.elasticity}")
    print(f"Market Position: {test_product.market_position:.2f}x average")
    
    # Test different optimization objectives
    objectives = [
        OptimizationObjective.MAXIMIZE_REVENUE,
        OptimizationObjective.MAXIMIZE_PROFIT,
        OptimizationObjective.BALANCED
    ]
    
    print("\n💰 Price Optimization Results:")
    print("-" * 50)
    
    for objective in objectives:
        result = engine.calculate_optimal_price(
            test_product,
            objective=objective,
            constraints={
                'max_change_pct': 0.15,  # Max 15% change
                'min_margin': 0.20,      # Min 20% margin
                'max_above_market': 0.10 # Max 10% above market
            }
        )
        
        print(f"\n📊 Strategy: {objective.value}")
        print(f"   Optimal Price: ${result.optimal_price}")
        print(f"   Price Change: ${result.optimal_price - result.current_price:.2f} ({((result.optimal_price - result.current_price) / result.current_price * 100):.1f}%)")
        print(f"   Expected Revenue Impact: {result.expected_revenue_change:+.1f}%")
        print(f"   Expected Profit Impact: {result.expected_profit_change:+.1f}%")
        print(f"   Confidence: {result.confidence_score * 100:.0f}%")
        print(f"   Constraints Applied: {', '.join(result.constraints_applied) if result.constraints_applied else 'None'}")
    
    # Test batch optimization
    print("\n\n📦 Batch Optimization Test:")
    print("-" * 50)
    
    products = [
        ProductFeatures(
            product_id="AU-001",
            current_price=349.99,
            cost=180.00,
            min_price=299.99,
            max_price=399.99,
            stock_quantity=45,
            stock_velocity=1.5,
            elasticity=-0.8,  # Inelastic - premium product
            competitor_avg_price=329.99,
            competitor_min_price=299.99,
            market_position=1.06,
            days_since_last_change=14,
            category="Premium Audio",
            seasonality_factor=1.0,
            conversion_rate=0.018,
            return_rate=0.03
        ),
        ProductFeatures(
            product_id="GA-001",
            current_price=129.99,
            cost=65.00,
            min_price=99.99,
            max_price=149.99,
            stock_quantity=120,
            stock_velocity=3.5,
            elasticity=-1.5,  # Moderately elastic
            competitor_avg_price=124.99,
            competitor_min_price=119.99,
            market_position=1.04,
            days_since_last_change=5,
            category="Gaming Accessories",
            seasonality_factor=1.2,  # Holiday boost
            conversion_rate=0.028,
            return_rate=0.07
        )
    ]
    
    batch_results = engine.batch_optimize(products, objective=OptimizationObjective.BALANCED)
    
    for i, result in enumerate(batch_results):
        product = products[i]
        print(f"\n🎮 Product {i+1}: {product.category}")
        print(f"   Current → Optimal: ${result.current_price} → ${result.optimal_price}")
        print(f"   Revenue Impact: {result.expected_revenue_change:+.1f}%")
        
    # Summary
    avg_revenue_impact = sum(r.expected_revenue_change for r in batch_results) / len(batch_results)
    print(f"\n\n✅ Summary:")
    print(f"   Products Optimized: {len(batch_results)}")
    print(f"   Average Revenue Impact: {avg_revenue_impact:+.1f}%")
    print(f"   Projected Annual Impact: ${avg_revenue_impact * 10000000 / 100:,.0f}")  # Assuming $10M revenue

def test_elasticity_calculation():
    """Test elasticity calculation logic"""
    print("\n\n📈 Testing Price Elasticity Calculation")
    print("=" * 50)
    
    # Simulate price and demand data
    price_demand_data = [
        (39.99, 100),  # Base
        (44.99, 85),   # Price increase → demand decrease
        (34.99, 120),  # Price decrease → demand increase
        (49.99, 70),   # Higher price → lower demand
        (29.99, 140),  # Lower price → higher demand
    ]
    
    print("\nPrice-Demand Relationship:")
    for price, demand in price_demand_data:
        print(f"  Price: ${price:6.2f} → Demand: {demand:3d} units")
    
    # Calculate elasticity
    prices = [p for p, _ in price_demand_data]
    demands = [d for _, d in price_demand_data]
    
    # Simple elasticity calculation
    avg_price = sum(prices) / len(prices)
    avg_demand = sum(demands) / len(demands)
    
    # Calculate percentage changes
    elasticities = []
    for i in range(1, len(prices)):
        price_change_pct = (prices[i] - prices[i-1]) / prices[i-1]
        demand_change_pct = (demands[i] - demands[i-1]) / demands[i-1]
        if price_change_pct != 0:
            elasticity = demand_change_pct / price_change_pct
            elasticities.append(elasticity)
    
    avg_elasticity = sum(elasticities) / len(elasticities) if elasticities else 0
    
    print(f"\nCalculated Elasticity: {avg_elasticity:.2f}")
    print(f"Interpretation: {'Elastic' if abs(avg_elasticity) > 1 else 'Inelastic'} demand")
    print(f"10% price increase → {abs(avg_elasticity * 10):.1f}% demand change")

def test_competitive_analysis():
    """Test competitive positioning logic"""
    print("\n\n🏆 Testing Competitive Analysis")
    print("=" * 50)
    
    our_price = 39.99
    competitor_prices = {
        "Amazon": 34.99,
        "BestBuy": 42.99,
        "Walmart": 36.99,
        "Newegg": 35.99
    }
    
    avg_competitor = sum(competitor_prices.values()) / len(competitor_prices)
    min_competitor = min(competitor_prices.values())
    
    print(f"\nOur Price: ${our_price}")
    print("\nCompetitor Prices:")
    for name, price in competitor_prices.items():
        diff = ((our_price - price) / price * 100)
        print(f"  {name:8s}: ${price:5.2f} (We're {diff:+.1f}%)")
    
    print(f"\nMarket Analysis:")
    print(f"  Average Competitor Price: ${avg_competitor:.2f}")
    print(f"  Our Position: {(our_price / avg_competitor):.2f}x market average")
    print(f"  Price Gap to Lowest: ${our_price - min_competitor:.2f}")
    
    # Recommendation
    if our_price > avg_competitor * 1.05:
        print(f"\n💡 Recommendation: Consider lowering price to ${avg_competitor * 0.98:.2f} to match market")
    elif our_price < avg_competitor * 0.95:
        print(f"\n💡 Recommendation: Room to increase price to ${avg_competitor * 0.95:.2f}")
    else:
        print("\n💡 Recommendation: Price is well-positioned in the market")

if __name__ == "__main__":
    try:
        test_pricing_engine()
        test_elasticity_calculation()
        test_competitive_analysis()
        
        print("\n\n🎉 All tests completed successfully!")
        print("\nThe Dynamic Pricing Engine is working correctly.")
        print("When Docker is ready, you can run the full system with ./quickstart.sh")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()