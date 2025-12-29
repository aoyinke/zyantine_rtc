#!/bin/bash

echo "Starting AI RTC System..."

echo "Step 1: Starting signaling server..."
python3 signaling_server.py &
SIGNALING_PID=$!
echo "Signaling server started with PID: $SIGNALING_PID"

sleep 2

echo "Step 2: Starting AI RTC client..."
python3 ai_rtc_system.py &
AI_CLIENT_PID=$!
echo "AI RTC client started with PID: $AI_CLIENT_PID"

echo ""
echo "System is running!"
echo "Press Ctrl+C to stop all services"

cleanup() {
    echo ""
    echo "Stopping services..."
    kill $AI_CLIENT_PID 2>/dev/null
    kill $SIGNALING_PID 2>/dev/null
    echo "All services stopped"
    exit 0
}

trap cleanup SIGINT

wait
