#!/bin/bash
# Stop all AI Curriculum Builder services

echo "Stopping AI Curriculum Builder services..."
echo ""

# Stop backend (uvicorn)
if pgrep -f "uvicorn" > /dev/null 2>&1; then
    pkill -f "uvicorn"
    echo "✓ Backend (uvicorn) stopped"
else
    echo "- Backend was not running"
fi

# Stop frontend (next.js)
if pgrep -f "next" > /dev/null 2>&1; then
    pkill -f "next"
    echo "✓ Frontend (next) stopped"
else
    echo "- Frontend was not running"
fi

# Also kill any node processes on port 3000
if lsof -ti:3000 > /dev/null 2>&1; then
    kill $(lsof -ti:3000) 2>/dev/null
    echo "✓ Port 3000 cleared"
fi

# Kill any python processes on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    kill $(lsof -ti:8000) 2>/dev/null
    echo "✓ Port 8000 cleared"
fi

sleep 1

echo ""
echo "Status:"
curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "⚠ Backend still running" || echo "✓ Backend: stopped"
curl -s http://localhost:3000 > /dev/null 2>&1 && echo "⚠ Frontend still running" || echo "✓ Frontend: stopped"
echo ""
echo "Done."

