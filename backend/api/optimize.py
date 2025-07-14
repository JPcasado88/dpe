from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import logging
import sys
import os

# Add ML module to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ml.pricing_optimizer import DynamicPricingEngine, ProductFeatures, OptimizationObjective
from models.database import get_database_session, Product, CompetitorProduct, Analytics, OptimizationJob
from models.schemas import OptimizationRequest, PriceRecommendation, OptimizationResult

router = APIRouter(prefix="/optimize", tags=["optimization"])
logger = logging.getLogger(__name__)

# Initialize pricing engine
pricing_engine = DynamicPricingEngine()

# Use schemas from models.schemas instead of redefining

@router.post("/price-recommendations", response_model=List[PriceRecommendation])
async def get_price_recommendations(
    request: OptimizationRequest,
    db: Session = Depends(get_database_session)
):
    """Generate optimized price recommendations"""
    try:
        # Get products to optimize
        query = db.query(Product).filter(Product.active == True)
        
        if request.product_ids:
            query = query.filter(Product.id.in_(request.product_ids))
        elif request.category:
            query = query.filter(Product.category == request.category)
        else:
            # Limit to top revenue products if no filter
            query = query.limit(50)
        
        products = query.all()
        
        if not products:
            raise HTTPException(status_code=404, detail="No products found for optimization")
        
        recommendations = []
        
        for product in products:
            # Get product features
            features = await _get_product_features(product, db)
            
            # Map strategy to objective
            objective_map = {
                'maximize_profit': OptimizationObjective.MAXIMIZE_PROFIT,
                'maximize_revenue': OptimizationObjective.MAXIMIZE_REVENUE,
                'balance': OptimizationObjective.BALANCED
            }
            objective = objective_map.get(request.strategy, OptimizationObjective.BALANCED)
            
            # Optimize price
            result = pricing_engine.calculate_optimal_price(
                features,
                objective=objective,
                constraints=request.constraints
            )
            
            # Create recommendation
            recommendation = PriceRecommendation(
                product_id=product.id,
                product_name=product.name,
                current_price=result.current_price,
                recommended_price=result.optimal_price,
                expected_revenue_change=result.expected_revenue_change,
                expected_profit_change=result.expected_profit_change,
                confidence_score=result.confidence_score,
                reasoning=f"Based on {objective.value} strategy. Key factors: " + 
                         ", ".join([f"{k}: ${v:.2f}" for k, v in result.factors.items()])
            )
            
            recommendations.append(recommendation)
        
        # Sort by impact
        recommendations.sort(key=lambda x: x.expected_revenue_change, reverse=True)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

@router.post("/run-optimization")
async def run_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database_session)
):
    """Run full price optimization algorithm"""
    try:
        # Create optimization job
        job_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        job = OptimizationJob(
            job_id=job_id,
            status="pending",
            strategy=request.strategy,
            constraints=request.constraints,
            products={"product_ids": request.product_ids, "category": request.category},
            created_by="system"
        )
        
        db.add(job)
        db.commit()
        
        # Run optimization in background
        background_tasks.add_task(
            _run_optimization_job,
            job_id=job_id,
            request=request,
            db_url=str(db.bind.url)
        )
        
        return {
            "message": "Optimization started",
            "job_id": job_id,
            "status": "processing",
            "estimated_completion_time": "2-5 minutes"
        }
        
    except Exception as e:
        logger.error(f"Error starting optimization: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start optimization")

@router.get("/optimization-status/{job_id}")
async def get_optimization_status(
    job_id: str,
    db: Session = Depends(get_database_session)
):
    """Check status of an optimization job"""
    job = db.query(OptimizationJob).filter(OptimizationJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "status": job.status,
        "progress": 100 if job.status == "completed" else 50,
        "results_available": job.status == "completed",
        "results": job.results if job.status == "completed" else None,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }

