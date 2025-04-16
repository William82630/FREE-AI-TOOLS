from flask import Flask, render_template, request, jsonify, send_file, url_for
import requests
from PIL import Image
import os
import base64
import json
import tempfile  # Add this for serverless file handling

app = Flask(__name__)

# Replace 'YOUR_API_KEY' with your actual OpenRouter API key
API_KEY = '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'
API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Google Cloud Vision API key
GOOGLE_VISION_API_KEY = os.environ.get('GOOGLE_VISION_API_KEY', 'AIzaSyD-ycpAL46xpKjeeBjRX7b8TJvR5pese3Q')
GOOGLE_VISION_API_URL = 'https://vision.googleapis.com/v1/images:annotate'

# For local development, use these folders
if os.environ.get('VERCEL_ENV') or os.environ.get('NETLIFY'):
    # For serverless environment, use temporary directory
    UPLOAD_FOLDER = tempfile.gettempdir()
    COMPRESSED_FOLDER = tempfile.gettempdir()
    FAVICON_FOLDER = tempfile.gettempdir()
else:
    # For local environment, use local folders
    UPLOAD_FOLDER = 'uploads/'
    COMPRESSED_FOLDER = 'compressed/'
    FAVICON_FOLDER = 'favicons/'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(COMPRESSED_FOLDER, exist_ok=True)
    os.makedirs(FAVICON_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ai-test')
def ai_test():
    return render_template('ai_test.html')

@app.route('/api/ai', methods=['POST'])
def ai_tool():
    user_input = request.json.get('input')
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400

    # Call the AI API
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'Free AI Tools',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': 'nvidia/llama-3.1-nemotron-ultra-253b-v1',
        'messages': [{'role': 'user', 'content': user_input}],  # Using correct chat format
        'temperature': 0.7
    }

    try:
        print(f"Sending request to OpenRouter API...")  # Debug logging
        response = requests.post(API_URL, headers=headers, json=payload, verify=False)  # Disable SSL verification
        print(f"Response status code: {response.status_code}")  # Debug logging
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")  # Debug logging
            return jsonify({'error': f"API Error: {response.text}"}), response.status_code
            
        response.raise_for_status()
        ai_response = response.json()
        return jsonify({'response': ai_response.get('choices', [{}])[0].get('message', {}).get('content', '')})
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {str(e)}")  # Debug logging
        return jsonify({'error': 'Connection error. Please check your internet connection and try again.'}), 500
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")  # Debug logging
        return jsonify({'error': str(e)}), 500

@app.route('/tools/image-editing/compress-image', methods=['GET', 'POST'])
def compress_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Compress the image
        compressed_path = os.path.join(COMPRESSED_FOLDER, file.filename)
        with Image.open(filepath) as img:
            img.save(compressed_path, optimize=True, quality=50)

        return send_file(compressed_path, as_attachment=True)

    return render_template('compress_image.html')

@app.route('/tools/image-editing/favicon-generator', methods=['GET', 'POST'])
def favicon_generator():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Generate favicon
        favicon_path = os.path.join(FAVICON_FOLDER, 'favicon.ico')
        with Image.open(filepath) as img:
            img = img.resize((64, 64))  # Resize to 64x64 for favicon
            img.save(favicon_path, format='ICO')

        return send_file(favicon_path, as_attachment=True)

    return render_template('favicon_generator.html')

@app.route('/tools/image-editing/convert-image', methods=['GET', 'POST'])
def convert_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        target_format = request.form.get('format')
        if target_format not in ['PNG', 'JPG', 'JPEG']:
            return 'Invalid format. Choose PNG, JPG, or JPEG.', 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        converted_filename = os.path.splitext(file.filename)[0] + f'.{target_format.lower()}'
        converted_path = os.path.join(COMPRESSED_FOLDER, converted_filename)

        with Image.open(filepath) as img:
            if target_format == 'JPG':
                target_format = 'JPEG'  # PIL uses 'JPEG' instead of 'JPG'
            img.convert('RGB').save(converted_path, format=target_format)

        return send_file(converted_path, as_attachment=True)

    return render_template('convert_image.html')

@app.route('/tools/image-editing/convert-webp-to-png', methods=['GET', 'POST'])
def convert_webp_to_png():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        if not file.filename.lower().endswith('.webp'):
            return 'Invalid file type. Please upload a WEBP file.', 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        converted_filename = os.path.splitext(file.filename)[0] + '.png'
        converted_path = os.path.join(COMPRESSED_FOLDER, converted_filename)

        with Image.open(filepath) as img:
            img.save(converted_path, format='PNG')

        return send_file(converted_path, as_attachment=True)

    return render_template('convert_webp_to_png.html')

@app.route('/tools/image-editing/convert-svg-to-png', methods=['GET', 'POST'])
def convert_svg_to_png():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        if not file.filename.lower().endswith('.svg'):
            return 'Invalid file type. Please upload an SVG file.', 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        converted_filename = os.path.splitext(file.filename)[0] + '.png'
        converted_path = os.path.join(COMPRESSED_FOLDER, converted_filename)

        # Convert SVG to PNG using cairosvg
        import cairosvg
        cairosvg.svg2png(url=filepath, write_to=converted_path)

        return send_file(converted_path, as_attachment=True)

    return render_template('convert_svg_to_png.html')

@app.route('/tools/image-editing/image-resizer', methods=['GET', 'POST'])
def image_resizer():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        width = request.form.get('width', type=int)
        height = request.form.get('height', type=int)
        if not width or not height:
            return 'Invalid dimensions. Please provide width and height.', 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        resized_filename = f"resized_{file.filename}"
        resized_path = os.path.join(COMPRESSED_FOLDER, resized_filename)

        with Image.open(filepath) as img:
            img = img.resize((width, height))
            img.save(resized_path)

        return send_file(resized_path, as_attachment=True)

    return render_template('image_resizer.html')

@app.route('/tools/image-editing/crop-image', methods=['GET', 'POST'])
def crop_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Get crop parameters
        try:
            x = int(request.form.get('x', 0))
            y = int(request.form.get('y', 0))
            width = int(request.form.get('width', 0))
            height = int(request.form.get('height', 0))
            
            if width <= 0 or height <= 0:
                return 'Invalid dimensions. Width and height must be positive values.', 400
        except ValueError:
            return 'Invalid crop parameters. Please enter valid numbers.', 400

        # Crop the image
        cropped_filename = f"cropped_{file.filename}"
        cropped_path = os.path.join(COMPRESSED_FOLDER, cropped_filename)
        
        try:
            with Image.open(filepath) as img:
                # Ensure crop dimensions are within image bounds
                img_width, img_height = img.size
                if x < 0 or y < 0 or x + width > img_width or y + height > img_height:
                    return 'Crop dimensions exceed image bounds.', 400
                
                # Perform the crop
                cropped_img = img.crop((x, y, x + width, y + height))
                cropped_img.save(cropped_path)
                
            return send_file(cropped_path, as_attachment=True)
        except Exception as e:
            return f'Error processing image: {str(e)}', 500

    return render_template('crop_image.html')

