from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, redirect, url_for, flash
import requests
from PIL import Image, ImageDraw, ImageFont
import os
import base64
import json

app = Flask(__name__)

# Replace 'YOUR_API_KEY' with your actual OpenRouter API key
API_KEY = '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'
API_URL = 'https://api.openrouter.ai/v1/completions'

GOOGLE_VISION_API_KEY = 'AIzaSyD-ycpAL46xpKjeeBjRX7b8TJvR5pese3Q'
GOOGLE_VISION_API_URL = f'https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}'

UPLOAD_FOLDER = 'uploads/'
COMPRESSED_FOLDER = 'compressed/'
FAVICON_FOLDER = 'favicons/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)
os.makedirs(FAVICON_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ai', methods=['POST'])
def ai_tool():
    user_input = request.json.get('input')
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400

    # Call the AI API
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': 'google-gemini-2.5-pro',  # Replace with the desired model
        'prompt': user_input,
        'max_tokens': 100
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_response = response.json()
        return jsonify({'response': ai_response.get('choices', [{}])[0].get('text', '')})
    except requests.exceptions.RequestException as e:
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
        # Check if user submitted text/emoji or image
        text = request.form.get('text')
        file = request.files.get('image')
        favicon_path = os.path.join(FAVICON_FOLDER, 'favicon.ico')
        if text and text.strip():
            # Generate favicon from text/emoji
            img = Image.new('RGBA', (64, 64), (255, 255, 255, 255))  # White background
            draw = ImageDraw.Draw(img)
            # Dynamically adjust font size based on text length
            font_size = 40
            if len(text) > 8:
                font_size = 24
            if len(text) > 16:
                font_size = 16
            try:
                font = ImageFont.truetype("arial.ttf", font_size)  # Use Arial for better compatibility
            except Exception:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((64-w)/2, (64-h)/2), text, font=font, fill=(0,0,0,255))
            img.save(favicon_path, format='ICO')
            return send_file(favicon_path, as_attachment=True)
        elif file and file.filename != '':
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            with Image.open(filepath) as img:
                img = img.resize((64, 64))  # Resize to 64x64 for favicon
                img.save(favicon_path, format='ICO')
            return send_file(favicon_path, as_attachment=True)
        else:
            return 'No input provided', 400
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
        # Handle image cropping logic here
        return 'Crop Image functionality is under development.'
    return render_template('crop_image.html')

@app.route('/tools/image-editing/reverse-image-search', methods=['GET', 'POST'])
def reverse_image_search():
    if request.method == 'POST':
        image = request.files.get('image')
        image_url = request.form.get('image_url')
        results = []
        error = None
        if (image and image.filename) or (image_url and image_url.strip()):
            img_content = None
            if image and image.filename:
                img_bytes = image.read()
                img_content = base64.b64encode(img_bytes).decode('utf-8')
            elif image_url and image_url.strip():
                # Download the image from the URL
                try:
                    resp = requests.get(image_url)
                    if resp.status_code == 200:
                        img_content = base64.b64encode(resp.content).decode('utf-8')
                    else:
                        error = 'Could not download image from the provided URL.'
                except Exception:
                    error = 'Invalid image URL.'
            if img_content and not error:
                vision_payload = {
                    "requests": [
                        {
                            "image": {"content": img_content},
                            "features": [{"type": "WEB_DETECTION", "maxResults": 8}]
                        }
                    ]
                }
                try:
                    vision_resp = requests.post(GOOGLE_VISION_API_URL, json=vision_payload)
                    vision_data = vision_resp.json()
                    web_detection = vision_data['responses'][0].get('webDetection', {})
                    visually_similar = web_detection.get('visuallySimilarImages', [])
                    pages_with_matching_images = web_detection.get('pagesWithMatchingImages', [])
                    # Prepare results from visually similar images
                    for img in visually_similar:
                        results.append({
                            'title': 'Visually Similar Image',
                            'url': img.get('url'),
                            'thumbnail': img.get('url')
                        })
                    # Prepare results from pages with matching images
                    for page in pages_with_matching_images:
                        results.append({
                            'title': page.get('pageTitle', 'Matching Page'),
                            'url': page.get('url'),
                            'thumbnail': visually_similar[0]['url'] if visually_similar else ''
                        })
                    if not results:
                        error = 'No visually similar images or matching pages found.'
                except Exception as e:
                    error = f'Error processing image: {str(e)}'
        else:
            error = 'Please upload an image or provide an image URL.'
        return render_template('reverse_image_search.html', results=results, error=error)
    return render_template('reverse_image_search.html', results=None, error=None)

@app.route('/tools/image-editing/face-search', methods=['GET', 'POST'])
def face_search():
    if request.method == 'POST':
        image = request.files.get('image')
        image_url = request.form.get('image_url')
        results = []
        error = None
        if (image and image.filename) or (image_url and image_url.strip()):
            img_content = None
            if image and image.filename:
                img_bytes = image.read()
                img_content = base64.b64encode(img_bytes).decode('utf-8')
            elif image_url and image_url.strip():
                try:
                    resp = requests.get(image_url)
                    if resp.status_code == 200:
                        img_content = base64.b64encode(resp.content).decode('utf-8')
                    else:
                        error = 'Could not download image from the provided URL.'
                except Exception:
                    error = 'Invalid image URL.'
            if img_content and not error:
                vision_payload = {
                    "requests": [
                        {
                            "image": {"content": img_content},
                            "features": [{"type": "FACE_DETECTION", "maxResults": 8}]
                        }
                    ]
                }
                try:
                    vision_resp = requests.post(GOOGLE_VISION_API_URL, json=vision_payload)
                    vision_data = vision_resp.json()
                    faces = vision_data['responses'][0].get('faceAnnotations', [])
                    if faces:
                        for idx, face in enumerate(faces):
                            bounding_poly = face.get('fdBoundingPoly', {}).get('vertices', [])
                            bbox = ', '.join([f"({v.get('x', 0)}, {v.get('y', 0)})" for v in bounding_poly])
                            joy = face.get('joyLikelihood', 'UNKNOWN')
                            sorrow = face.get('sorrowLikelihood', 'UNKNOWN')
                            anger = face.get('angerLikelihood', 'UNKNOWN')
                            surprise = face.get('surpriseLikelihood', 'UNKNOWN')
                            confidence = face.get('detectionConfidence', 0)
                            details = f"Confidence: {confidence:.2f}<br>Bounding Box: {bbox}<br>Joy: {joy}, Sorrow: {sorrow}, Anger: {anger}, Surprise: {surprise}"
                            results.append({
                                'title': f'Face #{idx+1}',
                                'url': details,
                                'thumbnail': request.form.get('image_url') if image_url else '/static/images/face_icon.png'
                            })
                    else:
                        error = 'No faces detected in the image.'
                except Exception as e:
                    error = f'Error processing image: {str(e)}'
        else:
            error = 'Please upload an image or provide an image URL.'
        return render_template('face_search.html', results=results, error=error)
    return render_template('face_search.html', results=None, error=None)

@app.route('/tools/online-calculators/free-online-calculator', methods=['GET'])
@app.route('/tools/online-calculators/simple-calculator', methods=['GET'])  # Keep old route for backward compatibility
def online_calculator():
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

@app.route('/privacy-policy.html')
def privacy_policy():
    return send_from_directory('templates', 'privacy-policy.html')

@app.route('/terms-of-use.html')
def terms_of_use():
    return send_from_directory('templates', 'terms-of-use.html')

# Ensure this block appears only once at the end of the file
if __name__ == '__main__':
    app.run(debug=True)