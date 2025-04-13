import webbrowser
import subprocess
import time

# Start the Flask app
process = subprocess.Popen(["python", "app.py"])

# Wait for the server to start (increase wait time to 5 seconds)
time.sleep(5)

# Open the default web browser
webbrowser.open("http://127.0.0.1:5000/")