from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

# Import routers
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api import products, prices, competitors, optimize, experiments, analytics
from config import settings, FEATURE_FLAGS
from models.database import init_db

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # Don't crash on Railway if DB init fails - it might already be initialized
        if os.getenv("RAILWAY_ENVIRONMENT"):
            logger.warning("Running on Railway, continuing despite DB init error")
        else:
            raise
    
    # Initialize Redis connection (if needed)
    # Initialize ML models (if needed)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    # Close database connections
    # Close Redis connections
    # Clean up resources

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc) if settings.DEBUG else None}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "features": FEATURE_FLAGS
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": settings.API_PREFIX
    }

# Include routers
app.include_router(products.router, prefix=f"{settings.API_PREFIX}")
app.include_router(prices.router, prefix=f"{settings.API_PREFIX}")
app.include_router(competitors.router, prefix=f"{settings.API_PREFIX}")
app.include_router(optimize.router, prefix=f"{settings.API_PREFIX}")
app.include_router(experiments.router, prefix=f"{settings.API_PREFIX}")
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}")

# API info endpoint
@app.get(f"{settings.API_PREFIX}/info")
async def api_info():
    return {
        "api_version": "v1",
        "endpoints": {
            "products": f"{settings.API_PREFIX}/products",
            "prices": f"{settings.API_PREFIX}/prices",
            "competitors": f"{settings.API_PREFIX}/competitors",
            "optimize": f"{settings.API_PREFIX}/optimize",
            "experiments": f"{settings.API_PREFIX}/experiments",
            "analytics": f"{settings.API_PREFIX}/analytics"
        },
        "features_enabled": FEATURE_FLAGS
    }

# Cache statistics endpoint
@app.get("/cache/stats")
async def cache_stats():
    """Get Redis cache statistics"""
    from services import cache_service
    return cache_service.get_cache_stats()

# Prometheus metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Expose Prometheus metrics"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )