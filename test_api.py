import requests
import sys
import json
import os

def test_api(image_path, api_url='http://127.0.0.1:5000/api/extract'):
    """Test the OCR API endpoint with a given image file."""
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' does not exist.")
        return
    
    print(f"Testing API with image: {image_path}")
    print(f"API URL: {api_url}")
    
    try:
        # Open the image file
        with open(image_path, 'rb') as f:
            # Create the files payload
            files = {'marksheet': f}
            
            # Make the POST request
            response = requests.post(api_url, files=files)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                result = response.json()
                
                # Pretty print the result
                print("\nAPI Response:")
                print(json.dumps(result, indent=2))
                
                # Display the extracted values
                print("\nExtracted Values:")
                print(f"SPI: {result.get('spi', 'Not found')}")
                print(f"CPI: {result.get('cpi', 'Not found')}")
                
                # Check if raw text is available
                if 'raw_text' in result:
                    print("\nRaw Text Preview (first 200 chars):")
                    print(result['raw_text'][:200] + "..." if len(result['raw_text']) > 200 else result['raw_text'])
            else:
                print(f"\nError: API request failed with status code {response.status_code}")
                print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Make sure the Flask application is running.")
    
    except Exception as e:
        print(f"\nError: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <path_to_image> [api_url]")
        print("Default API URL: http://127.0.0.1:5000/api/extract")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Use custom API URL if provided
    api_url = sys.argv[2] if len(sys.argv) > 2 else 'http://127.0.0.1:5000/api/extract'
    
    test_api(image_path, api_url)

if __name__ == "__main__":
    main()