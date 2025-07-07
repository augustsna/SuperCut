from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QProgressBar, QSizePolicy
from PyQt6.QtCore import QSize
import os
from src.config import PROJECT_ROOT
from PyQt6.QtGui import QIcon

def create_progress_controls(parent):
    """Create progress bar and stop button row. Returns a dict of widgets and the layout."""
    progress_row = QHBoxLayout()
    stop_btn = QPushButton()
    stop_btn.setFixedHeight(24)
    stop_btn.setFixedWidth(24)
    stop_btn.setEnabled(False)
    stop_btn.setVisible(False)
    stop_icon_path = os.path.join(PROJECT_ROOT, "src", "sources", "stopbutton.png")
    stop_btn.setIcon(QIcon(stop_icon_path))
    stop_btn.setIconSize(QSize(22, 22))
    stop_btn.setStyleSheet("QPushButton { background: transparent; border: none; } QPushButton:pressed { background: transparent; }")
    stop_btn.clicked.connect(parent.stop_video_creation)
    progress_row.addWidget(stop_btn)
    progress_bar = QProgressBar()
    progress_bar.setMinimum(0)
    progress_bar.setMaximum(1)
    progress_bar.setValue(0)
    progress_bar.setTextVisible(True)
    progress_bar.setFormat("Batch: 0/0")
    progress_bar.setVisible(False)
    progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    progress_row.addWidget(progress_bar)
    return {
        'stop_btn': stop_btn,
        'progress_bar': progress_bar,
        'progress_row': progress_row
    }
