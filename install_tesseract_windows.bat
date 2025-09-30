@echo off
echo ===================================================
echo Tesseract OCR Installation Helper for Windows
echo ===================================================
echo.

echo This script will help you install Tesseract OCR on Windows.
echo.

echo Step 1: Download Tesseract OCR installer
echo ---------------------------------------
echo Please download the Tesseract OCR installer from:
echo https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo Choose the appropriate version for your system (32-bit or 64-bit).
echo.
echo Press any key when you have downloaded the installer...
pause > nul

echo.
echo Step 2: Install Tesseract OCR
echo ---------------------------------------
echo Please run the installer you downloaded.
echo.
echo Important installation notes:
echo 1. Install to the default location (C:\Program Files\Tesseract-OCR)
echo 2. Make sure to check "Add to PATH" during installation
echo.
echo Press any key when you have completed the installation...
pause > nul

echo.
echo Step 3: Verify installation
echo ---------------------------------------
echo Checking if Tesseract is installed correctly...

where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Tesseract was not found in your PATH.
    echo.
    echo Please make sure you:
    echo 1. Installed Tesseract to the default location
    echo 2. Checked "Add to PATH" during installation
    echo.
    echo If you didn't check "Add to PATH", you can:
    echo 1. Reinstall Tesseract and check the option, or
    echo 2. Manually add C:\Program Files\Tesseract-OCR to your PATH
    echo.
    echo Alternatively, you can update the Tesseract path in app.py:
    echo pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    echo.
) else (
    echo.
    echo Tesseract OCR is installed correctly!
    echo.
    tesseract --version
    echo.
    echo You're all set to use the OCR application.
)

echo Press any key to exit...
pause > nul