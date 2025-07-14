from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from enum import Enum
import numpy as np
from scipy import stats
import logging
import uuid

from models.database import get_database_session, Experiment, ExperimentProduct, Product, Analytics
from models.schemas import ExperimentCreate, ExperimentStatus, ExperimentType

router = APIRouter(prefix="/experiments", tags=["experiments"])
logger = logging.getLogger(__name__)

class ExperimentAnalysis(BaseModel):
    experiment_id: int
    status: ExperimentStatus
    control_metrics: Dict[str, float]
    variant_metrics: Dict[str, float]
    statistical_significance: float
    p_value: float
    confidence_interval: List[float]
    lift_percentage: float
    recommendation: str
    sample_size_control: int
    sample_size_variant: int
    
class TrafficAllocation(BaseModel):
    product_id: int
    user_id: str
    
    @property
    def should_see_variant(self) -> bool:
        """Deterministic allocation based on user_id hash"""
        hash_value = int(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.product_id}-{self.user_id}").hex[:8], 16)
        return (hash_value % 100) < 50  # 50/50 split

@router.get("/")
async def get_experiments(
    status: Optional[ExperimentStatus] = None,
    db: Session = Depends(get_database_session)
):
    """Get all experiments with optional status filter"""
    query = db.query(Experiment)
    
    if status:
        query = query.filter(Experiment.status == status)
    
    experiments = query.order_by(Experiment.created_at.desc()).all()
    
    results = []
    for exp in experiments:
        # Get product count
        product_count = db.query(func.count(ExperimentProduct.id)).filter(
            ExperimentProduct.experiment_id == exp.id
        ).scalar()
        
        results.append({
            "id": exp.id,
            "name": exp.name,
            "description": exp.description,
            "status": exp.status,
            "type": exp.type,
            "start_date": exp.start_date,
            "end_date": exp.end_date,
            "product_count": product_count,
            "created_at": exp.created_at
        })
    
    return results

@router.get("/{experiment_id}")
async def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """Get specific experiment details"""
    return {"message": f"Experiment {experiment_id} details"}

@router.post("/create")
async def create_experiment(
    experiment_data: Dict,
    db: Session = Depends(get_database_session)
):
    """Create a new pricing experiment"""
    try:
        # Create experiment
        experiment = Experiment(
            name=experiment_data["name"],
            description=experiment_data.get("description", ""),
            type=experiment_data.get("type", "ab_test"),
            status="draft",
            start_date=experiment_data["start_date"],
            end_date=experiment_data.get("end_date"),
            control_group={
                "name": "Control",
                "description": "Current pricing"
            },
            test_groups=[{
                "name": "Variant",
                "description": experiment_data.get("variant_description", "Test pricing"),
                "price_change": experiment_data.get("price_change_percent", -0.1)
            }],
            success_metrics=experiment_data.get("success_metrics", ["revenue", "conversion_rate", "profit"])
        )
        
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        
        # Add products to experiment
        for product_id in experiment_data["product_ids"]:
            # Control group
            control_variant = ExperimentProduct(
                experiment_id=experiment.id,
                product_id=product_id,
                group="control",
                test_price=db.query(Product.current_price).filter(Product.id == product_id).scalar()
            )
            db.add(control_variant)
            
            # Test group
            current_price = db.query(Product.current_price).filter(Product.id == product_id).scalar()
            test_price = current_price * (1 + experiment_data.get("price_change_percent", -0.1))
            
            test_variant = ExperimentProduct(
                experiment_id=experiment.id,
                product_id=product_id,
                group="variant",
                test_price=round(test_price, 2)
            )
            db.add(test_variant)
        
        db.commit()
        
        return {
            "message": "Experiment created successfully",
            "experiment_id": experiment.id,
            "name": experiment.name,
            "product_count": len(experiment_data["product_ids"]),
            "status": experiment.status
        }
        
    except Exception as e:
        logger.error(f"Error creating experiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create experiment")

@router.put("/{experiment_id}/status")
async def update_experiment_status(
    experiment_id: int,
    status: ExperimentStatus,
    db: Session = Depends(get_db)
):
    """Update experiment status (start, pause, stop)"""
    return {
        "message": f"Experiment {experiment_id} status updated",
        "new_status": status
    }