@app.route('/tools/image-editing/reverse-image-search', methods=['GET', 'POST'])
def reverse_image_search():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        # For serverless environments, don't rely on filesystem
        try:
            # Read the image directly from the request
            img_content = file.read()
            
            # Prepare the request payload for Google Vision API
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": base64.b64encode(img_content).decode('utf-8')
                        },
                        "features": [
                            {"type": "WEB_DETECTION"}
                        ]
                    }
                ]
            }
            
            # Get API key from environment variable or use default
            api_key = os.environ.get('GOOGLE_VISION_API_KEY', GOOGLE_VISION_API_KEY)
            
            # Send the request to Google Cloud Vision API
            response = requests.post(
                f"{GOOGLE_VISION_API_URL}?key={api_key}",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Google Vision API error: {response.text}")
            
            annotations = response.json().get('responses', [{}])[0].get('webDetection', {})
            
            # Extract meaningful results
            similar_images = []
            possible_sources = []
            
            # Get visually similar images with confidence scores
            if 'visuallySimilarImages' in annotations:
                for i, img in enumerate(annotations['visuallySimilarImages']):
                    # Only include image URLs that end with common image extensions
                    url = img['url']
                    if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        # Calculate a fake similarity score for display purposes
                        score = 95 - (i * 5)  # Starting at 95% and decreasing
                        if score < 60:  # Don't show anything below 60% similarity
                            break
                        similar_images.append({
                            'url': url,
                            'score': score
                        })
            
            # Get pages with matching images (possible sources)
            if 'pagesWithMatchingImages' in annotations:
                for page in annotations['pagesWithMatchingImages']:
                    possible_sources.append(page['url'])
            
            # Get full matching images (additional sources)
            if 'fullMatchingImages' in annotations:
                for img in annotations['fullMatchingImages']:
                    possible_sources.append(img['url'])
            
            # If no results were found
            if not similar_images and not possible_sources:
                return render_template('reverse_image_search_results.html', 
                                      filename=file.filename,
                                      message="No similar images or sources found for this image.")

            # In serverless environments, we can't save the uploaded file for display
            # So, handle the temporary file save if local or skip if serverless
            if not (os.environ.get('VERCEL_ENV') or os.environ.get('NETLIFY')):
                # Only save file locally if not in serverless environment
                filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                with open(filepath, 'wb') as f:
                    f.write(img_content)

            # Limit results for display
            similar_images = similar_images[:6]  # Limit to 6 similar images
            possible_sources = list(set(possible_sources))[:10]  # Remove duplicates and limit to 10 sources

            return render_template('reverse_image_search_results.html', 
                                  filename=file.filename,
                                  similar_images=similar_images,
                                  possible_sources=possible_sources)

        except Exception as e:
            # Log the error for debugging
            print(f"Error during reverse image search: {e}")
            
            # Return a user-friendly error message
            return render_template('reverse_image_search_results.html', 
                                  filename=file.filename if file else "unknown",
                                  error=f"An error occurred: {e}")

    return render_template('reverse_image_search.html')

@app.route('/tools/image-editing/face-search', methods=['GET', 'POST'])
def face_search():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No file part', 400
        file = request.files['image']
        if file.filename == '':
            return 'No selected file', 400

        # For serverless environments, don't rely on filesystem
        try:
            # Read the image directly from the request
            img_content = file.read()
            
            # Prepare the request payload for Google Vision API
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": base64.b64encode(img_content).decode('utf-8')
                        },
                        "features": [
                            {"type": "WEB_DETECTION"}
                        ]
                    }
                ]
            }
            
            # Get API key from environment variable or use default
            api_key = os.environ.get('GOOGLE_VISION_API_KEY', GOOGLE_VISION_API_KEY)
            
            # Send the request to Google Cloud Vision API
            response = requests.post(
                f"{GOOGLE_VISION_API_URL}?key={api_key}",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Google Vision API error: {response.text}")
            
            annotations = response.json().get('responses', [{}])[0].get('webDetection', {})
            
            # Extract meaningful results
            results = []
            
            # Get web entities (descriptions of what's in the image)
            if 'webEntities' in annotations:
                for entity in annotations['webEntities']:
                    if entity.get('description') and entity.get('score', 0) > 0.5:  # Only include relevant matches
                        results.append(f"{entity['description']} (score: {entity['score']:.2f})")
            
            # Get visually similar images
            if 'visuallySimilarImages' in annotations:
                for img in annotations['visuallySimilarImages']:
                    results.append(img['url'])
            
            # Get pages with matching images
            if 'pagesWithMatchingImages' in annotations:
                for page in annotations['pagesWithMatchingImages'][:5]:  # Limit to 5 pages
                    results.append(page['url'])

            # If no results were found
            if not results:
                return render_template('face_search_results.html', 
                                      filename=file.filename,
                                      message="No similar faces or related images found.")

            # In serverless environments, we can't save the uploaded file for display
            # So, handle the temporary file save if local or skip if serverless
            if not (os.environ.get('VERCEL_ENV') or os.environ.get('NETLIFY')):
                # Only save file locally if not in serverless environment
                filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                with open(filepath, 'wb') as f:
                    f.write(img_content)

            # Limit results for display (to avoid overwhelming the page)
            results = list(set(results))  # Remove duplicates
            results = results[:20]  # Limit to 20 results

            return render_template('face_search_results.html', 
                                  filename=file.filename,
                                  results=results)

        except Exception as e:
            # Log the error for debugging
            print(f"Error during face search: {e}")
            
            # Return a user-friendly error message
            return render_template('face_search_results.html', 
                                  filename=file.filename if file else "unknown",
                                  error=f"An error occurred: {e}")

    return render_template('face_search.html')

@app.route('/tools/online-calculators/simple-calculator', methods=['GET'])
def simple_calculator():
    return render_template('simple_calculator.html')

@app.route('/tools/online-calculators/age-calculator', methods=['GET'])
def age_calculator():
    return render_template('age_calculator.html')

@app.route('/tools/online-calculators/bmi-calculator', methods=['GET'])
def bmi_calculator():
    return render_template('bmi_calculator.html')

@app.route('/tools/online-calculators/currency-converter', methods=['GET'])
def currency_converter():
    return render_template('currency_converter.html')

@app.route('/tools/online-calculators/password-generator', methods=['GET'])
def password_generator():
    return render_template('password_generator.html')

@app.route('/tools/online-calculators/loan-calculator', methods=['GET'])
def loan_calculator():
    return render_template('loan_calculator.html')

@app.route('/tools/online-calculators/unit-converter', methods=['GET'])
def unit_converter():
    return render_template('unit_converter.html')

@app.route('/tools/online-calculators/qr-code-generator', methods=['GET'])
def qr_code_generator():
    return render_template('qr_code_generator.html')

@app.route('/tools/online-calculators/gst-calculator', methods=['GET'])
def gst_calculator():
    return render_template('gst_calculator.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/terms-of-use')
def terms_of_use():
    return render_template('terms-of-use.html')

# New category: Keyword Research Tools
@app.route('/tools/keyword-research/keyword-generator', methods=['GET', 'POST'])
def keyword_generator():
    if request.method == 'POST':
        seed_keyword = request.form.get('seed_keyword', '')
        if not seed_keyword:
            return 'No seed keyword provided', 400
            
        # For demonstration purposes, generate some related keywords
        # In a real implementation, you would use a keyword research API
        related_keywords = [
            f"{seed_keyword} tools",
            f"{seed_keyword} online",
            f"best {seed_keyword}",
            f"{seed_keyword} free",
            f"{seed_keyword} software",
            f"how to use {seed_keyword}",
            f"{seed_keyword} alternatives",
            f"{seed_keyword} tutorial"
        ]
        
        return render_template('keyword_generator_results.html', 
                              seed_keyword=seed_keyword,
                              related_keywords=related_keywords)
        
    return render_template('keyword_generator.html')

@app.route('/tools/keyword-research/keyword-difficulty-checker', methods=['GET', 'POST'])
def keyword_difficulty_checker():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '')
        if not keyword:
            return 'No keyword provided', 400
            
        # For demonstration purposes, generate a random difficulty score
        # In a real implementation, you would use an SEO API
        import random
        difficulty_score = random.randint(1, 100)
        
        difficulty_level = "Easy"
        if difficulty_score > 70:
            difficulty_level = "Hard"
        elif difficulty_score > 40:
            difficulty_level = "Medium"
            
        return render_template('keyword_difficulty_results.html', 
                              keyword=keyword,
                              difficulty_score=difficulty_score,
                              difficulty_level=difficulty_level)
        
    return render_template('keyword_difficulty_checker.html')

