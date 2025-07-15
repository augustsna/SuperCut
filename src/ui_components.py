# This file uses PyQt6
import os
import sys
import time
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSpacerItem, QSizePolicy, QLineEdit, QProgressBar, QWidget,
    QScrollArea, QFrame, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMovie, QIcon, QFont, QShortcut, QKeySequence, QWheelEvent, QFontDatabase

from src.utils import clean_file_path

class KhmerSupportLineEdit(QLineEdit):
    """Custom QLineEdit with enhanced Khmer font support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_khmer_font_support()
    
    def _setup_khmer_font_support(self):
        """Setup Khmer font support with proper fallback"""
        # Get the project root to locate font files
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_dir = os.path.join(project_root, "src", "sources", "system fonts")
        
        # Load Khmer fonts if available
        khmer_fonts = []
        font_files = [
            "KhmerFont1.ttf",
            "KhmerFont2.ttf", 
            "KhmerFont3.ttf"
        ]
        
        for font_file in font_files:
            font_path = os.path.join(font_dir, font_file)
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    khmer_fonts.append(font_family)
        
        # Create font with fallback chain
        if khmer_fonts:
            # Use the first available Khmer font as primary
            primary_font = khmer_fonts[0]
            font = QFont(primary_font, 13)
            
            # Set the font
            self.setFont(font)
            
            # Apply specific styling for better Khmer text rendering
            self.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #ccc;
                    border-radius: 6px;
                    padding: 6px 8px;
                    background-color: white;
                    font-size: 13px;
                    line-height: 1.4;
                    text-align: left;
                }
                QLineEdit:focus {
                    border: 2px solid #4a90e2;
                    background-color: #ffffff;
                }
                QLineEdit:hover {
                    border: 1px solid #a0a0a0;
                    background-color: #f8f8f8;
                }
            """)
        else:
            # Fallback to system fonts if Khmer fonts not available
            font = QFont("Segoe UI", 13)
            self.setFont(font)
    
    def text(self):
        """Override to ensure proper text handling"""
        return super().text()
    
    def setText(self, text):
        """Override to ensure proper text setting"""
        super().setText(text)
    
    def insert(self, text):
        """Override to ensure proper text insertion"""
        super().insert(text)

class FolderDropLineEdit(KhmerSupportLineEdit):
    """Custom QLineEdit that accepts folder drag and drop with Khmer font support"""
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

    def paste(self):
        """Override paste to clean file paths"""
        clipboard = QtWidgets.QApplication.clipboard()
        if clipboard is None:
            super().paste()
            return
            
        mime_data = clipboard.mimeData()
        if mime_data is None:
            super().paste()
            return
        
        if mime_data.hasText():
            text = mime_data.text().strip()
            # Clean the pasted text if it looks like a file path
            cleaned_text = clean_file_path(text)
            self.insert(cleaned_text)
        else:
            super().paste()

