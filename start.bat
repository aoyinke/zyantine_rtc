@echo off
echo Starting AI RTC System...

echo Step 1: Starting signaling server...
start /B python signaling_server.py
timeout /t 2 /nobreak > nul

echo Step 2: Starting AI RTC client...
python ai_rtc_system.py

echo.
echo System stopped
