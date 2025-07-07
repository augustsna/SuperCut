from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PyQt6.QtGui import QIcon
import os
from src.config import ICON_PATH

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
        label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 6px;")
        layout.addWidget(label)
        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setPlaceholderText("Ask Sna")
        self.input.setFixedHeight(24)
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
