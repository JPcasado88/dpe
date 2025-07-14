#!/bin/bash

echo "Starting Dynamic Pricing Engine (Local Development)"
echo "=================================================="

# Navigate to the project directory
cd "$(dirname "$0")"

# Start backend
echo ""
echo "Starting backend server..."
cd backend
python3 demo_server.py &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"
echo "Backend URL: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"

# Wait a moment for backend to start
sleep 3

# Start frontend
echo ""
echo "Starting frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Frontend started with PID: $FRONTEND_PID"
echo "Frontend URL: http://localhost:3000"

echo ""
echo "=================================================="
echo "Both services are starting..."
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user to press Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait