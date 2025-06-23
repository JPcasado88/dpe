#!/bin/bash
# Start script for Railway demo deployment

echo "Starting Dynamic Pricing Engine Demo..."
echo "Port: ${PORT:-8000}"

# Install minimal dependencies
cd backend
pip install -r requirements-demo.txt

# Start the demo server with Railway's PORT
exec python demo_server.py