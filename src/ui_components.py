import os
import sys
import time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSpacerItem, QSizePolicy, QLineEdit, QProgressBar, QWidget,
    QScrollArea, QFrame, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMovie, QIcon, QFont

class FolderDropLineEdit(QLineEdit):
    """Custom QLineEdit that accepts folder drag and drop"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                path = urls[0].toLocalFile()
                if os.path.isdir(path):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            path = urls[0].toLocalFile()
            if os.path.isdir(path):
                self.setText(path)
                self.editingFinished.emit()

class ImageDropLineEdit(QLineEdit):
    """Custom QLineEdit that accepts GIF or PNG file drag and drop (*.gif, *.png)"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                path = urls[0].toLocalFile()
                if os.path.isfile(path) and os.path.splitext(path)[1].lower() in ['.gif', '.png']:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            path = urls[0].toLocalFile()
            if os.path.isfile(path) and os.path.splitext(path)[1].lower() in ['.gif', '.png']:
                self.setText(path)
                self.editingFinished.emit()

class WaitingDialog(QDialog):
    """Dialog shown while processing video creation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Running...")
        self.setModal(True)
        self.setFixedSize(180, 150)
        
        layout = QVBoxLayout(self)
        
        # Status label
        self.label = QLabel("Creating video, wait...")
        font = self.label.font()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        # Spinner
        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gif_path = os.path.join(os.path.dirname(__file__), "sources/spinner.gif")
        self.movie = QMovie(gif_path)
        self.spinner.setMovie(self.movie)
        layout.addWidget(self.spinner)
        self.movie.start()
        
        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.setFixedHeight(30)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

class PleaseWaitDialog(QDialog):
    """Dialog shown when stopping video creation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stopping...")
        self.setModal(True)
        self.setFixedSize(260, 100)
        self.setStyleSheet("""
            QDialog {
                background: #f5f7fa;
                border-radius: 8px;
            }
            QLabel {
                font-size: 13px;
                color: #333;
            }
        """)
        # Disable the close (X) button
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        # Optionally, also disable the context help button
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.setSpacing(10)
        label = QLabel("Wait, current batch to finish")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(label)
        self.setLayout(vbox)
    def closeEvent(self, event):
        # Ignore close events to prevent closing via Alt+F4 or other means
        event.ignore()

