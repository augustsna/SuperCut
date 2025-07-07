#!/usr/bin/env python3
# This file uses PyQt6
"""
SuperCut Video Maker - Main Entry Point
A modular video creation application that combines images and audio files.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtWidgets import QDialog
from src.config import check_ffmpeg_installation, ICON_PATH
from src.main_ui import SuperCutUI
from src.utils import cleanup_temp_files
from src.password_dialog import PasswordDialog

# Clear the log file at startup
with open('supercut.log', 'w'):
    pass

# --- One-time password using PC name ---
ACTIVATION_FILENAME = os.path.join(os.path.expanduser('~'), '.supercut_activated')
current_pc_name = os.environ.get('COMPUTERNAME', None)
if current_pc_name is None:
    current_pc_name = os.environ.get('HOSTNAME', None)
if current_pc_name is None:
    current_pc_name = ''

if not os.path.exists(ACTIVATION_FILENAME):
    app = QApplication(sys.argv)
    app.setApplicationName("SuperCut")
    app.setApplicationVersion("1.0")
    while True:
        dlg = PasswordDialog()
        if dlg.exec() == QDialog.DialogCode.Accepted:
            password = dlg.get_password()
            if password == current_pc_name:
                with open(ACTIVATION_FILENAME, 'w') as f:
                    f.write('activated')
                break
            else:
                dlg.set_error("Incorrect password. Please contact Sna.")
                continue
        else:
            sys.exit(0)
    app.exit()

# Only run main if the flag file exists (i.e., activation succeeded)
if os.path.exists(ACTIVATION_FILENAME):
    def main():
        """Main application entry point"""
        print("Starting SuperCut Video Maker...")        
        
        app = QApplication(sys.argv)
        app.setApplicationName("SuperCut")
        app.setApplicationVersion("1.0")
        
        # Check FFmpeg installation
        ffmpeg_ok, error_msg = check_ffmpeg_installation()
        if not ffmpeg_ok:
            print(f"Warning: FFmpeg not found. {error_msg or 'The application will attempt to extract it on first use.'}")
        
        window = SuperCutUI()
        window.show()
        
        print("Application started successfully!")        
        
        sys.exit(app.exec())

    if __name__ == "__main__":
        main()
else:
    sys.exit(0)

