"""
Railway-compatible database configuration
"""
import os
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def get_database_url():
    """
    Get database URL with Railway compatibility
    Railway provides DATABASE_URL in the format:
    postgresql://user:password@host:port/database
    """
    database_url = os.getenv("DATABASE_URL", "")
    
    if not database_url:
        logger.warning("DATABASE_URL not found, using default")
        return "postgresql://user:password@localhost/dpe_db"
    
    # Railway sometimes provides postgres:// instead of postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        logger.info("Converted postgres:// to postgresql://")
    
    # Parse the URL to check if it's valid
    try:
        parsed = urlparse(database_url)
        logger.info(f"Database host: {parsed.hostname}, port: {parsed.port}, database: {parsed.path.lstrip('/')}")
    except Exception as e:
        logger.error(f"Failed to parse DATABASE_URL: {e}")
    
    return database_url

def get_redis_url():
    """
    Get Redis URL with Railway compatibility
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Railway provides REDIS_URL in the correct format usually
    logger.info(f"Redis URL configured: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
    
    return redis_url