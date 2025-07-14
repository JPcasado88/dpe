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
        "features": {
            "docs": "/docs - Interactive API Documentation",
            "dashboard": "/api/analytics/dashboard - Executive KPI Dashboard",
            "products": "/api/products - View Demo Products",
            "optimize": "/api/optimize/{product_id} - ML Price Optimization",
            "experiments": "/api/experiments - A/B Testing Results",
            "elasticity": "/api/analytics/elasticity/{product_id} - Price Elasticity Analysis",
            "competitors": "/api/competitors/{product_id} - Competitor Intelligence",
            "impact": "/api/demo/impact - Revenue Impact Summary"
        },
        "try_these": [
            "/docs - Best place to start!",
            "/api/analytics/dashboard - See executive metrics",
            "/api/experiments - View A/B test results",
            "/api/demo/impact - See potential revenue lift"
        ]
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

@app.post("/api/optimize/recommendations")
async def get_price_recommendations(request_body: dict):
    """Get price recommendations for multiple products"""
    product_ids = request_body.get("product_ids", [])
    strategy = request_body.get("strategy", "balanced")
    constraints = request_body.get("constraints", {})
    
    recommendations = []
    
    for product_id in product_ids:
        if product_id not in DEMO_PRODUCTS:
            continue
            
        product = DEMO_PRODUCTS[product_id]
        
        # Create product features
        features = ProductFeatures(
            product_id=product_id,
            current_price=product["current_price"],
            cost=product["cost"],
            min_price=constraints.get("min_price", product["cost"] * 1.2),
            max_price=constraints.get("max_price", product["current_price"] * 1.5),
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
            "maximize_profit": OptimizationObjective.MAXIMIZE_PROFIT,
            "maximize_volume": OptimizationObjective.MAXIMIZE_VOLUME,
            "competitive": OptimizationObjective.BALANCED,
            "balanced": OptimizationObjective.BALANCED
        }
        objective = objective_map.get(strategy, OptimizationObjective.BALANCED)
        
        # Optimize
        result = pricing_engine.calculate_optimal_price(
            features,
            objective=objective,
            constraints={
                'max_change_pct': constraints.get("max_change_pct", 0.20),
                'min_margin': constraints.get("min_margin", 0.15),
                'max_above_market': constraints.get("max_above_market", 0.15)
            }
        )
        
        recommendations.append({
            "productId": product_id,
            "productName": product["name"],
            "currentPrice": result.current_price,
            "optimalPrice": result.optimal_price,
            "expectedRevenueIncrease": result.expected_revenue_change,
            "confidence": result.confidence_score
        })
    
    return {
        "recommendations": recommendations,
        "strategy": strategy,
        "totalProducts": len(recommendations),
        "avgRevenueIncrease": sum(r["expectedRevenueIncrease"] for r in recommendations) / len(recommendations) if recommendations else 0
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

# In-memory storage for A/B tests
DEMO_EXPERIMENTS = {}

@app.get("/api/experiments")
async def get_experiments():
    """Get all A/B test experiments"""
    return {
        "experiments": [
            {
                "id": "EXP-001",
                "name": "Gaming Headset Holiday Pricing",
                "product_id": "DEMO-001",
                "status": "completed",
                "control_price": 89.99,
                "variant_price": 79.99,
                "control_conversions": 245,
                "variant_conversions": 312,
                "control_revenue": 22047.55,
                "variant_revenue": 24956.88,
                "confidence": 94.5,
                "winner": "variant",
                "revenue_lift": "+13.2%",
                "started_at": "2024-12-15",
                "ended_at": "2024-12-22"
            },
            {
                "id": "EXP-002", 
                "name": "USB-C Hub Price Elasticity Test",
                "product_id": "DEMO-002",
                "status": "running",
                "control_price": 49.99,
                "variant_price": 44.99,
                "control_conversions": 123,
                "variant_conversions": 156,
                "control_revenue": 6148.77,
                "variant_revenue": 7018.44,
                "confidence": 78.3,
                "winner": "too_early",
                "revenue_lift": "+14.1%",
                "started_at": "2024-12-20",
                "ended_at": None
            }
        ],
        "summary": {
            "active_experiments": 1,
            "completed_experiments": 1,
            "total_revenue_lift": "$3,856",
            "avg_confidence": 86.4
        }
    }

@app.post("/api/experiments/create")
async def create_experiment(
    product_id: str,
    variant_price: float,
    name: str = None
):
    """Create a new A/B test experiment"""
    if product_id not in DEMO_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = DEMO_PRODUCTS[product_id]
    exp_id = f"EXP-{len(DEMO_EXPERIMENTS) + 3:03d}"
    
    experiment = {
        "id": exp_id,
        "name": name or f"{product['name']} Price Test",
        "product_id": product_id,
        "status": "running",
        "control_price": product["current_price"],
        "variant_price": variant_price,
        "control_conversions": 0,
        "variant_conversions": 0,
        "control_revenue": 0,
        "variant_revenue": 0,
        "confidence": 0,
        "started_at": datetime.utcnow().isoformat()
    }
    
    DEMO_EXPERIMENTS[exp_id] = experiment
    
    return {
        "experiment": experiment,
        "message": "A/B test created successfully",
        "estimated_duration": "7-14 days for statistical significance"
    }

@app.get("/api/analytics/dashboard")
async def analytics_dashboard():
    """Get executive dashboard metrics"""
    return {
        "kpi_summary": {
            "total_revenue_mtd": "$1,234,567",
            "revenue_from_optimization": "$156,789",
            "revenue_increase_pct": 12.7,
            "products_optimized": 312,
            "price_changes_mtd": 1247,
            "avg_margin": 42.3,
            "margin_improvement": 2.1
        },
        "recent_wins": [
            {
                "product": "Wireless Gaming Headset",
                "action": "Reduced price by $10",
                "impact": "+$5,200/mo revenue",
                "confidence": 92
            },
            {
                "product": "Premium USB-C Hub", 
                "action": "Matched competitor price",
                "impact": "+$3,100/mo revenue",
                "confidence": 88
            },
            {
                "product": "Mechanical Keyboard RGB",
                "action": "Increased price by $10",
                "impact": "+$2,800/mo revenue", 
                "confidence": 85
            }
        ],
        "optimization_opportunities": [
            {
                "product_id": "DEMO-003",
                "product_name": "Mechanical Keyboard RGB",
                "current_price": 129.99,
                "recommended_price": 119.99,
                "expected_impact": "+8.5% revenue",
                "reason": "Competitor undercut by 8%"
            }
        ],
        "system_health": {
            "api_uptime": "99.98%",
            "avg_response_time": "45ms",
            "optimizations_today": 47,
            "cache_hit_rate": "92%"
        }
    }

@app.get("/api/analytics/elasticity/{product_id}")
async def get_elasticity_analysis(product_id: str):
    """Get price elasticity analysis for a product"""
    if product_id not in DEMO_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = DEMO_PRODUCTS[product_id]
    
    # Simulate elasticity curve data
    price_points = []
    base_price = product["current_price"]
    base_demand = 100
    
    for i in range(-30, 31, 5):  # -30% to +30% price range
        price_pct_change = i / 100
        price = base_price * (1 + price_pct_change)
        demand_pct_change = price_pct_change * product["elasticity"]
        demand = base_demand * (1 + demand_pct_change)
        revenue = price * demand
        
        price_points.append({
            "price": round(price, 2),
            "demand": round(demand),
            "revenue": round(revenue, 2),
            "price_change_pct": i
        })
    
    optimal_point = max(price_points, key=lambda x: x["revenue"])
    
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "current_elasticity": product["elasticity"],
        "interpretation": "Elastic" if abs(product["elasticity"]) > 1 else "Inelastic",
        "price_sensitivity": "High" if abs(product["elasticity"]) > 2 else "Moderate" if abs(product["elasticity"]) > 1 else "Low",
        "elasticity_curve": price_points,
        "optimal_price_point": optimal_point,
        "recommendations": {
            "strategy": "Revenue Maximization" if abs(product["elasticity"]) > 1 else "Margin Protection",
            "price_range": {
                "min": round(base_price * 0.85, 2),
                "max": round(base_price * 1.15, 2)
            },
            "test_recommendation": "Run A/B test with -10% variant" if product["elasticity"] < -1.5 else "Run A/B test with +5% variant"
        }
    }

