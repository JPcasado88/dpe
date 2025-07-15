from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

# Enums
class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ExperimentType(str, Enum):
    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    TIME_BASED = "time_based"

class OptimizationStrategy(str, Enum):
    MAXIMIZE_PROFIT = "maximize_profit"
    MAXIMIZE_REVENUE = "maximize_revenue"
    BALANCE = "balance"

# Base Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    sku: str
    cost: float
    base_price: float
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    cost: Optional[float] = None
    base_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    active: Optional[bool] = None

class Product(ProductBase):
    id: int
    current_price: float
    created_at: datetime
    updated_at: datetime
    active: bool
    
    model_config = ConfigDict(from_attributes=True)

# Price Schemas
class PriceUpdate(BaseModel):
    product_id: int
    price: float
    effective_date: Optional[datetime] = None
    change_reason: Optional[str] = None

class PriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    price: float
    effective_date: datetime
    end_date: Optional[datetime] = None
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Competitor Schemas
class CompetitorBase(BaseModel):
    name: str
    website: HttpUrl
    active: bool = True

class CompetitorCreate(CompetitorBase):
    pass

class Competitor(CompetitorBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CompetitorProductCreate(BaseModel):
    competitor_id: int
    product_id: int
    competitor_product_url: HttpUrl
    competitor_price: float

class CompetitorProduct(CompetitorProductCreate):
    id: int
    last_checked: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Experiment Schemas
class ExperimentBase(BaseModel):
    name: str
    description: str
    type: ExperimentType
    start_date: date
    end_date: Optional[date] = None
    control_group: Dict[str, Any]
    test_groups: List[Dict[str, Any]]
    success_metrics: List[str]

class ExperimentCreate(ExperimentBase):
    product_ids: List[int]

class Experiment(ExperimentBase):
    id: int
    status: ExperimentStatus
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    created_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Analytics Schemas
class AnalyticsRequest(BaseModel):
    metrics: List[str]
    start_date: date
    end_date: date
    granularity: str = "daily"
    product_ids: Optional[List[int]] = None
    categories: Optional[List[str]] = None
    compare_period: bool = False

class AnalyticsResponse(BaseModel):
    period: str
    metrics: Dict[str, Any]
    data: List[Dict[str, Any]]
    comparison: Optional[Dict[str, Any]] = None

class KPIResponse(BaseModel):
    date: date
    total_revenue: float
    total_profit: float
    avg_margin: float
    price_optimization_impact: str
    competitor_price_index: float

# Optimization Schemas
class OptimizationRequest(BaseModel):
    product_ids: Optional[List[int]] = None
    category: Optional[str] = None
    strategy: OptimizationStrategy = OptimizationStrategy.MAXIMIZE_PROFIT
    constraints: Optional[Dict[str, Any]] = None

class PriceRecommendation(BaseModel):
    product_id: int
    product_name: str
    current_price: float
    recommended_price: float
    expected_revenue_change: float
    expected_profit_change: float
    confidence_score: float
    reasoning: str

class OptimizationResult(BaseModel):
    job_id: str
    status: str
    strategy: str
    recommendations: List[PriceRecommendation]
    total_expected_impact: Dict[str, float]
    created_at: datetime
    completed_at: Optional[datetime] = None

# Response Models
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

# Elasticity Analysis Schemas
class PriceRecommendationDetail(BaseModel):
    action: str
    amount: float
    percentage: float

class ElasticityResponse(BaseModel):
    product_id: str
    elasticity: float
    confidence: float
    data_points: int
    interpretation: str
    optimal_price: float
    current_price: float
    revenue_opportunity: str
    price_recommendations: Optional[List[PriceRecommendationDetail]] = None
    error: Optional[str] = None

# Competitive Analysis Schemas
class CompetitorPriceInfo(BaseModel):
    name: str
    price: float
    shipping: float
    total_price: float
    in_stock: bool
    last_updated: datetime

class CompetitivePositionResponse(BaseModel):
    product_id: str
    our_price: float
    market_position: str
    avg_competitor_price: Optional[float]
    min_competitor_price: Optional[float]
    max_competitor_price: Optional[float]
    competitors: List[CompetitorPriceInfo]
    recommendation: str
    expected_impact: str
    price_index: Optional[float]