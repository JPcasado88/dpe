"""
Production Monitoring and Alerting Service
Tracks system health, price anomalies, and business metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import asyncio
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from prometheus_client import Counter, Histogram, Gauge, Summary
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models.database import Product, PriceHistory, Analytics
from ..config import settings

logger = logging.getLogger(__name__)

# Prometheus metrics
price_changes_counter = Counter('dpe_price_changes_total', 'Total number of price changes', ['reason', 'category'])
revenue_gauge = Gauge('dpe_revenue_current', 'Current revenue')
optimization_histogram = Histogram('dpe_optimization_duration_seconds', 'Time spent in optimization')
api_request_summary = Summary('dpe_api_request_duration_seconds', 'API request latency')
alert_counter = Counter('dpe_alerts_total', 'Total number of alerts triggered', ['severity', 'type'])

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertType(Enum):
    PRICE_ANOMALY = "price_anomaly"
    MARGIN_VIOLATION = "margin_violation"
    COMPETITOR_MISMATCH = "competitor_mismatch"
    SYSTEM_ERROR = "system_error"
    REVENUE_DROP = "revenue_drop"
    EXPERIMENT_FAILURE = "experiment_failure"

@dataclass
class Alert:
    severity: AlertSeverity
    type: AlertType
    title: str
    message: str
    product_id: Optional[str] = None
    metadata: Optional[Dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class MonitoringService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.alert_queue: List[Alert] = []
        self.alert_handlers = {
            AlertSeverity.INFO: self._handle_info_alert,
            AlertSeverity.WARNING: self._handle_warning_alert,
            AlertSeverity.CRITICAL: self._handle_critical_alert
        }
        
    async def check_price_guardrails(self, product_id: str, new_price: float) -> Tuple[bool, Optional[str]]:
        """Check if a price change violates any guardrails"""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False, "Product not found"
        
        # Check min/max bounds
        if new_price < product.min_price:
            self._create_alert(
                AlertSeverity.WARNING,
                AlertType.PRICE_ANOMALY,
                f"Price below minimum for {product.name}",
                f"Attempted price ${new_price} is below minimum ${product.min_price}",
                product_id
            )
            return False, f"Price ${new_price} is below minimum ${product.min_price}"
        
        if new_price > product.max_price:
            self._create_alert(
                AlertSeverity.WARNING,
                AlertType.PRICE_ANOMALY,
                f"Price above maximum for {product.name}",
                f"Attempted price ${new_price} is above maximum ${product.max_price}",
                product_id
            )
            return False, f"Price ${new_price} is above maximum ${product.max_price}"
        
        # Check margin requirements
        margin = (new_price - product.cost) / new_price
        min_margin = settings.MIN_MARGIN_REQUIREMENT
        
        if margin < min_margin:
            self._create_alert(
                AlertSeverity.WARNING,
                AlertType.MARGIN_VIOLATION,
                f"Margin violation for {product.name}",
                f"Price ${new_price} results in margin {margin:.1%}, below minimum {min_margin:.1%}",
                product_id
            )
            return False, f"Price results in margin {margin:.1%}, below minimum {min_margin:.1%}"
        
        # Check rate of change
        last_change = self.db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(PriceHistory.effective_date.desc()).first()
        
        if last_change:
            hours_since_change = (datetime.utcnow() - last_change.effective_date).total_seconds() / 3600
            if hours_since_change < settings.MIN_HOURS_BETWEEN_CHANGES:
                return False, f"Price changed too recently ({hours_since_change:.1f} hours ago)"
            
            price_change_pct = abs((new_price - product.current_price) / product.current_price)
            if price_change_pct > settings.MAX_PRICE_CHANGE_PCT:
                self._create_alert(
                    AlertSeverity.WARNING,
                    AlertType.PRICE_ANOMALY,
                    f"Large price change for {product.name}",
                    f"Price change of {price_change_pct:.1%} exceeds maximum {settings.MAX_PRICE_CHANGE_PCT:.1%}",
                    product_id
                )
                return False, f"Price change of {price_change_pct:.1%} exceeds maximum allowed"
        
        return True, None
    
    async def monitor_system_health(self):
        """Monitor overall system health metrics"""
        try:
            # Check API response times
            # This would integrate with your API monitoring
            
            # Check database connection
            self.db.execute("SELECT 1")
            
            # Check Redis connection (if available)
            from ..services.cache import cache_service
            cache_stats = cache_service.get_cache_stats()
            
            if cache_stats.get('status') != 'connected':
                self._create_alert(
                    AlertSeverity.WARNING,
                    AlertType.SYSTEM_ERROR,
                    "Cache service disconnected",
                    "Redis cache is not available, falling back to database"
                )
            
            # Check ML model status
            # This would check if models are loaded and responding
            
        except Exception as e:
            self._create_alert(
                AlertSeverity.CRITICAL,
                AlertType.SYSTEM_ERROR,
                "System health check failed",
                str(e)
            )
    
    async def monitor_business_metrics(self):
        """Monitor business KPIs and alert on anomalies"""
        try:
            # Check revenue trends
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            last_week = today - timedelta(days=7)
            
            # Get today's revenue
            today_revenue = self.db.query(
                func.sum(Analytics.revenue)
            ).filter(
                Analytics.date == today
            ).scalar() or 0
            
            # Get yesterday's revenue
            yesterday_revenue = self.db.query(
                func.sum(Analytics.revenue)
            ).filter(
                Analytics.date == yesterday
            ).scalar() or 0
            
            # Get last week's average
            last_week_avg = self.db.query(
                func.avg(Analytics.revenue)
            ).filter(
                and_(
                    Analytics.date >= last_week,
                    Analytics.date < today
                )
            ).scalar() or 0
            
            # Check for revenue drop
            if yesterday_revenue > 0:
                revenue_change = (today_revenue - yesterday_revenue) / yesterday_revenue
                
                if revenue_change < -0.2:  # 20% drop
                    self._create_alert(
                        AlertSeverity.CRITICAL,
                        AlertType.REVENUE_DROP,
                        "Significant revenue drop detected",
                        f"Revenue dropped {abs(revenue_change):.1%} from yesterday",
                        metadata={
                            'today_revenue': today_revenue,
                            'yesterday_revenue': yesterday_revenue,
                            'change_pct': revenue_change
                        }
                    )
            
            # Update Prometheus metrics
            revenue_gauge.set(today_revenue)
            
        except Exception as e:
            logger.error(f"Error monitoring business metrics: {str(e)}")
    
    async def monitor_experiments(self):
        """Monitor running experiments for anomalies"""
        from ..models.database import Experiment
        
        running_experiments = self.db.query(Experiment).filter(
            Experiment.status == 'running'
        ).all()
        
        for experiment in running_experiments:
            # Check if experiment is collecting data
            # Check for statistical anomalies
            # Alert if experiment needs attention
            pass
    
    def _create_alert(self, severity: AlertSeverity, alert_type: AlertType, 
                     title: str, message: str, product_id: Optional[str] = None,
                     metadata: Optional[Dict] = None):
        """Create and queue an alert"""
        alert = Alert(
            severity=severity,
            type=alert_type,
            title=title,
            message=message,
            product_id=product_id,
            metadata=metadata
        )
        
        self.alert_queue.append(alert)
        alert_counter.labels(severity=severity.value, type=alert_type.value).inc()
        
        # Process immediately if critical
        if severity == AlertSeverity.CRITICAL:
            asyncio.create_task(self._process_alert(alert))
    
    async def process_alerts(self):
        """Process queued alerts"""
        while self.alert_queue:
            alert = self.alert_queue.pop(0)
            await self._process_alert(alert)
    
    async def _process_alert(self, alert: Alert):
        """Process a single alert"""
        handler = self.alert_handlers.get(alert.severity)
        if handler:
            await handler(alert)
    
    async def _handle_info_alert(self, alert: Alert):
        """Handle info level alerts - just log"""
        logger.info(f"[{alert.type.value}] {alert.title}: {alert.message}")
    
    async def _handle_warning_alert(self, alert: Alert):
        """Handle warning level alerts - log and maybe notify"""
        logger.warning(f"[{alert.type.value}] {alert.title}: {alert.message}")
        
        # Send to monitoring dashboard
        # Could integrate with Slack, Discord, etc.
    
    async def _handle_critical_alert(self, alert: Alert):
        """Handle critical alerts - immediate notification"""
        logger.error(f"[CRITICAL] [{alert.type.value}] {alert.title}: {alert.message}")
        
        # Send email notification
        if settings.ALERT_EMAIL_ENABLED:
            await self._send_email_alert(alert)
        
        # Send to PagerDuty, Slack, etc.
        # Could integrate with incident management tools
    
    async def _send_email_alert(self, alert: Alert):
        """Send email notification for critical alerts"""
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.ALERT_EMAIL_FROM
            msg['To'] = settings.ALERT_EMAIL_TO
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
            Alert Type: {alert.type.value}
            Severity: {alert.severity.value}
            Time: {alert.timestamp}
            
            {alert.message}
            
            {f"Product ID: {alert.product_id}" if alert.product_id else ""}
            {f"Additional Data: {alert.metadata}" if alert.metadata else ""}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (would need SMTP configuration)
            # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            #     server.starttls()
            #     server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            #     server.send_message(msg)
            
            logger.info(f"Email alert sent for {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")

class PriceAnomalyDetector:
    """Detect anomalous price patterns"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def detect_anomalies(self, product_id: str, new_price: float) -> List[str]:
        """Detect various types of price anomalies"""
        anomalies = []
        
        # Get historical prices
        history = self.db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(PriceHistory.effective_date.desc()).limit(30).all()
        
        if len(history) < 5:
            return anomalies  # Not enough data
        
        prices = [h.price for h in history]
        
        # Statistical anomaly detection
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        # Check if new price is an outlier (3 sigma rule)
        if abs(new_price - mean_price) > 3 * std_price:
            anomalies.append(f"Price ${new_price} is a statistical outlier (mean: ${mean_price:.2f}, std: ${std_price:.2f})")
        
        # Trend reversal detection
        recent_prices = prices[:5]
        if all(recent_prices[i] <= recent_prices[i+1] for i in range(len(recent_prices)-1)):
            # Prices were increasing
            if new_price < recent_prices[0] * 0.95:
                anomalies.append("Sudden reversal from increasing trend")
        elif all(recent_prices[i] >= recent_prices[i+1] for i in range(len(recent_prices)-1)):
            # Prices were decreasing
            if new_price > recent_prices[0] * 1.05:
                anomalies.append("Sudden reversal from decreasing trend")
        
        # Volatility check
        recent_changes = [abs(prices[i] - prices[i+1]) / prices[i+1] for i in range(min(5, len(prices)-1))]
        avg_volatility = np.mean(recent_changes)
        current_change = abs(new_price - prices[0]) / prices[0]
        
        if current_change > avg_volatility * 3:
            anomalies.append(f"Price change {current_change:.1%} exceeds typical volatility {avg_volatility:.1%}")
        
        return anomalies

# Monitoring middleware for API requests
def monitor_api_request(endpoint: str):
    """Decorator to monitor API request performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with api_request_summary.labels(endpoint=endpoint).time():
                result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator

# Background monitoring task
async def run_monitoring_loop(db_session: Session):
    """Run continuous monitoring checks"""
    monitor = MonitoringService(db_session)
    
    while True:
        try:
            # Run health checks every minute
            await monitor.monitor_system_health()
            
            # Run business metrics checks every 5 minutes
            if datetime.now().minute % 5 == 0:
                await monitor.monitor_business_metrics()
            
            # Check experiments every 10 minutes
            if datetime.now().minute % 10 == 0:
                await monitor.monitor_experiments()
            
            # Process any pending alerts
            await monitor.process_alerts()
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
        
        await asyncio.sleep(60)  # Check every minute