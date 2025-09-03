#!/usr/bin/env python3
"""
Offline Web Application Launcher for Daily Journal Assistant
Works without AI features - perfect for when API quota is exceeded
"""
import webbrowser
import time
import threading
from app_offline import app

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("🚀 Starting Daily Journal Assistant (Offline Mode)...")
    print("📱 Opening in your default browser...")
    print("🌐 Web interface will be available at: http://localhost:5000")
    print("📝 All features work except AI analysis (no API key needed)")
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
