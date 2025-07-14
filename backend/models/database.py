from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Date, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dpe_db")

# Railway compatibility - convert postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Add connection pool settings for production
engine_args = {}
if "railway.app" in DATABASE_URL or "postgres" in DATABASE_URL:
    engine_args = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 300,  # Recycle connections after 5 minutes
    }

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_database_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Models

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, index=True)
    sku = Column(String, unique=True, index=True)
    cost = Column(Float)
    base_price = Column(Float)
    current_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="product")
    competitor_products = relationship("CompetitorProduct", back_populates="product")
    experiment_products = relationship("ExperimentProduct", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float, nullable=False)
    effective_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    changed_by = Column(String)
    change_reason = Column(String)
    
    # Relationships
    product = relationship("Product", back_populates="price_history")

class Competitor(Base):
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    website = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor_products = relationship("CompetitorProduct", back_populates="competitor")

class CompetitorProduct(Base):
    __tablename__ = "competitor_products"
    
    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    competitor_product_url = Column(String)
    competitor_price = Column(Float)
    last_checked = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    competitor = relationship("Competitor", back_populates="competitor_products")
    product = relationship("Product", back_populates="competitor_products")

class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String)  # ab_test, multivariate, time_based
    status = Column(String, default="draft")  # draft, running, paused, completed, cancelled
    start_date = Column(Date)
    end_date = Column(Date)
    control_group = Column(JSON)
    test_groups = Column(JSON)
    success_metrics = Column(JSON)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)
    
    # Relationships
    experiment_products = relationship("ExperimentProduct", back_populates="experiment")

class ExperimentProduct(Base):
    __tablename__ = "experiment_products"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    group = Column(String)  # control, variant_a, variant_b, etc.
    test_price = Column(Float)
    
    # Relationships
    experiment = relationship("Experiment", back_populates="experiment_products")
    product = relationship("Product", back_populates="experiment_products")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    date = Column(Date, index=True)
    price = Column(Float)  # Added price field for elasticity calculations
    revenue = Column(Float)
    profit = Column(Float)
    units_sold = Column(Integer)
    conversion_rate = Column(Float)
    avg_order_value = Column(Float)
    price_elasticity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class OptimizationJob(Base):
    __tablename__ = "optimization_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    strategy = Column(String)
    constraints = Column(JSON)
    products = Column(JSON)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_by = Column(String)

# Database initialization
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()