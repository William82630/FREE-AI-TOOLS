# FREE AI TOOLS

A collection of free web-based tools built with Flask, including image editing utilities and calculators.

## Project Structure
```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Project dependencies
├── compressed/           # Directory for processed images
├── favicons/            # Directory for generated favicons
├── templates/           # HTML templates
└── uploads/            # Directory for user uploads
```

## Features

### Completed Features
#### Image Tools
- Image Compression
- Favicon Generator
- Image Format Conversion (PNG/JPG/JPEG)
- WebP to PNG Converter
- SVG to PNG Converter
- Image Resizer
- Image Cropping
- Reverse Image Search
- Face Search

### Under Development
#### Calculators
- Simple Calculator
- Age Calculator
- BMI Calculator
- Currency Converter
- Password Generator
- Loan Calculator
- Unit Converter
- QR Code Generator
- GST Calculator

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

## API Integration
The project uses OpenRouter API for AI features. API key configuration is required in app.py.

## Project Status
- All image processing features are fully implemented
- Calculator tools need implementation
- AI features are configured through OpenRouter API
- Frontend templates are ready for all features

## Next Steps
1. Implement calculator functionalities
2. Add error handling for all tools
3. Implement proper form validation
4. Add user feedback messages