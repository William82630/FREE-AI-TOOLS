from flask import Flask, render_template, request, jsonify, send_file
import requests
from PIL import Image
import os

app = Flask(__name__)

# Replace 'YOUR_API_KEY' with your actual OpenRouter API key
API_KEY = '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'
API_URL = 'https://api.openrouter.ai/v1/completions'

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
        # Handle image cropping logic here
        return 'Crop Image functionality is under development.'
    return render_template('crop_image.html')

@app.route('/tools/image-editing/reverse-image-search', methods=['GET', 'POST'])
def reverse_image_search():
    if request.method == 'POST':
        # Handle reverse image search logic here
        return 'Reverse Image Search functionality is under development.'
    return render_template('reverse_image_search.html')

@app.route('/tools/image-editing/face-search', methods=['GET', 'POST'])
def face_search():
    if request.method == 'POST':
        # Handle face search logic here
        return 'Face Search functionality is under development.'
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

if __name__ == '__main__':
    app.run(debug=True)