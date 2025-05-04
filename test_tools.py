import requests
import time
import sys
import os
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

# Base URL - change this to your actual domain when deployed
BASE_URL = "http://127.0.0.1:5000"  # Local development server

# List of tool paths to test
TOOL_PATHS = [
    # Calculators
    "/tools/online-calculators/bmi-calculator",
    "/tools/online-calculators/gst-calculator",
    "/tools/online-calculators/currency-converter",
    "/tools/online-calculators/age-calculator",
    "/tools/online-calculators/simple-calculator",
    "/tools/online-calculators/password-generator",
    
    # Image Tools
    "/tools/image-editing/compress-image",
    "/tools/image-editing/convert-image",
    "/tools/image-editing/convert-webp-to-png",
    "/tools/image-editing/image-resizer",
    "/tools/image-editing/crop-image",
    "/tools/image-editing/favicon-generator",
    "/tools/image-editing/face-search",
    "/tools/image-editing/reverse-image-search",
    
    # Converters
    "/tools/free-online-converter/pdf-to-word",
    "/tools/free-online-converter/mp4-to-mp3",
    "/tools/free-online-converter/compress-pdf",
    "/tools/free-online-converter/image-to-pdf",
]

def test_tool_page(url):
    """Test if a tool page loads correctly"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return True, None
        else:
            return False, f"HTTP Status: {response.status_code}"
    except requests.RequestException as e:
        return False, str(e)

def main():
    """Main function to test all tool pages"""
    print(f"{Fore.CYAN}=== Testing Tool Pages ===\n{Style.RESET_ALL}")
    
    # Check if server is running
    try:
        requests.get(BASE_URL, timeout=5)
    except requests.RequestException:
        print(f"{Fore.RED}Error: Cannot connect to server at {BASE_URL}")
        print(f"Make sure your Flask server is running before running this test.{Style.RESET_ALL}")
        return
    
    success_count = 0
    failure_count = 0
    failures = []
    
    # Test each tool page
    for path in TOOL_PATHS:
        url = BASE_URL + path
        print(f"Testing: {path} ... ", end="")
        sys.stdout.flush()  # Ensure output is displayed immediately
        
        success, error = test_tool_page(url)
        
        if success:
            print(f"{Fore.GREEN}OK{Style.RESET_ALL}")
            success_count += 1
        else:
            print(f"{Fore.RED}FAILED{Style.RESET_ALL}")
            failures.append((path, error))
            failure_count += 1
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    # Print summary
    print(f"\n{Fore.CYAN}=== Test Summary ==={Style.RESET_ALL}")
    print(f"Total tools tested: {success_count + failure_count}")
    print(f"Successful: {Fore.GREEN}{success_count}{Style.RESET_ALL}")
    print(f"Failed: {Fore.RED}{failure_count}{Style.RESET_ALL}")
    
    # Print details of failures
    if failures:
        print(f"\n{Fore.RED}=== Failed Tools ==={Style.RESET_ALL}")
        for path, error in failures:
            print(f"{Fore.RED}✗ {path}{Style.RESET_ALL}")
            print(f"  Error: {error}")
    
    print(f"\n{Fore.CYAN}=== Test Completed ==={Style.RESET_ALL}")

if __name__ == "__main__":
    main()
