import os
import sys
import cv2
import pytesseract
from PIL import Image

# Configure Tesseract path (update this path based on your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows path
# For Linux/Mac: pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def preprocess_image(image_path):
    # Read the image
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding to handle varying lighting conditions
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # Perform morphological operations to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Apply additional image enhancement
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Return both processed versions for OCR to try
    return {
        'binary': 255 - opening,  # Inverted binary image
        'enhanced': enhanced       # Contrast enhanced image
    }

def test_ocr(image_path):
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' does not exist.")
        return
    
    print(f"Testing OCR on image: {image_path}")
    
    # Try with multiple preprocessing techniques
    try:
        processed_images = preprocess_image(image_path)
        
        # Try OCR with different preprocessing methods and configurations
        texts = []
        
        # Try with binary image
        binary_text = pytesseract.image_to_string(processed_images['binary'], lang='eng')
        texts.append(binary_text)
        print("\n--- OCR Result with Binary Preprocessing ---")
        print(binary_text)
        
        # Try with enhanced contrast image
        enhanced_text = pytesseract.image_to_string(processed_images['enhanced'], lang='eng')
        texts.append(enhanced_text)
        print("\n--- OCR Result with Enhanced Contrast ---")
        print(enhanced_text)
        
        # Try with original image
        original_text = pytesseract.image_to_string(Image.open(image_path), lang='eng')
        texts.append(original_text)
        print("\n--- OCR Result with Original Image ---")
        print(original_text)
        
        # Try with different PSM modes for better table structure recognition
        # PSM 6 - Assume a single uniform block of text
        psm6_text = pytesseract.image_to_string(
            processed_images['enhanced'], 
            lang='eng',
            config='--psm 6'
        )
        texts.append(psm6_text)
        
        # PSM 4 - Assume a single column of text of variable sizes
        psm4_text = pytesseract.image_to_string(
            processed_images['enhanced'], 
            lang='eng',
            config='--psm 4'
        )
        texts.append(psm4_text)
        
        # PSM 11 - Sparse text. Find as much text as possible in no particular order
        psm11_text = pytesseract.image_to_string(
            processed_images['enhanced'], 
            lang='eng',
            config='--psm 11'
        )
        texts.append(psm11_text)
        
        # PSM 3 - Fully automatic page segmentation, but no OSD (default)
        psm3_text = pytesseract.image_to_string(
            processed_images['enhanced'], 
            lang='eng',
            config='--psm 3'
        )
        texts.append(psm3_text)
        
    except Exception as e:
        print(f"Error with preprocessing: {str(e)}")
        texts = []
    
    # If we couldn't get any text, return
    if not texts:
        print("No text could be extracted from the image.")
        return
    
    # Look for SPI/CPI patterns
    import re
    
    # No need for separate decimal_numbers variables anymore as we handle this
    # within the processing of each text in the texts list
    
    # Enhanced patterns for Sarvajanik University marksheet format
    spi_patterns = [
        # Specific patterns for Sarvajanik University marksheet format
        r'SPI\s*[^\d\n]*\s*(\d+\.\d+)',  # SPI followed by any non-digit chars then a decimal
        r'SPI[:\s]*([0-9]\.[0-9]{1,2})',  # Standard format
        r'SPI\s*\n*\s*([0-9]\.[0-9]{1,2})',  # SPI on one line, value on next
        r'Semester\s+Performance[\s\S]*?SPI[\s\n]*([0-9]\.[0-9]{1,2})',  # In Semester Performance section
        r'Grade\s+[Pp]oints[\s\S]*?SPI[\s\n]*([0-9]\.[0-9]{1,2})',  # Near Grade Points
        r'SPI[\s\S]{1,200}?(\d+\.\d+)',  # SPI anywhere near a decimal number (expanded range)
        r'[Pp]oints\s+SPI\s+[^\d]*(\d+\.\d+)',  # Table format with Points SPI header
        r'SPI\s+[^\d]*(\d+\.\d+)',  # SPI followed by whitespace then a number
        # Additional patterns for table format in Sarvajanik marksheets
        r'Earned[\s\S]{1,50}?SPI[\s\S]{1,50}?(\d+\.\d+)',  # SPI in table with Earned nearby
        r'Grade[\s\S]{1,50}?points[\s\S]{1,50}?SPI[\s\S]{1,50}?(\d+\.\d+)',  # SPI in table with Grade points
        r'Semester\s+Performance[\s\S]{1,200}?(\d+\.\d+)'  # Any decimal in Semester Performance section
    ]
    
    cpi_patterns = [
        # Specific patterns for Sarvajanik University marksheet format
        r'CPI\s*[^\d\n]*\s*(\d+\.\d+)',  # CPI followed by any non-digit chars then a decimal
        r'CPI[:\s]*([0-9]\.[0-9]{1,2})',  # Standard format
        r'CPI\s*\n*\s*([0-9]\.[0-9]{1,2})',  # CPI on one line, value on next
        r'Cumulative\s+Performance[\s\S]*?CPI[\s\n]*([0-9]\.[0-9]{1,2})',  # In Cumulative Performance section
        r'Cumulative\s+Grade\s+Point\s+Average[\s\S]*?:?\s*([0-9]\.[0-9]{1,2})',  # After CGPA text
        r'CPI[\s\S]{1,200}?(\d+\.\d+)',  # CPI anywhere near a decimal number (expanded range)
        r'[Pp]oints\s+CPI\s+[^\d]*(\d+\.\d+)',  # Table format with Points CPI header
        r'CPI\s+[^\d]*(\d+\.\d+)',  # CPI followed by whitespace then a number
        # Additional patterns for table format in Sarvajanik marksheets
        r'Earned[\s\S]{1,50}?CPI[\s\S]{1,50}?(\d+\.\d+)',  # CPI in table with Earned nearby
        r'Grade[\s\S]{1,50}?points[\s\S]{1,50}?CPI[\s\S]{1,50}?(\d+\.\d+)',  # CPI in table with Grade points
        r'Cumulative\s+Performance[\s\S]{1,200}?(\d+\.\d+)'  # Any decimal in Cumulative Performance section
    ]
    
    # Process each text to find SPI/CPI values
    results = []
    
    for i, text in enumerate(texts):
        # Create a result object for this text
        result = {'spi': None, 'cpi': None, 'source': f"Text {i+1}"}
        
        # Check with multiple patterns
        spi_match = None
        for pattern in spi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                spi_match = match
                result['spi'] = match.group(1)
                break
        
        cpi_match = None
        for pattern in cpi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cpi_match = match
                result['cpi'] = match.group(1)
                break
        
        # If still not found, try additional methods
        if not result['spi']:
            # Look for lines containing both 'SPI' and a decimal number
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'SPI' in line.upper():
                    # Check current line
                    line_numbers = re.findall(r'(\d+\.\d+)', line)
                    if line_numbers:
                        result['spi'] = line_numbers[0]
                        break
                    # Check next line if exists
                    if i+1 < len(lines):
                        next_line = lines[i+1]
                        next_line_numbers = re.findall(r'(\d+\.\d+)', next_line)
                        if next_line_numbers:
                            result['spi'] = next_line_numbers[0]
                            break
            
            # Look for specific table structure in Sarvajanik marksheets
            if not result['spi']:
                # Try to find the Semester Performance section and extract values
                semester_perf_section = None
                for i, line in enumerate(lines):
                    if 'Semester Performance' in line:
                        semester_perf_section = i
                        break
                
                if semester_perf_section:
                    # Look at next 5-10 lines for decimal numbers
                    for i in range(semester_perf_section, min(semester_perf_section + 10, len(lines))):
                        line_numbers = re.findall(r'(\d+\.\d+)', lines[i])
                        if line_numbers:
                            # Take the first decimal number that looks like a GPA (between 0-10)
                            for num in line_numbers:
                                if 0 <= float(num) <= 10:
                                    result['spi'] = num
                                    break
                            if result['spi']:
                                break
            
            # If still not found, check if we have any decimal numbers in the text
            decimal_numbers = re.findall(r'(\d+\.\d+)', text)
            if not result['spi'] and decimal_numbers:
                # Look for numbers that could be SPI (typically between 7-9.5 for GPA systems)
                for num in decimal_numbers:
                    if 7 <= float(num) <= 9.5:  # More specific range for typical GPAs
                        result['spi'] = num
                        break
        
        # Similar approach for CPI
        if not result['cpi']:
            # Look for lines containing both 'CPI' and a decimal number
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'CPI' in line.upper():
                    # Check current line
                    line_numbers = re.findall(r'(\d+\.\d+)', line)
                    if line_numbers:
                        result['cpi'] = line_numbers[0]
                        break
                    # Check next line if exists
                    if i+1 < len(lines):
                        next_line = lines[i+1]
                        next_line_numbers = re.findall(r'(\d+\.\d+)', next_line)
                        if next_line_numbers:
                            result['cpi'] = next_line_numbers[0]
                            break
            
            # Look for specific table structure in Sarvajanik marksheets
            if not result['cpi']:
                # Try to find the Cumulative Performance section and extract values
                cumulative_perf_section = None
                for i, line in enumerate(lines):
                    if 'Cumulative Performance' in line:
                        cumulative_perf_section = i
                        break
                
                if cumulative_perf_section:
                    # Look at next 5-10 lines for decimal numbers
                    for i in range(cumulative_perf_section, min(cumulative_perf_section + 10, len(lines))):
                        line_numbers = re.findall(r'(\d+\.\d+)', lines[i])
                        if line_numbers:
                            # Take the first decimal number that looks like a GPA (between 0-10)
                            for num in line_numbers:
                                if 0 <= float(num) <= 10 and num != result['spi']:  # Avoid using the same number as SPI
                                    result['cpi'] = num
                                    break
                            if result['cpi']:
                                break
            
            # If still not found and we have decimal numbers
            decimal_numbers = re.findall(r'(\d+\.\d+)', text)
            if not result['cpi'] and decimal_numbers:
                # Look for numbers that could be CPI (typically between 7-9.5 for GPA systems)
                for num in decimal_numbers:
                    if 7 <= float(num) <= 9.5 and num != result['spi']:  # More specific range for typical GPAs
                        result['cpi'] = num
                        break
        
        # Add this result to our results list
        results.append(result)
    
    # Combine results to get the best match
    final_result = {'spi': None, 'cpi': None}
    
    # First, try to find values from any of the results
    for result in results:
        if result['spi'] and not final_result['spi']:
            final_result['spi'] = result['spi']
        if result['cpi'] and not final_result['cpi']:
            final_result['cpi'] = result['cpi']
    
    # Print detailed results for each text processing method
    print("\n--- Detailed Extraction Results ---")
    for i, result in enumerate(results):
        print(f"Method {i+1}:")
        print(f"  SPI: {result['spi'] if result['spi'] else 'Not found'}")
        print(f"  CPI: {result['cpi'] if result['cpi'] else 'Not found'}")
    
    # Print final combined results
    print("\n--- Final Extracted Values ---")
    print(f"SPI: {final_result['spi'] if final_result['spi'] else 'Not found'}")
    print(f"CPI: {final_result['cpi'] if final_result['cpi'] else 'Not found'}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_ocr.py <path_to_image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_ocr(image_path)