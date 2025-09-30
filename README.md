# College TnP Portal OCR Application

This application is designed for college Training and Placement (TnP) portals to automatically extract SPI (Semester Performance Index) and CPI (Cumulative Performance Index) from student marksheets using Optical Character Recognition (OCR) technology.

## Features

- Upload marksheets in various formats (JPG, JPEG, PNG, PDF)
- Automatic extraction of SPI and CPI values
- User-friendly web interface
- API endpoint for integration with other systems
- Image preprocessing for improved OCR accuracy

## Prerequisites

- Python 3.7 or higher
- Tesseract OCR engine

## Installation

### 1. Install Tesseract OCR

#### Windows
1. Download and install Tesseract from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. Add Tesseract to your PATH or update the path in `app.py`

#### macOS
```
brew install tesseract
```

#### Linux (Ubuntu/Debian)
```
sudo apt update
sudo apt install tesseract-ocr
```

### 2. Clone or download this repository

### 3. Install Python dependencies

```
pip install -r requirements.txt
```

### 4. Configure the application

Update the Tesseract path in `app.py` if necessary:

```python
# For Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# For Linux/Mac
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
```

## Usage

### Running the application

```
python app.py
```

Open your web browser and navigate to `http://127.0.0.1:5000`

### Using the web interface

1. Upload a marksheet image or PDF
2. The system will process the document and extract SPI/CPI values
3. View the results on the results page

### Using the API

You can also use the API endpoint for integration with other systems:

```
POST /api/extract
```

Parameters:
- `marksheet`: The marksheet file (multipart/form-data)

Response (JSON):
```json
{
  "spi": "9.2",
  "cpi": "8.7",
  "raw_text": "...extracted text..."
}
```

## Customization

### Adjusting the OCR pattern matching

If your marksheet has a different format, you may need to adjust the regular expressions in the `extract_spi_from_text` function in `app.py`:

```python
def extract_spi_from_text(text):
    # Pattern to match SPI/CPI values (adjust based on your marksheet format)
    spi_pattern = r'SPI[:\s]*([0-9]\.[0-9]{1,2})'
    cpi_pattern = r'CPI[:\s]*([0-9]\.[0-9]{1,2})'
    
    # Add more patterns as needed
    # ...
```

### Improving OCR accuracy

You can adjust the image preprocessing steps in the `preprocess_image` function to improve OCR accuracy for your specific marksheet format.

## Troubleshooting

### OCR not detecting values correctly

1. Ensure the marksheet image is clear and high-resolution
2. Check if the SPI/CPI format in your marksheet matches the pattern in the code
3. Try adjusting the preprocessing parameters
4. View the raw extracted text (available in the results page) to debug

### Installation issues

1. Verify Tesseract OCR is installed correctly
2. Check the Tesseract path in the application configuration
3. Ensure all dependencies are installed

## License

This project is licensed under the MIT License - see the LICENSE file for details.