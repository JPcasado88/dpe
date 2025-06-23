"""
Redis Caching Service for Dynamic Pricing Engine
Handles caching of prices, optimization results, and competitor data
"""

import redis
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import os
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.client = None
        self._connect()
        
        # Cache TTL settings (in seconds)
        self.TTL = {
            'current_price': 300,        # 5 minutes
            'competitor_price': 900,     # 15 minutes
            'optimization_result': 3600, # 1 hour
            'elasticity': 86400,        # 24 hours
            'analytics': 1800,          # 30 minutes
            'experiment': 300,          # 5 minutes
        }
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            # Fallback to in-memory cache if Redis is not available
            self.client = None
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a standardized cache key"""
        return f"dpe:{prefix}:{identifier}"
    
    def _serialize(self, data: Any) -> str:
        """Serialize data for storage"""
        return json.dumps(data, default=str)
    
    def _deserialize(self, data: str) -> Any:
        """Deserialize data from storage"""
        return json.loads(data)
    
    # Current Prices Cache
    def get_current_price(self, product_id: str) -> Optional[float]:
        """Get cached current price for a product"""
        if not self.client:
            return None
            
        try:
            key = self._make_key("price:current", product_id)
            data = self.client.get(key)
            return float(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_current_price(self, product_id: str, price: float):
        """Cache current price for a product"""
        if not self.client:
            return
            
        try:
            key = self._make_key("price:current", product_id)
            self.client.setex(key, self.TTL['current_price'], price)
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    def invalidate_current_price(self, product_id: str):
        """Invalidate cached price when updated"""
        if not self.client:
            return
            
        try:
            key = self._make_key("price:current", product_id)
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Cache invalidate error: {str(e)}")
    
    # Competitor Prices Cache
    def get_competitor_prices(self, product_id: str) -> Optional[List[Dict]]:
        """Get cached competitor prices"""
        if not self.client:
            return None
            
        try:
            key = self._make_key("price:competitor", product_id)
            data = self.client.get(key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_competitor_prices(self, product_id: str, prices: List[Dict]):
        """Cache competitor prices"""
        if not self.client:
            return
            
        try:
            key = self._make_key("price:competitor", product_id)
            self.client.setex(key, self.TTL['competitor_price'], self._serialize(prices))
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    # Optimization Results Cache
    def get_optimization_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached optimization result"""
        if not self.client:
            return None
            
        try:
            key = self._make_key("optimization", cache_key)
            data = self.client.get(key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_optimization_result(self, cache_key: str, result: Dict):
        """Cache optimization result"""
        if not self.client:
            return
            
        try:
            key = self._make_key("optimization", cache_key)
            self.client.setex(key, self.TTL['optimization_result'], self._serialize(result))
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    def create_optimization_cache_key(self, product_ids: List[str], strategy: str, constraints: Dict) -> str:
        """Create a unique cache key for optimization parameters"""
        params = {
            'product_ids': sorted(product_ids),
            'strategy': strategy,
            'constraints': constraints
        }
        params_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()
    
    # Elasticity Cache
    def get_elasticity(self, product_id: str, days: int) -> Optional[Dict]:
        """Get cached elasticity calculation"""
        if not self.client:
            return None
            
        try:
            key = self._make_key("elasticity", f"{product_id}:{days}")
            data = self.client.get(key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_elasticity(self, product_id: str, days: int, result: Dict):
        """Cache elasticity calculation"""
        if not self.client:
            return
            
        try:
            key = self._make_key("elasticity", f"{product_id}:{days}")
            self.client.setex(key, self.TTL['elasticity'], self._serialize(result))
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    # Analytics Cache
    def get_analytics(self, cache_key: str) -> Optional[Dict]:
        """Get cached analytics data"""
        if not self.client:
            return None
            
        try:
            key = self._make_key("analytics", cache_key)
            data = self.client.get(key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_analytics(self, cache_key: str, data: Dict):
        """Cache analytics data"""
        if not self.client:
            return
            
        try:
            key = self._make_key("analytics", cache_key)
            self.client.setex(key, self.TTL['analytics'], self._serialize(data))
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    # Experiment Allocation Cache
    def get_experiment_allocation(self, product_id: str, user_id: str) -> Optional[Dict]:
        """Get cached experiment allocation for user/product"""
        if not self.client:
            return None
            
        try:
            key = self._make_key("experiment:allocation", f"{product_id}:{user_id}")
            data = self.client.get(key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set_experiment_allocation(self, product_id: str, user_id: str, allocation: Dict):
        """Cache experiment allocation"""
        if not self.client:
            return
            
        try:
            key = self._make_key("experiment:allocation", f"{product_id}:{user_id}")
            self.client.setex(key, self.TTL['experiment'], self._serialize(allocation))
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    # Batch Operations
    def get_multiple_prices(self, product_ids: List[str]) -> Dict[str, Optional[float]]:
        """Get multiple product prices in one operation"""
        if not self.client:
            return {pid: None for pid in product_ids}
            
        try:
            keys = [self._make_key("price:current", pid) for pid in product_ids]
            values = self.client.mget(keys)
            
            result = {}
            for i, product_id in enumerate(product_ids):
                result[product_id] = float(values[i]) if values[i] else None
            
            return result
        except Exception as e:
            logger.error(f"Cache batch get error: {str(e)}")
            return {pid: None for pid in product_ids}
    
    def set_multiple_prices(self, price_map: Dict[str, float]):
        """Set multiple product prices in one operation"""
        if not self.client:
            return
            
        try:
            pipe = self.client.pipeline()
            for product_id, price in price_map.items():
                key = self._make_key("price:current", product_id)
                pipe.setex(key, self.TTL['current_price'], price)
            pipe.execute()
        except Exception as e:
            logger.error(f"Cache batch set error: {str(e)}")
    
    # Cache Statistics
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.client:
            return {"status": "disconnected"}
            
        try:
            info = self.client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                    2
                )
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def flush_pattern(self, pattern: str):
        """Delete all keys matching a pattern"""
        if not self.client:
            return
            
        try:
            cursor = 0
            while True:
                cursor, keys = self.client.scan(cursor, match=f"dpe:{pattern}:*", count=100)
                if keys:
                    self.client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Cache flush error: {str(e)}")

# Singleton instance
cache_service = CacheService()

# Decorator for caching function results
def cached(prefix: str, ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache_service.get_analytics(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache_service.set_analytics(cache_key, result)
            
            return result
        
        return wrapper
    return decorator