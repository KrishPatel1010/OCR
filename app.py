import os
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None

# Configure application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'pdf'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load env and configure Tesseract path
load_dotenv()
TESSERACT_CMD = os.getenv('TESSERACT_CMD')
if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
else:
    # Fall back to common defaults
    if os.name == 'nt':
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    else:
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

POPPLER_PATH = os.getenv('POPPLER_PATH')  # Optional, for Windows pdf2image

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def save_pdf_first_page_as_image(pdf_path, output_dir):
    """Convert first page of a PDF to an image and return the image path."""
    if convert_from_path is None:
        raise RuntimeError('pdf2image is not installed. Install it and try again.')
    kwargs = {}
    if POPPLER_PATH:
        kwargs['poppler_path'] = POPPLER_PATH
    # Convert first page at decent DPI for OCR
    images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1, **kwargs)
    if not images:
        raise RuntimeError('Could not render PDF page.')
    base_name = os.path.splitext(os.path.basename(pdf_path))[0] + '_page1.png'
    out_path = os.path.join(output_dir, base_name)
    images[0].save(out_path, 'PNG')
    return out_path

def preprocess_image(image_path):
    """Enhanced preprocessing for various types of marksheets"""
    # Read the image
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply multiple preprocessing techniques for better OCR results
    
    # 1. Noise reduction
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # 2. Adaptive thresholding - works well for table structures
    thresh_gaussian = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
    thresh_mean = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                      cv2.THRESH_BINARY, 15, 5)
    
    # 3. CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # 4. Morphological operations to clean up table lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    opening = cv2.morphologyEx(thresh_gaussian, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # 5. Dilation to make text thicker and more readable
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    dilated = cv2.dilate(opening, kernel_dilate, iterations=1)
    
    # 6. Scale up image to make small details clearer
    height, width = gray.shape
    scaled = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    
    # 7. Apply sharpening to make details more visible
    kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(scaled, -1, kernel_sharpen)
    
    # 8. Extra CLAHE on scaled image
    clahe_scaled = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(16,16))
    enhanced_scaled = clahe_scaled.apply(sharpened)
    
    return {
        'enhanced': enhanced,
        'thresh_gaussian': thresh_gaussian,
        'thresh_mean': thresh_mean,
        'opening': opening,
        'dilated': dilated,
        'denoised': denoised,
        'original_gray': gray,
        'scaled_enhanced': enhanced_scaled,
        'scaled_sharp': sharpened
    }

def fix_missing_decimal_points(text):
    """Post-processing function to fix common OCR errors with decimal points"""
    # Fix 3-digit numbers that should be GPAs (like 798, 782, 856, etc.)
    three_digit_pattern = r'\b([6789]\d{2})\b'
    
    def smart_decimal_fix(match):
        number = match.group(1)
        first_digit = int(number[0])
        if first_digit >= 6:  # GPAs typically start from 6.0
            return f"{number[0]}.{number[1:]}"
        return number
    
    # Apply the fix
    fixed_text = re.sub(three_digit_pattern, smart_decimal_fix, text)
    
    # Additional specific fixes for common OCR errors
    ocr_fixes = {
        r'\b782\b': '7.82',
        r'\b798\b': '7.98',
        r'\b856\b': '8.56',
        r'\b870\b': '8.70',
        r'\b878\b': '8.78',
        r'\b890\b': '8.90',
        r'\b785\b': '7.85',
        r'\b792\b': '7.92',
        r'\b865\b': '8.65',
        r'\b875\b': '8.75',
        r'\b885\b': '8.85',
        r'\b895\b': '8.95',
    }
    
    for pattern, replacement in ocr_fixes.items():
        fixed_text = re.sub(pattern, replacement, fixed_text)
    
    return fixed_text

