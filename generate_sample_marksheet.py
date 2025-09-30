import os
import random
import argparse
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def generate_sample_marksheet(student_name, roll_number, semester, spi, cpi, output_path):
    # Create a white image
    width, height = 1000, 1400
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to load fonts, use default if not available
    try:
        header_font = ImageFont.truetype('arial.ttf', 36)
        title_font = ImageFont.truetype('arial.ttf', 24)
        normal_font = ImageFont.truetype('arial.ttf', 18)
        small_font = ImageFont.truetype('arial.ttf', 14)
    except IOError:
        # Use default font if arial.ttf is not available
        header_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw college header
    draw.text((width//2, 50), "SAMPLE UNIVERSITY", fill='black', font=header_font, anchor='mt')
    draw.text((width//2, 100), "EXAMINATION RESULT", fill='black', font=title_font, anchor='mt')
    
    # Draw horizontal line
    draw.line([(50, 150), (width-50, 150)], fill='black', width=2)
    
    # Student information
    draw.text((100, 200), f"Student Name: {student_name}", fill='black', font=normal_font)
    draw.text((100, 240), f"Roll Number: {roll_number}", fill='black', font=normal_font)
    draw.text((100, 280), f"Semester: {semester}", fill='black', font=normal_font)
    draw.text((100, 320), f"Academic Year: 2023-24", fill='black', font=normal_font)
    
    # Draw horizontal line
    draw.line([(50, 370), (width-50, 370)], fill='black', width=2)
    
    # Table header
    draw.text((100, 400), "Course Code", fill='black', font=normal_font)
    draw.text((300, 400), "Course Name", fill='black', font=normal_font)
    draw.text((600, 400), "Credits", fill='black', font=normal_font)
    draw.text((700, 400), "Grade", fill='black', font=normal_font)
    draw.text((800, 400), "Grade Points", fill='black', font=normal_font)
    
    # Draw horizontal line
    draw.line([(50, 430), (width-50, 430)], fill='black', width=1)
    
    # Generate random courses
    courses = [
        ("CS101", "Introduction to Programming", 4),
        ("CS102", "Data Structures", 4),
        ("MA101", "Calculus", 3),
        ("PH101", "Physics", 3),
        ("HU101", "Technical Communication", 2),
        ("CS103", "Computer Organization", 3),
    ]
    
    grades = ['AA', 'AB', 'BB', 'BC', 'CC', 'CD', 'DD', 'FF']
    grade_points = {'AA': 10, 'AB': 9, 'BB': 8, 'BC': 7, 'CC': 6, 'CD': 5, 'DD': 4, 'FF': 0}
    
    y_pos = 460
    total_credits = 0
    total_grade_points = 0
    
    for i, (code, name, credit) in enumerate(courses):
        # Assign random grade or use a distribution that matches the given SPI
        if float(spi) > 9.0:
            grade = random.choice(grades[:2])  # Mostly AA, AB
        elif float(spi) > 8.0:
            grade = random.choice(grades[:3])  # Mostly AA, AB, BB
        elif float(spi) > 7.0:
            grade = random.choice(grades[1:4])  # Mostly AB, BB, BC
        elif float(spi) > 6.0:
            grade = random.choice(grades[2:5])  # Mostly BB, BC, CC
        else:
            grade = random.choice(grades[3:])  # Mostly lower grades
            
        gp = grade_points[grade]
        total_credits += credit
        total_grade_points += credit * gp
        
        draw.text((100, y_pos), code, fill='black', font=normal_font)
        draw.text((300, y_pos), name, fill='black', font=normal_font)
        draw.text((600, y_pos), str(credit), fill='black', font=normal_font)
        draw.text((700, y_pos), grade, fill='black', font=normal_font)
        draw.text((800, y_pos), str(gp), fill='black', font=normal_font)
        
        y_pos += 40
    
    # Draw horizontal line
    draw.line([(50, y_pos), (width-50, y_pos)], fill='black', width=1)
    y_pos += 30
    
    # Calculate SPI (should be close to the input SPI)
    calculated_spi = total_grade_points / total_credits
    
    # Summary
    draw.text((100, y_pos), f"Total Credits: {total_credits}", fill='black', font=normal_font)
    y_pos += 40
    
    # Use the provided SPI and CPI instead of calculated ones
    draw.text((100, y_pos), f"SPI: {spi}", fill='black', font=normal_font)
    y_pos += 40
    draw.text((100, y_pos), f"CPI: {cpi}", fill='black', font=normal_font)
    y_pos += 60
    
    # Result
    draw.text((100, y_pos), "Result: PASSED", fill='black', font=title_font)
    
    # Footer
    draw.text((width//2, height-100), "This is a sample marksheet generated for testing purposes.", 
              fill='black', font=small_font, anchor='mt')
    draw.text((width//2, height-70), "Not a valid academic document.", 
              fill='black', font=small_font, anchor='mt')
    
    # Add some noise to make OCR more realistic
    img_array = np.array(image)
    noise = np.random.normal(0, 2, img_array.shape).astype(np.uint8)
    noisy_img = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    noisy_image = Image.fromarray(noisy_img)
    
    # Save the image
    noisy_image.save(output_path)
    print(f"Sample marksheet generated and saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate a sample marksheet for OCR testing')
    parser.add_argument('--name', default='John Doe', help='Student name')
    parser.add_argument('--roll', default='B123456', help='Roll number')
    parser.add_argument('--semester', default='4', help='Semester number')
    parser.add_argument('--spi', default='8.5', help='SPI value')
    parser.add_argument('--cpi', default='8.2', help='CPI value')
    parser.add_argument('--output', default='sample_marksheet.jpg', help='Output file path')
    
    args = parser.parse_args()
    
    # Create uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    
    # Generate the marksheet
    output_path = os.path.join('uploads', args.output)
    generate_sample_marksheet(args.name, args.roll, args.semester, args.spi, args.cpi, output_path)

if __name__ == '__main__':
    main()