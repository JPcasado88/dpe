#!/usr/bin/env python3
"""
Initialize database schema for Railway deployment
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def init_database():
    """Initialize database schema"""
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Parse database URL
    try:
        # Handle Railway's postgres:// URL format
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        print(f"Connecting to database...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        print("Creating database schema...")
        cursor.execute(schema_sql)
        
        print("Database initialized successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"ERROR: Failed to initialize database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()