#!/bin/bash

echo "========================================"
echo " MediGuardian - Flask + React Startup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python from https://python.org"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

echo "[1/4] Starting Backend (Flask API)..."
cd backend
python3 api.py &
BACKEND_PID=$!
cd ..

echo "[2/4] Waiting 5 seconds for backend to start..."
sleep 5

echo "[3/4] Starting Frontend (React)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "[4/4] Done!"
echo ""
echo "========================================"
echo " MediGuardian is running!"
echo "========================================"
echo ""
echo "Backend API:  http://localhost:5000"
echo "Frontend App: http://localhost:3000"
echo ""
echo "Backend PID:  $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop the servers, run:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or press Ctrl+C to stop both servers"
echo ""

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
