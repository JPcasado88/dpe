"""
Data Generation Script for Dynamic Pricing Engine
Generates realistic product catalog, sales history, and competitor data
"""

import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import psycopg2
from psycopg2.extras import execute_batch
import numpy as np
from typing import List, Dict, Tuple
import json

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'dynamic_pricing_engine',
    'user': 'dpe_user',
    'password': 'dpe_password'
}

class PricingDataGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()
        
        # Product categories with realistic pricing behaviors
        self.product_categories = {
            'Phone Accessories': {
                'count': 150,
                'elasticity_range': (-3.5, -2.0),  # High elasticity
                'competition': 'fierce',
                'subcategories': ['Cases', 'Screen Protectors', 'Chargers', 'Cables'],
                'brands': ['TechShield', 'PowerMax', 'FlexiCase', 'UltraProtect'],
                'margin_range': (0.4, 0.7),
                'price_range': (9.99, 79.99),
                'seasonality': {'back_to_school': 1.3, 'holiday': 1.5}
            },
            'Premium Audio': {
                'count': 80,
                'elasticity_range': (-1.0, -0.3),  # Low elasticity
                'competition': 'moderate',
                'subcategories': ['Headphones', 'Earbuds', 'Speakers'],
                'brands': ['Sony', 'Bose', 'Apple', 'Sennheiser', 'JBL'],
                'margin_range': (0.15, 0.25),
                'price_range': (99.99, 499.99),
                'brand_loyalty': 0.7  # 70% stick to brand regardless of price
            },
            'Gaming Accessories': {
                'count': 120,
                'elasticity_range': (-2.0, -1.0),  # Medium elasticity
                'competition': 'seasonal',
                'subcategories': ['Mice', 'Keyboards', 'Headsets', 'Controllers'],
                'brands': ['Razer', 'Logitech', 'SteelSeries', 'Corsair'],
                'margin_range': (0.25, 0.40),
                'price_range': (29.99, 199.99),
                'seasonality': {'holiday': 2.0, 'summer': 1.3}
            },
            'Smart Home': {
                'count': 100,
                'elasticity_range': (-1.5, -0.8),
                'competition': 'ecosystem',
                'subcategories': ['Lighting', 'Security', 'Climate', 'Hubs'],
                'brands': ['Philips Hue', 'Ring', 'Nest', 'Echo', 'TP-Link'],
                'margin_range': (0.20, 0.35),
                'price_range': (19.99, 299.99),
                'bundle_factor': 1.5  # People buy multiple items
            },
            'Cables & Adapters': {
                'count': 50,
                'elasticity_range': (-5.0, -3.0),  # Extreme elasticity
                'competition': 'price_only',
                'subcategories': ['HDMI', 'USB-C', 'Ethernet', 'Display'],
                'brands': ['AmazonBasics', 'Cable Matters', 'Anker', 'UGREEN'],
                'margin_range': (0.6, 0.8),
                'price_range': (4.99, 39.99)
            }
        }
        
        # Competitors
        self.competitors = [
            {'name': 'Amazon', 'aggressiveness': 0.9, 'price_factor': 0.95},
            {'name': 'BestBuy', 'aggressiveness': 0.6, 'price_factor': 1.05},
            {'name': 'Walmart', 'aggressiveness': 0.8, 'price_factor': 0.97},
            {'name': 'Newegg', 'aggressiveness': 0.7, 'price_factor': 0.98},
            {'name': 'B&H', 'aggressiveness': 0.5, 'price_factor': 1.02}
        ]
        
    def clear_data(self):
        """Clear existing data"""
        tables = ['optimization_jobs', 'analytics_daily', 'experiment_variants', 
                  'experiments', 'sales_data', 'competitor_prices', 'price_changes', 
                  'products', 'competitors', 'price_rules']
        
        for table in tables:
            self.cur.execute(f"TRUNCATE TABLE {table} CASCADE")
        self.conn.commit()
        
    def generate_competitors(self):
        """Generate competitor data"""
        print("Generating competitors...")
        
        for comp in self.competitors:
            self.cur.execute("""
                INSERT INTO competitors (id, name, website, is_active)
                VALUES (%s, %s, %s, %s)
            """, (
                str(uuid.uuid4()),
                comp['name'],
                f"https://www.{comp['name'].lower()}.com",
                True
            ))
        
        self.conn.commit()
        
    def generate_products(self) -> List[Dict]:
        """Generate product catalog"""
        print("Generating products...")
        products = []
        
        for category, config in self.product_categories.items():
            for i in range(config['count']):
                subcategory = random.choice(config['subcategories'])
                brand = random.choice(config['brands'])
                
                # Generate realistic product name
                product_name = self._generate_product_name(category, subcategory, brand, i)
                
                # Calculate prices
                base_price = random.uniform(*config['price_range'])
                margin = random.uniform(*config['margin_range'])
                cost = base_price * (1 - margin)
                
                # Add some variance to MSRP
                msrp = base_price * random.uniform(1.1, 1.3)
                
                # Set price boundaries
                min_price = cost * 1.1  # At least 10% margin
                max_price = msrp * 1.2  # Up to 20% above MSRP
                
                # Generate elasticity for this product
                elasticity = random.uniform(*config['elasticity_range'])
                
                product = {
                    'id': str(uuid.uuid4()),
                    'sku': f"{category[:2].upper()}-{subcategory[:3].upper()}-{i:04d}",
                    'name': product_name,
                    'category': category,
                    'subcategory': subcategory,
                    'brand': brand,
                    'cost': round(cost, 2),
                    'msrp': round(msrp, 2),
                    'current_price': round(base_price, 2),
                    'min_price': round(min_price, 2),
                    'max_price': round(max_price, 2),
                    'stock_quantity': random.randint(10, 500),
                    'stock_velocity': round(random.uniform(0.5, 10.0), 2),
                    'conversion_rate': round(random.uniform(0.01, 0.05), 4),
                    'return_rate': round(random.uniform(0.01, 0.10), 4),
                    'pricing_strategy': random.choice(['aggressive', 'match', 'premium']),
                    'is_featured': random.random() < 0.1,
                    'elasticity': elasticity,
                    'config': config
                }
                
                products.append(product)
                
                # Insert into database
                self.cur.execute("""
                    INSERT INTO products (
                        id, sku, name, category, subcategory, brand, cost, msrp,
                        current_price, min_price, max_price, stock_quantity,
                        stock_velocity, conversion_rate, return_rate,
                        pricing_strategy, is_featured
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    product['id'], product['sku'], product['name'],
                    product['category'], product['subcategory'], product['brand'],
                    product['cost'], product['msrp'], product['current_price'],
                    product['min_price'], product['max_price'], product['stock_quantity'],
                    product['stock_velocity'], product['conversion_rate'],
                    product['return_rate'], product['pricing_strategy'],
                    product['is_featured']
                ))
        
        self.conn.commit()
        return products
    
    def _generate_product_name(self, category: str, subcategory: str, brand: str, index: int) -> str:
        """Generate realistic product names"""
        templates = {
            'Phone Accessories': {
                'Cases': ["{brand} {adj} Case for iPhone {model}",
                         "{brand} {material} Protection Case",
                         "{brand} {adj} {subcategory} with {feature}"],
                'Screen Protectors': ["{brand} Tempered Glass for {device}",
                                    "{brand} {adj} Screen Shield",
                                    "{brand} Anti-{feature} Protector"],
                'Chargers': ["{brand} {watts}W Fast Charger",
                           "{brand} {adj} Charging {type}",
                           "{brand} Quick Charge {version}"],
                'Cables': ["{brand} {length}ft {type} Cable",
                         "{brand} {adj} {connector} to {connector2}",
                         "{brand} Premium {type} {version}"]
            },
            'Premium Audio': {
                'Headphones': ["{brand} {model} Wireless Headphones",
                             "{brand} {adj} Noise Cancelling",
                             "{brand} Studio {type} {version}"],
                'Earbuds': ["{brand} {adj} Pro Earbuds",
                          "{brand} True Wireless {version}",
                          "{brand} Sport {type}"],
                'Speakers': ["{brand} {adj} Bluetooth Speaker",
                           "{brand} {watts}W Portable {type}",
                           "{brand} Smart Speaker {version}"]
            }
        }
        
        # Attributes for name generation
        adjectives = ['Ultra', 'Premium', 'Pro', 'Elite', 'Advanced', 'Essential']
        materials = ['Silicone', 'Leather', 'Carbon Fiber', 'Aluminum']
        features = ['MagSafe', 'Kickstand', 'Wallet', 'Waterproof']
        devices = ['iPhone 15', 'iPhone 14', 'Samsung S23', 'Pixel 8']
        
        # Get template for this category/subcategory
        if category in templates and subcategory in templates[category]:
            template = random.choice(templates[category][subcategory])
            
            # Fill in the template
            name = template.format(
                brand=brand,
                adj=random.choice(adjectives),
                material=random.choice(materials),
                feature=random.choice(features),
                device=random.choice(devices),
                model=random.choice(['15', '14', '13', 'Pro', 'Pro Max']),
                watts=random.choice(['20', '30', '45', '65', '100']),
                type=random.choice(['USB-C', 'Lightning', 'Wireless']),
                length=random.choice(['3', '6', '10']),
                connector=random.choice(['USB-C', 'Lightning', 'USB-A']),
                connector2=random.choice(['USB-C', 'Lightning', 'HDMI']),
                version=random.choice(['3.0', '2.0', 'Plus', 'Max'])
            )
            return name
        
        # Fallback
        return f"{brand} {subcategory} Model {index + 1}"
    
    def generate_historical_sales(self, products: List[Dict], days: int = 180):
        """Generate historical sales data with realistic patterns"""
        print(f"Generating {days} days of sales history...")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Special events
        events = {
            'black_friday': {'date': datetime(2023, 11, 24).date(), 'multiplier': 5.0},
            'cyber_monday': {'date': datetime(2023, 11, 27).date(), 'multiplier': 4.0},
            'prime_day': {'date': datetime(2023, 7, 11).date(), 'multiplier': 3.5},
            'back_to_school': {'dates': [datetime(2023, 8, 15).date() + timedelta(days=i) for i in range(14)], 'multiplier': 2.0}
        }
        
        batch_data = []
        
        for product in products:
            current_date = start_date
            base_demand = random.randint(5, 50)  # Base daily demand
            
            while current_date <= end_date:
                # Check for special events
                event_multiplier = 1.0
                for event, details in events.items():
                    if 'date' in details and current_date == details['date']:
                        event_multiplier = details['multiplier']
                    elif 'dates' in details and current_date in details['dates']:
                        event_multiplier = details['multiplier']
                
                # Add day of week pattern (weekends slightly lower)
                dow_multiplier = 0.8 if current_date.weekday() in [5, 6] else 1.0
                
                # Price variation (simulate price changes)
                price_variation = random.uniform(0.9, 1.1)
                test_price = float(product['current_price']) * price_variation
                
                # Calculate demand based on elasticity
                price_change_pct = (test_price - float(product['current_price'])) / float(product['current_price'])
                demand_change_pct = price_change_pct * product['elasticity']
                demand_multiplier = 1 + demand_change_pct
                
                # Calculate units sold
                units_sold = max(0, int(
                    base_demand * demand_multiplier * event_multiplier * dow_multiplier * 
                    random.uniform(0.7, 1.3)  # Random daily variation
                ))
                
                # Calculate conversion rate (higher when price is lower)
                base_conversion = float(product['conversion_rate'])
                conversion_rate = base_conversion * (1 - price_change_pct * 0.5)
                
                # Page views (inversely related to conversion)
                page_views = int(units_sold / conversion_rate) if conversion_rate > 0 else 0
                
                batch_data.append((
                    current_date,
                    product['id'],
                    round(test_price, 2),
                    units_sold,
                    float(product['cost']),
                    round(conversion_rate, 4),
                    page_views
                ))
                
                current_date += timedelta(days=1)
        
        # Batch insert
        execute_batch(self.cur, """
            INSERT INTO sales_data (date, product_id, price_point, units_sold, cost, conversion_rate, page_views)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, batch_data, page_size=1000)
        
        self.conn.commit()
    
    def generate_competitor_prices(self, products: List[Dict]):
        """Generate competitor pricing data"""
        print("Generating competitor prices...")
        
        # Get competitor IDs
        self.cur.execute("SELECT id, name FROM competitors")
        competitors = {name: id for id, name in self.cur.fetchall()}
        
        batch_data = []
        
        for product in products:
            for comp_name, comp_id in competitors.items():
                # Competitor pricing strategy
                comp_config = next(c for c in self.competitors if c['name'] == comp_name)
                
                # Base competitor price
                comp_price = float(product['current_price']) * comp_config['price_factor']
                comp_price *= random.uniform(0.95, 1.05)  # Add some variance
                
                # Stock availability (Amazon rarely out of stock)
                in_stock = random.random() < (0.95 if comp_name == 'Amazon' else 0.85)
                
                # Shipping cost
                shipping = 0 if comp_price > 35 or comp_name == 'Amazon' else random.uniform(4.99, 9.99)
                
                batch_data.append((
                    product['id'],
                    comp_id,
                    f"{product['sku']}-{comp_name[:3]}",
                    round(comp_price, 2),
                    in_stock,
                    round(shipping, 2)
                ))
        
        execute_batch(self.cur, """
            INSERT INTO competitor_prices (product_id, competitor_id, competitor_sku, price, in_stock, shipping_cost)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, batch_data)
        
        self.conn.commit()
    
    def generate_price_changes(self, products: List[Dict]):
        """Generate historical price changes"""
        print("Generating price change history...")
        
        reasons = ['competitor', 'demand', 'inventory', 'experiment', 'manual']
        
        for product in products:
            # Generate 5-20 price changes per product over time
            num_changes = random.randint(5, 20)
            current_price = float(product['current_price'])
            
            for i in range(num_changes):
                old_price = current_price
                
                # Determine change reason and magnitude
                reason = random.choice(reasons)
                if reason == 'competitor':
                    change_pct = random.uniform(-0.15, -0.05)  # Usually lower
                elif reason == 'demand':
                    change_pct = random.uniform(-0.10, 0.10)  # Both ways
                elif reason == 'inventory':
                    change_pct = random.uniform(-0.20, 0.05)  # Clear stock
                else:
                    change_pct = random.uniform(-0.10, 0.10)
                
                new_price = old_price * (1 + change_pct)
                new_price = max(float(product['min_price']), min(float(product['max_price']), new_price))
                
                # Calculate revenue impact (simplified)
                revenue_impact = random.uniform(-1000, 5000) if change_pct < 0 else random.uniform(-500, 2000)
                
                self.cur.execute("""
                    INSERT INTO price_changes (product_id, old_price, new_price, change_reason, revenue_impact, changed_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    product['id'],
                    round(old_price, 2),
                    round(new_price, 2),
                    reason,
                    round(revenue_impact, 2),
                    datetime.now() - timedelta(days=random.randint(1, 180))
                ))
                
                current_price = new_price
        
        self.conn.commit()
    
    def generate_experiments(self, products: List[Dict]):
        """Generate A/B testing experiments"""
        print("Generating experiments...")
        
        # Create some experiments
        experiments = [
            {
                'name': 'Holiday Pricing Test - Phone Accessories',
                'description': 'Testing 10% discount vs regular price during holiday season',
                'status': 'completed',
                'category': 'Phone Accessories'
            },
            {
                'name': 'Premium Audio Bundle Test',
                'description': 'Testing bundle pricing for headphones + case',
                'status': 'running',
                'category': 'Premium Audio'
            },
            {
                'name': 'Gaming Weekend Flash Sale',
                'description': '20% off gaming accessories for weekend',
                'status': 'completed',
                'category': 'Gaming Accessories'
            }
        ]
        
        for exp in experiments:
            exp_id = str(uuid.uuid4())
            
            # Create experiment
            self.cur.execute("""
                INSERT INTO experiments (id, name, description, status, start_date, end_date, traffic_split, success_metrics)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                exp_id,
                exp['name'],
                exp['description'],
                exp['status'],
                datetime.now() - timedelta(days=30),
                datetime.now() - timedelta(days=1) if exp['status'] == 'completed' else None,
                0.5,
                json.dumps(['revenue', 'conversion_rate', 'units_sold'])
            ))
            
            # Add products to experiment
            category_products = [p for p in products if p['category'] == exp['category']][:5]
            
            for product in category_products:
                # Control variant
                self.cur.execute("""
                    INSERT INTO experiment_variants (experiment_id, product_id, variant_type, price, impressions, conversions, revenue)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    exp_id,
                    product['id'],
                    'control',
                    product['current_price'],
                    random.randint(1000, 5000),
                    random.randint(20, 200),
                    random.uniform(1000, 10000)
                ))
                
                # Variant
                variant_price = float(product['current_price']) * 0.9  # 10% discount
                self.cur.execute("""
                    INSERT INTO experiment_variants (experiment_id, product_id, variant_type, price, impressions, conversions, revenue)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    exp_id,
                    product['id'],
                    'variant',
                    round(variant_price, 2),
                    random.randint(1000, 5000),
                    random.randint(25, 250),
                    random.uniform(1000, 12000)
                ))
        
        self.conn.commit()
    
    def generate_analytics(self):
        """Generate analytics aggregations"""
        print("Generating analytics data...")
        
        # Generate daily analytics for last 30 days
        for days_ago in range(30):
            date = datetime.now().date() - timedelta(days=days_ago)
            
            self.cur.execute("""
                INSERT INTO analytics_daily (
                    date, total_revenue, total_units, total_profit,
                    avg_price_change, total_price_changes, conversion_rate,
                    products_above_market, products_below_market, products_at_market
                )
                SELECT 
                    %s,
                    COALESCE(SUM(revenue), 0),
                    COALESCE(SUM(units_sold), 0),
                    COALESCE(SUM(profit), 0),
                    COALESCE(AVG(ABS((new_price - old_price) / old_price * 100)), 0),
                    COUNT(DISTINCT pc.id),
                    COALESCE(AVG(sd.conversion_rate), 0),
                    COUNT(CASE WHEN cp.market_position = 'above_market' THEN 1 END),
                    COUNT(CASE WHEN cp.market_position = 'below_market' THEN 1 END),
                    COUNT(CASE WHEN cp.market_position = 'at_market' THEN 1 END)
                FROM sales_data sd
                LEFT JOIN price_changes pc ON pc.changed_at::date = %s
                LEFT JOIN current_competitive_position cp ON cp.id = sd.product_id
                WHERE sd.date = %s
            """, (date, date, date))
        
        self.conn.commit()
    
    def run(self):
        """Run the complete data generation process"""
        try:
            print("Starting data generation...")
            
            # Clear existing data
            self.clear_data()
            
            # Generate data in order
            self.generate_competitors()
            products = self.generate_products()
            print(f"Generated {len(products)} products")
            
            self.generate_historical_sales(products)
            self.generate_competitor_prices(products)
            self.generate_price_changes(products)
            self.generate_experiments(products)
            self.generate_analytics()
            
            print("Data generation complete!")
            
        except Exception as e:
            print(f"Error: {e}")
            self.conn.rollback()
        finally:
            self.cur.close()
            self.conn.close()


if __name__ == "__main__":
    generator = PricingDataGenerator()
    generator.run()