#!/usr/bin/env python3
"""
Working AI-Powered Web Application Launcher
"""
import webbrowser
import time
import threading
from working_ai_app import app

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("🚀 Starting Working AI-Powered Daily Journal Assistant...")
    print("📱 Opening in your default browser...")
    print("🌐 Web interface will be available at: http://localhost:5000")
    print("🤖 AI features enabled with direct OpenAI API integration")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start Flask app
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Daily Journal Assistant...")
        print("Thank you for journaling! 📝✨")
