/**
 * Error Tracker - A simple JavaScript error tracking utility
 * 
 * This script captures JavaScript errors that occur on the page and logs them
 * to the console. It can also be configured to send errors to a server endpoint.
 */

(function() {
    // Configuration
    const config = {
        // Set to true to enable error tracking
        enabled: true,
        
        // Set to true to log errors to console
        logToConsole: true,
        
        // Set to true to show error notifications to the user
        showNotifications: false,
        
        // Set to true to send errors to server (requires serverEndpoint)
        sendToServer: false,
        
        // Server endpoint to send errors to (if sendToServer is true)
        serverEndpoint: '/log-error',
        
        // Maximum number of errors to track (to prevent flooding)
        maxErrors: 10
    };
    
    // Error counter
    let errorCount = 0;
    
    // Original console.error function
    const originalConsoleError = console.error;
    
    // Function to handle errors
    function handleError(errorEvent) {
        if (!config.enabled || errorCount >= config.maxErrors) return;
        
        errorCount++;
        
        // Extract error information
        const errorInfo = {
            message: errorEvent.message || 'Unknown error',
            source: errorEvent.filename || errorEvent.sourceURL || 'Unknown source',
            lineno: errorEvent.lineno || 0,
            colno: errorEvent.colno || 0,
            stack: (errorEvent.error && errorEvent.error.stack) || 'No stack trace',
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            toolName: getToolName()
        };
        
        // Log to console if enabled
        if (config.logToConsole) {
            originalConsoleError('JavaScript Error:', errorInfo);
        }
        
        // Show notification if enabled
        if (config.showNotifications) {
            showErrorNotification(errorInfo);
        }
        
        // Send to server if enabled
        if (config.sendToServer) {
            sendErrorToServer(errorInfo);
        }
    }
    
    // Function to get the current tool name from the URL
    function getToolName() {
        const path = window.location.pathname;
        const pathParts = path.split('/').filter(part => part.length > 0);
        
        if (pathParts.length >= 3) {
            // Format: /tools/category/tool-name
            return pathParts[2];
        } else if (pathParts.length >= 1) {
            return pathParts[pathParts.length - 1];
        }
        
        return 'unknown-tool';
    }
    
    // Function to show error notification
    function showErrorNotification(errorInfo) {
        // Create notification element if it doesn't exist
        let notification = document.getElementById('error-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'error-notification';
            notification.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: #f44336;
                color: white;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                z-index: 9999;
                max-width: 300px;
                font-family: Arial, sans-serif;
            `;
            document.body.appendChild(notification);
        }
        
        // Set notification content
        notification.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 5px;">JavaScript Error Detected</div>
            <div>${errorInfo.message}</div>
            <div style="font-size: 0.8em; margin-top: 5px;">
                at ${errorInfo.source}:${errorInfo.lineno}:${errorInfo.colno}
            </div>
            <button style="
                background: white;
                color: #f44336;
                border: none;
                padding: 5px 10px;
                margin-top: 10px;
                border-radius: 3px;
                cursor: pointer;
            " onclick="this.parentNode.style.display='none'">Dismiss</button>
        `;
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.display = 'none';
            }
        }, 10000);
    }
    
    // Function to send error to server
    function sendErrorToServer(errorInfo) {
        try {
            fetch(config.serverEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(errorInfo)
            }).catch(err => {
                // Silently fail to avoid infinite error loops
            });
        } catch (e) {
            // Silently fail to avoid infinite error loops
        }
    }
    
    // Override console.error to capture console errors
    console.error = function() {
        // Call original console.error
        originalConsoleError.apply(console, arguments);
        
        // Handle as an error if it's an Error object
        if (arguments[0] instanceof Error) {
            handleError({
                message: arguments[0].message,
                error: arguments[0],
                stack: arguments[0].stack
            });
        }
    };
    
    // Add global error event listener
    window.addEventListener('error', handleError);
    
    // Add unhandled promise rejection listener
    window.addEventListener('unhandledrejection', function(event) {
        handleError({
            message: 'Unhandled Promise Rejection: ' + (event.reason || 'Unknown reason'),
            error: event.reason,
            stack: event.reason && event.reason.stack
        });
    });
    
    // Add to window for external access
    window.ErrorTracker = {
        // Method to manually log an error
        logError: function(error, additionalInfo) {
            handleError({
                message: error instanceof Error ? error.message : String(error),
                error: error,
                stack: error instanceof Error ? error.stack : 'No stack trace',
                additionalInfo: additionalInfo
            });
        },
        
        // Method to enable/disable error tracking
        setEnabled: function(enabled) {
            config.enabled = !!enabled;
        },
        
        // Method to reset error count
        resetErrorCount: function() {
            errorCount = 0;
        }
    };
    
    // Log initialization
    if (config.logToConsole) {
        console.log('Error Tracker initialized');
    }
})();
