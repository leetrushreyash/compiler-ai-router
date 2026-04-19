@echo off
cd /d "%~dp0"
echo Starting the AST Analyzer Web Backend...
echo The GUI should open automatically in your browser...

:: Open the default web browser to the local server
start http://127.0.0.1:5000

:: Start the Flask Python server
python app.py

:: If it crashes, pause so you can read the error message
if %errorlevel% neq 0 (
    echo.
    echo Server closed or crashed.
    pause
)
