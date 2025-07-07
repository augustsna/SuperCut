# This file uses PyQt6
import os
import sys
import time
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSpacerItem, QSizePolicy, QLineEdit, QProgressBar, QWidget,
    QScrollArea, QFrame, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMovie, QIcon, QFont, QShortcut, QKeySequence

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
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        # Optionally, also disable the context help button
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
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
        QShortcut(QKeySequence("Ctrl+W"), self, self.close)
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

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)
        btn_row.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.folder_btn = QPushButton("Result Folder")
        self.folder_btn.setMinimumWidth(120)
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

class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None, fps_options=None):
        super().__init__(parent)
        self.setWindowTitle("Default Settings")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.settings = settings
        self.fps_options = fps_options or [("24", 24)]
        self.selected_fps = None
        main_layout = QtWidgets.QVBoxLayout(self)        
        # Add Settings label at the top
        main_layout.addSpacing(-160)  # Move label up by 20px
        settings_label = QLabel("Default Settings")
        settings_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 0px;")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(settings_label)
        # Add Default button below Settings label  
        main_layout.addSpacing(-15)      
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedSize(100, 28)
        self.reset_btn.setStyleSheet("QPushButton { background: white; border: 1px solid #ccc; color: #333; } QPushButton:hover { background: #f5f5f5; }")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn_layout = QHBoxLayout()
        reset_btn_layout.addStretch()
        reset_btn_layout.addWidget(self.reset_btn)
        reset_btn_layout.addStretch()
        main_layout.addLayout(reset_btn_layout)
        main_layout.addSpacing(15)

        # --- Two-column layout ---
        columns_layout = QHBoxLayout()
        # Left column: FPS and Intro
        left_form = QFormLayout()
        self.fps_combo = QComboBox(self)
        self.fps_combo.setFixedWidth(120)
        for label, value in self.fps_options:
            self.fps_combo.addItem(label, value)
        if self.settings is not None:
            default_fps = self.settings.value('default_fps', type=int)
        else:
            default_fps = None
        if default_fps is not None:
            idx = next((i for i, (label, value) in enumerate(self.fps_options) if value == default_fps), 0)
            self.fps_combo.setCurrentIndex(idx)
        else:
            self.fps_combo.setCurrentIndex(0)
        left_form.addRow("FPS:", self.fps_combo)
        # --- Default Intro Path ---
        intro_path_layout = QHBoxLayout()
        self.default_intro_path_edit = QLineEdit()
        self.default_intro_path_edit.setFixedWidth(120)
        if self.settings is not None:
            self.default_intro_path_edit.setText(self.settings.value('default_intro_path', '', type=str))
        self.default_intro_path_btn = QPushButton('...')
        self.default_intro_path_btn.setFixedWidth(32)
        def pick_intro_path():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Default Intro Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.default_intro_path_edit.setText(file_path)
        self.default_intro_path_btn.clicked.connect(pick_intro_path)
        intro_path_layout.addWidget(self.default_intro_path_edit)
        intro_path_layout.addWidget(self.default_intro_path_btn)
        left_form.addRow("Intro Path:", intro_path_layout)
        # --- Default Intro Position ---
        self.default_intro_position_combo = QComboBox()
        self.default_intro_position_combo.setFixedWidth(120)
        intro_positions = [
            ("Center", "center"),
            ("Top Left", "top_left"),
            ("Top Right", "top_right"),
            ("Bottom Left", "bottom_left"),
            ("Bottom Right", "bottom_right")
        ]
        for label, value in intro_positions:
            self.default_intro_position_combo.addItem(label, value)
        if self.settings is not None:
            default_intro_position = self.settings.value('default_intro_position', 'center', type=str)
            idx = next((i for i, (label, value) in enumerate(intro_positions) if value == default_intro_position), 0)
            self.default_intro_position_combo.setCurrentIndex(idx)
        left_form.addRow("Intro Position:", self.default_intro_position_combo)
        # --- Default Intro Size ---
        self.default_intro_size_combo = QComboBox()
        self.default_intro_size_combo.setFixedWidth(120)
        for percent in range(5, 101, 5):
            self.default_intro_size_combo.addItem(f"{percent}%", percent)
        if self.settings is not None:
            default_intro_size = self.settings.value('default_intro_size', 50, type=int)
            idx = (default_intro_size // 5) - 1 if 5 <= default_intro_size <= 100 else 9
            self.default_intro_size_combo.setCurrentIndex(idx)
        left_form.addRow("Intro Size:", self.default_intro_size_combo)
        # --- Default Intro Enabled Checkbox ---
        self.default_intro_enabled_checkbox = QtWidgets.QCheckBox("Enable Intro Defaults")
        self.default_intro_enabled_checkbox.setChecked(
            self.settings.value('default_intro_enabled', True, type=bool) if self.settings is not None else True
        )
        left_form.addRow("Intro Defaults:", self.default_intro_enabled_checkbox)
        # --- Default Overlay 1 Enabled Checkbox ---
        self.default_overlay1_enabled_checkbox = QtWidgets.QCheckBox("Enable Overlay 1 Defaults")
        self.default_overlay1_enabled_checkbox.setChecked(
            self.settings.value('default_overlay1_enabled', True, type=bool) if self.settings is not None else True
        )
        left_form.addRow("Overlay 1 Defaults:", self.default_overlay1_enabled_checkbox)
        # --- Default Overlay 2 Enabled Checkbox ---
        self.default_overlay2_enabled_checkbox = QtWidgets.QCheckBox("Enable Overlay 2 Defaults")
        self.default_overlay2_enabled_checkbox.setChecked(
            self.settings.value('default_overlay2_enabled', True, type=bool) if self.settings is not None else True
        )
        left_form.addRow("Overlay 2 Defaults:", self.default_overlay2_enabled_checkbox)

        # Right column: Overlay 1 and 2
        right_form = QFormLayout()
        # --- Default Overlay 1 Path ---
        overlay1_path_layout = QHBoxLayout()
        self.default_overlay1_path_edit = QLineEdit()
        self.default_overlay1_path_edit.setFixedWidth(120)
        if self.settings is not None:
            self.default_overlay1_path_edit.setText(self.settings.value('default_overlay1_path', '', type=str))
        self.default_overlay1_path_btn = QPushButton('...')
        self.default_overlay1_path_btn.setFixedWidth(32)
        def pick_overlay1_path():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Default Overlay 1 Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.default_overlay1_path_edit.setText(file_path)
        self.default_overlay1_path_btn.clicked.connect(pick_overlay1_path)
        overlay1_path_layout.addWidget(self.default_overlay1_path_edit)
        overlay1_path_layout.addWidget(self.default_overlay1_path_btn)
        right_form.addRow("Overlay 1 Path:", overlay1_path_layout)
        # --- Default Overlay 1 Position ---
        self.default_overlay1_position_combo = QComboBox()
        self.default_overlay1_position_combo.setFixedWidth(120)
        for label, value in intro_positions:
            self.default_overlay1_position_combo.addItem(label, value)
        if self.settings is not None:
            default_overlay1_position = self.settings.value('default_overlay1_position', 'bottom_left', type=str)
            idx = next((i for i, (label, value) in enumerate(intro_positions) if value == default_overlay1_position), 3)
            self.default_overlay1_position_combo.setCurrentIndex(idx)
        right_form.addRow("Overlay 1 Position:", self.default_overlay1_position_combo)
        # --- Default Overlay 1 Size ---
        self.default_overlay1_size_combo = QComboBox()
        self.default_overlay1_size_combo.setFixedWidth(120)
        for percent in range(5, 101, 5):
            self.default_overlay1_size_combo.addItem(f"{percent}%", percent)
        if self.settings is not None:
            default_overlay1_size = self.settings.value('default_overlay1_size', 15, type=int)
            idx = (default_overlay1_size // 5) - 1 if 5 <= default_overlay1_size <= 100 else 2
            self.default_overlay1_size_combo.setCurrentIndex(idx)
        right_form.addRow("Overlay 1 Size:", self.default_overlay1_size_combo)
        # --- Default Overlay 2 Path ---
        overlay2_path_layout = QHBoxLayout()
        self.default_overlay2_path_edit = QLineEdit()
        self.default_overlay2_path_edit.setFixedWidth(120)
        if self.settings is not None:
            self.default_overlay2_path_edit.setText(self.settings.value('default_overlay2_path', '', type=str))
        self.default_overlay2_path_btn = QPushButton('...')
        self.default_overlay2_path_btn.setFixedWidth(32)
        def pick_overlay2_path():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Default Overlay 2 Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.default_overlay2_path_edit.setText(file_path)
        self.default_overlay2_path_btn.clicked.connect(pick_overlay2_path)
        overlay2_path_layout.addWidget(self.default_overlay2_path_edit)
        overlay2_path_layout.addWidget(self.default_overlay2_path_btn)
        right_form.addRow("Overlay 2 Path:", overlay2_path_layout)
        # --- Default Overlay 2 Position ---
        self.default_overlay2_position_combo = QComboBox()
        self.default_overlay2_position_combo.setFixedWidth(120)
        for label, value in intro_positions:
            self.default_overlay2_position_combo.addItem(label, value)
        if self.settings is not None:
            default_overlay2_position = self.settings.value('default_overlay2_position', 'top_right', type=str)
            idx = next((i for i, (label, value) in enumerate(intro_positions) if value == default_overlay2_position), 2)
            self.default_overlay2_position_combo.setCurrentIndex(idx)
        right_form.addRow("Overlay 2 Position:", self.default_overlay2_position_combo)
        # --- Default Overlay 2 Size ---
        self.default_overlay2_size_combo = QComboBox()
        self.default_overlay2_size_combo.setFixedWidth(120)
        for percent in range(5, 101, 5):
            self.default_overlay2_size_combo.addItem(f"{percent}%", percent)
        if self.settings is not None:
            default_overlay2_size = self.settings.value('default_overlay2_size', 15, type=int)
            idx = (default_overlay2_size // 5) - 1 if 5 <= default_overlay2_size <= 100 else 2
            self.default_overlay2_size_combo.setCurrentIndex(idx)
        right_form.addRow("Overlay 2 Size:", self.default_overlay2_size_combo)

        # Add both forms to columns_layout
        columns_layout.addSpacing(20)
        columns_layout.addLayout(left_form)
        columns_layout.addSpacing(-25)  # Reduced from 30 to 10
        columns_layout.addLayout(right_form)
        main_layout.addLayout(columns_layout)

        # Add more space before the button row
        main_layout.addSpacing(7)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.setFixedSize(100, 32)
        self.cancel_btn.setFixedSize(100, 32)
        button_layout.addWidget(self.save_btn)
        button_layout.addSpacing(20)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        main_layout.addSpacing(12)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.setFixedSize(640, 520)
    def accept(self):
        self.selected_fps = self.fps_combo.currentData()
        if self.settings is not None:
            self.settings.setValue('default_fps', self.selected_fps)
            self.settings.setValue('default_intro_enabled', self.default_intro_enabled_checkbox.isChecked())
            self.settings.setValue('default_overlay1_enabled', self.default_overlay1_enabled_checkbox.isChecked())
            self.settings.setValue('default_overlay2_enabled', self.default_overlay2_enabled_checkbox.isChecked())
            self.settings.setValue('default_intro_path', self.default_intro_path_edit.text())
            self.settings.setValue('default_intro_position', self.default_intro_position_combo.currentData())
            self.settings.setValue('default_intro_size', self.default_intro_size_combo.currentData())
            self.settings.setValue('default_overlay1_path', self.default_overlay1_path_edit.text())
            self.settings.setValue('default_overlay1_position', self.default_overlay1_position_combo.currentData())
            self.settings.setValue('default_overlay1_size', self.default_overlay1_size_combo.currentData())
            self.settings.setValue('default_overlay2_path', self.default_overlay2_path_edit.text())
            self.settings.setValue('default_overlay2_position', self.default_overlay2_position_combo.currentData())
            self.settings.setValue('default_overlay2_size', self.default_overlay2_size_combo.currentData())
        super().accept()

    def reset_to_defaults(self):
        # FPS
        self.fps_combo.setCurrentIndex(0)
        # Intro
        self.default_intro_enabled_checkbox.setChecked(True)
        self.default_intro_path_edit.setText("")
        self.default_intro_position_combo.setCurrentIndex(0)  # Center
        idx_intro_size = (50 // 5) - 1  # 50% size
        self.default_intro_size_combo.setCurrentIndex(idx_intro_size)
        # Overlay 1
        self.default_overlay1_enabled_checkbox.setChecked(True)
        self.default_overlay1_path_edit.setText("")
        self.default_overlay1_position_combo.setCurrentIndex(3)  # Bottom Left
        idx_overlay1_size = (15 // 5) - 1  # 15% size
        self.default_overlay1_size_combo.setCurrentIndex(idx_overlay1_size)
        # Overlay 2
        self.default_overlay2_enabled_checkbox.setChecked(True)
        self.default_overlay2_path_edit.setText("")
        self.default_overlay2_position_combo.setCurrentIndex(2)  # Top Right
        idx_overlay2_size = (15 // 5) - 1  # 15% size
        self.default_overlay2_size_combo.setCurrentIndex(idx_overlay2_size)

class NameListDialog(QDialog):
    def __init__(self, parent=None, initial_names=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Name List")
        self.setModal(True)
        self.setMinimumSize(400, 350)
        layout = QVBoxLayout(self)
        label = QLabel("Enter one name per line (max 180 chars per line). Each name will be used for one video batch.")
        label.setWordWrap(True)
        layout.addWidget(label)
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        if initial_names:
            self.set_names(initial_names)
        layout.addWidget(self.text_edit)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)
        # Button box with Preview
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.preview_btn = QPushButton("Preview")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        btn_width = 90
        self.preview_btn.setFixedWidth(btn_width)
        self.ok_btn.setFixedWidth(btn_width)
        self.cancel_btn.setFixedWidth(btn_width)
        self.preview_btn.setStyleSheet("background-color: white; color: black; border: 1px solid #cfcfcf;")
        button_layout.addWidget(self.preview_btn)
        button_layout.addSpacing(12)
        button_layout.addWidget(self.ok_btn)
        button_layout.addSpacing(12)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.preview_btn.clicked.connect(self.open_preview_dialog)
    def set_names(self, names):
        # Show indicators
        lines = [f"{i+1}. {name}" for i, name in enumerate(names)]
        self.text_edit.setPlainText("\n".join(lines))
    def get_names(self):
        # Strip indicators
        lines = self.text_edit.toPlainText().splitlines()
        names = []
        for line in lines:
            if ". " in line:
                name = line.split(". ", 1)[1].strip()
            else:
                name = line.strip()
            if name:
                names.append(name)
        return names
    def accept(self):
        # On accept, re-apply indicators for display, but only save names
        names = self.get_names()
        for name in names:
            if len(name) > 180:
                self.error_label.setText(f"A name exceeds 180 characters: {name[:30]}...")
                return
        if not names:
            self.error_label.setText("Name list cannot be empty.")
            return
        self._names = names
        super().accept()
    def open_preview_dialog(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QPlainTextEdit
        dlg = QDialog(self)
        dlg.setWindowTitle("Preview Name List")
        dlg.setMinimumSize(350, 300)
        layout = QVBoxLayout(dlg)
        label = QLabel("Current name list:")
        layout.addWidget(label)
        preview_text = QPlainTextEdit()
        preview_text.setReadOnly(True)
        names = self.get_names()
        if names:
            lines = [f"{i+1}. {name}" for i, name in enumerate(names)]
            preview_text.setPlainText("\n".join(lines))
        else:
            preview_text.setPlainText("(No names entered)")
        layout.addWidget(preview_text)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dlg.accept)
        layout.addWidget(button_box)
        dlg.exec()