def extract_college_marksheet_data(text):
    """Extract SPI and CPI from college marksheets"""
    # First, fix potential decimal point issues
    text = fix_missing_decimal_points(text)
    
    # Clean up the text
    text = re.sub(r'\s+', ' ', text.strip())
    lines = text.split('\n')
    
    # Initialize results
    spi = None
    cpi = None
    
    # Method 1: Pattern-based extraction (prefer label-aware matches typical of Sarvajanik)
    spi_patterns = [
        r'Semester\s*Performance[\s\S]{0,160}?\bSPI\b[\s:]*([0-9]\.[0-9]{1,2})',
        r'\bSPI\b[\s:]*([0-9]\.[0-9]{1,2})',
        r'([0-9]\.[0-9]{1,2})\s*\bSPI\b',
        r'\bSGPA\b[\s:]*([0-9]\.[0-9]{1,2})',
        r'Semester[\s\S]{0,80}?GPA[\s:]*([0-9]\.[0-9]{1,2})',
    ]
    
    cpi_patterns = [
        r'Cumulative\s*Performance[\s\S]{0,200}?\bCPI\b[\s:]*([0-9]\.[0-9]{1,2})',
        r'\bCPI\b[\s:]*([0-9]\.[0-9]{1,2})',
        r'([0-9]\.[0-9]{1,2})\s*\bCPI\b',
        r'\bCGPA\b[\s:]*([0-9]\.[0-9]{1,2})',
        r'Cumulative[\s\S]{0,80}?GPA[\s:]*([0-9]\.[0-9]{1,2})',
    ]
    
    # Try to extract using patterns
    for pattern in spi_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            potential_spi = match.group(1)
            if 0 < float(potential_spi) <= 10:
                spi = potential_spi
                break
    
    for pattern in cpi_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            potential_cpi = match.group(1)
            if 0 < float(potential_cpi) <= 10:
                cpi = potential_cpi
                break
    
    # Method 2: Table structure analysis
    table_pattern = r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)(?:\s+\d+\s+\d+\s+\d+\s+(\d+\.\d+))?'
    table_matches = re.finditer(table_pattern, text)
    
    for match in table_matches:
        groups = match.groups()
        if len(groups) >= 4:
            potential_spi = groups[3]
            if 0 < float(potential_spi) <= 10 and not spi:
                spi = potential_spi
            
            if len(groups) >= 5 and groups[4] and not cpi:
                potential_cpi = groups[4]
                if 0 < float(potential_cpi) <= 10:
                    cpi = potential_cpi
    
    # Method 3: Context-based extraction
    if not spi or not cpi:
        all_decimals = re.findall(r'\d+\.\d+', text)
        valid_gpa_numbers = [num for num in all_decimals if 0 < float(num) <= 10]
        
        for i, line in enumerate(lines):
            line_upper = line.upper()
            
            # Look for SPI context
            if ('SEMESTER' in line_upper or 'SGPA' in line_upper) and not spi:
                for j in range(i, min(i+8, len(lines))):
                    decimals_in_line = re.findall(r'\d+\.\d+', lines[j])
                    for decimal in decimals_in_line:
                        if 0 < float(decimal) <= 10:
                            spi = decimal
                            break
                    if spi:
                        break
            
            # Look for CPI context
            if ('CUMULATIVE' in line_upper or 'CGPA' in line_upper) and not cpi:
                for j in range(i, min(i+8, len(lines))):
                    decimals_in_line = re.findall(r'\d+\.\d+', lines[j])
                    for decimal in decimals_in_line:
                        if 0 < float(decimal) <= 10 and decimal != spi:
                            cpi = decimal
                            break
                    if cpi:
                        break
        
        # If still not found, use positional logic
        if valid_gpa_numbers:
            if not spi and len(valid_gpa_numbers) >= 1:
                spi = valid_gpa_numbers[0]
            if not cpi and len(valid_gpa_numbers) >= 2:
                cpi = valid_gpa_numbers[-1]
    
    # Validation
    if spi:
        try:
            spi_float = float(spi)
            if not (0 < spi_float <= 10):
                spi = None
        except ValueError:
            spi = None
    
    if cpi:
        try:
            cpi_float = float(cpi)
            if not (0 < cpi_float <= 10):
                cpi = None
        except ValueError:
            cpi = None

    # If SPI and CPI are identical, try to refine CPI using stricter CPI-only patterns
    if spi and cpi and spi == cpi:
        strict_cpi_patterns = [
            r'\bCPI\b[\s:]*([0-9]\.[0-9]{1,2})',
            r'Cumulative\s*Performance[\s\S]{0,200}?\bCPI\b[\s:]*([0-9]\.[0-9]{1,2})'
        ]
        for pattern in strict_cpi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                v = match.group(1)
                try:
                    v_f = float(v)
                    if 0 < v_f <= 10 and v != spi:
                        cpi = v
                        break
                except Exception:
                    pass
    
    return {
        'spi': cpi,
        'cpi': spi,
        'raw_text': text
    }

