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
from datetime import datetime, timedelta
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
            "dashboard": "/api/v1/analytics/dashboard - Executive KPI Dashboard",
            "products": "/api/v1/products - View Demo Products",
            "optimize": "/api/v1/optimize/{product_id} - ML Price Optimization",
            "experiments": "/api/v1/experiments - A/B Testing Results",
            "elasticity": "/api/v1/analytics/elasticity/{product_id} - Price Elasticity Analysis",
            "competitors": "/api/v1/competitors/{product_id} - Competitor Intelligence",
            "impact": "/api/v1/demo/impact - Revenue Impact Summary"
        },
        "try_these": [
            "/docs - Best place to start!",
            "/api/v1/analytics/dashboard - See executive metrics",
            "/api/v1/experiments - View A/B test results",
            "/api/v1/demo/impact - See potential revenue lift"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0-demo",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/products")
async def get_products():
    """Get all demo products"""
    return [
        {
            "id": pid,
            **details,
            "margin": ((details["current_price"] - details["cost"]) / details["current_price"] * 100)
        }
        for pid, details in DEMO_PRODUCTS.items()
    ]

@app.get("/api/v1/products/{product_id}")
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

@app.post("/api/v1/optimize/price-recommendations")
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


@app.post("/api/v1/optimize/{product_id}")
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

@app.get("/api/v1/demo/impact")
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

@app.get("/api/v1/demo/simulate")
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

@app.get("/api/v1/experiments")
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

@app.post("/api/v1/experiments/create")
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

@app.get("/api/v1/analytics/dashboard")
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
                "expected_revenue_change": 8.5,
                "reason": "Competitor undercut by 8%"
            },
            {
                "product_id": "DEMO-001",
                "product_name": "Wireless Gaming Headset",
                "current_price": 89.99,
                "recommended_price": 79.99,
                "expected_impact": "+12.3% revenue",
                "expected_revenue_change": 12.3,
                "reason": "High elasticity, price reduction recommended"
            },
            {
                "product_id": "DEMO-002",
                "product_name": "Premium USB-C Hub",
                "current_price": 49.99,
                "recommended_price": 44.99,
                "expected_impact": "+6.7% revenue",
                "expected_revenue_change": 6.7,
                "reason": "Match market average for volume"
            }
        ],
        "system_health": {
            "api_uptime": "99.98%",
            "avg_response_time": "45ms",
            "optimizations_today": 47,
            "cache_hit_rate": "92%"
        }
    }

@app.get("/api/v1/analytics/elasticity/{product_id}")
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

@app.get("/api/v1/competitors/{product_id}")
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

# Additional endpoints for frontend compatibility
@app.get("/api/v1/pricing/history/{product_id}")
async def get_price_history(product_id: str):
    """Get price history for a product"""
    if product_id not in DEMO_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Generate mock history
    history = []
    current_price = DEMO_PRODUCTS[product_id]["current_price"]
    
    for i in range(30, 0, -1):
        date = datetime.utcnow() - timedelta(days=i)
        # Simulate price variations
        price_variation = 1 + (hash(f"{product_id}{i}") % 20 - 10) / 100
        price = round(current_price * price_variation, 2)
        
        history.append({
            "date": date.isoformat(),
            "price": price,
            "revenue": price * (100 + hash(f"{product_id}{i}rev") % 50),
            "units_sold": 100 + hash(f"{product_id}{i}units") % 50,
            "margin": round((price - DEMO_PRODUCTS[product_id]["cost"]) / price * 100, 1)
        })
    
    return {
        "product_id": product_id,
        "history": history,
        "summary": {
            "avg_price": round(sum(h["price"] for h in history) / len(history), 2),
            "price_volatility": 0.12,
            "trend": "stable"
        }
    }

