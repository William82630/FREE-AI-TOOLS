"""
Error Logger - A simple Flask route handler for logging JavaScript errors

This module provides a route for receiving and logging JavaScript errors
from the client-side error tracker.

To use this, you need to:
1. Import this module in your main Flask app
2. Register the route with your Flask app
3. Enable server-side error logging in error-tracker.js

Example:
    from error_logger import error_logger_bp
    app.register_blueprint(error_logger_bp)
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

# Create a blueprint for the error logger
error_logger_bp = Blueprint('error_logger', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('js_error_logger')

# Create a file handler if you want to log to a file
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.FileHandler('logs/js_errors.log')
file_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)

@error_logger_bp.route('/log-error', methods=['POST'])
def log_error():
    """
    Route handler for logging JavaScript errors
    
    Expects a JSON payload with error information
    """
    try:
        # Get error data from request
        error_data = request.get_json()
        
        if not error_data:
            return jsonify({'status': 'error', 'message': 'No error data provided'}), 400
        
        # Add timestamp if not present
        if 'timestamp' not in error_data:
            error_data['timestamp'] = datetime.now().isoformat()
        
        # Log the error
        logger.error(f"JavaScript Error: {json.dumps(error_data)}")
        
        # Return success response
        return jsonify({'status': 'success', 'message': 'Error logged successfully'}), 200
    
    except Exception as e:
        # Log server-side error
        logger.error(f"Error logging JavaScript error: {str(e)}")
        
        # Return error response
        return jsonify({'status': 'error', 'message': 'Failed to log error'}), 500
