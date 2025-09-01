#!/usr/bin/env python3
import os
import sys
import subprocess
import webbrowser
import time
from threading import Thread

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def start_web_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    from web_app import app
    app.run(debug=False, host='127.0.0.1', port=5001, use_reloader=False)

def main():
    print("EscapeRoom Assistant")
    print("Starting web server...")
    
    server_thread = Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    time.sleep(3)
    
    print("Opening browser...")
    webbrowser.open('http://127.0.0.1:5001')
    
    print("Web application running at http://127.0.0.1:5001")
    print("Close this window to stop the application")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()