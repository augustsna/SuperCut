#!/usr/bin/env python3
"""
SuperCut Video Maker - Main Entry Point
A modular video creation application that combines images and audio files.
"""

import sys
import time
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

for idx, (mp3s, img, out) in enumerate(zip(mp3_groups, image_files, output_paths), 1):
    print(f"Starting batch {idx}: {out}")
    start_time = time.time()
    # ... your video creation logic here ...
    # For example: create_video_with_ffmpeg(img, mp3s, out, ...)
    elapsed = time.time() - start_time
    print(f"✓ Batch {idx}/{len(output_paths)} completed: {out}")
    print(f"Time spent for batch {idx}: {elapsed:.2f} seconds\n")