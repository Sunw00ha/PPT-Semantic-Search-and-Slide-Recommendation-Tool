#!/usr/bin/env python3
"""
Startup script for PPT Recommendation System GUI App
"""

import subprocess
import sys
import os

def main():
    print("PPT Recommendation System - GUI App")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('gui_app.py'):
        print("Error: Please run this script from the PPTtool directory")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("   Warning: Virtual environment not detected")
        print("   It's recommended to activate PPTenv first:")
        print("   source PPTenv/bin/activate")
        print()
    
    print("Starting GUI application...")
    print("   A popup window should appear shortly...")
    print()
    
    # Start the GUI app
    try:
        subprocess.run([sys.executable, 'gui_app.py'], check=True)
    except KeyboardInterrupt:
        print("\nApp stopped. Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"Error starting app: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
