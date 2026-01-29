#!/usr/bin/env python3
"""
Simple launcher script for the Texture Channel Processor
"""

import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import PIL
        import numpy
        import tkinterdnd2
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def main():
    """Main entry point"""
    print("Starting Texture Channel Processor...")
    
    if not check_dependencies():
        print("Dependencies check failed. Exiting...")
        sys.exit(1)
    
    try:
        # Import and run the application
        # from customtkinter_texture_processor_ui import TextureProcessorApp
        from texture_processor_ui import TextureProcessorApp
        app = TextureProcessorApp()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()