#!/usr/bin/env python3
"""
SuperCut Video Maker - Main Entry Point
A modular video creation application that combines images and audio files.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from src.config import check_ffmpeg_installation
from src.main_ui import SuperCutUI
from src.utils import cleanup_temp_files

# Clear the log file at startup
with open('supercut.log', 'w'):
    pass

def main():
    """Main application entry point"""
    # Clean up temp files on startup
    cleanup_temp_files()
    app = QApplication(sys.argv)
    # Check FFmpeg installation first
    ffmpeg_ok, error_msg = check_ffmpeg_installation()
    if not ffmpeg_ok:
        QMessageBox.critical(None, "FFmpeg Not Found", error_msg or "FFmpeg installation not found")
        sys.exit(1)
    
    # Create and show main window
    window = SuperCutUI()
    window.show()
    
    # Start application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

