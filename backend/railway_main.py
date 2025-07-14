"""
Railway-specific main entry point
Handles missing database gracefully
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Railway deployment...")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="Dynamic Pricing Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for Railway
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://dpe-fe-production.up.railway.app",
        "https://*.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Try to import main app routes
try:
    from api import products, prices, competitors, optimize, experiments, analytics
    from config import settings
    
    # Include routers
    app.include_router(products.router, prefix="/api/v1")
    app.include_router(prices.router, prefix="/api/v1")
    app.include_router(competitors.router, prefix="/api/v1")
    app.include_router(optimize.router, prefix="/api/v1")
    app.include_router(experiments.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    
    logger.info("Successfully loaded all API routes")
    
except Exception as e:
    logger.error(f"Failed to load main API routes: {e}")
    
    # Fallback - load demo server endpoints
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Import demo_server functions
        from demo_server import (
            get_products, get_product, optimize_price, 
            get_price_recommendations, demo_impact, get_experiments
        )
        
        # Register demo endpoints
        app.get("/api/v1/products")(get_products)
        app.get("/api/v1/products/{product_id}")(get_product)
        app.post("/api/v1/optimize/{product_id}")(optimize_price)
        app.post("/api/v1/optimize/price-recommendations")(get_price_recommendations)
        app.get("/api/v1/analytics/dashboard")(demo_impact)
        app.get("/api/v1/experiments")(get_experiments)
        
        logger.info("Loaded demo server endpoints as fallback")
        
    except Exception as e2:
        logger.error(f"Failed to load demo endpoints: {e2}")

@app.get("/")
async def root():
    return {
        "message": "Dynamic Pricing Engine API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)