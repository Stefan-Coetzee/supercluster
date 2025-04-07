#!/bin/bash
# Script to start both the frontend and backend

# Exit on error
set -e

echo "🚀 Starting the Supercluster Application..."

# Start the backend
echo "📡 Starting the backend API server..."
cd backend
./start_server.sh &
BACKEND_PID=$!
cd ..

echo "⏳ Waiting for backend to initialize..."
sleep 3

# Start the frontend
echo "🌐 Starting the frontend React application..."
cd frontend

# Check if node_modules exists, if not, install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies (this may take a minute)..."
    npm install
fi

npm start &
FRONTEND_PID=$!

# Trap to kill both processes on exit
function cleanup {
  echo "🛑 Stopping services..."
  kill $FRONTEND_PID $BACKEND_PID 2>/dev/null || true
  echo "✅ Services stopped"
}

trap cleanup EXIT

# Wait for user to press Ctrl+C
echo "✅ Both services started!"
echo "📊 Backend running at: http://localhost:8000"
echo "🖥️ Frontend running at: http://localhost:3000"
echo "Press Ctrl+C to stop both services"
wait 