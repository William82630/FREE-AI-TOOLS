from flask import Flask, render_template, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
import os
import random
import io
import base64
import qrcode
import zipfile
from datetime import datetime, timedelta

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
    return render_template('image_to_pdf.html')

@app.route('/tools/free-online-converter/compress-pdf', methods=['GET', 'POST'])
def compress_pdf():
    return render_template('compress_pdf.html')

@app.route('/tools/free-online-converter/mp3-to-mp4', methods=['GET', 'POST'])
def mp3_to_mp4():
    return render_template('mp3_to_mp4.html')

@app.route('/tools/free-online-converter/mp4-to-mp3', methods=['GET', 'POST'])
def mp4_to_mp3():
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

if __name__ == '__main__':
    app.run(debug=True)