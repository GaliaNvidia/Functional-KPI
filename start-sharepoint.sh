#!/bin/bash

echo "🚀 Starting SharePoint MCP Backend..."
echo ""
echo "This will start two servers:"
echo "  1. SharePoint Backend (port 3000)"
echo "  2. Dashboard Server (port 8000)"
echo ""

# Start SharePoint backend in background
python3 sharepoint_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start dashboard server
echo "🌐 Starting dashboard server..."
python3 -m http.server 8000 &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers are running!"
echo ""
echo "📊 Dashboard: http://localhost:8000/kpi-dashboard.html"
echo "🔧 Backend:   http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '👋 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '✅ Servers stopped'; exit 0" INT

# Keep script running
wait