class ImageDropLineEdit(KhmerSupportLineEdit):
    """Custom QLineEdit that accepts GIF, PNG, or MP4 file drag and drop (*.gif, *.png, *.mp4) with Khmer font support"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                path = urls[0].toLocalFile()
                if os.path.isfile(path) and os.path.splitext(path)[1].lower() in ['.gif', '.png', '.mp4']:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            path = urls[0].toLocalFile()
            if os.path.isfile(path) and os.path.splitext(path)[1].lower() in ['.gif', '.png', '.mp4']:
                self.setText(path)
                self.editingFinished.emit()

    def paste(self):
        """Override paste to clean file paths"""
        clipboard = QtWidgets.QApplication.clipboard()
        if clipboard is None:
            super().paste()
            return
            
        mime_data = clipboard.mimeData()
        if mime_data is None:
            super().paste()
            return
        
        if mime_data.hasText():
            text = mime_data.text().strip()
            # Clean the pasted text if it looks like a file path
            cleaned_text = clean_file_path(text)
            self.insert(cleaned_text)
        else:
            super().paste()

class NoWheelComboBox(QComboBox):
    """Custom QComboBox that prevents mouse wheel scrolling when dropdown is closed and has custom styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                color: #333333;
                min-height: 20px;
            }
            QComboBox:hover {
                border: 1px solid #a0a0a0;
                background-color: #f8f8f8;
            }
            QComboBox:focus {
                border: 1px solid #4a90e2;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                selection-background-color: #3f92e3;
                border: 1px solid #ccc;
                outline: none;
            }
        """)
    
    def wheelEvent(self, event: QWheelEvent):
        """Override wheel event to prevent scrolling through items when dropdown is closed"""
        view = self.view()
        if view is None or not view.isVisible():
            # When dropdown is closed, ignore wheel events to allow parent UI scrolling
            event.ignore()
        else:
            # When dropdown is open, allow normal scrolling through items
            super().wheelEvent(event)

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
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        # Optionally, also disable the context help button
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.setSpacing(10)
        label = QLabel("Wait, current batch to finish")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
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

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        # Open Folder button
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.setMinimumWidth(120)
        def on_open_folder():
            if parent and hasattr(parent, 'open_result_folder'):
                parent.open_result_folder()
        open_folder_btn.clicked.connect(on_open_folder)
        btn_row.addWidget(open_folder_btn)
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Shortcut
        QShortcut(QKeySequence("Ctrl+W"), self, self.close)
        self.adjustSize()

    def _close_dialog(self):
        self.close()
        return None

class SuccessDialog(QDialog):
    """Dialog shown when video creation completes successfully"""
    def __init__(self, parent=None, open_folder=None, leftover_files=None, leftover_images=None, min_mp3_count=3, batch_count=None):
        super().__init__(parent)
        self.open_folder = open_folder
        self.setWindowTitle("Task Completed")
        
        # Always use fixed size 370x200
        self.setFixedSize(370, 200)
        
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
        icon = QLabel("✓")
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

        # Batch info (if available)
        if batch_count is not None:
            batch_info = QLabel(f"Batches completed: {batch_count}")
            batch_info.setObjectName("batchLabel")
            batch_info.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(batch_info)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)
        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.folder_btn = QPushButton("Result Folder")
        self.folder_btn.setMinimumWidth(80)
        self.folder_btn.clicked.connect(self.on_folder)
        btn_row.addWidget(self.folder_btn)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.ok_btn)

        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        vbox.addLayout(btn_row)

        # Shortcut
        QShortcut(QKeySequence("Ctrl+W"), self, self._close_dialog)

    def on_folder(self):
        """Open result folder when folder button is clicked"""
        if self.open_folder:
            self.open_folder()

    def _close_dialog(self):
        self.close()
        return None

class SuccessWithLeftoverDialog(QDialog):
    """Dialog shown when video creation completes successfully but with leftover files"""
    def __init__(self, parent=None, open_folder=None, leftover_mp3s=None, leftover_images=None, min_mp3_count=3):
        super().__init__(parent)
        self.open_folder = open_folder
        self.setWindowTitle("Task Completed")
        
        # Always use fixed size 370x200
        self.setFixedSize(370, 200)
        
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
        icon = QLabel("✓")
        icon.setObjectName("iconLabel")
        icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        icon.setStyleSheet("font-size: 28px; color: #4BB543; border: none; background: transparent;")
        vbox.addWidget(icon)

        # Main message
        msg = QLabel("Success with leftover!")
        msg.setObjectName("msgLabel")
        msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(msg)

        # Leftover MP3 files section
        if leftover_mp3s:
            leftover_label = QLabel(f"{len(leftover_mp3s)} MP3 files left over (not enough for a group of {min_mp3_count}):")
            leftover_label.setObjectName("leftoverLabel")
            leftover_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(leftover_label)
            file_list = QLabel("\n".join([os.path.basename(f) for f in leftover_mp3s]))
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
        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.folder_btn = QPushButton("Result Folder")
        self.folder_btn.setMinimumWidth(80)
        self.folder_btn.clicked.connect(self.on_folder)
        btn_row.addWidget(self.folder_btn)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.ok_btn)

        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        vbox.addLayout(btn_row)

        # Shortcut
        QShortcut(QKeySequence("Ctrl+W"), self, self._close_dialog)

    def on_folder(self):
        """Open result folder when folder button is clicked"""
        if self.open_folder:
            self.open_folder()

    def _close_dialog(self):
        self.close()
        return None

class DryRunSuccessDialog(QDialog):
    """Dialog shown when dry run completes successfully"""
    def __init__(self, parent=None, video_path=None, open_folder=None):
        super().__init__(parent)
        self.video_path = video_path
        self.open_folder = open_folder
        self.setWindowTitle("Dry Run Success")
        
        # Fixed size similar to SuccessDialog
        self.setFixedSize(300, 200)
        
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
            QLabel#pathLabel {
                font-size: 11px;
                color: #555;
                margin-left: 8px;
                margin-bottom: 8px;
            }
            QPushButton.dryrun-btn {
                min-width: 80px !important;
                max-width: 80px !important;
                width: 80px !important;
                padding-left: 0px; padding-right: 0px;
            }
            QPushButton#okBtn.dryrun-btn {
                min-width: 80px !important;
                max-width: 80px !important;
                width: 80px !important;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 6px;
                padding: 7px 0px;
                font-size: 13px;
                margin-top: 8px;
            }
            QPushButton#okBtn {
                background-color: #4BB543;
                font-size: 13px;
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
        icon = QLabel("✓")
        icon.setObjectName("iconLabel")
        icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        icon.setStyleSheet("font-size: 28px; color: #4BB543; border: none; background: transparent;")
        vbox.addWidget(icon)

        # Main message
        msg = QLabel("Dry Run completed successfully!")
        msg.setObjectName("msgLabel")
        msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        vbox.addWidget(msg)

        # Video path info
        if video_path:
            path_label = QLabel(f"{os.path.basename(video_path)}")
            path_label.setObjectName("pathLabel")
            path_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox.addWidget(path_label)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)
        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.view_video_btn = QPushButton("View")
        self.view_video_btn.setFixedWidth(80)
        self.view_video_btn.setProperty("class", "dryrun-btn")
        self.view_video_btn.setObjectName("viewBtn")
        self.view_video_btn.clicked.connect(self.on_view_video)
        btn_row.addWidget(self.view_video_btn)

        self.folder_btn = QPushButton("Folder")
        self.folder_btn.setFixedWidth(80)
        self.folder_btn.setProperty("class", "dryrun-btn")
        self.folder_btn.setObjectName("folderBtn")
        self.folder_btn.clicked.connect(self.on_folder)
        btn_row.addWidget(self.folder_btn)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.setProperty("class", "dryrun-btn")
        self.ok_btn.setFixedWidth(80)
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.ok_btn)

        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        vbox.addLayout(btn_row)

        # Shortcut
        QShortcut(QKeySequence("Ctrl+W"), self, self._close_dialog)

    def on_view_video(self):
        """Open the dry run video when view video button is clicked"""
        if self.video_path and os.path.exists(self.video_path):
            import subprocess
            import platform
            try:
                if platform.system() == "Windows":
                    os.startfile(self.video_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", self.video_path])
                else:  # Linux
                    subprocess.run(["xdg-open", self.video_path])
            except Exception as e:
                print(f"Failed to open video: {e}")

    def on_folder(self):
        """Open folder when folder button is clicked"""
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
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title_label)

        # Scrollable error log
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(message)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text_edit.setMinimumHeight(200)
        # --- Apply main UI scroll bar style ---
        SCROLLBAR_STYLE = """
        QScrollBar:vertical {
            background: rgba(240, 240, 240, 0.20);
            width: 12px;
            border-radius: 6px;
            margin: 0px;
            position: absolute;
            right: 0px;
        }
        QScrollBar::handle:vertical {
            background: rgba(192, 192, 192, 0.20);
            border-radius: 6px;
            min-height: 20px;
            margin: 0px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(160, 160, 160, 0.35);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background: rgba(240, 240, 240, 0.35);
            height: 12px;
            border-radius: 6px;
            margin: 0px;
            position: absolute;
            bottom: 0px;
        }
        QScrollBar::handle:horizontal {
            background: rgba(192, 192, 192, 0.35);
            border-radius: 6px;
            min-width: 20px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal:hover {
            background: rgba(160, 160, 160, 0.35);
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QScrollBar:sub-control:corner {
            background: transparent;
        }
        """
        self.text_edit.setStyleSheet(self.text_edit.styleSheet() + SCROLLBAR_STYLE)
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
        QShortcut(QKeySequence("Ctrl+W"), self, self.close) 

class KhmerSupportPlainTextEdit(QtWidgets.QPlainTextEdit):
    """Custom QPlainTextEdit with enhanced Khmer font support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_khmer_font_support()
    
    def _setup_khmer_font_support(self):
        """Setup Khmer font support with proper fallback"""
        # Get the project root to locate font files
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_dir = os.path.join(project_root, "src", "sources", "system fonts")
        
        # Load Khmer fonts if available
        khmer_fonts = []
        font_files = [
            "KhmerFont1.ttf",
            "KhmerFont2.ttf", 
            "KhmerFont3.ttf"
        ]
        
        for font_file in font_files:
            font_path = os.path.join(font_dir, font_file)
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                    khmer_fonts.append(font_family)
        
        # Create font with fallback chain
        if khmer_fonts:
            # Use the first available Khmer font as primary
            primary_font = khmer_fonts[0]
            font = QFont(primary_font, 13)
            
            # Set the font
            self.setFont(font)
            
            # Apply specific styling for better Khmer text rendering
            self.setStyleSheet("""
                QPlainTextEdit {
                    border: 1px solid #ccc;
                    border-radius: 6px;
                    padding: 6px 8px;
                    background-color: white;
                    font-size: 13px;
                    line-height: 1.4;
                    text-align: left;
                }
                QPlainTextEdit:focus {
                    border: 2px solid #4a90e2;
                    background-color: #ffffff;
                }
                QPlainTextEdit:hover {
                    border: 1px solid #a0a0a0;
                    background-color: #f8f8f8;
                }
            """)
        else:
            # Fallback to system fonts if Khmer fonts not available
            font = QFont("Segoe UI", 13)
            self.setFont(font) 