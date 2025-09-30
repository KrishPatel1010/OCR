#!/bin/bash

echo "==================================================="
echo "Quick Test for OCR Application"
echo "==================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please ensure you have venv module installed."
        exit 1
    fi
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Please check your internet connection and try again."
    exit 1
fi

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract OCR is not installed."
    echo "Please install Tesseract OCR:"
    echo "  - For Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "  - For macOS: brew install tesseract"
    echo "And update the path in app.py if necessary."
    echo ""
    read -p "Press Enter to continue anyway..."
fi

# Update Tesseract path in app.py for Linux/Mac
sed -i.bak 's|pytesseract.pytesseract.tesseract_cmd = r.*|# pytesseract.pytesseract.tesseract_cmd = r\'C:\\Program Files\\Tesseract-OCR\\tesseract.exe\'  # Windows path\npytesseract.pytesseract.tesseract_cmd = r\'/usr/bin/tesseract\'|' app.py

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Generate a sample marksheet
echo "Generating a sample marksheet..."
python generate_sample_marksheet.py --name "Test Student" --roll "B123456" --semester "4" --spi "8.75" --cpi "8.50" --output "test_marksheet.jpg"

# Test OCR on the generated marksheet
echo ""
echo "Testing OCR on the generated marksheet..."
python test_ocr.py uploads/test_marksheet.jpg

echo ""
echo "==================================================="
echo "Test completed!"
echo "==================================================="
echo ""
echo "If you want to run the full application, use run_app.sh"
echo ""

# Deactivate virtual environment
deactivate

read -p "Press Enter to exit..."