-- Dynamic Pricing Engine Database Schema
-- PostgreSQL Database

-- Create database
-- CREATE DATABASE dynamic_pricing_engine;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Products table: Core product catalog
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    cost DECIMAL(10,2) NOT NULL,
    msrp DECIMAL(10,2) NOT NULL,
    current_price DECIMAL(10,2) NOT NULL,
    min_price DECIMAL(10,2) NOT NULL, -- Price floor
    max_price DECIMAL(10,2) NOT NULL, -- Price ceiling
    
    -- Inventory
    stock_quantity INTEGER DEFAULT 0,
    stock_velocity DECIMAL(5,2), -- Units sold per day
    
    -- Performance metrics
    conversion_rate DECIMAL(5,4) DEFAULT 0.0,
    return_rate DECIMAL(5,4) DEFAULT 0.0,
    
    -- Strategy
    pricing_strategy VARCHAR(50) DEFAULT 'match', -- 'aggressive', 'match', 'premium'
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Price changes history
CREATE TABLE price_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    old_price DECIMAL(10,2) NOT NULL,
    new_price DECIMAL(10,2) NOT NULL,
    change_percentage DECIMAL(5,2) GENERATED ALWAYS AS ((new_price - old_price) / old_price * 100) STORED,
    change_reason VARCHAR(100) NOT NULL, -- 'competitor', 'demand', 'inventory', 'experiment', 'manual'
    revenue_impact DECIMAL(10,2), -- Calculated after change
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by VARCHAR(100) DEFAULT 'system',
    
    INDEX idx_product_changed_at (product_id, changed_at DESC)
);

-- Competitor tracking
CREATE TABLE competitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Competitor prices
CREATE TABLE competitor_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    competitor_id UUID REFERENCES competitors(id) ON DELETE CASCADE,
    competitor_sku VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    in_stock BOOLEAN DEFAULT TRUE,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) GENERATED ALWAYS AS (price + shipping_cost) STORED,
    scraped_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_product_competitor_scraped (product_id, competitor_id, scraped_at DESC),
    UNIQUE (product_id, competitor_id, scraped_at)
);

-- Sales data for elasticity calculations
CREATE TABLE sales_data (
    date DATE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    price_point DECIMAL(10,2) NOT NULL,
    units_sold INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) GENERATED ALWAYS AS (units_sold * price_point) STORED,
    cost DECIMAL(10,2) NOT NULL,
    profit DECIMAL(10,2) GENERATED ALWAYS AS ((price_point - cost) * units_sold) STORED,
    conversion_rate DECIMAL(5,4),
    page_views INTEGER DEFAULT 0,
    
    PRIMARY KEY (date, product_id, price_point),
    INDEX idx_product_date (product_id, date DESC)
);

-- A/B Testing experiments
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'running', 'completed', 'cancelled'
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    traffic_split DECIMAL(3,2) DEFAULT 0.50, -- Percentage for variant
    success_metrics JSONB, -- ['revenue', 'conversion_rate', 'profit']
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Experiment variants
CREATE TABLE experiment_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID REFERENCES experiments(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    variant_type VARCHAR(20) NOT NULL, -- 'control' or 'variant'
    price DECIMAL(10,2) NOT NULL,
    
    -- Results
    impressions INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    conversion_rate DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE WHEN impressions > 0 THEN conversions::DECIMAL / impressions 
        ELSE 0 END
    ) STORED,
    
    UNIQUE (experiment_id, product_id, variant_type)
);

-- Price rules and constraints
CREATE TABLE price_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'margin', 'competitor', 'velocity', 'category'
    condition JSONB NOT NULL, -- Flexible condition storage
    action JSONB NOT NULL, -- What to do when condition is met
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analytics aggregations
CREATE TABLE analytics_daily (
    date DATE NOT NULL,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    total_units INTEGER DEFAULT 0,
    total_profit DECIMAL(12,2) DEFAULT 0,
    avg_price_change DECIMAL(5,2),
    total_price_changes INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4),
    
    -- By category
    category_metrics JSONB,
    
    -- Competitive position
    products_above_market INTEGER DEFAULT 0,
    products_below_market INTEGER DEFAULT 0,
    products_at_market INTEGER DEFAULT 0,
    
    PRIMARY KEY (date)
);

-- Optimization jobs tracking
CREATE TABLE optimization_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL, -- 'full_catalog', 'category', 'single_product'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    parameters JSONB,
    products_optimized INTEGER DEFAULT 0,
    revenue_impact DECIMAL(12,2),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_price_changes_reason ON price_changes(change_reason);
CREATE INDEX idx_sales_data_date ON sales_data(date DESC);
CREATE INDEX idx_experiments_status ON experiments(status);

-- Create views for common queries
CREATE VIEW current_competitive_position AS
SELECT 
    p.id,
    p.sku,
    p.name,
    p.current_price,
    AVG(cp.price) as avg_competitor_price,
    MIN(cp.price) as min_competitor_price,
    MAX(cp.price) as max_competitor_price,
    COUNT(DISTINCT cp.competitor_id) as competitors_tracked,
    CASE 
        WHEN p.current_price < AVG(cp.price) * 0.95 THEN 'below_market'
        WHEN p.current_price > AVG(cp.price) * 1.05 THEN 'above_market'
        ELSE 'at_market'
    END as market_position
FROM products p
LEFT JOIN competitor_prices cp ON p.id = cp.product_id 
    AND cp.scraped_at > NOW() - INTERVAL '24 hours'
WHERE p.is_active = TRUE
GROUP BY p.id, p.sku, p.name, p.current_price;

-- Create view for price elasticity data
CREATE VIEW price_elasticity_data AS
SELECT 
    product_id,
    COUNT(DISTINCT price_point) as price_points_tested,
    MIN(price_point) as min_price_tested,
    MAX(price_point) as max_price_tested,
    AVG(units_sold) as avg_units_sold,
    STDDEV(units_sold) as stddev_units_sold,
    CORR(price_point, units_sold) as price_demand_correlation
FROM sales_data
WHERE date > NOW() - INTERVAL '90 days'
GROUP BY product_id
HAVING COUNT(DISTINCT price_point) >= 3;

-- Function to update product timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for products table
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to log price changes
CREATE OR REPLACE FUNCTION log_price_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.current_price != NEW.current_price THEN
        INSERT INTO price_changes (product_id, old_price, new_price, change_reason)
        VALUES (NEW.id, OLD.current_price, NEW.current_price, 'manual');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic price change logging
CREATE TRIGGER track_price_changes AFTER UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION log_price_change();