@app.get("/api/competitors/{product_id}")
async def get_competitor_analysis(product_id: str):
    """Get competitor pricing analysis"""
    if product_id not in DEMO_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = DEMO_PRODUCTS[product_id]
    
    # Simulate competitor data
    competitors = [
        {"name": "Amazon", "price": product["competitor_avg"] * 0.92, "in_stock": True, "rating": 4.5},
        {"name": "BestBuy", "price": product["competitor_avg"] * 1.05, "in_stock": True, "rating": 4.3},
        {"name": "Walmart", "price": product["competitor_avg"] * 0.88, "in_stock": False, "rating": 4.1},
        {"name": "Newegg", "price": product["competitor_avg"] * 0.95, "in_stock": True, "rating": 4.4},
        {"name": "Target", "price": product["competitor_avg"] * 1.02, "in_stock": True, "rating": 4.2}
    ]
    
    our_position = product["current_price"] / product["competitor_avg"]
    
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "our_price": product["current_price"],
        "market_position": {
            "vs_average": f"{(our_position - 1) * 100:+.1f}%",
            "percentile": 65 if our_position > 1 else 35,
            "competitiveness": "Premium" if our_position > 1.1 else "Competitive" if our_position > 0.95 else "Aggressive"
        },
        "competitors": competitors,
        "market_analysis": {
            "avg_competitor_price": round(product["competitor_avg"], 2),
            "min_competitor_price": round(min(c["price"] for c in competitors), 2),
            "max_competitor_price": round(max(c["price"] for c in competitors), 2),
            "in_stock_competitors": sum(1 for c in competitors if c["in_stock"])
        },
        "opportunities": [
            {
                "type": "Out of Stock Opportunity" if any(not c["in_stock"] for c in competitors) else "Price Gap Opportunity",
                "description": "Walmart is out of stock - consider 5% price increase" if any(not c["in_stock"] for c in competitors) else "We're priced above market - consider price match",
                "potential_impact": "+$1,200/month"
            }
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)