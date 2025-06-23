#!/usr/bin/env python3
"""
Lightweight demo server for Railway free tier
Uses SQLite instead of PostgreSQL and in-memory cache instead of Redis
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import json
import sqlite3
from typing import Dict, List, Optional

# Add parent directory to Python path to find ml module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import from ml module
from ml.pricing_optimizer import DynamicPricingEngine, ProductFeatures, OptimizationObjective

# Create FastAPI app
app = FastAPI(
    title="Dynamic Pricing Engine - Demo",
    description="Free tier demo of ML-powered pricing optimization",
    version="1.0.0-demo"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
DEMO_PRODUCTS = {
    "DEMO-001": {
        "name": "Wireless Gaming Headset",
        "current_price": 89.99,
        "cost": 45.00,
        "category": "Gaming",
        "elasticity": -1.8,
        "competitor_avg": 79.99,
        "stock": 150
    },
    "DEMO-002": {
        "name": "Premium USB-C Hub",
        "current_price": 49.99,
        "cost": 22.00,
        "category": "Accessories",
        "elasticity": -2.5,
        "competitor_avg": 44.99,
        "stock": 200
    },
    "DEMO-003": {
        "name": "Mechanical Keyboard RGB",
        "current_price": 129.99,
        "cost": 65.00,
        "category": "Gaming",
        "elasticity": -1.2,
        "competitor_avg": 119.99,
        "stock": 75
    }
}

# Initialize ML engine
pricing_engine = DynamicPricingEngine()

# In-memory cache
cache = {}

@app.get("/")
async def root():
    return {
        "message": "Dynamic Pricing Engine - Demo Version",
        "status": "running",
        "limitations": [
            "Uses in-memory storage (data resets on restart)",
            "Limited to 3 demo products",
            "No database persistence",
            "No Redis caching"
        ],
        "endpoints": {
            "docs": "/docs",
            "products": "/api/products",
            "optimize": "/api/optimize/{product_id}",
            "demo": "/api/demo/impact"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0-demo",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/products")
async def get_products():
    """Get all demo products"""
    return {
        "products": [
            {
                "id": pid,
                **details,
                "margin": ((details["current_price"] - details["cost"]) / details["current_price"] * 100)
            }
            for pid, details in DEMO_PRODUCTS.items()
        ]
    }

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Get specific product details"""
    if product_id not in DEMO_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = DEMO_PRODUCTS[product_id]
    return {
        "id": product_id,
        **product,
        "margin": ((product["current_price"] - product["cost"]) / product["current_price"] * 100)
    }

@app.post("/api/optimize/{product_id}")
async def optimize_price(product_id: str, strategy: str = "balanced"):
    """Optimize price for a product"""
    if product_id not in DEMO_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = DEMO_PRODUCTS[product_id]
    
    # Create product features
    features = ProductFeatures(
        product_id=product_id,
        current_price=product["current_price"],
        cost=product["cost"],
        min_price=product["cost"] * 1.2,
        max_price=product["current_price"] * 1.3,
        stock_quantity=product["stock"],
        stock_velocity=5.0,
        elasticity=product["elasticity"],
        competitor_avg_price=product["competitor_avg"],
        competitor_min_price=product["competitor_avg"] * 0.95,
        market_position=product["current_price"] / product["competitor_avg"],
        days_since_last_change=7,
        category=product["category"],
        seasonality_factor=1.0,
        conversion_rate=0.03,
        return_rate=0.05
    )
    
    # Map strategy
    objective_map = {
        "revenue": OptimizationObjective.MAXIMIZE_REVENUE,
        "profit": OptimizationObjective.MAXIMIZE_PROFIT,
        "balanced": OptimizationObjective.BALANCED
    }
    objective = objective_map.get(strategy, OptimizationObjective.BALANCED)
    
    # Optimize
    result = pricing_engine.calculate_optimal_price(
        features,
        objective=objective,
        constraints={
            'max_change_pct': 0.20,
            'min_margin': 0.15,
            'max_above_market': 0.15
        }
    )
    
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "current_price": result.current_price,
        "optimal_price": result.optimal_price,
        "price_change": result.optimal_price - result.current_price,
        "price_change_pct": ((result.optimal_price - result.current_price) / result.current_price * 100),
        "expected_revenue_change": result.expected_revenue_change,
        "expected_profit_change": result.expected_profit_change,
        "confidence": result.confidence_score * 100,
        "constraints_applied": result.constraints_applied,
        "strategy_used": strategy
    }

@app.get("/api/demo/impact")
async def demo_impact():
    """Show potential impact across all products"""
    total_revenue_impact = 0
    optimizations = []
    
    for product_id, product in DEMO_PRODUCTS.items():
        # Create features
        features = ProductFeatures(
            product_id=product_id,
            current_price=product["current_price"],
            cost=product["cost"],
            min_price=product["cost"] * 1.2,
            max_price=product["current_price"] * 1.3,
            stock_quantity=product["stock"],
            stock_velocity=5.0,
            elasticity=product["elasticity"],
            competitor_avg_price=product["competitor_avg"],
            competitor_min_price=product["competitor_avg"] * 0.95,
            market_position=product["current_price"] / product["competitor_avg"],
            days_since_last_change=7,
            category=product["category"],
            seasonality_factor=1.0,
            conversion_rate=0.03,
            return_rate=0.05
        )
        
        # Optimize
        result = pricing_engine.calculate_optimal_price(features, OptimizationObjective.BALANCED)
        
        revenue_impact = result.expected_revenue_change
        total_revenue_impact += revenue_impact
        
        optimizations.append({
            "product": product["name"],
            "current_price": f"${product['current_price']:.2f}",
            "optimal_price": f"${result.optimal_price:.2f}",
            "revenue_impact": f"{revenue_impact:+.1f}%"
        })
    
    avg_impact = total_revenue_impact / len(DEMO_PRODUCTS)
    
    return {
        "demo_summary": {
            "products_analyzed": len(DEMO_PRODUCTS),
            "average_revenue_impact": f"{avg_impact:+.1f}%",
            "projected_monthly_impact": f"${avg_impact * 100000 / 100:,.0f}",  # Assuming $100k monthly revenue
            "optimizations": optimizations
        },
        "full_version_benefits": [
            "Unlimited products",
            "Historical data analysis",
            "A/B testing framework",
            "Competitor tracking",
            "Real-time optimization",
            "Advanced ML models",
            "PostgreSQL + Redis",
            "Production monitoring"
        ]
    }

@app.get("/api/demo/simulate")
async def simulate_optimization():
    """Simulate a week of optimizations"""
    results = []
    
    # Simulate 7 days
    for day in range(1, 8):
        daily_revenue = 0
        daily_changes = 0
        
        for product_id, product in DEMO_PRODUCTS.items():
            # Random chance of optimization
            import random
            if random.random() > 0.7:  # 30% chance
                daily_changes += 1
                # Simulate revenue impact
                impact = random.uniform(5, 15)
                daily_revenue += product["current_price"] * product["stock"] * (impact / 100)
        
        results.append({
            "day": f"Day {day}",
            "price_changes": daily_changes,
            "revenue_impact": f"${daily_revenue:,.0f}"
        })
    
    return {
        "simulation": "7-day optimization simulation",
        "results": results,
        "total_impact": f"${sum(float(r['revenue_impact'].replace('$', '').replace(',', '')) for r in results):,.0f}"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)