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

### Under Development
#### Image Tools
- Image Cropping
- Reverse Image Search
- Face Search

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
- Core image processing features are implemented
- Calculator tools need implementation
- AI features are configured through OpenRouter API
- Frontend templates are ready for all features

## Next Steps
1. Implement calculator functionalities
2. Complete image editing features (crop, search)
3. Add error handling for all tools
4. Implement proper form validation
5. Add user feedback messages