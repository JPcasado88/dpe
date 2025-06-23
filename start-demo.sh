#!/bin/bash
# Start script for Railway demo deployment

echo "Starting Dynamic Pricing Engine Demo..."

# Install minimal dependencies
cd backend
pip install -r requirements-demo.txt

# Start the demo server
python demo_server.py