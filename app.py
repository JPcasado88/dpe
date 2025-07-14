#!/usr/bin/env python3
"""
Railway entry point - imports the backend app
"""
import sys
import os

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

# Import the app
from main import app

# This allows Railway to find the app
__all__ = ['app']