# New category: PDF Solutions
@app.route('/tools/pdf-solutions/pdf-to-text', methods=['GET', 'POST'])
def pdf_to_text():
    if request.method == 'POST':
        if 'pdf' not in request.files:
            return 'No file part', 400
        file = request.files['pdf']
        if file.filename == '':
            return 'No selected file', 400
            
        if not file.filename.lower().endswith('.pdf'):
            return 'Invalid file type. Please upload a PDF file.', 400
            
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        # For demonstration purposes
        # In a real implementation, you would use a PDF parsing library like PyPDF2
        text_content = "This is a placeholder for the extracted text content from your PDF."
        text_filename = os.path.splitext(file.filename)[0] + '.txt'
        text_path = os.path.join(COMPRESSED_FOLDER, text_filename)
        
        with open(text_path, 'w') as f:
            f.write(text_content)
            
        return send_file(text_path, as_attachment=True)
        
    return render_template('pdf_to_text.html')

@app.route('/tools/pdf-solutions/pdf-merger', methods=['GET', 'POST'])
def pdf_merger():
    if request.method == 'POST':
        if 'pdfs' not in request.files:
            return 'No file part', 400
            
        files = request.files.getlist('pdfs')
        if not files or files[0].filename == '':
            return 'No selected files', 400
            
        # Check if all files are PDFs
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                return 'All files must be PDFs', 400
                
        # Save all files
        filepaths = []
        for file in files:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            filepaths.append(filepath)
            
        # For demonstration purposes
        # In a real implementation, you would use a PDF library to merge the files
        merged_filename = "merged_document.pdf"
        merged_path = os.path.join(COMPRESSED_FOLDER, merged_filename)
        
        # Placeholder for actual merging logic
        # Here we would use PyPDF2 or a similar library to merge the PDFs
        
        # For now, just copy the first PDF as a placeholder
        import shutil
        shutil.copy(filepaths[0], merged_path)
            
        return send_file(merged_path, as_attachment=True)
        
    return render_template('pdf_merger.html')

if __name__ == '__main__':
    app.run(debug=True)
