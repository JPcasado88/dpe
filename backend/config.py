import os
from typing import Optional
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Dynamic Pricing Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API settings
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dpe_db")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_TTL: int = 3600  # 1 hour cache TTL
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External API Keys
    COMPETITOR_API_KEY: Optional[str] = os.getenv("COMPETITOR_API_KEY")
    ANALYTICS_API_KEY: Optional[str] = os.getenv("ANALYTICS_API_KEY")
    
    # Machine Learning settings
    ML_MODEL_PATH: str = "models/ml"
    ML_UPDATE_FREQUENCY: int = 86400  # Update models daily
    
    # Optimization settings
    OPTIMIZATION_BATCH_SIZE: int = 100
    MAX_PRICE_CHANGE_PERCENT: float = 0.15  # 15% max price change
    MIN_PROFIT_MARGIN: float = 0.20  # 20% minimum profit margin
    
    # Experiment settings
    MIN_EXPERIMENT_DURATION_DAYS: int = 7
    MIN_SAMPLE_SIZE: int = 100
    CONFIDENCE_LEVEL: float = 0.95
    
    # Monitoring and Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/app.log"
    ENABLE_METRICS: bool = True
    
    # Price Guardrails
    MIN_MARGIN_REQUIREMENT: float = 0.15  # 15% minimum margin
    MAX_PRICE_CHANGE_PCT: float = 0.20  # 20% max change per update
    MIN_HOURS_BETWEEN_CHANGES: int = 4  # Minimum 4 hours between price changes
    
    # Alert Settings
    ALERT_EMAIL_ENABLED: bool = bool(os.getenv("ALERT_EMAIL_ENABLED", "False"))
    ALERT_EMAIL_FROM: str = os.getenv("ALERT_EMAIL_FROM", "alerts@dynamicpricing.io")
    ALERT_EMAIL_TO: str = os.getenv("ALERT_EMAIL_TO", "admin@dynamicpricing.io")
    ALERT_WEBHOOK_URL: Optional[str] = os.getenv("ALERT_WEBHOOK_URL")  # Slack, Discord, etc.
    
    # Background Jobs
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    
    # Email settings (for notifications)
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    NOTIFICATION_EMAIL: Optional[str] = os.getenv("NOTIFICATION_EMAIL")
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create settings instance
settings = Settings()

# Feature flags
FEATURE_FLAGS = {
    "enable_ml_optimization": True,
    "enable_competitor_tracking": True,
    "enable_ab_testing": True,
    "enable_real_time_updates": False,
    "enable_email_notifications": bool(settings.SMTP_HOST),
}

# Validation rules for pricing
PRICING_RULES = {
    "min_margin_threshold": 0.10,
    "max_margin_threshold": 0.60,
    "competitor_price_match_threshold": 0.95,  # Price within 95% of competitor
    "volume_discount_tiers": [
        {"min_quantity": 10, "discount": 0.05},
        {"min_quantity": 50, "discount": 0.10},
        {"min_quantity": 100, "discount": 0.15},
    ],
    "seasonal_adjustments": {
        "holiday": 1.10,  # 10% increase during holidays
        "off_season": 0.90,  # 10% decrease during off-season
    }
}