@echo off
echo Starting College TnP Portal OCR Application...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.7 or higher.
    pause
    exit /b
)

:: Check if virtual environment exists, if not create one
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please ensure you have venv module installed.
        pause
        exit /b
    )
)

:: Activate virtual environment and install dependencies
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Please check your internet connection and try again.
    pause
    exit /b
)

:: Check if Tesseract is installed
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Tesseract OCR might not be installed or not in PATH.
    echo Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
    echo And update the path in app.py if necessary.
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

:: Create uploads directory if it doesn't exist
if not exist uploads mkdir uploads

:: Run the application
echo Starting Flask application...
python app.py

:: Deactivate virtual environment when done
call venv\Scripts\deactivate.bat

pause