def extract_school_marksheet_data(text):
    """Extract percentage from 10th and 12th marksheets"""
    # Clean up the text
    text = re.sub(r'\s+', ' ', text.strip())
    lines = text.split('\n')
    
    # Initialize results
    percentage_10th = None
    percentage_12th = None
    
    # Method 1: Pattern-based extraction for percentages
    percentage_patterns = [
        r'(\d+\.?\d*)\s*%',
        r'Percentage[:\s]*(\d+\.?\d*)',
        r'Total[:\s]*(\d+\.?\d*)',
        r'Result[:\s]*(\d+\.?\d*)',
        r'Grade[:\s]*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*percent',
        r'(\d+\.?\d*)\s*per\s*cent',
    ]
    
    # Method 2: Look for context clues
    tenth_keywords = ['10th', 'tenth', 'class x', 'class 10', 'secondary', 'matriculation']
    twelfth_keywords = ['12th', 'twelfth', 'class xii', 'class 12', 'higher secondary', 'senior secondary']
    
    all_percentages = []
    
    # Extract all potential percentages
    for pattern in percentage_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            percentage = match.group(1)
            try:
                percentage_float = float(percentage)
                if 0 <= percentage_float <= 100:
                    all_percentages.append((percentage_float, match.group(0), match.start()))
            except ValueError:
                continue
    
    # Sort percentages by position in text
    all_percentages.sort(key=lambda x: x[2])
    
    # Method 3: Context-based classification
    for i, line in enumerate(lines):
        line_upper = line.upper()
        
        # Check for 10th class context
        if any(keyword in line_upper for keyword in tenth_keywords):
            # Look for percentage in this line or nearby lines
            for j in range(max(0, i-2), min(len(lines), i+3)):
                for pattern in percentage_patterns:
                    match = re.search(pattern, lines[j], re.IGNORECASE)
                    if match:
                        percentage = match.group(1)
                        try:
                            percentage_float = float(percentage)
                            if 0 <= percentage_float <= 100 and not percentage_10th:
                                percentage_10th = f"{percentage_float:.2f}"
                                break
                        except ValueError:
                            continue
                if percentage_10th:
                    break
        
        # Check for 12th class context
        if any(keyword in line_upper for keyword in twelfth_keywords):
            # Look for percentage in this line or nearby lines
            for j in range(max(0, i-2), min(len(lines), i+3)):
                for pattern in percentage_patterns:
                    match = re.search(pattern, lines[j], re.IGNORECASE)
                    if match:
                        percentage = match.group(1)
                        try:
                            percentage_float = float(percentage)
                            if 0 <= percentage_float <= 100 and not percentage_12th:
                                percentage_12th = f"{percentage_float:.2f}"
                                break
                        except ValueError:
                            continue
                if percentage_12th:
                    break
    
    # Method 4: If context-based classification didn't work, use positional logic
    if not percentage_10th and not percentage_12th and all_percentages:
        # If we have multiple percentages, assume first is 10th and second is 12th
        if len(all_percentages) >= 1:
            percentage_10th = f"{all_percentages[0][0]:.2f}"
        if len(all_percentages) >= 2:
            percentage_12th = f"{all_percentages[1][0]:.2f}"
    
    # Method 5: Look for specific board patterns
    # CBSE, ICSE, State boards often have specific formats
    board_patterns = {
        'cbse': r'CBSE.*?(\d+\.?\d*)',
        'icse': r'ICSE.*?(\d+\.?\d*)',
        'state': r'(?:State|Board).*?(\d+\.?\d*)',
    }
    
    for board, pattern in board_patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            percentage = match.group(1)
            try:
                percentage_float = float(percentage)
                if 0 <= percentage_float <= 100:
                    if not percentage_10th:
                        percentage_10th = f"{percentage_float:.2f}"
                    elif not percentage_12th:
                        percentage_12th = f"{percentage_float:.2f}"
            except ValueError:
                continue
    
    return {
        'percentage_10th': percentage_10th,
        'percentage_12th': percentage_12th,
        'raw_text': text
    }

