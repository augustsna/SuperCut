#!/usr/bin/env python3
"""
SuperCut Video Maker - Main Entry Point
A modular video creation application that combines images and audio files.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from config import check_ffmpeg_installation
from main_ui import SuperCutUI
from utils import cleanup_temp_files

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