class StoppedDialog(QDialog):
    """Dialog shown when video creation is stopped by user"""
    def __init__(self, parent=None, batch_count=0, total_batches=0):
        super().__init__(parent)
        self.setWindowTitle("Stopped")
        self.setStyleSheet("""
            QDialog {
                background: #f5f7fa;
                border-radius: 10px;
            }
            QLabel#iconLabel {
                font-size: 34px;
                color: #e67e22;
                margin: 0;
                padding: 0;
            }
            QLabel#msgLabel {
                font-size: 14px;
                color: #222;
                font-weight: 600;
                margin-top: 4px;
                margin-bottom: 4px;
            }
            QLabel#batchLabel {
                font-size: 13px;
                color: #555;
                margin-top: 2px;
                margin-bottom: 8px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                font-size: 13px;
                padding: 6px 16px;
                border-radius: 6px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 14)
        layout.setSpacing(10)

        # Icon
        icon = QLabel("📛")
        icon.setObjectName("iconLabel")
        icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(icon)

        # Message
        msg = QLabel("Video creation was stopped.")
        msg.setObjectName("msgLabel")
        msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(msg)

        # Batch info
        unsuccessful = max(0, total_batches - batch_count)
        batch_info = QLabel(f"Batches completed: {batch_count} / {total_batches}<br>Unsuccessful: {unsuccessful}")
        batch_info.setObjectName("batchLabel")
        batch_info.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        batch_info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(batch_info)

        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Shortcut
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self._close_dialog)
        self.adjustSize()

    def _close_dialog(self):
        self.close()
        return None

class SuccessDialog(QDialog):
    """Dialog shown when video creation completes successfully"""
    def __init__(self, parent=None, open_folder=None, leftover_files=None, leftover_images=None, min_mp3_count=3):
        super().__init__(parent)
        self.open_folder = open_folder
        self.setWindowTitle("Task Completed")
        
        # Calculate dialog height based on leftover files
        extra_height = 0
        if leftover_files:
            extra_height += 50 + 15 * len(leftover_files)
        if leftover_images:
            extra_height += 50 + 15 * len(leftover_images)
        self.setFixedSize(370, 170 + extra_height)
        
        self.setStyleSheet("""
            QDialog {
                background: #f5f7fa;
                border-radius: 10px;
            }
            QLabel#iconLabel {
                font-size: 44px;
                color: #4BB543;
                margin-bottom: 0px;
            }
            QLabel#msgLabel {
                font-size: 16px;
                color: #222;
                font-weight: bold;
                margin-bottom: 8px;
                margin-top: 6px;
            }
            QLabel#leftoverLabel {
                font-size: 13px;
                color: #b00;
                margin-top: 10px;
                margin-bottom: 2px;
                font-weight: bold;
            }
            QLabel#fileListLabel {
                font-size: 11px;
                color: #555;
                margin-left: 8px;
                margin-bottom: 8px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 6px;
                padding: 7px 18px;
                font-size: 13px;
                min-width: 110px;
                margin-top: 8px;
            }
            QPushButton#okBtn {
                background-color: #4BB543;
                font-weight: bold;
                font-size: 13px;
                min-width: 70px;
                max-width: 80px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton#okBtn:hover {
                background-color: #388e3c;
            }
        """)
        
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(24, 18, 24, 18)
        vbox.setSpacing(8)

        # Success icon
        icon = QLabel("✅")
        icon.setObjectName("iconLabel")
        icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        icon.setStyleSheet("font-size: 28px; color: #4BB543; border: none; background: transparent;")
        vbox.addWidget(icon)

        # Main message
        msg = QLabel("Video created successfully!")
        msg.setObjectName("msgLabel")
        msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(msg)

        # Leftover MP3 files section
        if leftover_files:
            leftover_label = QLabel(f"{len(leftover_files)} MP3 files left over (not enough for a group of {min_mp3_count}):")
            leftover_label.setObjectName("leftoverLabel")
            leftover_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(leftover_label)
            file_list = QLabel("\n".join([os.path.basename(f) for f in leftover_files]))
            file_list.setObjectName("fileListLabel")
            file_list.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(file_list)

        # Leftover image files section
        if leftover_images:
            leftover_img_label = QLabel(f"{len(leftover_images)} image files left over (not enough for a group):")
            leftover_img_label.setObjectName("leftoverLabel")
            leftover_img_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(leftover_img_label)
            img_file_list = QLabel("\n".join([os.path.basename(f) for f in leftover_images]))
            img_file_list.setObjectName("fileListLabel")
            img_file_list.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(img_file_list)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)
        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.folder_btn = QPushButton("Result Folder")
        self.folder_btn.setMinimumWidth(120)
        self.folder_btn.clicked.connect(self.on_folder)
        btn_row.addWidget(self.folder_btn)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.ok_btn)

        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Expanding, QSizePolicy.Minimum))
        vbox.addLayout(btn_row)

        # Shortcut
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self._close_dialog)

    def on_folder(self):
        """Open result folder when folder button is clicked"""
        if self.open_folder:
            self.open_folder()

    def _close_dialog(self):
        self.close()
        return None

class ScrollableErrorDialog(QDialog):
    """Dialog for displaying long error messages/logs in a scrollable area."""
    def __init__(self, parent=None, title="Error Log", message=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(520, 320)
        self.setMaximumSize(900, 700)
        self.resize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background: #f5f7fa;
                border-radius: 10px;
            }
            QLabel#titleLabel {
                font-size: 16px;
                color: #b00;
                font-weight: bold;
                margin-bottom: 8px;
            }
            QTextEdit {
                background: #fff;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
                color: #222;
                padding: 8px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 6px;
                padding: 7px 18px;
                font-size: 13px;
                min-width: 90px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        # Title label
        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(title_label)

        # Scrollable error log
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(message)
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self.text_edit.setMinimumHeight(200)
        layout.addWidget(self.text_edit, 1)

        # OK button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Shortcut
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, lambda: (self.close(), None)[-1]) 