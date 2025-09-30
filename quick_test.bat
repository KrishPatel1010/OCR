@echo off
echo ===================================================
echo Quick Test for OCR Application
echo ===================================================
echo.

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

:: Create uploads directory if it doesn't exist
if not exist uploads mkdir uploads

:: Generate a sample marksheet
echo Generating a sample marksheet...
python generate_sample_marksheet.py --name "Test Student" --roll "B123456" --semester "4" --spi "8.75" --cpi "8.50" --output "test_marksheet.jpg"

:: Test OCR on the generated marksheet
echo.
echo Testing OCR on the generated marksheet...
python test_ocr.py uploads\test_marksheet.jpg

echo.
echo ===================================================
echo Test completed!
echo ===================================================
echo.
echo If you want to run the full application, use run_app.bat
echo.

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat

pause