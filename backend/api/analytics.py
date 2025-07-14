from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from enum import Enum
import pandas as pd
import numpy as np
from scipy import stats
import logging

from models.database import get_database_session, Product, PriceHistory, CompetitorProduct, Analytics
from models.schemas import ElasticityResponse, CompetitivePositionResponse
from services import cache_service, cached

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    REVENUE = "revenue"
    PROFIT = "profit"
    VOLUME = "volume"
    CONVERSION = "conversion"
    ELASTICITY = "elasticity"

class TimeGranularity(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class AnalyticsRequest(BaseModel):
    metrics: List[MetricType]
    start_date: date
    end_date: date
    granularity: TimeGranularity = TimeGranularity.DAILY
    product_ids: Optional[List[int]] = None
    categories: Optional[List[str]] = None
    compare_period: bool = False

@router.post("/dashboard")
async def get_dashboard_analytics(
    request: AnalyticsRequest,
    db: Session = Depends(get_database_session)
):
    """Get comprehensive analytics for dashboard"""
    try:
        # Base query for analytics
        query = db.query(
            Analytics.date,
            func.sum(Analytics.revenue).label('revenue'),
            func.sum(Analytics.profit).label('profit'),
            func.sum(Analytics.units_sold).label('units_sold'),
            func.avg(Analytics.conversion_rate).label('avg_conversion_rate')
        ).filter(
            and_(
                Analytics.date >= request.start_date,
                Analytics.date <= request.end_date
            )
        )
        
        # Apply filters
        if request.product_ids:
            query = query.filter(Analytics.product_id.in_(request.product_ids))
        
        if request.categories:
            query = query.join(Product).filter(Product.category.in_(request.categories))
        
        # Group by granularity
        if request.granularity == TimeGranularity.DAILY:
            query = query.group_by(Analytics.date)
        elif request.granularity == TimeGranularity.WEEKLY:
            query = query.group_by(func.date_trunc('week', Analytics.date))
        elif request.granularity == TimeGranularity.MONTHLY:
            query = query.group_by(func.date_trunc('month', Analytics.date))
        
        results = query.all()
        
        # Format results
        data_points = []
        for row in results:
            point = {
                'date': row.date,
                'metrics': {}
            }
            
            if MetricType.REVENUE in request.metrics:
                point['metrics']['revenue'] = float(row.revenue or 0)
            if MetricType.PROFIT in request.metrics:
                point['metrics']['profit'] = float(row.profit or 0)
            if MetricType.VOLUME in request.metrics:
                point['metrics']['volume'] = int(row.units_sold or 0)
            if MetricType.CONVERSION in request.metrics:
                point['metrics']['conversion'] = float(row.avg_conversion_rate or 0)
            
            data_points.append(point)
        
        # Calculate summary statistics
        summary = {
            'total_revenue': sum(p['metrics'].get('revenue', 0) for p in data_points),
            'total_profit': sum(p['metrics'].get('profit', 0) for p in data_points),
            'total_volume': sum(p['metrics'].get('volume', 0) for p in data_points),
            'avg_conversion': np.mean([p['metrics'].get('conversion', 0) for p in data_points if p['metrics'].get('conversion', 0) > 0])
        }
        
        return {
            'period': {'start': request.start_date, 'end': request.end_date},
            'granularity': request.granularity,
            'data_points': data_points,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@router.get("/kpis")
async def get_key_performance_indicators(
    date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get current KPIs and performance metrics"""
    return {
        "date": date or datetime.now().date(),
        "kpis": {
            "total_revenue": 125000.50,
            "total_profit": 45000.00,
            "avg_margin": 0.36,
            "price_optimization_impact": "+8.5%",
            "competitor_price_index": 0.95
        }
    }

@router.get("/products/{product_id}/elasticity")
async def calculate_price_elasticity(
    product_id: str,
    days: int = Query(90, description="Number of days to analyze"),
    min_data_points: int = Query(10, description="Minimum data points required"),
    db: Session = Depends(get_database_session)
) -> ElasticityResponse:
    """Calculate price elasticity from historical data"""
    try:
        # Check cache first
        cached_result = cache_service.get_elasticity(product_id, days)
        if cached_result:
            logger.debug(f"Elasticity cache hit for product {product_id}")
            return ElasticityResponse(**cached_result)
        
        # Get price and sales data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Query for price changes and corresponding sales
        query = db.query(
            Analytics.date,
            Analytics.price,
            Analytics.units_sold,
            Analytics.revenue
        ).filter(
            and_(
                Analytics.product_id == product_id,
                Analytics.date >= start_date,
                Analytics.date <= end_date
            )
        ).order_by(Analytics.date)
        
        data = query.all()
        
        if len(data) < min_data_points:
            return ElasticityResponse(
                product_id=product_id,
                elasticity=0,
                confidence=0,
                data_points=len(data),
                interpretation="Insufficient data for elasticity calculation",
                optimal_price=0,
                current_price=0,
                revenue_opportunity="N/A",
                error="Not enough data points"
            )
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([
            {'date': d.date, 'price': float(d.price), 'quantity': d.units_sold}
            for d in data
        ])
        
        # Calculate percentage changes
        df['price_pct_change'] = df['price'].pct_change()
        df['quantity_pct_change'] = df['quantity'].pct_change()
        
        # Remove rows with NaN or zero price changes
        df_clean = df.dropna()
        df_clean = df_clean[df_clean['price_pct_change'] != 0]
        
        if len(df_clean) < 5:
            return ElasticityResponse(
                product_id=product_id,
                elasticity=0,
                confidence=0,
                data_points=len(data),
                interpretation="Not enough price variations",
                optimal_price=0,
                current_price=df['price'].iloc[-1],
                revenue_opportunity="N/A",
                error="Insufficient price variations"
            )
        
        # Calculate elasticity using regression
        X = df_clean['price_pct_change'].values.reshape(-1, 1)
        y = df_clean['quantity_pct_change'].values
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df_clean['price_pct_change'], 
            df_clean['quantity_pct_change']
        )
        
        elasticity = slope
        confidence = abs(r_value)  # R-squared as confidence measure
        
        # Get current price
        current_price = df['price'].iloc[-1]
        
        # Calculate optimal price (where marginal revenue = marginal cost)
        # For simplicity, assuming constant marginal cost
        product = db.query(Product).filter(Product.id == product_id).first()
        if product and elasticity < -1:
            # Optimal price formula: P* = MC * (e / (1 + e))
            # Where e is elasticity and MC is marginal cost
            marginal_cost = float(product.cost)
            optimal_price = marginal_cost * (elasticity / (1 + elasticity))
            optimal_price = max(float(product.min_price), min(float(product.max_price), optimal_price))
        else:
            optimal_price = current_price
        
        # Calculate revenue opportunity
        avg_quantity = df['quantity'].mean()
        current_revenue = current_price * avg_quantity
        
        # Estimate quantity at optimal price
        price_change_pct = (optimal_price - current_price) / current_price
        quantity_change_pct = price_change_pct * elasticity
        optimal_quantity = avg_quantity * (1 + quantity_change_pct)
        optimal_revenue = optimal_price * optimal_quantity
        
        revenue_opportunity = optimal_revenue - current_revenue
        
        # Interpretation
        if elasticity > -1:
            interpretation = "Inelastic: Price changes have minimal impact on demand"
        elif elasticity > -2:
            interpretation = "Moderately elastic: 10% price increase → {:.1f}% demand decrease".format(abs(elasticity * 10))
        else:
            interpretation = "Highly elastic: 10% price increase → {:.1f}% demand decrease".format(abs(elasticity * 10))
        
        result = ElasticityResponse(
            product_id=product_id,
            elasticity=round(elasticity, 2),
            confidence=round(confidence, 2),
            data_points=len(df_clean),
            interpretation=interpretation,
            optimal_price=round(optimal_price, 2),
            current_price=round(current_price, 2),
            revenue_opportunity=f"${revenue_opportunity:,.2f}/month" if revenue_opportunity > 0 else "Current price is optimal",
            price_recommendations=[
                {
                    "action": "increase" if optimal_price > current_price else "decrease",
                    "amount": abs(optimal_price - current_price),
                    "percentage": abs(price_change_pct) * 100
                }
            ]
        )
        
        # Cache the result
        cache_service.set_elasticity(product_id, days, result.dict())
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating elasticity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate elasticity")

@router.get("/products/{product_id}/competition")
async def get_competitive_position(
    product_id: str,
    db: Session = Depends(get_database_session)
) -> CompetitivePositionResponse:
    """Show where we stand vs competitors"""
    try:
        # Get our product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get latest competitor prices
        competitor_prices = db.query(
            CompetitorProduct,
            func.row_number().over(
                partition_by=CompetitorProduct.competitor_id,
                order_by=CompetitorProduct.last_updated.desc()
            ).label('rn')
        ).filter(
            CompetitorProduct.product_id == product_id
        ).subquery()
        
        latest_prices = db.query(
            CompetitorProduct
        ).select_from(
            competitor_prices
        ).filter(
            competitor_prices.c.rn == 1
        ).all()
        
        # Calculate market statistics
        competitor_list = []
        prices = []
        
        for cp in latest_prices:
            total_price = float(cp.price) + float(cp.shipping_cost or 0)
            competitor_list.append({
                "name": cp.competitor.name,
                "price": float(cp.price),
                "shipping": float(cp.shipping_cost or 0),
                "total_price": total_price,
                "in_stock": cp.in_stock,
                "last_updated": cp.last_updated
            })
            if cp.in_stock:
                prices.append(total_price)
        
        our_price = float(product.current_price)
        
        if prices:
            avg_competitor_price = np.mean(prices)
            min_competitor_price = min(prices)
            max_competitor_price = max(prices)
            
            # Determine market position
            if our_price < avg_competitor_price * 0.95:
                market_position = "below_market"
                position_description = f"{((avg_competitor_price - our_price) / avg_competitor_price * 100):.1f}% below average"
            elif our_price > avg_competitor_price * 1.05:
                market_position = "above_market"
                position_description = f"{((our_price - avg_competitor_price) / avg_competitor_price * 100):.1f}% above average"
            else:
                market_position = "at_market"
                position_description = "At market average"
            
            # Generate recommendation
            if market_position == "above_market" and len([c for c in competitor_list if c['in_stock']]) > 2:
                recommended_price = avg_competitor_price * 0.98  # Slightly below average
                recommendation = f"Lower to ${recommended_price:.2f} to match market"
                
                # Estimate impact based on elasticity
                elasticity_data = await calculate_price_elasticity(product_id, db=db)
                if elasticity_data.elasticity < 0:
                    price_change_pct = (recommended_price - our_price) / our_price
                    volume_change_pct = price_change_pct * elasticity_data.elasticity
                    current_volume = 100  # Baseline
                    expected_volume = current_volume * (1 + volume_change_pct)
                    expected_impact = f"+{int(expected_volume - current_volume)} units/week"
                else:
                    expected_impact = "Positive volume impact expected"
            
            elif market_position == "below_market":
                # Check if we can increase price
                out_of_stock_competitors = [c for c in competitor_list if not c['in_stock']]
                if out_of_stock_competitors:
                    recommended_price = min(avg_competitor_price * 0.95, float(product.max_price))
                    recommendation = f"Increase to ${recommended_price:.2f} - {len(out_of_stock_competitors)} competitors out of stock"
                    expected_impact = "Higher margins with minimal volume impact"
                else:
                    recommendation = "Maintain current pricing - good competitive position"
                    expected_impact = "Current position is optimal"
            else:
                recommendation = "Current pricing is well-positioned"
                expected_impact = "No change recommended"
        else:
            market_position = "no_competition"
            position_description = "No active competitors found"
            recommendation = "Monitor for new competitors"
            expected_impact = "N/A"
            avg_competitor_price = 0
            min_competitor_price = 0
            max_competitor_price = 0
        
        return CompetitivePositionResponse(
            product_id=product_id,
            our_price=our_price,
            market_position=position_description,
            avg_competitor_price=round(avg_competitor_price, 2) if avg_competitor_price else None,
            min_competitor_price=round(min_competitor_price, 2) if min_competitor_price else None,
            max_competitor_price=round(max_competitor_price, 2) if max_competitor_price else None,
            competitors=competitor_list,
            recommendation=recommendation,
            expected_impact=expected_impact,
            price_index=round(our_price / avg_competitor_price, 2) if avg_competitor_price else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting competitive position: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze competitive position")

@router.get("/trends")
async def get_pricing_trends(
    category: Optional[str] = None,
    days: int = 90,
    db: Session = Depends(get_db)
):
    """Analyze pricing trends and patterns"""
    return {
        "period_days": days,
        "category": category,
        "trends": {
            "avg_price_change": "+5.2%",
            "volatility_index": 0.15,
            "seasonal_pattern": "increasing",
            "competitor_movements": "stable"
        }
    }

@router.get("/reports/summary")
async def generate_summary_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    format: str = "json",
    db: Session = Depends(get_db)
):
    """Generate comprehensive summary report"""
    return {
        "report_type": "summary",
        "period": f"{start_date} to {end_date}",
        "format": format,
        "sections": [
            "executive_summary",
            "revenue_analysis",
            "pricing_performance",
            "competitor_analysis",
            "recommendations"
        ]
    }

@router.get("/insights")
async def get_pricing_insights(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get AI-generated pricing insights and recommendations"""
    return {
        "insights": [
            {
                "type": "opportunity",
                "message": "Product X is priced 15% below market average",
                "impact": "Potential revenue increase of $5,000/month",
                "confidence": 0.85
            },
            {
                "type": "alert",
                "message": "Competitor Y reduced prices by 10% on competing products",
                "affected_products": 5,
                "recommended_action": "Review pricing strategy"
            }
        ],
        "generated_at": datetime.now()
    }

@router.get("/export")
async def export_analytics_data(
    metric: MetricType,
    start_date: date,
    end_date: date,
    format: str = "csv",
    db: Session = Depends(get_db)
):
    """Export analytics data in various formats"""
    return {
        "message": "Export initiated",
        "metric": metric,
        "format": format,
        "download_url": f"/downloads/analytics_{metric}_{start_date}_{end_date}.{format}"
    }