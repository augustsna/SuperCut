#!/usr/bin/env python3
"""
SuperCut Video Maker - Main Entry Point
A modular video creation application that combines images and audio files.
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from config import check_ffmpeg_installation
from main_ui import SuperCutUI

def main():
    """Main application entry point"""
    # Check FFmpeg installation first
    ffmpeg_ok, error_msg = check_ffmpeg_installation()
    if not ffmpeg_ok:
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "FFmpeg Not Found", error_msg)
        sys.exit(1)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = SuperCutUI()
    window.show()
    
    # Start application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 