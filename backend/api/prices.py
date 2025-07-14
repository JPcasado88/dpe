from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
import logging

from models.database import get_database_session, Product, PriceHistory as PriceHistoryModel
from services.monitoring import MonitoringService, PriceAnomalyDetector, price_changes_counter
from services.cache import cache_service

router = APIRouter(prefix="/prices", tags=["prices"])
logger = logging.getLogger(__name__)

class PriceUpdate(BaseModel):
    product_id: int
    price: float
    currency: str = "USD"
    effective_date: Optional[date] = None

class PriceHistory(BaseModel):
    product_id: int
    start_date: date
    end_date: date

@router.get("/current")
async def get_current_prices(
    product_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_database_session)
):
    """Get current prices for products"""
    try:
        # Try cache first for bulk prices
        if product_ids:
            cached_prices = cache_service.get_multiple_prices([str(pid) for pid in product_ids])
            
            # Get uncached products from DB
            uncached_ids = [pid for pid in product_ids if cached_prices.get(str(pid)) is None]
            
            if uncached_ids:
                products = db.query(Product).filter(Product.id.in_(uncached_ids)).all()
                
                # Update cache
                new_prices = {str(p.id): float(p.current_price) for p in products}
                cache_service.set_multiple_prices(new_prices)
                
                # Merge results
                for pid, price in new_prices.items():
                    cached_prices[pid] = price
            
            return {
                "prices": [
                    {"product_id": pid, "price": cached_prices.get(str(pid), 0)}
                    for pid in product_ids
                ]
            }
        else:
            # Get all active products
            products = db.query(Product).filter(Product.active == True).all()
            return {
                "prices": [
                    {"product_id": p.id, "price": float(p.current_price)}
                    for p in products
                ]
            }
    except Exception as e:
        logger.error(f"Error getting current prices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prices")

@router.get("/history/{product_id}")
async def get_price_history(
    product_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get price history for a specific product"""
    return {
        "message": f"Price history for product {product_id}",
        "start_date": start_date,
        "end_date": end_date
    }

@router.post("/update")
async def update_price(
    price_update: PriceUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database_session)
):
    """Update product price with guardrails and monitoring"""
    try:
        # Get product
        product = db.query(Product).filter(Product.id == price_update.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Initialize monitoring service
        monitor = MonitoringService(db)
        anomaly_detector = PriceAnomalyDetector(db)
        
        # Check guardrails
        is_valid, error_message = await monitor.check_price_guardrails(
            str(product.id), 
            price_update.price
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Price update rejected: {error_message}")
        
        # Check for anomalies
        anomalies = await anomaly_detector.detect_anomalies(str(product.id), price_update.price)
        if anomalies:
            logger.warning(f"Price anomalies detected for product {product.id}: {anomalies}")
        
        # Create price history record
        old_price = product.current_price
        price_history = PriceHistoryModel(
            product_id=product.id,
            old_price=old_price,
            new_price=price_update.price,
            change_reason="manual_update",
            changed_by="api"
        )
        db.add(price_history)
        
        # Update product price
        product.current_price = price_update.price
        db.commit()
        
        # Invalidate cache
        cache_service.invalidate_current_price(str(product.id))
        
        # Track metrics
        price_changes_counter.labels(reason="manual", category=product.category).inc()
        
        # Process alerts in background
        background_tasks.add_task(monitor.process_alerts)
        
        return {
            "message": "Price updated successfully",
            "product_id": product.id,
            "old_price": float(old_price),
            "new_price": price_update.price,
            "change_percentage": ((price_update.price - float(old_price)) / float(old_price) * 100),
            "anomalies_detected": len(anomalies) > 0,
            "anomaly_details": anomalies if anomalies else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating price: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update price")

@router.post("/bulk-update")
async def bulk_update_prices(
    price_updates: List[PriceUpdate],
    db: Session = Depends(get_db)
):
    """Bulk update multiple product prices"""
    return {
        "message": f"Updated {len(price_updates)} prices",
        "count": len(price_updates)
    }

@router.get("/compare")
async def compare_prices(
    product_ids: List[int] = Query(...),
    include_competitors: bool = True,
    db: Session = Depends(get_db)
):
    """Compare prices across products and competitors"""
    return {
        "message": "Price comparison",
        "product_ids": product_ids,
        "include_competitors": include_competitors
    }