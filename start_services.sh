#!/bin/bash
# Start all AI Curriculum Builder services

echo "Starting AI Curriculum Builder services..."
echo ""

# Start backend
echo "Starting backend..."
cd /home/ubuntu/Dev/ai_curriculam/backend
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5

# Start frontend
echo "Starting frontend..."
cd /home/ubuntu/Dev/ai_curriculam/frontend
nohup npm run start > /tmp/frontend.log 2>&1 &
sleep 8

echo ""
echo "Status:"
curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "✓ Backend: running on port 8000" || echo "✗ Backend: failed to start"
curl -s http://localhost:3000 > /dev/null 2>&1 && echo "✓ Frontend: running on port 3000" || echo "✗ Frontend: failed to start"

echo ""
echo "Access URLs:"
echo "  Frontend: http://3.150.159.160:3000"
echo "  Backend:  http://3.150.159.160:8000"
echo ""
echo "Logs:"
echo "  Backend:  /tmp/backend.log"
echo "  Frontend: /tmp/frontend.log"