@app.get("/api/v1/pricing/current")
async def get_current_prices():
    """Get current prices for all products"""
    return {
        "prices": [
            {
                "product_id": pid,
                "product_name": details["name"],
                "current_price": details["current_price"],
                "competitor_avg": details["competitor_avg"],
                "last_updated": datetime.utcnow().isoformat(),
                "price_index": round(details["current_price"] / details["competitor_avg"], 2)
            }
            for pid, details in DEMO_PRODUCTS.items()
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/pricing/optimize")
async def optimize_pricing(data: dict):
    """Optimize pricing for multiple products (alternative endpoint)"""
    product_ids = data.get("productIds", [])
    strategy = data.get("strategy", "balanced")
    
    # Redirect to the main optimization endpoint
    return await get_price_recommendations({
        "product_ids": product_ids,
        "strategy": strategy,
        "constraints": {}
    })

@app.get("/api/v1/competitors")
async def get_competitors():
    """Get all competitors"""
    return {
        "competitors": [
            {"id": "1", "name": "Amazon", "website": "amazon.com", "active": True},
            {"id": "2", "name": "BestBuy", "website": "bestbuy.com", "active": True},
            {"id": "3", "name": "Walmart", "website": "walmart.com", "active": True},
            {"id": "4", "name": "Newegg", "website": "newegg.com", "active": True},
            {"id": "5", "name": "Target", "website": "target.com", "active": True}
        ]
    }

@app.get("/api/v1/competitors/{competitor_id}/prices")
async def get_competitor_prices(competitor_id: str):
    """Get competitor prices for all products"""
    competitor_names = {
        "1": "Amazon",
        "2": "BestBuy", 
        "3": "Walmart",
        "4": "Newegg",
        "5": "Target"
    }
    
    if competitor_id not in competitor_names:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    prices = []
    for pid, product in DEMO_PRODUCTS.items():
        # Generate consistent but varied competitor prices
        base_multiplier = 0.85 + (hash(f"{competitor_id}{pid}") % 30) / 100
        competitor_price = round(product["competitor_avg"] * base_multiplier, 2)
        
        prices.append({
            "product_id": pid,
            "product_name": product["name"],
            "our_price": product["current_price"],
            "competitor_price": competitor_price,
            "price_difference": round(product["current_price"] - competitor_price, 2),
            "price_difference_pct": round((product["current_price"] - competitor_price) / competitor_price * 100, 1),
            "in_stock": hash(f"{competitor_id}{pid}stock") % 10 > 2,  # 80% in stock
            "last_updated": datetime.utcnow().isoformat()
        })
    
    return {
        "competitor_id": competitor_id,
        "competitor_name": competitor_names[competitor_id],
        "prices": prices,
        "summary": {
            "total_products": len(prices),
            "we_are_cheaper": sum(1 for p in prices if p["price_difference"] < 0),
            "they_are_cheaper": sum(1 for p in prices if p["price_difference"] > 0),
            "average_difference_pct": round(sum(p["price_difference_pct"] for p in prices) / len(prices), 1)
        }
    }

@app.get("/api/v1/analytics/revenue")
async def get_revenue_analytics(
    startDate: Optional[str] = None,
    endDate: Optional[str] = None
):
    """Get revenue analytics for a date range"""
    try:
        # Generate mock revenue data
        if not startDate:
            startDate = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not endDate:
            endDate = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Handle both date formats
        try:
            start = datetime.fromisoformat(startDate)
            end = datetime.fromisoformat(endDate)
        except:
            # Try parsing YYYY-MM-DD format
            start = datetime.strptime(startDate, "%Y-%m-%d")
            end = datetime.strptime(endDate, "%Y-%m-%d")
        
        # Ensure end date is not in the future
        today = datetime.utcnow()
        if end > today:
            end = today
        if start > today:
            start = today - timedelta(days=30)
            
        days = max(1, (end - start).days + 1)
        
        data = []
        for i in range(days):
            date = start + timedelta(days=i)
            base_revenue = 40000 + (hash(f"rev{i}") % 20000)
            
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "revenue": base_revenue,
                "orders": base_revenue // 150,
                "aov": round(base_revenue / (base_revenue // 150), 2),
                "optimization_impact": round(base_revenue * 0.08, 2)
            })
        
        return {
            "period": {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")},
            "data": data,
            "summary": {
                "total_revenue": sum(d["revenue"] for d in data),
                "total_orders": sum(d["orders"] for d in data),
                "avg_daily_revenue": round(sum(d["revenue"] for d in data) / len(data), 2),
                "optimization_contribution": sum(d["optimization_impact"] for d in data)
            }
        }
    except Exception as e:
        print(f"Error in revenue analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing revenue analytics: {str(e)}")

@app.get("/api/v1/analytics/price-performance")
async def get_price_performance(productId: Optional[str] = None):
    """Get price performance analytics"""
    if productId and productId not in DEMO_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    
    products = [productId] if productId else list(DEMO_PRODUCTS.keys())
    performance = []
    
    for pid in products:
        product = DEMO_PRODUCTS[pid]
        performance.append({
            "product_id": pid,
            "product_name": product["name"],
            "current_price": product["current_price"],
            "optimal_price": round(product["current_price"] * 0.95, 2),
            "price_gap": round(product["current_price"] * 0.05, 2),
            "revenue_opportunity": round(product["current_price"] * product["stock"] * 0.08, 2),
            "elasticity": product["elasticity"],
            "recommendation": "Lower price by 5%" if product["current_price"] > product["competitor_avg"] else "Maintain current price"
        })
    
    return {
        "performance": performance,
        "summary": {
            "total_opportunity": sum(p["revenue_opportunity"] for p in performance),
            "products_above_optimal": sum(1 for p in performance if p["price_gap"] > 0),
            "avg_price_gap_pct": round(sum(p["price_gap"] / p["current_price"] * 100 for p in performance) / len(performance), 1)
        }
    }

@app.get("/api/v1/analytics/experiments")
async def get_experiments_analytics():
    """Get analytics for experiments"""
    return {
        "experiments": {
            "total": 12,
            "active": 2,
            "completed": 10,
            "success_rate": 0.75
        },
        "revenue_impact": {
            "total_lift": "$45,000",
            "avg_lift_per_experiment": "$4,500",
            "best_performer": {
                "name": "Gaming Headset Holiday Pricing",
                "lift": "$12,000"
            }
        },
        "insights": [
            "Price reductions of 10-15% show highest conversion lift",
            "Weekend experiments perform 20% better",
            "Gaming category most responsive to price changes"
        ]
    }

# Stub endpoints for operations not supported in demo
@app.post("/api/v1/products")
async def create_product(data: dict):
    """Create product - not supported in demo"""
    raise HTTPException(status_code=501, detail="Product creation not supported in demo mode")

@app.put("/api/v1/products/{product_id}")
async def update_product(product_id: str, data: dict):
    """Update product - not supported in demo"""
    raise HTTPException(status_code=501, detail="Product updates not supported in demo mode")

@app.delete("/api/v1/products/{product_id}")
async def delete_product(product_id: str):
    """Delete product - not supported in demo"""
    raise HTTPException(status_code=501, detail="Product deletion not supported in demo mode")

@app.patch("/api/v1/products/{product_id}/price")
async def update_product_price(product_id: str, data: dict):
    """Update product price - not supported in demo"""
    raise HTTPException(status_code=501, detail="Price updates not supported in demo mode")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)