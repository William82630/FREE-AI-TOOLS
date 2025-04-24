# FREE AI TOOLS

A collection of free AI-powered tools, including image editing, calculators, and online converters.

## Tools Available

### Image Editing Tools
- Compress Image
- Favicon Generator
- Convert Image Formats
- Convert WEBP to PNG
- Convert SVG to PNG
- Image Resizer
- Crop Image
- Reverse Image Search
- Face Search

### Online Calculators
- Simple Calculator
- Age Calculator
- BMI Calculator
- Loan Calculator
- GST Calculator
- Currency Converter
- Password Generator
- Unit Converter
- QR Code Generator

### Free Online Converter
- Convert PDF to Word
- Convert Word to PDF
- Convert Image to PDF
- Compress PDF
- Convert MP3 to MP4
- Convert MP4 to MP3

## Deployment to Vercel

This application is configured for deployment on Vercel. Follow these steps to deploy:

1. Create a Vercel account if you don't have one already.
2. Connect your GitHub repository to Vercel.
3. Configure the deployment settings:
   - Build Command: None (leave empty)
   - Output Directory: None (leave empty)
   - Install Command: `pip install -r requirements.txt`
   - Development Command: `python app.py`

4. Deploy the application.

## Embedding in WordPress

Once deployed to Vercel, you can embed the tools in your WordPress site using iframes:

1. Get the URL of your deployed application (e.g., `https://your-app-name.vercel.app`).
2. Add an iframe to your WordPress post or page:

```html
<iframe src="https://your-app-name.vercel.app" width="100%" height="800px" frameborder="0"></iframe>
```

3. For individual tools, you can use the specific tool URL:

```html
<iframe src="https://your-app-name.vercel.app/tools/image-editing/compress-image" width="100%" height="800px" frameborder="0"></iframe>
```

## Local Development

To run the application locally:

1. Install the required dependencies:
```
pip install -r requirements.txt
```

2. Run the application:
```
python app.py
```

3. Open your browser and navigate to `http://127.0.0.1:5000`.

## Notes for WordPress Embedding

- Make sure your WordPress theme allows iframe embedding.
- You may need to adjust the iframe height based on the tool's content.
- Consider using a responsive iframe solution for better mobile experience.
- Some WordPress security plugins might block iframes, so you may need to configure them accordingly.
