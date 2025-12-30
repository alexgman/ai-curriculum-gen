#!/bin/bash
# AI Curriculum Builder - Start Script
# Properly manages ports and starts both services

set -e

echo "🛑 Stopping any existing services..."

# Kill processes by port (most reliable)
for port in 3000 3001 3002 3003 8000; do
    pid=$(lsof -ti:$port 2>/dev/null) || true
    if [ -n "$pid" ]; then
        echo "  Killing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
    fi
done

# Also kill by process name
pkill -9 -f "next-server" 2>/dev/null || true
pkill -9 -f "npm run dev" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "python -m app.main" 2>/dev/null || true

sleep 2

# Verify ports are free
echo "✅ Checking ports..."
for port in 3000 8000; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "❌ Port $port still in use!"
        exit 1
    else
        echo "  Port $port is free"
    fi
done

echo ""
echo "🚀 Starting Backend (port 8000)..."
cd /home/ubuntu/Dev/ai-curriculum-gen/backend
source ~/anaconda3/etc/profile.d/conda.sh
conda activate curriculum
python -m app.main &
BACKEND_PID=$!

# Wait for backend to start
sleep 3
if ! lsof -ti:8000 >/dev/null 2>&1; then
    echo "❌ Backend failed to start!"
    exit 1
fi
echo "✅ Backend running on http://localhost:8000"

echo ""
echo "🚀 Starting Frontend (port 3000)..."
cd /home/ubuntu/Dev/ai-curriculum-gen/frontend
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5
if lsof -ti:3000 >/dev/null 2>&1; then
    echo "✅ Frontend running on http://localhost:3000"
else
    echo "⚠️  Frontend might be on a different port, check output above"
fi

echo ""
echo "=========================================="
echo "🎉 AI Curriculum Builder is running!"
echo ""
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "=========================================="

# Wait for processes
wait


