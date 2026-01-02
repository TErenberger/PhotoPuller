"""
PhotoPuller - Windows application to find and organize important photos and videos
"""
import sys
import os
from pathlib import Path

def main():
    """Main entry point for the application"""
    # Check if running in CLI mode (if any arguments provided)
    if len(sys.argv) > 1:
        # Import and run CLI
        from photopuller_cli import main as cli_main
        sys.exit(cli_main())
    else:
        # Run GUI mode
        from gui import PhotoPullerGUI
        app = PhotoPullerGUI()
        app.run()

if __name__ == "__main__":
    main()



