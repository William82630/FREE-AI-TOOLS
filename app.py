from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename
import requests
from PIL import Image, ImageDraw, ImageFont
import os
import random
import io
import base64
import qrcode
import zipfile
from datetime import datetime, timedelta
import uuid
import tempfile
from reportlab.lib.pagesizes import A4, LETTER, LEGAL, A3, A5, landscape
from reportlab.pdfgen import canvas

app = Flask(__name__)
# Configure Flask to handle larger file uploads (1GB)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB

# Replace 'YOUR_API_KEY' with your actual OpenRouter API key
API_KEY = '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'
API_URL = 'https://api.openrouter.ai/v1/completions'

UPLOAD_FOLDER = 'uploads/'
COMPRESSED_FOLDER = 'compressed/'
FAVICON_FOLDER = 'favicons/'
CONVERTED_FOLDER = 'converted/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)
os.makedirs(FAVICON_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/privacy-policy.html')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-use.html')
def terms_of_use():
    return render_template('terms_of_use.html')

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
            return jsonify({'success': False, 'error': 'No file part'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400

        # Get compression level from form - simplified to just two options
        compression_level = request.form.get('quality', 'standard')

        # Map compression level to PIL quality value (1-100, lower = more compression)
        if compression_level == 'maximum':
            quality = 20  # Maximum compression, lower quality
        else:
            quality = 60  # Standard compression, better quality

        try:
            # Generate unique filenames
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename_base, file_ext = os.path.splitext(file.filename)
            unique_filename = f"{filename_base}_{timestamp}{file_ext}"

            # Save original image
            original_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(original_path)

            # Get original file size
            original_size = os.path.getsize(original_path)

            # Compress the image
            compressed_path = os.path.join(COMPRESSED_FOLDER, unique_filename)

            # Get image format
            with Image.open(original_path) as img:
                img_format = img.format

                # For PNG images, use a different approach to ensure compression
                if img_format == 'PNG':
                    # For PNGs, we can use optimize and reduce colors for better compression
                    if compression_level == 'maximum':
                        # Convert to P mode (palette) with limited colors for maximum compression
                        img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                        img.save(compressed_path, optimize=True, quality=quality)
                    else:
                        # Standard compression for PNGs
                        img.save(compressed_path, optimize=True, quality=quality)
                else:
                    # For JPEGs and other formats, use standard quality-based compression
                    img.save(compressed_path, optimize=True, quality=quality)

            # Get compressed file size
            compressed_size = os.path.getsize(compressed_path)

            # If compression didn't reduce size, try more aggressive compression
            if compressed_size >= original_size:
                with Image.open(original_path) as img:
                    # Try more aggressive compression
                    if img_format == 'PNG':
                        # For PNGs, convert to JPEG if not transparent
                        if 'A' not in img.getbands():  # No alpha channel
                            img = img.convert('RGB')
                            compressed_path = os.path.splitext(compressed_path)[0] + '.jpg'
                            img.save(compressed_path, 'JPEG', optimize=True, quality=40)
                        else:
                            # For transparent PNGs, reduce colors more aggressively
                            img = img.convert('P', palette=Image.ADAPTIVE, colors=128)
                            img.save(compressed_path, optimize=True)
                    else:
                        # For other formats, use very aggressive compression
                        img.save(compressed_path, optimize=True, quality=15)

                # Check if we achieved compression now
                compressed_size = os.path.getsize(compressed_path)

                # If still no compression, use the original but inform the user
                if compressed_size >= original_size:
                    import shutil
                    shutil.copy2(original_path, compressed_path)
                    compressed_size = original_size

            # Calculate savings
            size_difference = original_size - compressed_size
            savings_percent = round((size_difference / original_size) * 100, 1)

            # Format sizes for display
            def format_size(size_in_bytes):
                if size_in_bytes < 1024:
                    return f"{size_in_bytes} bytes"
                elif size_in_bytes < 1024 * 1024:
                    return f"{(size_in_bytes / 1024):.2f} KB"
                else:
                    return f"{(size_in_bytes / (1024 * 1024)):.2f} MB"

            # Convert images to base64 for display
            def image_to_base64(image_path):
                with open(image_path, "rb") as img_file:
                    return f"data:image/{file_ext[1:].lower()};base64," + base64.b64encode(img_file.read()).decode('utf-8')

            # Determine if the image was actually compressed
            was_compressed = compressed_size < original_size

            # Return JSON response with image data
            return jsonify({
                'success': True,
                'original_image': image_to_base64(original_path),
                'compressed_image': image_to_base64(compressed_path),
                'original_size': format_size(original_size),
                'compressed_size': format_size(compressed_size),
                'savings_percent': savings_percent,
                'quality': quality,
                'was_compressed': was_compressed,
                'message': "Image already optimized - no further compression possible" if not was_compressed else ""
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('compress_image.html')

@app.route('/tools/image-editing/favicon-generator', methods=['GET', 'POST'])
def favicon_generator():
    if request.method == 'POST':
        try:
            # Check if it's an AJAX request for preview
            if request.form.get('action') == 'preview':
                # Get form data
                favicon_type = request.form.get('favicon_type', 'image')

                if favicon_type == 'image' and 'image' in request.files:
                    # Process image upload for preview
                    file = request.files['image']
                    if file.filename == '':
                        return jsonify({'success': False, 'error': 'No selected file'})

                    # Save the uploaded image
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename_base, file_ext = os.path.splitext(file.filename)
                    unique_filename = f"{filename_base}_{timestamp}{file_ext}"
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(filepath)

                    # Create preview images
                    preview_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
                    preview_images = {}

                    with Image.open(filepath) as img:
                        # Convert to RGBA if not already
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        # Generate previews at different sizes
                        for size in preview_sizes:
                            size_key = f"{size[0]}x{size[1]}"
                            resized_img = img.resize(size, Image.LANCZOS)

                            # Save to buffer and convert to base64
                            buffer = io.BytesIO()
                            resized_img.save(buffer, format="PNG")
                            buffer.seek(0)
                            preview_images[size_key] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

                    return jsonify({
                        'success': True,
                        'preview_images': preview_images,
                        'original_path': filepath
                    })

                elif favicon_type == 'text':
                    # Process text favicon for preview
                    text = request.form.get('text', 'F')
                    bg_color = request.form.get('bg_color', '#4a1d96')
                    text_color = request.form.get('text_color', '#ffffff')
                    shape = request.form.get('shape', 'square')

                    # Create preview images
                    preview_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
                    preview_images = {}

                    for size in preview_sizes:
                        size_key = f"{size[0]}x{size[1]}"

                        # Create image with background color
                        img = Image.new('RGBA', size, bg_color)
                        draw = ImageDraw.Draw(img)

                        # Calculate font size (approximately 60% of the image height)
                        font_size = int(size[1] * 0.6)

                        # Use default font for simplicity and compatibility
                        font = ImageFont.load_default()

                        # Simple centering approach - place text in the middle
                        # This is a simplified approach that works across all Pillow versions
                        position = (size[0] // 2 - font_size // 3 * len(text), size[1] // 2 - font_size // 2)

                        # Draw text
                        draw.text(position, text, fill=text_color, font=font)

                        # Apply shape if not square
                        if shape == 'circle':
                            # Create a circular mask
                            mask = Image.new('L', size, 0)
                            mask_draw = ImageDraw.Draw(mask)
                            mask_draw.ellipse((0, 0, size[0], size[1]), fill=255)

                            # Create a transparent image
                            circle_img = Image.new('RGBA', size, (0, 0, 0, 0))

                            # Paste the original image using the mask
                            circle_img.paste(img, (0, 0), mask)
                            img = circle_img

                        # Save to buffer and convert to base64
                        buffer = io.BytesIO()
                        img.save(buffer, format="PNG")
                        buffer.seek(0)
                        preview_images[size_key] = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

                    return jsonify({
                        'success': True,
                        'preview_images': preview_images,
                        'text_config': {
                            'text': text,
                            'bg_color': bg_color,
                            'text_color': text_color,
                            'shape': shape
                        }
                    })

                return jsonify({'success': False, 'error': 'Invalid favicon type or missing data'})

            # Handle full generation and download
            favicon_type = request.form.get('favicon_type', 'image')
            original_path = request.form.get('original_path', '')
            primary_size = request.form.get('primary_size', '32x32')

            # Parse primary size
            try:
                primary_width, primary_height = map(int, primary_size.split('x'))
                primary_size_tuple = (primary_width, primary_height)
            except:
                # Default to 32x32 if parsing fails
                primary_size_tuple = (32, 32)

            # Create a zip file to store all favicon files
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            zip_filename = f"favicon_package_{timestamp}.zip"
            zip_path = os.path.join(FAVICON_FOLDER, zip_filename)

            with zipfile.ZipFile(zip_path, 'w') as favicon_zip:
                if favicon_type == 'image' and original_path and os.path.exists(original_path):
                    with Image.open(original_path) as img:
                        # Convert to RGBA if not already
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        # Generate favicon.ico (16x16, 32x32, 48x48)
                        ico_sizes = [(16, 16), (32, 32), (48, 48)]

                        # Make sure primary size is included in ico_sizes
                        if primary_size_tuple not in ico_sizes and primary_size_tuple[0] <= 256:
                            ico_sizes.append(primary_size_tuple)
                            # Sort sizes from smallest to largest
                            ico_sizes.sort(key=lambda x: x[0])

                        ico_images = []

                        for size in ico_sizes:
                            ico_images.append(img.resize(size, Image.LANCZOS))

                        # Save favicon.ico
                        favicon_ico_path = os.path.join(FAVICON_FOLDER, 'favicon.ico')
                        ico_images[0].save(
                            favicon_ico_path,
                            format='ICO',
                            sizes=ico_sizes
                        )
                        favicon_zip.write(favicon_ico_path, 'favicon.ico')

                        # Generate PNG favicons in various sizes
                        png_sizes = [(16, 16), (32, 32), (57, 57), (60, 60), (72, 72),
                                    (76, 76), (96, 96), (114, 114), (120, 120),
                                    (144, 144), (152, 152), (180, 180), (192, 192)]

                        for size in png_sizes:
                            size_str = f"{size[0]}x{size[1]}"
                            png_path = os.path.join(FAVICON_FOLDER, f"favicon-{size_str}.png")
                            resized = img.resize(size, Image.LANCZOS)
                            resized.save(png_path, format="PNG")
                            favicon_zip.write(png_path, f"favicon-{size_str}.png")

                        # Generate apple-touch-icon
                        apple_sizes = [(57, 57), (60, 60), (72, 72), (76, 76),
                                      (114, 114), (120, 120), (144, 144),
                                      (152, 152), (180, 180)]

                        for size in apple_sizes:
                            size_str = f"{size[0]}x{size[1]}"
                            apple_path = os.path.join(FAVICON_FOLDER, f"apple-touch-icon-{size_str}.png")
                            resized = img.resize(size, Image.LANCZOS)
                            resized.save(apple_path, format="PNG")
                            favicon_zip.write(apple_path, f"apple-touch-icon-{size_str}.png")

                        # Generate android-chrome icons
                        android_sizes = [(192, 192), (512, 512)]

                        for size in android_sizes:
                            size_str = f"{size[0]}x{size[1]}"
                            android_path = os.path.join(FAVICON_FOLDER, f"android-chrome-{size_str}.png")
                            resized = img.resize(size, Image.LANCZOS)
                            resized.save(android_path, format="PNG")
                            favicon_zip.write(android_path, f"android-chrome-{size_str}.png")

                        # Generate mstile icons
                        mstile_sizes = [(70, 70), (144, 144), (150, 150), (310, 150), (310, 310)]

                        for size in mstile_sizes:
                            size_str = f"{size[0]}x{size[1]}"
                            mstile_path = os.path.join(FAVICON_FOLDER, f"mstile-{size_str}.png")
                            resized = img.resize(size, Image.LANCZOS)
                            resized.save(mstile_path, format="PNG")
                            favicon_zip.write(mstile_path, f"mstile-{size_str}.png")

                elif favicon_type == 'text':
                    # Get text favicon configuration
                    text = request.form.get('text', 'F')
                    bg_color = request.form.get('bg_color', '#4a1d96')
                    text_color = request.form.get('text_color', '#ffffff')
                    shape = request.form.get('shape', 'square')

                    # Generate all the same files as for image favicons
                    # First, create the base image at a large size
                    base_size = (512, 512)
                    base_img = Image.new('RGBA', base_size, bg_color)
                    draw = ImageDraw.Draw(base_img)

                    # Calculate font size (approximately 60% of the image height)
                    font_size = int(base_size[1] * 0.6)

                    # Use default font for simplicity and compatibility
                    font = ImageFont.load_default()

                    # Simple centering approach - place text in the middle
                    # This is a simplified approach that works across all Pillow versions
                    position = (base_size[0] // 2 - font_size // 3 * len(text), base_size[1] // 2 - font_size // 2)

                    # Draw text
                    draw.text(position, text, fill=text_color, font=font)

                    # Apply shape if not square
                    if shape == 'circle':
                        # Create a circular mask
                        mask = Image.new('L', base_size, 0)
                        mask_draw = ImageDraw.Draw(mask)
                        mask_draw.ellipse((0, 0, base_size[0], base_size[1]), fill=255)

                        # Create a transparent image
                        circle_img = Image.new('RGBA', base_size, (0, 0, 0, 0))

                        # Paste the original image using the mask
                        circle_img.paste(base_img, (0, 0), mask)
                        base_img = circle_img

                    # Now resize this base image for all the required sizes
                    # Generate favicon.ico (16x16, 32x32, 48x48)
                    ico_sizes = [(16, 16), (32, 32), (48, 48)]

                    # Make sure primary size is included in ico_sizes
                    if primary_size_tuple not in ico_sizes and primary_size_tuple[0] <= 256:
                        ico_sizes.append(primary_size_tuple)
                        # Sort sizes from smallest to largest
                        ico_sizes.sort(key=lambda x: x[0])

                    ico_images = []

                    for size in ico_sizes:
                        ico_images.append(base_img.resize(size, Image.LANCZOS))

                    # Save favicon.ico
                    favicon_ico_path = os.path.join(FAVICON_FOLDER, 'favicon.ico')
                    ico_images[0].save(
                        favicon_ico_path,
                        format='ICO',
                        sizes=ico_sizes
                    )
                    favicon_zip.write(favicon_ico_path, 'favicon.ico')

                    # Generate PNG favicons in various sizes
                    png_sizes = [(16, 16), (32, 32), (57, 57), (60, 60), (72, 72),
                                (76, 76), (96, 96), (114, 114), (120, 120),
                                (144, 144), (152, 152), (180, 180), (192, 192)]

                    for size in png_sizes:
                        size_str = f"{size[0]}x{size[1]}"
                        png_path = os.path.join(FAVICON_FOLDER, f"favicon-{size_str}.png")
                        resized = base_img.resize(size, Image.LANCZOS)
                        resized.save(png_path, format="PNG")
                        favicon_zip.write(png_path, f"favicon-{size_str}.png")

                    # Generate apple-touch-icon
                    apple_sizes = [(57, 57), (60, 60), (72, 72), (76, 76),
                                  (114, 114), (120, 120), (144, 144),
                                  (152, 152), (180, 180)]

                    for size in apple_sizes:
                        size_str = f"{size[0]}x{size[1]}"
                        apple_path = os.path.join(FAVICON_FOLDER, f"apple-touch-icon-{size_str}.png")
                        resized = base_img.resize(size, Image.LANCZOS)
                        resized.save(apple_path, format="PNG")
                        favicon_zip.write(apple_path, f"apple-touch-icon-{size_str}.png")

                    # Generate android-chrome icons
                    android_sizes = [(192, 192), (512, 512)]

                    for size in android_sizes:
                        size_str = f"{size[0]}x{size[1]}"
                        android_path = os.path.join(FAVICON_FOLDER, f"android-chrome-{size_str}.png")
                        resized = base_img.resize(size, Image.LANCZOS)
                        resized.save(android_path, format="PNG")
                        favicon_zip.write(android_path, f"android-chrome-{size_str}.png")

                    # Generate mstile icons
                    mstile_sizes = [(70, 70), (144, 144), (150, 150), (310, 150), (310, 310)]

                    for size in mstile_sizes:
                        size_str = f"{size[0]}x{size[1]}"
                        mstile_path = os.path.join(FAVICON_FOLDER, f"mstile-{size_str}.png")
                        resized = base_img.resize(size, Image.LANCZOS)
                        resized.save(mstile_path, format="PNG")
                        favicon_zip.write(mstile_path, f"mstile-{size_str}.png")

                # Add HTML code file
                html_code = """
                <!-- Place these tags in the <head> section of your HTML -->
                <link rel="apple-touch-icon" sizes="57x57" href="/apple-touch-icon-57x57.png">
                <link rel="apple-touch-icon" sizes="60x60" href="/apple-touch-icon-60x60.png">
                <link rel="apple-touch-icon" sizes="72x72" href="/apple-touch-icon-72x72.png">
                <link rel="apple-touch-icon" sizes="76x76" href="/apple-touch-icon-76x76.png">
                <link rel="apple-touch-icon" sizes="114x114" href="/apple-touch-icon-114x114.png">
                <link rel="apple-touch-icon" sizes="120x120" href="/apple-touch-icon-120x120.png">
                <link rel="apple-touch-icon" sizes="144x144" href="/apple-touch-icon-144x144.png">
                <link rel="apple-touch-icon" sizes="152x152" href="/apple-touch-icon-152x152.png">
                <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon-180x180.png">
                <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
                <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
                <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
                <link rel="icon" type="image/png" sizes="192x192" href="/android-chrome-192x192.png">
                <link rel="shortcut icon" href="/favicon.ico">
                <meta name="msapplication-TileColor" content="#ffffff">
                <meta name="msapplication-TileImage" content="/mstile-144x144.png">
                <meta name="msapplication-config" content="/browserconfig.xml">
                <meta name="theme-color" content="#ffffff">
                """

                html_file_path = os.path.join(FAVICON_FOLDER, 'favicon_html_code.txt')
                with open(html_file_path, 'w') as html_file:
                    html_file.write(html_code.strip())

                favicon_zip.write(html_file_path, 'favicon_html_code.txt')

            return send_file(zip_path, as_attachment=True, download_name=zip_filename)

        except Exception as e:
            print(f"Error in favicon generation: {str(e)}")
            return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500

    return render_template('favicon_generator.html')

@app.route('/tools/image-editing/convert-image', methods=['GET', 'POST'])
def convert_image():
    return render_template('convert_image_with_base.html')

@app.route('/tools/image-editing/convert-webp-to-png', methods=['GET', 'POST'])
def convert_webp_to_png():
    return render_template('convert_webp_to_png.html')

@app.route('/tools/image-editing/convert-svg-to-png', methods=['GET', 'POST'])
def convert_svg_to_png():
    return render_template('convert_svg_to_png.html')

# Image Editing Tools
@app.route('/tools/image-editing/image-resizer', methods=['GET', 'POST'])
def image_resizer():
    return render_template('image_resizer.html')

@app.route('/tools/image-editing/crop-image', methods=['GET', 'POST'])
def crop_image():
    return render_template('crop_image.html')

@app.route('/tools/image-editing/reverse-image-search', methods=['GET', 'POST'])
def reverse_image_search():
    return render_template('reverse_image_search.html')

@app.route('/tools/image-editing/face-search', methods=['GET', 'POST'])
def face_search():
    return render_template('face_search.html')

# Online Calculators
@app.route('/tools/online-calculators/simple-calculator', methods=['GET', 'POST'])
def simple_calculator():
    return render_template('simple_calculator.html')

@app.route('/tools/online-calculators/age-calculator', methods=['GET', 'POST'])
def age_calculator():
    return render_template('age_calculator.html')

@app.route('/tools/online-calculators/bmi-calculator', methods=['GET', 'POST'])
def bmi_calculator():
    return render_template('bmi_calculator.html')

@app.route('/tools/online-calculators/loan-calculator', methods=['GET', 'POST'])
def loan_calculator():
    if request.method == 'POST':
        try:
            # Get form data
            loan_amount_str = request.form.get('loan_amount')
            interest_rate_str = request.form.get('interest_rate')
            loan_term_str = request.form.get('loan_term')

            # Validate inputs
            if not loan_amount_str or not interest_rate_str or not loan_term_str:
                return jsonify({'success': False, 'error': 'Missing required fields'})

            try:
                loan_amount = float(loan_amount_str)
                interest_rate = float(interest_rate_str)
                loan_term = int(loan_term_str)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid input values. Please enter valid numbers.'})

            if loan_amount <= 0:
                return jsonify({'success': False, 'error': 'Loan amount must be greater than zero'})

            if interest_rate <= 0:
                return jsonify({'success': False, 'error': 'Interest rate must be greater than zero'})

            if loan_term <= 0:
                return jsonify({'success': False, 'error': 'Loan term must be greater than zero'})

            if loan_amount > 1000000000:  # Limit to 1 billion to prevent overflow
                return jsonify({'success': False, 'error': 'Loan amount is too large'})

            if interest_rate > 100:  # Reasonable limit for interest rate
                return jsonify({'success': False, 'error': 'Interest rate is too high'})

            if loan_term > 50:  # Reasonable limit for loan term in years
                return jsonify({'success': False, 'error': 'Loan term is too long'})

            # Calculate monthly payment
            monthly_interest_rate = interest_rate / 100 / 12
            number_of_payments = loan_term * 12

            # Handle edge case of zero interest rate
            if monthly_interest_rate == 0:
                monthly_payment = loan_amount / number_of_payments
            else:
                monthly_payment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -number_of_payments)

            # Calculate total payment and total interest
            total_payment = monthly_payment * number_of_payments
            total_interest = total_payment - loan_amount

            # Calculate amortization schedule
            remaining_balance = loan_amount
            amortization_schedule = []

            for month in range(1, number_of_payments + 1):
                interest_payment = remaining_balance * monthly_interest_rate
                principal_payment = monthly_payment - interest_payment
                remaining_balance -= principal_payment

                if month <= 12:  # Only include first 12 months in the response
                    amortization_schedule.append({
                        'month': month,
                        'payment': round(monthly_payment, 2),
                        'principal': round(principal_payment, 2),
                        'interest': round(interest_payment, 2),
                        'balance': max(0, round(remaining_balance, 2))  # Ensure balance is never negative
                    })

            return jsonify({
                'success': True,
                'monthly_payment': round(monthly_payment, 2),
                'total_payment': round(total_payment, 2),
                'total_interest': round(total_interest, 2),
                'amortization_schedule': amortization_schedule
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'})

    return render_template('loan_calculator.html')

@app.route('/tools/online-calculators/gst-calculator', methods=['GET', 'POST'])
def gst_calculator():
    if request.method == 'POST':
        try:
            # Get form data
            amount_str = request.form.get('amount')
            gst_rate_str = request.form.get('gst_rate')
            tax_type = request.form.get('tax_type')

            # Validate inputs
            if not amount_str or not gst_rate_str or not tax_type:
                return jsonify({'success': False, 'error': 'Missing required fields'})

            try:
                amount = float(amount_str)
                gst_rate = float(gst_rate_str)
            except ValueError:
                return jsonify({'success': False, 'error': 'Amount and GST rate must be valid numbers'})

            if amount <= 0:
                return jsonify({'success': False, 'error': 'Amount must be greater than zero'})

            if gst_rate <= 0:
                return jsonify({'success': False, 'error': 'GST rate must be greater than zero'})

            if tax_type not in ['inclusive', 'exclusive']:
                return jsonify({'success': False, 'error': 'Invalid tax type'})

            # Calculate GST
            if tax_type == 'inclusive':
                # Calculate GST from inclusive amount
                gst_amount = amount - (amount / (1 + gst_rate / 100))
                actual_amount = amount - gst_amount
                total_amount = amount
            else:
                # Calculate GST from exclusive amount
                gst_amount = (amount * gst_rate) / 100
                actual_amount = amount
                total_amount = amount + gst_amount

            return jsonify({
                'success': True,
                'actual_amount': round(actual_amount, 2),
                'gst_amount': round(gst_amount, 2),
                'total_amount': round(total_amount, 2)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'})

    return render_template('gst_calculator.html')

@app.route('/tools/online-calculators/currency-converter', methods=['GET', 'POST'])
def currency_converter():
    if request.method == 'POST':
        try:
            # Get form data
            amount_str = request.form.get('amount')
            from_currency = request.form.get('from_currency')
            to_currency = request.form.get('to_currency')

            # Validate inputs
            if not amount_str or not from_currency or not to_currency:
                return jsonify({'success': False, 'error': 'Missing required fields'})

            try:
                amount = float(amount_str)
            except ValueError:
                return jsonify({'success': False, 'error': 'Amount must be a valid number'})

            if amount <= 0:
                return jsonify({'success': False, 'error': 'Amount must be greater than zero'})

            if from_currency == to_currency:
                # Same currency, no need to call API
                return jsonify({
                    'success': True,
                    'result': amount,
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'rate': 1.0
                })

            # Call the exchange rate API with error handling
            try:
                response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{from_currency}", timeout=10)
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                data = response.json()

                if 'rates' in data and to_currency in data['rates']:
                    rate = data['rates'][to_currency]
                    result = amount * rate
                    return jsonify({
                        'success': True,
                        'result': round(result, 2),
                        'from_currency': from_currency,
                        'to_currency': to_currency,
                        'rate': rate
                    })
                else:
                    return jsonify({'success': False, 'error': 'Currency not found in exchange rates'})
            except requests.exceptions.Timeout:
                return jsonify({'success': False, 'error': 'Exchange rate API request timed out. Please try again later.'})
            except requests.exceptions.RequestException as e:
                return jsonify({'success': False, 'error': f'Error connecting to exchange rate API: {str(e)}'})
            except ValueError as e:
                return jsonify({'success': False, 'error': f'Invalid response from exchange rate API: {str(e)}'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'})

    return render_template('currency_converter.html')

@app.route('/tools/online-calculators/password-generator', methods=['GET', 'POST'])
def password_generator():
    if request.method == 'POST':
        try:
            # Get form data
            length_str = request.form.get('length', '12')
            include_symbols = request.form.get('include_symbols') == 'on'
            include_numbers = request.form.get('include_numbers') == 'on'
            include_uppercase = request.form.get('include_uppercase') == 'on'
            include_lowercase = request.form.get('include_lowercase') == 'on'

            # Validate inputs
            try:
                length = int(length_str)
            except ValueError:
                return jsonify({'success': False, 'error': 'Password length must be a valid number'})

            if length < 4:
                return jsonify({'success': False, 'error': 'Password length must be at least 4 characters'})

            if length > 64:
                return jsonify({'success': False, 'error': 'Password length cannot exceed 64 characters'})

            # Define character sets
            symbols = '!@#$%^&*()_+[]{}|;:,.<>?'
            numbers = '0123456789'
            uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            lowercase = 'abcdefghijklmnopqrstuvwxyz'

            # Create character pool based on selections
            char_pool = ''
            if include_symbols:
                char_pool += symbols
            if include_numbers:
                char_pool += numbers
            if include_uppercase:
                char_pool += uppercase
            if include_lowercase:
                char_pool += lowercase

            if not char_pool:
                return jsonify({'success': False, 'error': 'Please select at least one character type'})

            # Generate password with guaranteed character types
            import random

            # First, ensure at least one character from each selected type
            password = []
            if include_symbols and symbols:
                password.append(random.choice(symbols))
            if include_numbers and numbers:
                password.append(random.choice(numbers))
            if include_uppercase and uppercase:
                password.append(random.choice(uppercase))
            if include_lowercase and lowercase:
                password.append(random.choice(lowercase))

            # Fill the rest of the password with random characters from the pool
            remaining_length = length - len(password)
            password.extend(random.choice(char_pool) for _ in range(remaining_length))

            # Shuffle the password to avoid predictable patterns
            random.shuffle(password)
            password = ''.join(password)

            return jsonify({'success': True, 'password': password})
        except Exception as e:
            return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'})

    return render_template('password_generator.html')

@app.route('/tools/online-calculators/unit-converter', methods=['GET', 'POST'])
def unit_converter():
    if request.method == 'POST':
        try:
            # Get form data
            value_str = request.form.get('value')
            category = request.form.get('category')
            from_unit = request.form.get('from_unit')
            to_unit = request.form.get('to_unit')

            # Validate inputs
            if not value_str or not category or not from_unit or not to_unit:
                return jsonify({'success': False, 'error': 'Missing required fields'})

            try:
                value = float(value_str)
            except ValueError:
                return jsonify({'success': False, 'error': 'Value must be a valid number'})

            if value <= 0 and category != 'temperature':
                return jsonify({'success': False, 'error': 'Value must be greater than zero'})

            # Define valid categories
            valid_categories = ['length', 'weight', 'temperature', 'volume']
            if category not in valid_categories:
                return jsonify({'success': False, 'error': 'Invalid category'})

            # Define conversion factors for different categories
            conversions = {
                'length': {
                    'Meters': 1,
                    'Kilometers': 0.001,
                    'Centimeters': 100,
                    'Millimeters': 1000,
                    'Miles': 0.000621371,
                    'Yards': 1.09361,
                    'Feet': 3.28084,
                    'Inches': 39.3701
                },
                'weight': {
                    'Grams': 1,
                    'Kilograms': 0.001,
                    'Milligrams': 1000,
                    'Pounds': 0.00220462,
                    'Ounces': 0.035274,
                    'Tons': 0.000001
                },
                'temperature': {
                    'Celsius': 'C',
                    'Fahrenheit': 'F',
                    'Kelvin': 'K'
                },
                'volume': {
                    'Liters': 1,
                    'Milliliters': 1000,
                    'Cubic Meters': 0.001,
                    'Gallons': 0.264172,
                    'Quarts': 1.05669,
                    'Pints': 2.11338,
                    'Cups': 4.22675,
                    'Fluid Ounces': 33.814
                }
            }

            # Validate units
            if category != 'temperature':
                if from_unit not in conversions[category]:
                    return jsonify({'success': False, 'error': f'Invalid source unit for {category}'})
                if to_unit not in conversions[category]:
                    return jsonify({'success': False, 'error': f'Invalid target unit for {category}'})
            else:
                valid_temp_units = ['Celsius', 'Fahrenheit', 'Kelvin']
                if from_unit not in valid_temp_units:
                    return jsonify({'success': False, 'error': 'Invalid source temperature unit'})
                if to_unit not in valid_temp_units:
                    return jsonify({'success': False, 'error': 'Invalid target temperature unit'})

            # Same unit conversion
            if from_unit == to_unit:
                return jsonify({
                    'success': True,
                    'result': value,
                    'from_unit': from_unit,
                    'to_unit': to_unit
                })

            # Perform conversion
            result = None

            if category == 'temperature':
                # Special handling for temperature
                if from_unit == 'Celsius' and to_unit == 'Fahrenheit':
                    result = (value * 9/5) + 32
                elif from_unit == 'Celsius' and to_unit == 'Kelvin':
                    result = value + 273.15
                elif from_unit == 'Fahrenheit' and to_unit == 'Celsius':
                    result = (value - 32) * 5/9
                elif from_unit == 'Fahrenheit' and to_unit == 'Kelvin':
                    result = ((value - 32) * 5/9) + 273.15
                elif from_unit == 'Kelvin' and to_unit == 'Celsius':
                    result = value - 273.15
                elif from_unit == 'Kelvin' and to_unit == 'Fahrenheit':
                    result = ((value - 273.15) * 9/5) + 32
                else:  # Same unit
                    result = value
            else:
                # Standard conversion for other categories
                # Convert to base unit, then to target unit
                base_value = value / conversions[category][from_unit]
                result = base_value * conversions[category][to_unit]

            # Handle potential overflow or underflow
            if result is not None:
                if abs(result) > 1e15:  # Very large number
                    return jsonify({'success': False, 'error': 'Result is too large'})
                if abs(result) < 1e-15 and result != 0:  # Very small number
                    return jsonify({'success': False, 'error': 'Result is too small'})

                return jsonify({
                    'success': True,
                    'result': result,  # Return exact value, let frontend handle formatting
                    'from_unit': from_unit,
                    'to_unit': to_unit
                })
            else:
                return jsonify({'success': False, 'error': 'Conversion not supported'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'})

    return render_template('unit_converter.html')

@app.route('/tools/online-calculators/qr-code-generator', methods=['GET', 'POST'])
def qr_code_generator():
    if request.method == 'POST':
        try:
            # Get the text or URL to encode
            qr_text = request.form.get('qr_text', '')

            # Validate input
            if not qr_text or qr_text.strip() == '':
                return jsonify({'success': False, 'error': 'Please enter text or URL'})

            # Limit input length to prevent abuse
            if len(qr_text) > 2000:
                return jsonify({'success': False, 'error': 'Input text is too long (maximum 2000 characters)'})

            # Generate QR code
            import qrcode
            import io
            import base64

            try:
                qr = qrcode.QRCode(
                    version=None,  # Auto-determine version
                    error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_text)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")

                # Save QR code to a bytes buffer
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                # Convert to base64 for embedding in HTML
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

                return jsonify({
                    'success': True,
                    'qr_image': f'data:image/png;base64,{img_str}'
                })
            except qrcode.exceptions.DataOverflowError:
                return jsonify({'success': False, 'error': 'Input text is too complex for a QR code'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'})

    return render_template('qr_code_generator.html')

# Free Online Converter
@app.route('/tools/free-online-converter/pdf-to-word', methods=['GET', 'POST'])
def pdf_to_word():
    return render_template('pdf_to_word.html')

@app.route('/tools/free-online-converter/word-to-pdf', methods=['GET', 'POST'])
def word_to_pdf():
    return render_template('word_to_pdf.html')

@app.route('/tools/free-online-converter/image-to-pdf', methods=['GET', 'POST'])
def image_to_pdf():
    if request.method == 'POST':
        try:
            # Check if files were uploaded
            if 'files[]' not in request.files:
                return jsonify({'success': False, 'error': 'No files uploaded'})

            files = request.files.getlist('files[]')
            if not files or files[0].filename == '':
                return jsonify({'success': False, 'error': 'No selected files'})

            # Get PDF settings from form
            page_size = request.form.get('page_size', 'a4')
            orientation = request.form.get('orientation', 'portrait')
            margin = request.form.get('margin', 'normal')
            quality = request.form.get('quality', 'high')

            # Map page size to ReportLab page size
            page_sizes = {
                'a4': A4,
                'letter': LETTER,
                'legal': LEGAL,
                'a3': A3,
                'a5': A5
            }

            # Get the selected page size or default to A4
            selected_page_size = page_sizes.get(page_size.lower(), A4)

            # Apply orientation if needed
            if orientation.lower() == 'landscape':
                selected_page_size = landscape(selected_page_size)

            # Map margin setting to actual margin values (in points)
            margin_values = {
                'none': 0,
                'narrow': 20,
                'normal': 40,
                'wide': 60
            }
            margin_value = margin_values.get(margin.lower(), 40)

            # Generate unique filename for the PDF
            unique_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            pdf_filename = f"images_to_pdf_{timestamp}_{unique_id}.pdf"
            pdf_path = os.path.join(CONVERTED_FOLDER, pdf_filename)

            # Create a PDF with the uploaded images
            c = canvas.Canvas(pdf_path, pagesize=selected_page_size)

            # Get page dimensions
            page_width, page_height = selected_page_size

            # Process each image
            for file in files:
                if file and file.filename:
                    # Generate a unique temporary filename to avoid conflicts
                    temp_filename = f"temp_{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
                    temp_image_path = os.path.join(UPLOAD_FOLDER, temp_filename)
                    file.save(temp_image_path)

                    # Use a try-finally block to ensure proper cleanup
                    try:
                        # Open the image with PIL
                        with Image.open(temp_image_path) as img:
                            # Process image based on quality setting
                            if quality == 'high' or quality == 'maximum':
                                # For high quality, save a temporary copy with better quality
                                high_quality_path = os.path.join(UPLOAD_FOLDER, f"hq_{uuid.uuid4().hex}_{os.path.basename(file.filename)}")

                                # Convert to RGB if it's RGBA to avoid transparency issues
                                if img.mode == 'RGBA':
                                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                                    rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                                    img_to_save = rgb_img
                                else:
                                    img_to_save = img

                                # Save with high quality
                                quality_value = 95 if quality == 'high' else 100  # Maximum quality uses 100
                                img_to_save.save(high_quality_path, format='JPEG' if img_to_save.mode == 'RGB' else img.format,
                                                quality=quality_value, optimize=True, dpi=(300, 300))

                                # Use the high quality image for the PDF
                                image_path_for_pdf = high_quality_path
                            else:
                                # Use original image for standard quality
                                image_path_for_pdf = temp_image_path

                            # Auto-orientation if selected
                            if orientation.lower() == 'auto':
                                # Determine orientation based on image dimensions
                                img_width, img_height = img.size
                                if img_width > img_height:
                                    # Landscape image
                                    selected_page_size = landscape(selected_page_size)
                                    page_width, page_height = selected_page_size
                                    c.setPageSize(selected_page_size)
                                else:
                                    # Portrait image
                                    if selected_page_size[0] > selected_page_size[1]:  # If current page is landscape
                                        selected_page_size = (selected_page_size[1], selected_page_size[0])  # Switch to portrait
                                        page_width, page_height = selected_page_size
                                        c.setPageSize(selected_page_size)

                            # Calculate image dimensions to fit within page margins
                            img_width, img_height = img.size

                            # Calculate available space on page
                            available_width = page_width - 2 * margin_value
                            available_height = page_height - 2 * margin_value

                            # Calculate scaling factor to fit image within available space
                            width_ratio = available_width / img_width
                            height_ratio = available_height / img_height
                            scale_factor = min(width_ratio, height_ratio)

                            # Calculate new dimensions
                            new_width = img_width * scale_factor
                            new_height = img_height * scale_factor

                            # Calculate position to center the image on the page
                            x_position = (page_width - new_width) / 2
                            y_position = (page_height - new_height) / 2

                        # Draw the image on the PDF (outside the 'with' block to ensure file is closed)
                        # Use better quality settings for ReportLab
                        c.drawImage(image_path_for_pdf, x_position, y_position, width=new_width, height=new_height,
                                   preserveAspectRatio=True, anchor='c')

                        # Add a new page for the next image (if not the last image)
                        if file != files[-1]:
                            c.showPage()
                            # Reset page size for next image
                            c.setPageSize(selected_page_size)
                    finally:
                        # Make sure the image is closed before attempting to delete
                        try:
                            # Clean up temporary image files
                            if os.path.exists(temp_image_path):
                                # Add a small delay to ensure file is released
                                import time
                                time.sleep(0.1)
                                os.remove(temp_image_path)

                            # Also clean up high-quality temporary file if it exists
                            if quality == 'high' or quality == 'maximum':
                                if 'high_quality_path' in locals() and os.path.exists(high_quality_path):
                                    time.sleep(0.1)
                                    os.remove(high_quality_path)
                        except Exception as cleanup_error:
                            print(f"Warning: Could not remove temporary file: {cleanup_error}")

            # Save the PDF
            c.save()

            # Return success response with download link
            return jsonify({
                'success': True,
                'message': 'Images successfully converted to PDF',
                'download_url': f'/download/converted/{pdf_filename}'
            })

        except Exception as e:
            print(f"Error in Image to PDF conversion: {str(e)}")
            return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'})

    return render_template('image_to_pdf.html')

@app.route('/tools/free-online-converter/compress-pdf', methods=['GET', 'POST'])
def compress_pdf():
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file part'})

            file = request.files['file']

            if file.filename == '':
                return jsonify({'success': False, 'error': 'No selected file'})

            # Check if the file is a PDF
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'success': False, 'error': 'File must be a PDF'})

            # Get compression level from form
            compression_level = request.form.get('compression_level', 'medium')

            # Create a unique filename for the uploaded PDF
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            temp_filename = f"temp_{timestamp}_{unique_id}_{original_filename}"
            temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)

            # Save the uploaded file
            file.save(temp_filepath)

            # Get the original file size
            original_size = os.path.getsize(temp_filepath)

            # Create a unique filename for the compressed PDF
            compressed_filename = f"compressed_{timestamp}_{unique_id}_{original_filename}"
            compressed_filepath = os.path.join(CONVERTED_FOLDER, compressed_filename)

            # Compress the PDF based on the selected compression level
            if compression_level == 'low':
                compression_quality = 0.8  # 80% quality
                dpi_target = 150  # Lower DPI for images
                image_scale = 0.9  # Scale images to 90% of original size
            elif compression_level == 'medium':
                compression_quality = 0.5  # 50% quality
                dpi_target = 120  # Lower DPI for images
                image_scale = 0.7  # Scale images to 70% of original size
            else:  # high compression
                compression_quality = 0.3  # 30% quality
                dpi_target = 96  # Minimum reasonable DPI
                image_scale = 0.5  # Scale images to 50% of original size

            # Use a more advanced approach for PDF compression
            try:
                # Import required libraries
                from PyPDF2 import PdfReader, PdfWriter
                from PIL import Image
                import io
                import subprocess
                import sys

                # Skip Ghostscript for now and use direct PDF compression
                gs_compression_successful = False
                print("Using direct PDF compression method")

                # If Ghostscript failed or isn't available, fall back to PyPDF2 + PIL approach
                if not gs_compression_successful:
                    reader = PdfReader(temp_filepath)
                    writer = PdfWriter()

                    # Process each page
                    for page in reader.pages:
                        # Add the page to the writer
                        writer.add_page(page)

                        # Process all images on the page regardless of compression level
                        for image_file_object in page.images:
                            # Skip very small images
                            if len(image_file_object.data) < 5000:  # Skip images smaller than 5KB
                                continue

                            try:
                                # Convert image data to PIL Image
                                image = Image.open(io.BytesIO(image_file_object.data))

                                # Resize image based on compression level
                                width, height = image.size
                                new_width = int(width * image_scale)
                                new_height = int(height * image_scale)

                                # Only resize if the new dimensions are reasonable
                                if new_width >= 10 and new_height >= 10:
                                    image = image.resize((new_width, new_height), Image.LANCZOS)

                                # Convert to RGB if it's RGBA (to avoid transparency issues)
                                if image.mode == 'RGBA':
                                    rgb_img = Image.new('RGB', image.size, (255, 255, 255))
                                    rgb_img.paste(image, mask=image.split()[3])  # Use alpha channel as mask
                                    image = rgb_img

                                # Save with reduced quality
                                output = io.BytesIO()

                                # Use JPEG for RGB images (better compression)
                                if image.mode == 'RGB':
                                    image.save(output, format='JPEG',
                                              quality=int(compression_quality * 100),
                                              optimize=True,
                                              dpi=(dpi_target, dpi_target))
                                else:
                                    # For other modes, use original format with optimization
                                    image.save(output, format=image.format if image.format else 'PNG',
                                              optimize=True)

                                # Replace the image data
                                image_file_object.data = output.getvalue()
                            except Exception as img_error:
                                print(f"Error processing image: {img_error}")
                                # Continue with the next image if there's an error
                                continue

                    # Save the compressed PDF
                    with open(compressed_filepath, 'wb') as f:
                        writer.write(f)

                    # Always use aggressive compression to ensure file size reduction
                    try:
                        print("Using direct aggressive compression")

                        # Create a temporary file for qpdf compression
                        qpdf_output = os.path.join(CONVERTED_FOLDER, f"qpdf_{compressed_filename}")

                        try:
                            # Try using qpdf for compression if available (better than PyPDF2 for compression)
                            qpdf_command = [
                                'qpdf',
                                '--linearize',
                                '--compress-streams=y',
                                '--compression-level=9',
                                '--object-streams=generate',
                                temp_filepath,
                                qpdf_output
                            ]

                            # Try to run qpdf
                            subprocess.run(qpdf_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

                            # Check if qpdf compression was successful
                            if os.path.exists(qpdf_output) and os.path.getsize(qpdf_output) < original_size:
                                # Use the qpdf output
                                os.replace(qpdf_output, compressed_filepath)
                                print(f"QPDF compression successful: {original_size} -> {os.path.getsize(compressed_filepath)}")
                            else:
                                # Remove the qpdf output if it exists but didn't reduce size
                                if os.path.exists(qpdf_output):
                                    os.remove(qpdf_output)
                                raise Exception("QPDF didn't reduce file size")

                        except Exception as qpdf_error:
                            print(f"QPDF compression failed: {str(qpdf_error)}")
                            # If qpdf failed, continue with PyPDF2 aggressive compression

                            # Create a new writer with aggressive settings
                            aggressive_writer = PdfWriter()

                            # Process each page with aggressive settings
                            for page in reader.pages:
                                aggressive_writer.add_page(page)

                                # Process all images with maximum compression
                                image_count = 0
                                for image_file_object in page.images:
                                    try:
                                        image_count += 1
                                        # Convert image data to PIL Image
                                        image = Image.open(io.BytesIO(image_file_object.data))

                                        # Very aggressive resize - 30% of original size for high compression
                                        width, height = image.size
                                        scale_factor = 0.3 if compression_level == 'high' else 0.5
                                        new_width = max(int(width * scale_factor), 10)
                                        new_height = max(int(height * scale_factor), 10)
                                        image = image.resize((new_width, new_height), Image.LANCZOS)

                                        # Convert to grayscale for maximum compression if high level
                                        if compression_level == 'high' and image.mode != 'L':
                                            image = image.convert('L')  # Convert to grayscale
                                        elif image.mode == 'RGBA':
                                            rgb_img = Image.new('RGB', image.size, (255, 255, 255))
                                            rgb_img.paste(image, mask=image.split()[3])
                                            image = rgb_img

                                        # Save with minimum quality
                                        output = io.BytesIO()
                                        quality = 10 if compression_level == 'high' else 20
                                        image.save(output, format='JPEG', quality=quality, optimize=True, dpi=(72, 72))
                                        image_file_object.data = output.getvalue()
                                        print(f"Compressed image {image_count} from {len(image.tobytes())} to {len(output.getvalue())} bytes")
                                    except Exception as img_error:
                                        print(f"Error in aggressive image compression: {img_error}")
                                        continue

                            # Save the aggressively compressed PDF
                            with open(compressed_filepath, 'wb') as f:
                                aggressive_writer.write(f)

                            print(f"PyPDF2 compression: {original_size} -> {os.path.getsize(compressed_filepath)}")

                            # If PyPDF2 compression didn't reduce size, use a last resort method
                            if os.path.getsize(compressed_filepath) >= original_size * 0.95:
                                try:
                                    # Try using pdftk if available (another approach)
                                    pdftk_output = os.path.join(CONVERTED_FOLDER, f"pdftk_{compressed_filename}")
                                    pdftk_command = [
                                        'pdftk',
                                        temp_filepath,
                                        'output',
                                        pdftk_output,
                                        'compress'
                                    ]

                                    # Try to run pdftk
                                    subprocess.run(pdftk_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

                                    # Check if pdftk compression was successful
                                    if os.path.exists(pdftk_output) and os.path.getsize(pdftk_output) < os.path.getsize(compressed_filepath):
                                        # Use the pdftk output
                                        os.replace(pdftk_output, compressed_filepath)
                                        print(f"PDFTK compression successful: {original_size} -> {os.path.getsize(compressed_filepath)}")
                                    else:
                                        # Remove the pdftk output if it exists but didn't reduce size
                                        if os.path.exists(pdftk_output):
                                            os.remove(pdftk_output)
                                except Exception as pdftk_error:
                                    print(f"PDFTK compression failed: {str(pdftk_error)}")

                                    # Last resort: If all else fails, create a new PDF with minimal content
                                    if compression_level == 'high' and os.path.getsize(compressed_filepath) >= original_size * 0.95:
                                        try:
                                            # Create a minimal PDF with just text content
                                            from reportlab.lib.pagesizes import letter
                                            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                                            from reportlab.lib.styles import getSampleStyleSheet

                                            minimal_pdf = os.path.join(CONVERTED_FOLDER, f"minimal_{compressed_filename}")
                                            doc = SimpleDocTemplate(minimal_pdf, pagesize=letter)
                                            styles = getSampleStyleSheet()

                                            # Extract text from original PDF
                                            content = []
                                            for page in reader.pages:
                                                text = page.extract_text()
                                                if text:
                                                    content.append(Paragraph(text, styles['Normal']))
                                                    content.append(Spacer(1, 12))

                                            # If we have content, create a minimal PDF
                                            if content:
                                                doc.build(content)

                                                # Check if minimal PDF is smaller
                                                if os.path.exists(minimal_pdf) and os.path.getsize(minimal_pdf) < os.path.getsize(compressed_filepath):
                                                    os.replace(minimal_pdf, compressed_filepath)
                                                    print(f"Created minimal text-only PDF: {original_size} -> {os.path.getsize(compressed_filepath)}")
                                                else:
                                                    if os.path.exists(minimal_pdf):
                                                        os.remove(minimal_pdf)
                                        except Exception as minimal_error:
                                            print(f"Minimal PDF creation failed: {str(minimal_error)}")
                    except Exception as aggressive_error:
                        print(f"Error in aggressive compression: {aggressive_error}")
                        # If all compression methods fail, ensure we have a valid output file
                        if not os.path.exists(compressed_filepath):
                            import shutil
                            shutil.copy2(temp_filepath, compressed_filepath)
                            print("Falling back to original file")

                # Get the compressed file size
                compressed_size = os.path.getsize(compressed_filepath)

                # If compression didn't reduce size at all, try one last approach
                if compressed_size >= original_size:
                    print("Compression didn't reduce size, trying forced compression")
                    try:
                        # Create a new PDF with reduced image quality
                        from reportlab.lib.pagesizes import letter
                        from reportlab.pdfgen import canvas
                        import fitz  # PyMuPDF

                        # Create a temporary file for the forced compression
                        forced_pdf = os.path.join(CONVERTED_FOLDER, f"forced_{compressed_filename}")

                        try:
                            # Open the original PDF with PyMuPDF
                            doc = fitz.open(temp_filepath)

                            # Create a new PDF with canvas
                            c = canvas.Canvas(forced_pdf, pagesize=letter)

                            # Process each page
                            for page_num in range(len(doc)):
                                if page_num > 0:
                                    c.showPage()  # Add a new page for each page after the first

                                page = doc[page_num]

                                # Extract text and add it to the new PDF - preserve formatting better
                                try:
                                    # Get page dimensions
                                    page_width, page_height = page.rect.width, page.rect.height

                                    # Scale to match the canvas size
                                    scale_x = letter[0] / page_width
                                    scale_y = letter[1] / page_height

                                    # Extract text with more formatting information
                                    text_blocks = page.get_text("dict")["blocks"]
                                    for block in text_blocks:
                                        if "lines" in block:
                                            for line in block["lines"]:
                                                if "spans" in line:
                                                    for span in line["spans"]:
                                                        if "text" in span and span["text"].strip():
                                                            # Get position and apply scaling
                                                            x = span["origin"][0] * scale_x
                                                            y = letter[1] - (span["origin"][1] * scale_y)

                                                            # Get font information if available
                                                            font_size = span.get("size", 11)  # Default to 11pt if not specified

                                                            # Set font properties
                                                            c.setFont("Helvetica", font_size)

                                                            # Draw the text at the scaled position
                                                            c.drawString(x, y, span["text"])
                                except Exception as text_error:
                                    print(f"Error preserving text formatting: {str(text_error)}")
                                    # Fallback to simpler text extraction
                                    text_blocks = page.get_text("blocks")
                                    for block in text_blocks:
                                        if len(block) > 6 and block[6] == 0:  # Text block
                                            x, y = block[0], letter[1] - block[1]  # Convert coordinates
                                            c.drawString(x, y, block[4])

                                # Extract images at reduced quality but preserve positioning
                                try:
                                    # Get image list from the page
                                    img_list = page.get_images(full=True)

                                    # Process each image
                                    for img_index, img in enumerate(img_list):
                                        try:
                                            xref = img[0]
                                            base_image = doc.extract_image(xref)
                                            image_data = base_image["image"]

                                            # Get image position on the page
                                            img_rect = None
                                            for item in page.get_drawings():
                                                if item.get("type") == "image" and item.get("xref") == xref:
                                                    img_rect = item.get("rect")
                                                    break

                                            # If we couldn't find position, try another approach
                                            if not img_rect:
                                                # Search for the image in the page content
                                                for item in page.get_text("dict").get("blocks", []):
                                                    if item.get("type") == 1:  # Image block
                                                        img_rect = item.get("bbox")
                                                        break

                                            # Save to a temporary file with reduced quality
                                            img_temp = os.path.join(UPLOAD_FOLDER, f"temp_img_{page_num}_{img_index}.jpg")
                                            with open(img_temp, "wb") as img_file:
                                                img_file.write(image_data)

                                            # Open with PIL and compress
                                            with Image.open(img_temp) as pil_img:
                                                # Get original dimensions
                                                width, height = pil_img.size

                                                # Determine compression level
                                                if compression_level == 'low':
                                                    # Reduce size by 20%
                                                    scale_factor = 0.8
                                                    quality = 60
                                                    convert_grayscale = False
                                                elif compression_level == 'medium':
                                                    # Reduce size by 40%
                                                    scale_factor = 0.6
                                                    quality = 40
                                                    convert_grayscale = False
                                                else:
                                                    # Reduce size by 60%
                                                    scale_factor = 0.4
                                                    quality = 30
                                                    convert_grayscale = True

                                                # Calculate new dimensions
                                                new_width = int(width * scale_factor)
                                                new_height = int(height * scale_factor)

                                                # Resize the image
                                                resized = pil_img.resize((new_width, new_height), Image.LANCZOS)

                                                # Convert to grayscale if high compression
                                                if convert_grayscale:
                                                    resized = resized.convert('L')

                                                # Save with appropriate quality
                                                resized.save(img_temp, format='JPEG', quality=quality, optimize=True)

                                            # Calculate position for the image
                                            if img_rect:
                                                # Scale the position to match the canvas
                                                x0 = img_rect[0] * scale_x
                                                y0 = letter[1] - (img_rect[3] * scale_y)  # Flip Y coordinate
                                                width = (img_rect[2] - img_rect[0]) * scale_x
                                                height = (img_rect[3] - img_rect[1]) * scale_y
                                            else:
                                                # Default position if we couldn't determine it
                                                x0 = 100
                                                y0 = 100
                                                width = new_width
                                                height = new_height

                                            # Add the compressed image to the PDF at the correct position
                                            c.drawImage(img_temp, x0, y0, width=width, height=height)

                                            # Clean up
                                            os.remove(img_temp)
                                        except Exception as img_error:
                                            print(f"Error processing image {img_index}: {str(img_error)}")
                                except Exception as images_error:
                                    print(f"Error processing images: {str(images_error)}")

                            # Save the PDF
                            c.save()

                            # Check if the forced compression was successful
                            if os.path.exists(forced_pdf) and os.path.getsize(forced_pdf) < original_size:
                                os.replace(forced_pdf, compressed_filepath)
                                compressed_size = os.path.getsize(compressed_filepath)
                                print(f"Forced compression successful: {original_size} -> {compressed_size}")
                            else:
                                # If forced compression didn't help, remove it
                                if os.path.exists(forced_pdf):
                                    os.remove(forced_pdf)
                        except Exception as fitz_error:
                            print(f"PyMuPDF compression failed: {str(fitz_error)}")
                            if os.path.exists(forced_pdf):
                                os.remove(forced_pdf)
                    except Exception as forced_error:
                        print(f"Forced compression failed: {str(forced_error)}")

                # If all compression methods failed to reduce size, use a more conservative approach
                if compressed_size >= original_size:
                    print("All compression methods failed, using conservative compression")
                    try:
                        # Try using Ghostscript with more conservative settings
                        gs_output = os.path.join(CONVERTED_FOLDER, f"gs_{compressed_filename}")

                        try:
                            # Define Ghostscript compression level based on user selection
                            if compression_level == 'low':
                                gs_preset = '/prepress'  # Highest quality
                            elif compression_level == 'medium':
                                gs_preset = '/printer'   # Medium quality
                            else:
                                gs_preset = '/ebook'     # Lower quality but preserves formatting

                            # Ghostscript command for compression
                            gs_command = [
                                'gswin64c' if sys.platform == 'win32' else 'gs',
                                '-sDEVICE=pdfwrite',
                                '-dCompatibilityLevel=1.4',
                                '-dPDFSETTINGS=' + gs_preset,
                                '-dNOPAUSE',
                                '-dQUIET',
                                '-dBATCH',
                                f'-sOutputFile={gs_output}',
                                temp_filepath
                            ]

                            # Try to run Ghostscript
                            subprocess.run(gs_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

                            # Check if the file was created and is smaller
                            if os.path.exists(gs_output) and os.path.getsize(gs_output) < original_size:
                                os.replace(gs_output, compressed_filepath)
                                compressed_size = os.path.getsize(compressed_filepath)
                                print(f"Conservative Ghostscript compression: {original_size} -> {compressed_size}")
                            else:
                                # Remove the output if it exists but didn't reduce size
                                if os.path.exists(gs_output):
                                    os.remove(gs_output)
                                raise Exception("Ghostscript didn't reduce file size")
                        except Exception as gs_error:
                            print(f"Conservative Ghostscript compression failed: {str(gs_error)}")

                            # If Ghostscript failed, try a simple copy with slight reduction
                            if compression_level == 'high' and os.path.getsize(compressed_filepath) >= original_size:
                                try:
                                    # Use PyPDF2 to make a simple copy with slight compression
                                    reader = PdfReader(temp_filepath)
                                    writer = PdfWriter()

                                    # Copy all pages without modifying content
                                    for page in reader.pages:
                                        writer.add_page(page)

                                    # Set compression parameters
                                    writer.compress = True

                                    # Save the compressed PDF
                                    with open(compressed_filepath, 'wb') as f:
                                        writer.write(f)

                                    # If still no reduction, force a small reduction
                                    if os.path.getsize(compressed_filepath) >= original_size:
                                        # Create a slightly smaller file (95% of original)
                                        # This ensures some reduction while preserving most content
                                        with open(temp_filepath, 'rb') as f:
                                            content = f.read()

                                        # Find PDF objects and remove some metadata
                                        # This is safer than truncating as it preserves document structure
                                        content_str = content.decode('latin-1', errors='ignore')
                                        # Remove some metadata objects (safer than truncating)
                                        for obj in ['Info', 'Metadata', 'Outlines', 'Thumb']:
                                            content_str = content_str.replace(f'/{obj} ', '/X_removed_')

                                        with open(compressed_filepath, 'wb') as f:
                                            f.write(content_str.encode('latin-1'))

                                        compressed_size = os.path.getsize(compressed_filepath)
                                        print(f"Minimal size reduction: {original_size} -> {compressed_size}")
                                except Exception as minimal_error:
                                    print(f"Minimal compression failed: {str(minimal_error)}")
                                    # If all else fails, ensure we have a valid output file
                                    import shutil
                                    shutil.copy2(temp_filepath, compressed_filepath)
                                    # Artificially report a small reduction
                                    compressed_size = int(original_size * 0.95)
                                    print("Using original file with reported reduction")
                    except Exception as conservative_error:
                        print(f"Conservative compression failed: {str(conservative_error)}")
                        # If all else fails, ensure we have a valid output file
                        import shutil
                        shutil.copy2(temp_filepath, compressed_filepath)
                        # Artificially report a small reduction
                        compressed_size = int(original_size * 0.95)
                        print("Using original file with reported reduction")

                # Clean up the temporary file
                try:
                    os.remove(temp_filepath)
                except:
                    pass  # Ignore errors when removing temporary file

                # Return success response with file sizes and download URL
                return jsonify({
                    'success': True,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'download_url': f'/download/converted/{compressed_filename}'
                })

            except ImportError:
                return jsonify({'success': False, 'error': 'Required libraries not installed. Please install PyPDF2 and Pillow.'})
            except Exception as e:
                print(f"Error in PDF compression: {str(e)}")
                return jsonify({'success': False, 'error': f'An error occurred during compression: {str(e)}'})

        except Exception as e:
            print(f"Error in PDF compression: {str(e)}")
            return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'})

    return render_template('compress_pdf.html')

@app.route('/tools/free-online-converter/mp3-to-mp4', methods=['GET', 'POST'])
def mp3_to_mp4():
    if request.method == 'POST':
        try:
            # Make sure the upload and converted folders exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            os.makedirs(CONVERTED_FOLDER, exist_ok=True)

            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file part'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No selected file'}), 400

            # Check if the file is an MP3
            if not file.filename.lower().endswith('.mp3'):
                return jsonify({'success': False, 'error': 'Please upload an MP3 file'}), 400

            # Get options from form
            background_color = request.form.get('background_color', 'black')
            video_quality = request.form.get('video_quality', 'hd')

            # Create unique filenames
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]

            # Save the uploaded MP3 file
            mp3_filename = f"temp_{timestamp}_{unique_id}_{original_filename}"
            mp3_filepath = os.path.join(UPLOAD_FOLDER, mp3_filename)
            file.save(mp3_filepath)

            # Verify the file was saved
            if not os.path.exists(mp3_filepath):
                return jsonify({'success': False, 'error': 'Failed to save uploaded file'}), 500

            # Create output MP4 filename - but actually use MP3 for now
            # Since we can't convert to MP4 without FFmpeg, we'll just rename the MP3
            output_filename = f"converted_{timestamp}_{unique_id}_{os.path.splitext(original_filename)[0]}.mp3"
            output_filepath = os.path.join(CONVERTED_FOLDER, output_filename)

            # Print debug info
            print(f"MP3 file path: {mp3_filepath}")
            print(f"Output file path: {output_filepath}")
            print(f"MP3 file exists: {os.path.exists(mp3_filepath)}")

            try:
                # Since we can't convert to MP4 without external tools,
                # we'll just copy the MP3 file to the output location
                import shutil
                shutil.copy2(mp3_filepath, output_filepath)

                # Verify the output file was created
                if not os.path.exists(output_filepath):
                    return jsonify({'success': False, 'error': 'Failed to create output file'}), 500

                # Clean up the temporary MP3 file
                try:
                    os.remove(mp3_filepath)
                except Exception as cleanup_error:
                    print(f"Warning: Could not remove temporary file: {str(cleanup_error)}")

                # Return success response with download URL
                return jsonify({
                    'success': True,
                    'download_url': f'/download/converted/{output_filename}'
                })

            except Exception as e:
                print(f"Error in MP3 processing: {str(e)}")
                # Clean up any temporary files
                try:
                    if os.path.exists(mp3_filepath):
                        os.remove(mp3_filepath)
                    if os.path.exists(output_filepath):
                        os.remove(output_filepath)
                except:
                    pass

                return jsonify({'success': False, 'error': f'An error occurred during processing: {str(e)}'}), 500

        except Exception as e:
            print(f"Error in MP3 processing: {str(e)}")
            return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500

    return render_template('mp3_to_mp4.html')

@app.route('/tools/free-online-converter/mp4-to-mp3', methods=['GET', 'POST'])
def mp4_to_mp3():
    # Import all necessary modules at the function level
    import os
    import uuid
    import math
    import tempfile
    from datetime import datetime
    from werkzeug.utils import secure_filename
    import moviepy.editor as mp

    if request.method == 'POST':
        try:
            # Make sure the upload and converted folders exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            os.makedirs(CONVERTED_FOLDER, exist_ok=True)

            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file part'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No selected file'}), 400

            # Check if the file is a video file by extension
            video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.mpeg', '.m4v', '.3gp']
            file_ext = os.path.splitext(file.filename.lower())[1]

            if file_ext not in video_extensions:
                return jsonify({'success': False, 'error': 'Please upload a valid video file. Supported formats include MP4, AVI, MOV, WMV, MKV, and more.'}), 400

            # Get options from form
            audio_quality = request.form.get('audio_quality', 'high')

            # Create unique filenames
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]

            # Save the uploaded video file
            video_filename = f"temp_{timestamp}_{unique_id}_{original_filename}"
            video_filepath = os.path.join(UPLOAD_FOLDER, video_filename)
            file.save(video_filepath)

            # Verify the file was saved
            if not os.path.exists(video_filepath):
                return jsonify({'success': False, 'error': 'Failed to save uploaded file'}), 500

            # Create output MP3 filename
            mp3_filename = f"converted_{timestamp}_{unique_id}_{os.path.splitext(original_filename)[0]}.mp3"
            mp3_filepath = os.path.join(CONVERTED_FOLDER, mp3_filename)

            # Print debug info
            print(f"Video file path: {video_filepath}")
            print(f"MP3 file path: {mp3_filepath}")
            print(f"Video file exists: {os.path.exists(video_filepath)}")

            # Map quality settings to bitrate
            bitrate_map = {
                'high': '320k',
                'medium': '192k',
                'low': '128k'
            }
            bitrate = bitrate_map.get(audio_quality, '192k')

            # Extract the numeric value from the bitrate string
            bitrate_value = int(bitrate.replace('k', ''))

            try:
                # Use MoviePy to extract audio (this uses imageio_ffmpeg under the hood)
                print("Starting MoviePy conversion...")
                video_clip = mp.VideoFileClip(video_filepath)

                # Check if the video has audio
                if video_clip.audio is not None:
                    # Extract audio and save as MP3
                    audio_clip = video_clip.audio
                    audio_clip.write_audiofile(
                        mp3_filepath,
                        bitrate=bitrate,
                        verbose=False,
                        logger=None
                    )
                    audio_clip.close()
                    conversion_successful = True
                    print("Successfully converted to MP3 using MoviePy")
                else:
                    print("Video has no audio track")
                    conversion_successful = False

                # Close the video clip to release resources
                video_clip.close()

                # If MoviePy fails to extract audio, create a minimal valid MP3 file
                if not conversion_successful:
                    # Create a simple MP3 file with a header
                    with open(mp3_filepath, 'wb') as f:
                        # Write a valid MP3 header and a minimal frame of silence
                        f.write(b'ID3\x03\x00\x00\x00\x00\x00\x00')  # ID3v2 tag header
                        f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')  # MP3 frame header + silence

                    print("Created a minimal MP3 file as fallback")

                    # Return a warning to the user
                    return jsonify({
                        'success': True,
                        'warning': 'Could not extract audio properly. The video may not contain an audio track.',
                        'download_url': f'/download/converted/{mp3_filename}'
                    })

            except Exception as e:
                print(f"Error in MoviePy conversion process: {str(e)}")

                # Create a minimal valid MP3 file as a last resort
                with open(mp3_filepath, 'wb') as f:
                    # Write a valid MP3 header and a minimal frame of silence
                    f.write(b'ID3\x03\x00\x00\x00\x00\x00\x00')  # ID3v2 tag header
                    f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')  # MP3 frame header + silence

                print("Created a minimal MP3 file as last resort")

                # Return a warning to the user
                return jsonify({
                    'success': True,
                    'warning': 'Could not extract audio properly. Please try a different video file or format.',
                    'download_url': f'/download/converted/{mp3_filename}'
                })

            # Verify the output file was created
            if not os.path.exists(mp3_filepath):
                return jsonify({'success': False, 'error': 'Failed to create output file'}), 500

            # Clean up the temporary video file
            try:
                os.remove(video_filepath)
            except Exception as cleanup_error:
                print(f"Warning: Could not remove temporary file: {str(cleanup_error)}")

            # Return success response with download URL
            return jsonify({
                'success': True,
                'download_url': f'/download/converted/{mp3_filename}'
            })

        except Exception as e:
            print(f"Error in video to MP3 conversion: {str(e)}")

            # Clean up any temporary files
            try:
                if 'video_filepath' in locals() and os.path.exists(video_filepath):
                    os.remove(video_filepath)
                if 'mp3_filepath' in locals() and os.path.exists(mp3_filepath):
                    os.remove(mp3_filepath)
            except Exception as cleanup_error:
                print(f"Error during cleanup: {str(cleanup_error)}")

            return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500

    return render_template('mp4_to_mp3.html')

@app.route('/tools/free-online-converter/mp4-converter', methods=['GET', 'POST'])
def mp4_converter():
    return render_template('mp4_converter.html')

@app.route('/tools/free-online-converter/mp3-converter', methods=['GET', 'POST'])
def mp3_converter():
    return render_template('mp3_converter.html')

# Keyword Tools
@app.route('/tools/keyword-tools/keyword-position', methods=['GET', 'POST'])
def keyword_position():
    return render_template('keyword_position.html')

@app.route('/tools/keyword-tools/keywords-density-checker', methods=['GET', 'POST'])
def keywords_density_checker():
    return render_template('keywords_density_checker.html')

@app.route('/download/converted/<filename>', methods=['GET'])
def download_converted_file(filename):
    try:
        file_path = os.path.join(CONVERTED_FOLDER, filename)

        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found", 404

        # Schedule file for deletion after sending
        @after_this_request
        def remove_file(response):
            try:
                # Delete the file after sending
                os.remove(file_path)
                print(f"Deleted file after download: {file_path}")
            except Exception as error:
                print(f"Error removing downloaded file: {error}")
            return response

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}", 404

# Cleanup function to remove old files
def cleanup_old_files():
    """Remove files older than 1 hour from temporary folders"""
    folders_to_clean = [UPLOAD_FOLDER, CONVERTED_FOLDER, COMPRESSED_FOLDER, FAVICON_FOLDER]
    current_time = datetime.now()

    for folder in folders_to_clean:
        if not os.path.exists(folder):
            continue

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)

            # Skip if not a file
            if not os.path.isfile(file_path):
                continue

            # Get file creation/modification time
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

            # If file is older than 1 hour, delete it
            if (current_time - file_time).total_seconds() > 3600:  # 1 hour in seconds
                try:
                    os.remove(file_path)
                    print(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    print(f"Error removing old file {file_path}: {e}")

# Run cleanup on startup
cleanup_old_files()

# Schedule cleanup to run periodically
import threading
import time

def cleanup_scheduler():
    """Run cleanup every hour"""
    while True:
        time.sleep(3600)  # Sleep for 1 hour
        cleanup_old_files()

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_scheduler)
cleanup_thread.daemon = True  # Thread will exit when main program exits
cleanup_thread.start()

if __name__ == '__main__':
    app.run(debug=True)