#!/usr/bin/env python3
"""
Test script for the Layer Manager
Demonstrates the layer reordering functionality
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.layer_manager import LayerManagerDialog

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layer Manager Test")
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Layer Manager Test")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Open layer manager button
        self.open_btn = QPushButton("Open Layer Manager")
        self.open_btn.clicked.connect(self.open_layer_manager)
        layout.addWidget(self.open_btn)
        
        # Result display
        self.result_label = QLabel("Layer order will appear here...")
        self.result_label.setStyleSheet("padding: 10px; border: 1px solid #ccc; margin: 10px;")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
        
        self.setLayout(layout)
        
    def open_layer_manager(self):
        """Open the layer manager dialog"""
        # Create mock layer states
        layer_states = {
            'background': True,
            'overlay1': True,
            'overlay2': False,
            'overlay3': True,
            'overlay4': False,
            'overlay5': False,
            'overlay6': False,
            'overlay7': False,
            'overlay8': False,
            'overlay9': False,
            'overlay10': False,
            'intro': True,
            'frame_box': False,
            'frame_mp3cover': False,
            'song_titles': True,
            'soundwave': False,
        }
        
        dialog = LayerManagerDialog(self)
        dialog.update_layer_states(layer_states)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            layer_order = dialog.get_layer_order()
            enabled_layers = dialog.get_enabled_layers()
            
            # Display results
            result_text = f"✅ Layer order updated!\n\n"
            result_text += f"📋 Full order:\n{', '.join(layer_order)}\n\n"
            result_text += f"✅ Enabled layers:\n{', '.join(enabled_layers)}"
            
            self.result_label.setText(result_text)
            print(f"Layer order: {layer_order}")
            print(f"Enabled layers: {enabled_layers}")
        else:
            self.result_label.setText("❌ Dialog was cancelled")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 