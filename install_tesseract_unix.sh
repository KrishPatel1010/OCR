#!/bin/bash

echo "==================================================="
echo "Tesseract OCR Installation Helper for Linux/Mac"
echo "==================================================="
echo ""

echo "This script will help you install Tesseract OCR on your system."
echo ""

# Detect operating system
if [[ "$(uname)" == "Darwin" ]]; then
    # macOS
    echo "Detected macOS system"
    echo ""
    
    echo "Step 1: Check if Homebrew is installed"
    echo "---------------------------------------"
    if ! command -v brew &> /dev/null; then
        echo "Homebrew is not installed. Installing Homebrew..."
        echo "This may require your password."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        if ! command -v brew &> /dev/null; then
            echo "Failed to install Homebrew. Please install it manually from:"
            echo "https://brew.sh/"
            exit 1
        fi
    else
        echo "Homebrew is already installed."
    fi
    
    echo ""
    echo "Step 2: Install Tesseract OCR"
    echo "---------------------------------------"
    echo "Installing Tesseract OCR using Homebrew..."
    brew install tesseract
    
    # Check if installation was successful
    if ! command -v tesseract &> /dev/null; then
        echo "Failed to install Tesseract. Please try installing it manually:"
        echo "brew install tesseract"
        exit 1
    fi
    
    echo ""
    echo "Tesseract OCR has been successfully installed!"
    tesseract --version
    
    echo ""
    echo "The Tesseract path on your system is likely:"
    which tesseract
    echo ""
    echo "You may need to update the path in app.py:"
    echo "pytesseract.pytesseract.tesseract_cmd = r'$(which tesseract)'"
    
else
    # Linux
    echo "Detected Linux system"
    echo ""
    
    # Check for common package managers
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "Step 1: Update package lists"
        echo "---------------------------------------"
        echo "This may require your password."
        sudo apt-get update
        
        echo ""
        echo "Step 2: Install Tesseract OCR"
        echo "---------------------------------------"
        echo "Installing Tesseract OCR..."
        sudo apt-get install -y tesseract-ocr
        
    elif command -v dnf &> /dev/null; then
        # Fedora
        echo "Step 1: Install Tesseract OCR"
        echo "---------------------------------------"
        echo "This may require your password."
        sudo dnf install -y tesseract
        
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        echo "Step 1: Install Tesseract OCR"
        echo "---------------------------------------"
        echo "This may require your password."
        sudo yum install -y tesseract
        
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        echo "Step 1: Install Tesseract OCR"
        echo "---------------------------------------"
        echo "This may require your password."
        sudo pacman -S --noconfirm tesseract
        
    else
        echo "Could not detect your package manager."
        echo "Please install Tesseract OCR manually for your distribution."
        exit 1
    fi
    
    # Check if installation was successful
    if ! command -v tesseract &> /dev/null; then
        echo "Failed to install Tesseract. Please try installing it manually."
        exit 1
    fi
    
    echo ""
    echo "Tesseract OCR has been successfully installed!"
    tesseract --version
    
    echo ""
    echo "The Tesseract path on your system is likely:"
    which tesseract
    echo ""
    echo "You may need to update the path in app.py:"
    echo "pytesseract.pytesseract.tesseract_cmd = r'$(which tesseract)'"
    
fi

echo ""
echo "Installation complete! You're all set to use the OCR application."