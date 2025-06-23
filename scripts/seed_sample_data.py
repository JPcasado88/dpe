"""
Seed sample data for quick testing
Creates a smaller dataset for development
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from backend.models.database import Base, Product, Competitor, CompetitorProduct, PriceHistory, Analytics

# Database URL from environment or default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://dpe_user:dpe_password@localhost:5432/dynamic_pricing_engine')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def clear_data():
    """Clear existing data"""
    session.query(Analytics).delete()
    session.query(PriceHistory).delete()
    session.query(CompetitorProduct).delete()
    session.query(Product).delete()
    session.query(Competitor).delete()
    session.commit()

def seed_competitors():
    """Create sample competitors"""
    competitors = [
        Competitor(name='Amazon', website='https://amazon.com'),
        Competitor(name='BestBuy', website='https://bestbuy.com'),
        Competitor(name='Walmart', website='https://walmart.com'),
    ]
    session.add_all(competitors)
    session.commit()
    return competitors

def seed_products():
    """Create sample products"""
    products = []
    
    # Phone Accessories
    products.extend([
        Product(
            sku='PA-001',
            name='Premium iPhone 15 Case - Carbon Fiber',
            category='Phone Accessories',
            subcategory='Cases',
            brand='TechShield',
            cost=12.00,
            msrp=49.99,
            current_price=39.99,
            min_price=25.00,
            max_price=55.00,
            stock_quantity=150,
            conversion_rate=0.032
        ),
        Product(
            sku='PA-002',
            name='Ultra Clear Screen Protector Pack',
            category='Phone Accessories',
            subcategory='Screen Protectors',
            brand='ClearView',
            cost=3.50,
            msrp=19.99,
            current_price=14.99,
            min_price=9.99,
            max_price=24.99,
            stock_quantity=500,
            conversion_rate=0.045
        ),
    ])
    
    # Premium Audio
    products.extend([
        Product(
            sku='AU-001',
            name='Sony WH-1000XM5 Wireless Headphones',
            category='Premium Audio',
            subcategory='Headphones',
            brand='Sony',
            cost=180.00,
            msrp=399.99,
            current_price=349.99,
            min_price=299.99,
            max_price=399.99,
            stock_quantity=45,
            conversion_rate=0.018
        ),
        Product(
            sku='AU-002',
            name='Apple AirPods Pro (2nd Gen)',
            category='Premium Audio',
            subcategory='Earbuds',
            brand='Apple',
            cost=150.00,
            msrp=249.99,
            current_price=229.99,
            min_price=199.99,
            max_price=249.99,
            stock_quantity=80,
            conversion_rate=0.025
        ),
    ])
    
    # Gaming Accessories
    products.extend([
        Product(
            sku='GA-001',
            name='Razer DeathAdder V3 Gaming Mouse',
            category='Gaming Accessories',
            subcategory='Mice',
            brand='Razer',
            cost=65.00,
            msrp=149.99,
            current_price=129.99,
            min_price=99.99,
            max_price=149.99,
            stock_quantity=120,
            conversion_rate=0.028
        ),
        Product(
            sku='GA-002',
            name='Corsair K70 RGB Mechanical Keyboard',
            category='Gaming Accessories',
            subcategory='Keyboards',
            brand='Corsair',
            cost=70.00,
            msrp=169.99,
            current_price=139.99,
            min_price=119.99,
            max_price=169.99,
            stock_quantity=60,
            conversion_rate=0.022
        ),
    ])
    
    session.add_all(products)
    session.commit()
    return products

def seed_competitor_prices(products, competitors):
    """Create competitor pricing data"""
    for product in products:
        for competitor in competitors:
            # Amazon tends to be cheaper
            if competitor.name == 'Amazon':
                price_factor = random.uniform(0.92, 0.98)
            # BestBuy tends to be at MSRP
            elif competitor.name == 'BestBuy':
                price_factor = random.uniform(0.98, 1.05)
            # Walmart competitive but not always cheapest
            else:
                price_factor = random.uniform(0.94, 1.02)
            
            comp_price = CompetitorProduct(
                product_id=product.id,
                competitor_id=competitor.id,
                price=round(product.current_price * price_factor, 2),
                in_stock=random.choice([True, True, True, False]),  # 75% in stock
                shipping_cost=0 if product.current_price > 35 else random.uniform(4.99, 9.99),
                last_updated=datetime.utcnow()
            )
            session.add(comp_price)
    
    session.commit()

def seed_price_history(products):
    """Create price change history"""
    reasons = ['competitor_match', 'demand_based', 'inventory_clearance', 'promotion']
    
    for product in products:
        # Generate 3-8 price changes over last 30 days
        num_changes = random.randint(3, 8)
        current_price = product.current_price
        
        for i in range(num_changes):
            days_ago = random.randint(1, 30)
            old_price = current_price
            
            # Determine price change
            if random.random() < 0.6:  # 60% chance of decrease
                change_factor = random.uniform(0.85, 0.95)
            else:
                change_factor = random.uniform(1.02, 1.10)
            
            new_price = round(old_price * change_factor, 2)
            new_price = max(product.min_price, min(product.max_price, new_price))
            
            price_change = PriceHistory(
                product_id=product.id,
                old_price=old_price,
                new_price=new_price,
                change_reason=random.choice(reasons),
                changed_at=datetime.utcnow() - timedelta(days=days_ago)
            )
            session.add(price_change)
            
            current_price = new_price
    
    session.commit()

def main():
    """Run the seeding process"""
    print("Seeding sample data...")
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        
        # Clear existing data
        clear_data()
        
        # Seed data
        competitors = seed_competitors()
        print(f"Created {len(competitors)} competitors")
        
        products = seed_products()
        print(f"Created {len(products)} products")
        
        seed_competitor_prices(products, competitors)
        print("Created competitor prices")
        
        seed_price_history(products)
        print("Created price history")
        
        print("Sample data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()