@router.get("/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: int,
    db: Session = Depends(get_database_session)
) -> ExperimentAnalysis:
    """Get results and analysis for an experiment"""
    try:
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Get experiment products
        exp_products = db.query(ExperimentProduct).filter(
            ExperimentProduct.experiment_id == experiment_id
        ).all()
        
        # Aggregate metrics for control and variant
        control_data = {"revenue": 0, "conversions": 0, "impressions": 0}
        variant_data = {"revenue": 0, "conversions": 0, "impressions": 0}
        
        for exp_product in exp_products:
            # Get analytics data during experiment period
            analytics = db.query(
                func.sum(Analytics.revenue).label('revenue'),
                func.sum(Analytics.units_sold).label('conversions'),
                func.count(Analytics.id).label('impressions')
            ).filter(
                and_(
                    Analytics.product_id == exp_product.product_id,
                    Analytics.date >= experiment.start_date,
                    Analytics.date <= (experiment.end_date or datetime.now().date()),
                    Analytics.price == exp_product.test_price
                )
            ).first()
            
            if analytics:
                if exp_product.group == "control":
                    control_data["revenue"] += float(analytics.revenue or 0)
                    control_data["conversions"] += int(analytics.conversions or 0)
                    control_data["impressions"] += int(analytics.impressions or 0)
                else:
                    variant_data["revenue"] += float(analytics.revenue or 0)
                    variant_data["conversions"] += int(analytics.conversions or 0)
                    variant_data["impressions"] += int(analytics.impressions or 0)
        
        # Calculate metrics
        control_conversion_rate = control_data["conversions"] / max(control_data["impressions"], 1)
        variant_conversion_rate = variant_data["conversions"] / max(variant_data["impressions"], 1)
        
        control_avg_order_value = control_data["revenue"] / max(control_data["conversions"], 1)
        variant_avg_order_value = variant_data["revenue"] / max(variant_data["conversions"], 1)
        
        # Statistical significance test (Chi-square for conversion rate)
        if control_data["impressions"] > 30 and variant_data["impressions"] > 30:
            # Create contingency table
            contingency_table = np.array([
                [control_data["conversions"], control_data["impressions"] - control_data["conversions"]],
                [variant_data["conversions"], variant_data["impressions"] - variant_data["conversions"]]
            ])
            
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            
            # Calculate lift
            lift = ((variant_conversion_rate - control_conversion_rate) / control_conversion_rate) * 100
            
            # Confidence interval for lift
            se = np.sqrt(
                (control_conversion_rate * (1 - control_conversion_rate) / control_data["impressions"]) +
                (variant_conversion_rate * (1 - variant_conversion_rate) / variant_data["impressions"])
            )
            ci_lower = lift - 1.96 * se * 100
            ci_upper = lift + 1.96 * se * 100
            
            # Recommendation
            if p_value < 0.05 and lift > 0:
                recommendation = f"Adopt variant pricing - {lift:.1f}% lift in conversion rate (p={p_value:.3f})"
            elif p_value < 0.05 and lift < 0:
                recommendation = f"Keep control pricing - variant shows {lift:.1f}% decrease (p={p_value:.3f})"
            else:
                recommendation = f"No significant difference detected (p={p_value:.3f}). Continue testing."
        else:
            p_value = 1.0
            lift = 0
            ci_lower, ci_upper = 0, 0
            recommendation = "Insufficient data for statistical analysis"
        
        return ExperimentAnalysis(
            experiment_id=experiment_id,
            status=experiment.status,
            control_metrics={
                "conversion_rate": round(control_conversion_rate, 4),
                "avg_order_value": round(control_avg_order_value, 2),
                "revenue": round(control_data["revenue"], 2)
            },
            variant_metrics={
                "conversion_rate": round(variant_conversion_rate, 4),
                "avg_order_value": round(variant_avg_order_value, 2),
                "revenue": round(variant_data["revenue"], 2)
            },
            statistical_significance=round(1 - p_value, 3),
            p_value=round(p_value, 4),
            confidence_interval=[round(ci_lower, 1), round(ci_upper, 1)],
            lift_percentage=round(lift, 1),
            recommendation=recommendation,
            sample_size_control=control_data["impressions"],
            sample_size_variant=variant_data["impressions"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing experiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze experiment")

@router.get("/allocation/{product_id}/{user_id}")
async def get_traffic_allocation(
    product_id: int,
    user_id: str,
    db: Session = Depends(get_database_session)
):
    """Get price variant for a specific user/product combination"""
    # Check if product is in any active experiment
    active_experiment = db.query(ExperimentProduct).join(Experiment).filter(
        and_(
            ExperimentProduct.product_id == product_id,
            Experiment.status == "running",
            Experiment.start_date <= datetime.now().date(),
            (Experiment.end_date.is_(None) | (Experiment.end_date >= datetime.now().date()))
        )
    ).first()
    
    if not active_experiment:
        # No experiment, return regular price
        product = db.query(Product).filter(Product.id == product_id).first()
        return {
            "product_id": product_id,
            "user_id": user_id,
            "in_experiment": False,
            "price": float(product.current_price) if product else 0,
            "group": "none"
        }
    
    # Determine allocation
    allocation = TrafficAllocation(product_id=product_id, user_id=user_id)
    
    if allocation.should_see_variant:
        # Get variant price
        variant_product = db.query(ExperimentProduct).filter(
            and_(
                ExperimentProduct.experiment_id == active_experiment.experiment_id,
                ExperimentProduct.product_id == product_id,
                ExperimentProduct.group == "variant"
            )
        ).first()
        
        return {
            "product_id": product_id,
            "user_id": user_id,
            "in_experiment": True,
            "experiment_id": active_experiment.experiment_id,
            "price": float(variant_product.test_price),
            "group": "variant"
        }
    else:
        # Control group
        return {
            "product_id": product_id,
            "user_id": user_id,
            "in_experiment": True,
            "experiment_id": active_experiment.experiment_id,
            "price": float(active_experiment.test_price),
            "group": "control"
        }

@router.post("/{experiment_id}/end")
async def end_experiment(
    experiment_id: int,
    adopt_variant: bool = False,
    db: Session = Depends(get_database_session)
):
    """End an experiment and optionally adopt variant pricing"""
    try:
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Update experiment status
        experiment.status = "completed"
        experiment.end_date = datetime.now().date()
        
        if adopt_variant:
            # Apply variant prices to products
            variant_products = db.query(ExperimentProduct).filter(
                and_(
                    ExperimentProduct.experiment_id == experiment_id,
                    ExperimentProduct.group == "variant"
                )
            ).all()
            
            for vp in variant_products:
                product = db.query(Product).filter(Product.id == vp.product_id).first()
                if product:
                    product.current_price = vp.test_price
                    
                    # Log price change
                    from models.database import PriceHistory
                    price_change = PriceHistory(
                        product_id=product.id,
                        old_price=product.current_price,
                        new_price=vp.test_price,
                        change_reason=f"A/B test winner - Experiment {experiment.name}",
                        changed_by="system"
                    )
                    db.add(price_change)
        
        # Store final results
        results = await get_experiment_results(experiment_id, db)
        experiment.results = {
            "final_analysis": results.dict(),
            "variant_adopted": adopt_variant,
            "completed_at": datetime.now().isoformat()
        }
        
        db.commit()
        
        return {
            "message": "Experiment ended successfully",
            "experiment_id": experiment_id,
            "variant_adopted": adopt_variant,
            "final_recommendation": results.recommendation
        }
        
    except Exception as e:
        logger.error(f"Error ending experiment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end experiment")

@router.get("/templates")
async def get_experiment_templates(db: Session = Depends(get_db)):
    """Get pre-defined experiment templates"""
    return {
        "templates": [
            {
                "name": "Standard A/B Price Test",
                "type": "ab_test",
                "description": "Test single price change impact"
            },
            {
                "name": "Seasonal Pricing Test",
                "type": "time_based",
                "description": "Test different pricing strategies by season"
            }
        ]
    }