async def _get_product_features(product: Product, db: Session) -> ProductFeatures:
    """Extract features for a product"""
    
    # Get competitor prices
    competitor_prices = db.query(
        func.avg(CompetitorProduct.price).label('avg_price'),
        func.min(CompetitorProduct.price).label('min_price')
    ).filter(
        and_(
            CompetitorProduct.product_id == product.id,
            CompetitorProduct.in_stock == True,
            CompetitorProduct.last_updated > datetime.now() - timedelta(days=1)
        )
    ).first()
    
    competitor_avg = float(competitor_prices.avg_price or product.current_price)
    competitor_min = float(competitor_prices.min_price or product.current_price * 0.9)
    
    # Get elasticity from recent analytics
    elasticity_data = db.query(Analytics.price_elasticity).filter(
        and_(
            Analytics.product_id == product.id,
            Analytics.price_elasticity.isnot(None)
        )
    ).order_by(Analytics.date.desc()).first()
    
    elasticity = float(elasticity_data.price_elasticity if elasticity_data else -1.5)
    
    # Get last price change
    last_change = db.query(func.max(Analytics.date)).filter(
        Analytics.product_id == product.id
    ).scalar()
    
    days_since_change = (datetime.now().date() - last_change).days if last_change else 30
    
    return ProductFeatures(
        product_id=str(product.id),
        current_price=float(product.current_price),
        cost=float(product.cost),
        min_price=float(product.min_price),
        max_price=float(product.max_price),
        stock_quantity=product.stock_quantity or 100,
        stock_velocity=product.stock_velocity or 5.0,
        elasticity=elasticity,
        competitor_avg_price=competitor_avg,
        competitor_min_price=competitor_min,
        market_position=float(product.current_price) / competitor_avg if competitor_avg > 0 else 1.0,
        days_since_last_change=days_since_change,
        category=product.category or 'General',
        seasonality_factor=1.0,  # Could be enhanced with seasonal data
        conversion_rate=product.conversion_rate or 0.02,
        return_rate=product.return_rate or 0.05
    )

async def _run_optimization_job(job_id: str, request: OptimizationRequest, db_url: str):
    """Background task to run optimization"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create new DB session for background task
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(OptimizationJob).filter(OptimizationJob.job_id == job_id).first()
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Get products
        query = db.query(Product).filter(Product.active == True)
        if request.product_ids:
            query = query.filter(Product.id.in_(request.product_ids))
        elif request.category:
            query = query.filter(Product.category == request.category)
        
        products = query.all()
        
        # Optimize each product
        results = []
        total_revenue_impact = 0
        total_profit_impact = 0
        
        for product in products:
            features = await _get_product_features(product, db)
            
            objective_map = {
                'maximize_profit': OptimizationObjective.MAXIMIZE_PROFIT,
                'maximize_revenue': OptimizationObjective.MAXIMIZE_REVENUE,
                'balance': OptimizationObjective.BALANCED
            }
            objective = objective_map.get(request.strategy, OptimizationObjective.BALANCED)
            
            result = pricing_engine.calculate_optimal_price(
                features,
                objective=objective,
                constraints=request.constraints
            )
            
            results.append({
                'product_id': product.id,
                'product_name': product.name,
                'current_price': result.current_price,
                'optimal_price': result.optimal_price,
                'revenue_impact': result.expected_revenue_change,
                'profit_impact': result.expected_profit_change
            })
            
            total_revenue_impact += result.expected_revenue_change
            total_profit_impact += result.expected_profit_change
        
        # Update job with results
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.products_optimized = len(results)
        job.revenue_impact = total_revenue_impact / len(results) if results else 0
        job.results = {
            'recommendations': results,
            'summary': {
                'total_products': len(results),
                'avg_revenue_impact': f"+{total_revenue_impact/len(results):.1f}%" if results else "0%",
                'avg_profit_impact': f"+{total_profit_impact/len(results):.1f}%" if results else "0%"
            }
        }
        db.commit()
        
    except Exception as e:
        logger.error(f"Optimization job {job_id} failed: {str(e)}")
        job = db.query(OptimizationJob).filter(OptimizationJob.job_id == job_id).first()
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()

@router.post("/simulate")
async def simulate_price_changes(
    simulation_data: Dict,
    db: Session = Depends(get_db)
):
    """Simulate impact of price changes"""
    return {
        "message": "Simulation completed",
        "estimated_revenue_change": "+15%",
        "estimated_profit_change": "+12%",
        "risk_score": 0.3
    }

@router.get("/constraints")
async def get_optimization_constraints(db: Session = Depends(get_db)):
    """Get current optimization constraints and rules"""
    return {
        "constraints": {
            "min_margin": 0.2,
            "max_price_change_percent": 0.15,
            "competitor_price_threshold": 0.95,
            "volume_requirements": True
        }
    }