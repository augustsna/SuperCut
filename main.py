#!/usr/bin/env python3
# This file uses PyQt6
"""
SuperCut Video Maker - Main Entry Point
A modular video creation application that combines images and audio files.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from src.config import check_ffmpeg_installation, ICON_PATH
from src.main_ui import SuperCutUI
from src.utils import cleanup_temp_files

# Clear the log file at startup prgram
with open('supercut.log', 'w'):
    pass

# Clean up any leftover temp files before starting the program
cleanup_temp_files()

# Create the QApplication instance ONCE at the very start
app = QApplication(sys.argv)
app.setApplicationName("SuperCut")
app.setApplicationVersion("1.0")

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Activation Required")
        self.setWindowFlags(self.windowFlags())
        self.setModal(True)
        self.setFixedSize(320, 120)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        layout = QVBoxLayout(self)
        label = QLabel("Enter your one-time password:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 6px;")
        layout.addWidget(label)
        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setPlaceholderText("Ask Sna")
        self.input.setFixedHeight(28)
        self.input.setStyleSheet("font-size: 13px; padding: 2px 2px;")
        layout.addWidget(self.input)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #c00; font-size: 12px; margin-top: 2px;")
        layout.addSpacing(-30)
        layout.addWidget(self.error_label)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setFixedWidth(60)
        self.ok_btn.setStyleSheet("font-size: 13px;")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(60)
        self.cancel_btn.setStyleSheet("font-size: 13px;")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addSpacing(8)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.input.returnPressed.connect(self.accept)
    def get_password(self):
        return self.input.text().strip()
    def set_error(self, msg):
        self.error_label.setText(msg)

# --- One-time password using PC name ---
ACTIVATION_FILENAME = os.path.join(os.path.expanduser('~'), '.supercut_activated')
current_pc_name = os.environ.get('COMPUTERNAME', None)
if current_pc_name is None:
    current_pc_name = os.environ.get('HOSTNAME', None)
if current_pc_name is None:
    current_pc_name = ''

if not os.path.exists(ACTIVATION_FILENAME):
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
    # No need to call app.exit() here; continue to main window

# Only run main if the flag file exists (i.e., activation succeeded)
if os.path.exists(ACTIVATION_FILENAME):
    def main():
        """Main application entry point"""
        print("Starting SuperCut Video Maker...")        
        # QApplication already created above
        # Check FFmpeg installation
        ffmpeg_ok, error_msg = check_ffmpeg_installation()
        if not ffmpeg_ok:
            print(f"Warning: FFmpeg not found. {error_msg or 'The application will attempt to extract it on first use.'}")
        window = SuperCutUI()
        window.show()
        print("Application started successfully! \u2727 ")
        
        # Print current FFmpeg settings that will be used for video creation
        # Use a timer to ensure UI is fully initialized
        def print_ffmpeg_settings():
            try:
                print("\n📹 Current FFmpeg Settings for Video Creation:")
                print(f"FPS: {window.fps_combo.currentData() if hasattr(window, 'fps_combo') else 'N/A'}")
                print(f"Preset: {window.preset_combo.currentData() if hasattr(window, 'preset_combo') else 'N/A'}")
                print(f"Maxrate: {window.settings.value('default_ffmpeg_maxrate', '16M', type=str)}")
                print(f"Bufsize: {window.settings.value('default_ffmpeg_bufsize', '24M', type=str)}")
                print(f"Video bitrate: {window.settings.value('default_ffmpeg_video_bitrate', '12M', type=str)}")
                print(f"Audio bitrate: {window.settings.value('default_ffmpeg_audio_bitrate', '384k', type=str)}")
                print(f"Resolution: {window.resolution_combo.currentData() if hasattr(window, 'resolution_combo') else 'N/A'}")
                print()
            except Exception as e:
                print(f"\n⚠️ Could not display FFmpeg settings: {e}")
                print()
        
        # Schedule the print after a longer delay to ensure all UI elements are ready
        from PyQt6.QtCore import QTimer
        timer = QTimer()
        timer.singleShot(100, print_ffmpeg_settings)
        
        sys.exit(app.exec())

    if __name__ == "__main__":
        main()
else:
    sys.exit(0)

