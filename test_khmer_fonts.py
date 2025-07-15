#!/usr/bin/env python3
"""
Test script to verify Khmer font support in SuperCut
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QFont, QFontDatabase

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui_components import KhmerSupportLineEdit, KhmerSupportPlainTextEdit

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Khmer Font Support Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test label
        test_label = QLabel("Test Khmer Text Input:")
        layout.addWidget(test_label)
        
        # Test single line input
        self.line_edit = KhmerSupportLineEdit()
        self.line_edit.setPlaceholderText("Type Khmer text here...")
        layout.addWidget(self.line_edit)
        
        # Test multi-line input
        self.text_edit = KhmerSupportPlainTextEdit()
        self.text_edit.setPlaceholderText("Type multi-line Khmer text here...")
        self.text_edit.setMaximumHeight(150)
        layout.addWidget(self.text_edit)
        
        # Sample Khmer text
        sample_text = "សួស្តី ពិភពលោក! នេះគឺជាការធ្វើតេស្តអក្សរខ្មែរ។"
        info_label = QLabel(f"Sample Khmer text: {sample_text}")
        layout.addWidget(info_label)
        
        # Instructions
        instructions = QLabel("""
        Instructions:
        1. Try typing Khmer text in the input fields above
        2. Copy and paste the sample text
        3. Check if the text displays correctly with proper Khmer fonts
        4. Verify that the text looks better than before
        """)
        layout.addWidget(instructions)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 