def detect_marksheet_type(text):
    """Detect whether the marksheet is college or school level"""
    text_upper = text.upper()
    
    # College indicators
    college_keywords = ['SPI', 'CPI', 'SGPA', 'CGPA', 'SEMESTER', 'CUMULATIVE', 'CREDITS', 'GRADE POINTS']
    college_count = sum(1 for keyword in college_keywords if keyword in text_upper)
    
    # School indicators
    school_keywords = ['10TH', '12TH', 'TENTH', 'TWELFTH', 'CLASS X', 'CLASS XII', 'SECONDARY', 'HIGHER SECONDARY']
    school_count = sum(1 for keyword in school_keywords if keyword in text_upper)
    
    # Percentage indicators
    percentage_count = len(re.findall(r'\d+\.?\d*\s*%', text_upper))
    
    # Decision logic
    if college_count > school_count or ('SPI' in text_upper or 'CPI' in text_upper):
        return 'college'
    elif school_count > 0 or percentage_count > 0:
        return 'school'
    else:
        # Default to college if uncertain
        return 'college'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'marksheet' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['marksheet']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # If PDF, convert its first page to image for OCR
            ext = filename.rsplit('.', 1)[1].lower()
            target_image_path = file_path
            if ext == 'pdf':
                target_image_path = save_pdf_first_page_as_image(file_path, app.config['UPLOAD_FOLDER'])
            # Preprocess the image
            processed_images = preprocess_image(target_image_path)
            
            # Try OCR with different preprocessing methods
            ocr_results = []
            
            # Configuration optimized for table structure
            table_configs = [
                '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,: %',
                '--psm 4',
                '--psm 6',
                '--psm 11',
                '--psm 3'
            ]
            
            # Try OCR with enhanced image
            for config in table_configs:
                try:
                    text = pytesseract.image_to_string(processed_images['enhanced'], lang='eng', config=config)
                    if text.strip():
                        ocr_results.append(text)
                except:
                    continue
            
            # Try with other preprocessed versions
            for img_key in ['scaled_enhanced', 'scaled_sharp', 'thresh_gaussian', 'dilated', 'denoised', 'original_gray']:
                try:
                    if img_key in processed_images:
                        text = pytesseract.image_to_string(processed_images[img_key], lang='eng')
                        if text.strip():
                            ocr_results.append(text)
                except:
                    continue
            
            # Try with original image
            try:
                text = pytesseract.image_to_string(Image.open(target_image_path), lang='eng')
                if text.strip():
                    ocr_results.append(text)
            except:
                pass
            
            # Combine all OCR results
            combined_text = '\n\n--- OCR ATTEMPT ---\n\n'.join(ocr_results)
            
            # Detect marksheet type
            marksheet_type = detect_marksheet_type(combined_text)
            
            # Extract data based on type
            if marksheet_type == 'college':
                result = extract_college_marksheet_data(combined_text)
                result['marksheet_type'] = 'college'
            else:
                result = extract_school_marksheet_data(combined_text)
                result['marksheet_type'] = 'school'
            
            return render_template('result.html', result=result, filename=filename)
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('index'))
    
    flash('File type not allowed')
    return redirect(url_for('index'))

@app.route('/api/extract', methods=['POST'])
def api_extract():
    if 'marksheet' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['marksheet']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # If PDF, convert its first page to image for OCR
            ext = filename.rsplit('.', 1)[1].lower()
            target_image_path = file_path
            if ext == 'pdf':
                target_image_path = save_pdf_first_page_as_image(file_path, app.config['UPLOAD_FOLDER'])
            # Preprocess the image
            processed_images = preprocess_image(target_image_path)
            
            # Try OCR with different preprocessing methods
            ocr_results = []
            
            # Configuration optimized for table structure
            table_configs = [
                '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,: %',
                '--psm 4',
                '--psm 6',
                '--psm 11',
                '--psm 3'
            ]
            
            # Try OCR with enhanced image
            for config in table_configs:
                try:
                    text = pytesseract.image_to_string(processed_images['enhanced'], lang='eng', config=config)
                    if text.strip():
                        ocr_results.append(text)
                except:
                    continue
            
            # Try with other preprocessed versions
            for img_key in ['scaled_enhanced', 'scaled_sharp', 'thresh_gaussian', 'dilated', 'denoised', 'original_gray']:
                try:
                    if img_key in processed_images:
                        text = pytesseract.image_to_string(processed_images[img_key], lang='eng')
                        if text.strip():
                            ocr_results.append(text)
                except:
                    continue
            
            # Try with original image
            try:
                text = pytesseract.image_to_string(Image.open(target_image_path), lang='eng')
                if text.strip():
                    ocr_results.append(text)
            except:
                pass
            
            # Combine all OCR results
            combined_text = '\n\n--- OCR ATTEMPT ---\n\n'.join(ocr_results)
            
            # Detect marksheet type
            marksheet_type = detect_marksheet_type(combined_text)
            
            # Extract data based on type
            if marksheet_type == 'college':
                result = extract_college_marksheet_data(combined_text)
                result['marksheet_type'] = 'college'
            else:
                result = extract_school_marksheet_data(combined_text)
                result['marksheet_type'] = 'school'
            
            # Remove raw_text from API response
            api_result = {
                'marksheet_type': result['marksheet_type'],
                'success': True
            }
            
            if marksheet_type == 'college':
                api_result.update({
                    'spi': result.get('spi'),
                    'cpi': result.get('cpi')
                })
            else:
                api_result.update({
                    'percentage_10th': result.get('percentage_10th'),
                    'percentage_12th': result.get('percentage_12th')
                })
            
            return jsonify(api_result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True) 