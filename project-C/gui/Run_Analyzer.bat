@echo off
cd /d "%~dp0"
echo Starting AST Analyzer...
python analyzer_gui.py
if %errorlevel% neq 0 (
    echo.
    echo An error occurred while opening the application.
    pause
)
