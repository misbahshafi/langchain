#!/usr/bin/env python3
"""
Simple launcher script for the Daily Journal Assistant
"""
import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the main application
from main import app

if __name__ == "__main__":
    app()
