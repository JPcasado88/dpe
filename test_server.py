#!/usr/bin/env python3
"""
Minimal test server for Railway debugging
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI(title="DPE Test Server")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Test server is running!", "env": os.environ.get("RAILWAY_ENVIRONMENT", "local")}

@app.get("/health")
async def health():
    return {"status": "healthy", "server": "test_server"}

@app.get("/api/v1/products")
async def get_products():
    return [
        {"id": 1, "name": "Test Product 1", "current_price": 99.99},
        {"id": 2, "name": "Test Product 2", "current_price": 149.99}
    ]

@app.post("/api/v1/optimize/price-recommendations")
async def optimize(data: dict):
    return {
        "recommendations": [
            {
                "product_id": 1,
                "product_name": "Test Product 1",
                "current_price": 99.99,
                "recommended_price": 89.99,
                "expected_revenue_change": 10.5,
                "confidence_score": 0.85
            }
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting test server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)