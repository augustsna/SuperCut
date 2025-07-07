"""
action_buttons.py - Contains logic for creating action buttons for SuperCutUI
"""
import os
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize

def create_action_buttons(self, layout, PROJECT_ROOT):
    button_layout = QHBoxLayout()
    button_layout.addSpacing(10)
    self.settings_btn = QPushButton()
    icon_path = os.path.join(PROJECT_ROOT, "src", "sources", "settings.png")
    self.settings_btn.setIcon(QIcon(icon_path))
    self.settings_btn.setFixedSize(32, 32)
    self.settings_btn.setIconSize(self.settings_btn.size())
    self.settings_btn.setToolTip("Settings")
    self.settings_btn.setStyleSheet("QPushButton { background: transparent; border: none; padding: 0px; margin: 0px; } QPushButton:pressed { background: transparent; }")
    self.settings_btn.clicked.connect(self.show_settings_dialog)
    button_layout.addWidget(self.settings_btn)
    button_layout.addSpacing(10)
    self.terminal_btn = QPushButton("\U0001F5A5 Terminal")
    self.terminal_btn.setFixedHeight(35)
    self.terminal_btn.setFixedWidth(100)
    self.terminal_btn.clicked.connect(self.show_terminal)
    button_layout.addWidget(self.terminal_btn)
    button_layout.addSpacing(0)
    self.create_btn = QPushButton("Create Video")
    self.create_btn.setFixedHeight(35)
    self.create_btn.setFixedWidth(350)
    self.create_btn.clicked.connect(self.create_video)
    button_layout.addWidget(self.create_btn)
    button_layout.addSpacing(5)
    self.placeholder_btn = QPushButton()
    rocket_icon_path = os.path.join(PROJECT_ROOT, "src", "sources", "rocket.png")
    self.placeholder_btn.setIcon(QIcon(rocket_icon_path))
    self.placeholder_btn.setIconSize(QSize(28, 28))
    self.placeholder_btn.setFixedHeight(32)
    self.placeholder_btn.setFixedWidth(32)
    self.placeholder_btn.setStyleSheet("QPushButton { background: transparent; border: none; padding: 0px; margin: 0px; } QPushButton:pressed { background: transparent; }")
    button_layout.addWidget(self.placeholder_btn)
    button_layout.addStretch()
    layout.addLayout(button_layout)
