# This file uses PyQt6
import os
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog, QComboBox, QDialogButtonBox, QFormLayout,
    QColorDialog
)
from PyQt6.QtCore import Qt, QSettings, QThread, QPoint, QSize, QTimer
from PyQt6.QtGui import QIntValidator, QIcon, QPixmap, QMovie, QImage, QShortcut, QKeySequence, QColor
from src.logger import logger

# Force console output to be visible (safe for .pyw)
import sys
if getattr(sys, 'stdout', None) is not None:
    try:
        sys.stdout.flush()
    except Exception:
        pass
if getattr(sys, 'stderr', None) is not None:
    try:
        sys.stderr.flush()
    except Exception:
        pass

from src.config import (
    WINDOW_SIZE, WINDOW_TITLE, ICON_PATH, STYLE_SHEET,
    DEFAULT_CODECS, DEFAULT_RESOLUTIONS, DEFAULT_FPS_OPTIONS,
    DEFAULT_EXPORT_NAME, DEFAULT_START_NUMBER, DEFAULT_FPS,
    DEFAULT_RESOLUTION, DEFAULT_CODEC, check_ffmpeg_installation,
    DEFAULT_MIN_MP3_COUNT,
    PROJECT_ROOT,
    DEFAULT_FFMPEG_PRESETS, DEFAULT_FFMPEG_PRESET,
    DEFAULT_AUDIO_BITRATE_OPTIONS, DEFAULT_AUDIO_BITRATE,
    DEFAULT_VIDEO_BITRATE_OPTIONS, DEFAULT_VIDEO_BITRATE,
    DEFAULT_MAXRATE_OPTIONS, DEFAULT_MAXRATE,
    DEFAULT_BUFSIZE_OPTIONS, DEFAULT_BUFSIZE
)
from src.utils import (
    sanitize_filename, get_desktop_folder, open_folder_in_explorer,
    validate_inputs, validate_media_files, clean_file_path
)
from src.ui_components import FolderDropLineEdit, WaitingDialog, PleaseWaitDialog, StoppedDialog, SuccessDialog, ScrollableErrorDialog, ImageDropLineEdit
from src.video_worker import VideoWorker
from src.terminal_widget import TerminalWidget

import time
import threading

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
        # Right column: Overlay 1 and 2 (define right_form first so it can be used for intro fields)
        right_form = QFormLayout()
        # Left column: FPS and Intro
        left_form = QFormLayout()
        # --- Default MP3 # Enabled Checkbox ---
        self.default_mp3_count_enabled_checkbox = QtWidgets.QCheckBox("Enable MP3 #")
        self.default_mp3_count_enabled_checkbox.setChecked(
            self.settings.value('default_mp3_count_enabled', False, type=bool) if self.settings is not None else False
        )
        # --- Default List Name Enabled Checkbox ---
        self.default_list_name_enabled_checkbox = QtWidgets.QCheckBox("Enable List Name")
        self.default_list_name_enabled_checkbox.setChecked(
            self.settings.value('default_list_name_enabled', False, type=bool) if self.settings is not None else False
        )
        # --- Default Intro Enabled Checkbox ---
        self.default_intro_enabled_checkbox = QtWidgets.QCheckBox("Enable Intro")
        self.default_intro_enabled_checkbox.setChecked(
            self.settings.value('default_intro_enabled', True, type=bool) if self.settings is not None else True
        )
        # --- Default Overlay 1 Enabled Checkbox ---
        self.default_overlay1_enabled_checkbox = QtWidgets.QCheckBox("Enable Overlay 1")
        self.default_overlay1_enabled_checkbox.setChecked(
            self.settings.value('default_overlay1_enabled', True, type=bool) if self.settings is not None else True
        )
        # --- Default Overlay 2 Enabled Checkbox ---
        self.default_overlay2_enabled_checkbox = QtWidgets.QCheckBox("Enable Overlay 2")
        self.default_overlay2_enabled_checkbox.setChecked(
            self.settings.value('default_overlay2_enabled', True, type=bool) if self.settings is not None else True
        )
        # --- FPS Combo ---
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
        # --- Resolution Combo ---
        self.resolution_combo = QComboBox(self)
        self.resolution_combo.setFixedWidth(120)
        for label, value in DEFAULT_RESOLUTIONS:
            self.resolution_combo.addItem(label, value)
        if self.settings is not None:
            default_resolution = self.settings.value('default_resolution', type=str)
        else:
            default_resolution = None
        if default_resolution is not None:
            idx = next((i for i, (label, value) in enumerate(DEFAULT_RESOLUTIONS) if value == default_resolution), 0)
            self.resolution_combo.setCurrentIndex(idx)
        else:
            self.resolution_combo.setCurrentIndex(0)
        # --- FFmpeg Preset Combo ---
        self.preset_combo = QComboBox(self)
        self.preset_combo.setFixedWidth(120)
        for label, value in DEFAULT_FFMPEG_PRESETS:
            self.preset_combo.addItem(label, value)
        if self.settings is not None:
            default_preset = self.settings.value('default_ffmpeg_preset', DEFAULT_FFMPEG_PRESET, type=str)
        else:
            default_preset = DEFAULT_FFMPEG_PRESET
        idx = next((i for i, (label, value) in enumerate(DEFAULT_FFMPEG_PRESETS) if value == default_preset), 6)
        self.preset_combo.setCurrentIndex(idx)
        # --- FFmpeg Audio Bitrate Combo ---
        self.audio_bitrate_combo = QComboBox(self)
        self.audio_bitrate_combo.setFixedWidth(120)
        for label, value in DEFAULT_AUDIO_BITRATE_OPTIONS:
            self.audio_bitrate_combo.addItem(label, value)
        if self.settings is not None:
            default_audio_bitrate = self.settings.value('default_ffmpeg_audio_bitrate', DEFAULT_AUDIO_BITRATE, type=str)
        else:
            default_audio_bitrate = DEFAULT_AUDIO_BITRATE
        idx = next((i for i, (label, value) in enumerate(DEFAULT_AUDIO_BITRATE_OPTIONS) if value == default_audio_bitrate), 5)
        self.audio_bitrate_combo.setCurrentIndex(idx)
        # --- FFmpeg Video Bitrate Combo ---
        self.video_bitrate_combo = QComboBox(self)
        self.video_bitrate_combo.setFixedWidth(120)
        for label, value in DEFAULT_VIDEO_BITRATE_OPTIONS:
            self.video_bitrate_combo.addItem(label, value)
        if self.settings is not None:
            default_video_bitrate = self.settings.value('default_ffmpeg_video_bitrate', DEFAULT_VIDEO_BITRATE, type=str)
        else:
            default_video_bitrate = DEFAULT_VIDEO_BITRATE
        idx = next((i for i, (label, value) in enumerate(DEFAULT_VIDEO_BITRATE_OPTIONS) if value == default_video_bitrate), 5)
        self.video_bitrate_combo.setCurrentIndex(idx)
        # --- FFmpeg Maxrate Combo ---
        self.maxrate_combo = QComboBox(self)
        self.maxrate_combo.setFixedWidth(120)
        for label, value in DEFAULT_MAXRATE_OPTIONS:
            self.maxrate_combo.addItem(label, value)
        if self.settings is not None:
            default_maxrate = self.settings.value('default_ffmpeg_maxrate', DEFAULT_MAXRATE, type=str)
        else:
            default_maxrate = DEFAULT_MAXRATE
        idx = next((i for i, (label, value) in enumerate(DEFAULT_MAXRATE_OPTIONS) if value == default_maxrate), 5)
        self.maxrate_combo.setCurrentIndex(idx)
        # --- FFmpeg Bufsize Combo ---
        self.bufsize_combo = QComboBox(self)
        self.bufsize_combo.setFixedWidth(120)
        for label, value in DEFAULT_BUFSIZE_OPTIONS:
            self.bufsize_combo.addItem(label, value)
        if self.settings is not None:
            default_bufsize = self.settings.value('default_ffmpeg_bufsize', DEFAULT_BUFSIZE, type=str)
        else:
            default_bufsize = DEFAULT_BUFSIZE
        idx = next((i for i, (label, value) in enumerate(DEFAULT_BUFSIZE_OPTIONS) if value == default_bufsize), 4)
        self.bufsize_combo.setCurrentIndex(idx)
        # Add to left_form in new order with reduced spacing
        left_form.addRow("MP3 # Default:", self.default_mp3_count_enabled_checkbox)
        left_form.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))
        left_form.addRow("List Name Default:", self.default_list_name_enabled_checkbox)
        left_form.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))
        left_form.addRow("Intro Defaults:", self.default_intro_enabled_checkbox)
        left_form.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))
        left_form.addRow("Overlay 1 Defaults:", self.default_overlay1_enabled_checkbox)
        left_form.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))
        left_form.addRow("Overlay 2 Defaults:", self.default_overlay2_enabled_checkbox)
        left_form.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))
        left_form.addRow("FPS:", self.fps_combo)
        left_form.addRow("Resolution:", self.resolution_combo)
        left_form.addRow("FFmpeg Preset:", self.preset_combo)
        left_form.addRow("Audio Bitrate:", self.audio_bitrate_combo)
        left_form.addRow("Video Bitrate:", self.video_bitrate_combo)
        left_form.addRow("Maxrate:", self.maxrate_combo)
        left_form.addRow("Bufsize:", self.bufsize_combo)
        # --- Default Intro Path ---
        intro_path_layout = QHBoxLayout()
        self.default_intro_path_edit = QLineEdit()
        self.default_intro_path_edit.setFixedWidth(120)
        if self.settings is not None:
            self.default_intro_path_edit.setText(self.settings.value('default_intro_path', '', type=str))
        
        # Add text change handler to clean file paths
        def clean_default_intro_path():
            current_text = self.default_intro_path_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.default_intro_path_edit.setText(cleaned_text)
        self.default_intro_path_edit.textChanged.connect(clean_default_intro_path)
        self.default_intro_path_btn = QPushButton('...')
        self.default_intro_path_btn.setFixedWidth(32)
        def pick_intro_path():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Default Intro Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.default_intro_path_edit.setText(file_path)
        self.default_intro_path_btn.clicked.connect(pick_intro_path)
        intro_path_layout.addWidget(self.default_intro_path_edit)
        intro_path_layout.addWidget(self.default_intro_path_btn)
        right_form.addRow("Intro Path:", intro_path_layout)
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
        right_form.addRow("Intro Position:", self.default_intro_position_combo)
        # --- Default Intro Size ---
        self.default_intro_size_combo = QComboBox()
        self.default_intro_size_combo.setFixedWidth(120)
        for percent in range(5, 101, 5):
            self.default_intro_size_combo.addItem(f"{percent}%", percent)
        if self.settings is not None:
            default_intro_size = self.settings.value('default_intro_size', 50, type=int)
            idx = (default_intro_size // 5) - 1 if 5 <= default_intro_size <= 100 else 9
            self.default_intro_size_combo.setCurrentIndex(idx)
        right_form.addRow("Intro Size:", self.default_intro_size_combo)
        # --- Default Overlay 1 Path ---
        overlay1_path_layout = QHBoxLayout()
        self.default_overlay1_path_edit = QLineEdit()
        self.default_overlay1_path_edit.setFixedWidth(120)
        if self.settings is not None:
            self.default_overlay1_path_edit.setText(self.settings.value('default_overlay1_path', '', type=str))
        
        # Add text change handler to clean file paths
        def clean_default_overlay1_path():
            current_text = self.default_overlay1_path_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.default_overlay1_path_edit.setText(cleaned_text)
        self.default_overlay1_path_edit.textChanged.connect(clean_default_overlay1_path)
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
        
        # Add text change handler to clean file paths
        def clean_default_overlay2_path():
            current_text = self.default_overlay2_path_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.default_overlay2_path_edit.setText(cleaned_text)
        self.default_overlay2_path_edit.textChanged.connect(clean_default_overlay2_path)
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
        columns_layout.addSpacing(45)  # Increased spacing between columns
        columns_layout.addLayout(right_form)
        main_layout.addLayout(columns_layout)

        # Add more space before the button row
        main_layout.addSpacing(15)
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
        self.setFixedSize(640, 640)
    def accept(self):
        self.selected_fps = self.fps_combo.currentData()
        if self.settings is not None:
            self.settings.setValue('default_fps', self.selected_fps)
            self.settings.setValue('default_intro_enabled', self.default_intro_enabled_checkbox.isChecked())
            self.settings.setValue('default_intro_path', self.default_intro_path_edit.text())
            self.settings.setValue('default_intro_position', self.default_intro_position_combo.currentData())
            self.settings.setValue('default_intro_size', self.default_intro_size_combo.currentData())
            self.settings.setValue('default_overlay1_path', self.default_overlay1_path_edit.text())
            self.settings.setValue('default_overlay1_position', self.default_overlay1_position_combo.currentData())
            self.settings.setValue('default_overlay1_size', self.default_overlay1_size_combo.currentData())
            self.settings.setValue('default_overlay2_path', self.default_overlay2_path_edit.text())
            self.settings.setValue('default_overlay2_position', self.default_overlay2_position_combo.currentData())
            self.settings.setValue('default_overlay2_size', self.default_overlay2_size_combo.currentData())
            self.settings.setValue('default_overlay1_enabled', self.default_overlay1_enabled_checkbox.isChecked())
            self.settings.setValue('default_overlay2_enabled', self.default_overlay2_enabled_checkbox.isChecked())
            self.settings.setValue('default_list_name_enabled', self.default_list_name_enabled_checkbox.isChecked())
            self.settings.setValue('default_mp3_count_enabled', self.default_mp3_count_enabled_checkbox.isChecked())
            self.settings.setValue('default_resolution', self.resolution_combo.currentData())
            self.settings.setValue('default_ffmpeg_preset', self.preset_combo.currentData())
            self.settings.setValue('default_ffmpeg_audio_bitrate', self.audio_bitrate_combo.currentData())
            self.settings.setValue('default_ffmpeg_video_bitrate', self.video_bitrate_combo.currentData())
            self.settings.setValue('default_ffmpeg_maxrate', self.maxrate_combo.currentData())
            self.settings.setValue('default_ffmpeg_bufsize', self.bufsize_combo.currentData())
        super().accept()

    def reset_to_defaults(self):
        # FPS
        self.fps_combo.setCurrentIndex(0)
        # Resolution
        self.resolution_combo.setCurrentIndex(0)
        # FFmpeg Preset
        self.preset_combo.setCurrentIndex(6)  # 'slow' is default
        # FFmpeg Audio Bitrate
        self.audio_bitrate_combo.setCurrentIndex(5)  # '384k' is default
        # FFmpeg Video Bitrate
        self.video_bitrate_combo.setCurrentIndex(5)  # '12M' is default
        # Maxrate
        self.maxrate_combo.setCurrentIndex(5)  # '16M' is default
        # Bufsize
        self.bufsize_combo.setCurrentIndex(4)  # '24M' is default
        # Intro
        self.default_intro_enabled_checkbox.setChecked(True)
        self.default_intro_path_edit.setText("")
        self.default_intro_position_combo.setCurrentIndex(0)  # Center
        idx_intro_size = (50 // 5) - 1  # 50% size
        self.default_intro_size_combo.setCurrentIndex(idx_intro_size)
        # Overlay 1
        self.default_overlay1_path_edit.setText("")
        self.default_overlay1_position_combo.setCurrentIndex(3)  # Bottom Left
        idx_overlay1_size = (15 // 5) - 1  # 15% size
        self.default_overlay1_size_combo.setCurrentIndex(idx_overlay1_size)
        self.default_overlay1_enabled_checkbox.setChecked(True)
        # Overlay 2
        self.default_overlay2_path_edit.setText("")
        self.default_overlay2_position_combo.setCurrentIndex(2)  # Top Right
        idx_overlay2_size = (15 // 5) - 1  # 15% size
        self.default_overlay2_size_combo.setCurrentIndex(idx_overlay2_size)
        self.default_overlay2_enabled_checkbox.setChecked(True)
        # List Name
        self.default_list_name_enabled_checkbox.setChecked(False)
        # MP3 #
        self.default_mp3_count_enabled_checkbox.setChecked(False)

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

class SuccessWithLeftoverDialog(QDialog):
    """Dialog shown when video creation completes successfully but with leftover files"""
    def __init__(self, parent=None, open_folder=None, leftover_mp3s=None, leftover_images=None, min_mp3_count=3):
        super().__init__(parent)
        self.open_folder = open_folder
        self.setWindowTitle("Task Completed")
        
        # Calculate dialog height based on leftover files
        extra_height = 0
        if leftover_mp3s:
            extra_height += 50 + 15 * len(leftover_mp3s)
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
        btn_row.addSpacerItem(QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))

        self.folder_btn = QPushButton("Result Folder")
        self.folder_btn.setMinimumWidth(120)
        self.folder_btn.clicked.connect(self.on_folder)
        btn_row.addWidget(self.folder_btn)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.ok_btn)

        btn_row.addSpacerItem(QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum))
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

class SuperCutUI(QWidget):
    """Main application window for SuperCut Video Maker"""
    
    def __init__(self):
        super().__init__()
        self.output_folder_manual = False
        self._worker = None
        self._thread = None
        self._stopped_by_user = False
        self._auto_close_on_stop = False
        self._stopping_msgbox = None
        self.terminal_widget = None
        self.settings = QSettings('SuperCut', 'SuperCutUI')
        self._original_size = None  # Store original window size
        self._expanded_for_progress = False  # Track if expanded
        
        self.init_ui()
        self.restore_window_position()
        self.setup_shortcuts()
        self.update_output_name()

    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setWindowTitle(WINDOW_TITLE)
        self.setFixedSize(WINDOW_SIZE[0], WINDOW_SIZE[1])
        self.setStyleSheet(STYLE_SHEET)
        
        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Add program title with icon at the top ---
        layout.addSpacing(0)
        title_widget = QtWidgets.QWidget()
        title_widget.setFixedHeight(75)
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        # Add PNG logo in front of SuperCut title
        title_icon = QLabel()
        title_icon.setPixmap(QPixmap(os.path.join(PROJECT_ROOT, "src", "sources", "icon.png")).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title_label = QLabel("SuperCut")
        title_label.setStyleSheet("font-size: 35px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        static_icon = QLabel()
        static_icon.setPixmap(QPixmap(os.path.join(PROJECT_ROOT, "src", "sources", "static.png")))
        static_icon.setVisible(True)  # Show by default
        self.static_icon = static_icon  # Store as instance variable for later control
        spinner_label = QLabel()
        spinner_movie = QMovie(os.path.join(PROJECT_ROOT, "src", "sources", "spinner.gif"))
        spinner_label.setMovie(spinner_movie)       
        spinner_movie.start()
        spinner_label.setVisible(False)  # Hide by default
        self.spinner_label = spinner_label  # Store as instance variable for later control
        # Add loading.gif after spinner gif
        loading_label = QLabel()
        loading_movie = QMovie(os.path.join(PROJECT_ROOT, "src", "sources", "loading.gif"))
        loading_label.setMovie(loading_movie)
        loading_label.setStyleSheet("margin-top: 18px;")
        loading_label.setVisible(False)
        self.loading_label = loading_label  # Store as instance variable for later control
        title_layout.addSpacing(80)
        title_layout.addStretch()
        title_layout.addWidget(title_icon)
        # Add spacing after title label
        title_layout.addSpacing(1)
        title_layout.addWidget(title_label)
        title_layout.addSpacing(10)
        title_layout.addWidget(static_icon)
        # Add empty button holder (placeholder) size 16x4 after static icon
        self.title_placeholder_btn = QPushButton()
        self.title_placeholder_btn.setFixedSize(24, 4)
        self.title_placeholder_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self.title_placeholder_btn.setEnabled(False)
        self.title_placeholder_btn.setVisible(self.static_icon.isVisible())
        title_layout.addWidget(self.title_placeholder_btn)
        title_layout.addWidget(spinner_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        title_layout.addWidget(loading_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        title_layout.addStretch()
        title_widget.setLayout(title_layout)
        layout.addWidget(title_widget)
        # Add spacer below title bar to prevent overlap
        layout.addSpacing(50)
        # --- End program title ---

        # Add UI components
        self.create_folder_inputs(layout)
        self.create_export_inputs(layout)
        self.create_video_settings(layout)
        self.create_action_buttons(layout)
        self.create_progress_controls(layout)
        
        self.setLayout(layout)
        self.update_output_name()
        # Apply intro defaults on startup
        self.apply_settings()
        # Connect text change for media_sources_edit and folder_edit
        self.media_sources_edit.textChanged.connect(self.on_media_folder_changed)
        self.folder_edit.textChanged.connect(self.update_output_name)
        self.folder_edit.textChanged.connect(self.on_output_folder_changed)

    def create_folder_inputs(self, layout):
        """Create folder selection inputs"""
        folder_row_style = {
            "label_width": 90,
            "edit_min_width": 220,
            "btn_width": 110
        }

        # Media Folder input
        media_sources_layout = QHBoxLayout()
        label_media = QLabel("Media Folder:")
        label_media.setFixedWidth(folder_row_style["label_width"])
        
        self.media_sources_edit = FolderDropLineEdit()
        self.media_sources_edit.setReadOnly(False)
        self.media_sources_edit.setMinimumWidth(folder_row_style["edit_min_width"])
        self.media_sources_edit.setPlaceholderText("Drag & drop or click Select Folder")
        self.media_sources_edit.setToolTip("Drag and drop a folder here or click 'Select Folder'")
        
        # Add text change handler to clean file paths
        def clean_media_folder_path():
            current_text = self.media_sources_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.media_sources_edit.setText(cleaned_text)
        self.media_sources_edit.textChanged.connect(clean_media_folder_path)
        
        media_sources_btn = QPushButton("Select Folder")
        media_sources_btn.setFixedWidth(folder_row_style["btn_width"])
        media_sources_btn.clicked.connect(self.select_media_sources_folder)
        self.media_sources_select_btn = media_sources_btn
        
        media_sources_layout.addWidget(label_media)
        media_sources_layout.addWidget(self.media_sources_edit)
        media_sources_layout.addWidget(media_sources_btn)
        layout.addLayout(media_sources_layout)

        # Output folder selection
        folder_layout = QHBoxLayout()
        label_output = QLabel("Output Folder:")
        label_output.setFixedWidth(folder_row_style["label_width"] + 1)
        
        self.folder_edit = FolderDropLineEdit()
        self.folder_edit.setReadOnly(False)
        self.folder_edit.setMinimumWidth(folder_row_style["edit_min_width"])
        self.folder_edit.setPlaceholderText("Drag & drop or click Select Folder")
        self.folder_edit.setToolTip("Drag and drop a folder here or click 'Select Folder'")
        
        # Add text change handler to clean file paths
        def clean_output_folder_path():
            current_text = self.folder_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.folder_edit.setText(cleaned_text)
        self.folder_edit.textChanged.connect(clean_output_folder_path)
        
        folder_btn = QPushButton("Select Folder")
        folder_btn.setFixedWidth(folder_row_style["btn_width"])
        folder_btn.clicked.connect(self.select_output_folder)
        self.output_folder_select_btn = folder_btn
        
        folder_layout.addWidget(label_output)
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)

    def create_export_inputs(self, layout):
        """Create export name, number, and mp3 per video inputs"""
        part_layout = QHBoxLayout()
        self.part1_edit = QLineEdit(DEFAULT_EXPORT_NAME)
        self.part1_edit.setPlaceholderText("Export Name")
        self.part1_edit.setFixedWidth(100)  # Make Name textbox wider
        self.part2_edit = QLineEdit(DEFAULT_START_NUMBER)
        self.part2_edit.setPlaceholderText("12345")
        self.part2_edit.setValidator(QIntValidator(1, 9999999, self))
        self.part2_edit.setFixedWidth(60)   # Make Number textbox smaller
        # --- Name list option ---
        self.name_list_checkbox = QtWidgets.QCheckBox("List name:")
        self.name_list_checkbox.setChecked(True)
        self.name_list_enter_btn = QPushButton("Enter")
        self.name_list_enter_btn.setFixedWidth(60)
        # Remove Preview button from main UI if present
        # self.name_list_preview_btn = QPushButton("Preview")
        # self.name_list_preview_btn.setFixedWidth(70)
        # Remove initial setEnabled, always update via handler
        # Set initial style for name_list_enter_btn
        self.name_list = []  # Store the name list
        self.name_list_dialog = None
        def update_name_list_controls():
            checked = self.name_list_checkbox.isChecked()
            self.name_list_enter_btn.setEnabled(checked)
            # self.name_list_preview_btn.setEnabled(checked)
            self.part1_edit.setEnabled(not checked)
            self.part2_edit.setEnabled(not checked)
            if checked:
                self.name_list_enter_btn.setStyleSheet("")
                # self.name_list_preview_btn.setStyleSheet("")
                self.part1_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.part2_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
            else:
                self.name_list_enter_btn.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                # self.name_list_preview_btn.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.part1_edit.setStyleSheet("")
                self.part2_edit.setStyleSheet("")
            if not checked:
                self.name_list = []
        self.name_list_checkbox.stateChanged.connect(lambda _: update_name_list_controls())
        # Apply logic for initial state
        update_name_list_controls()
        def open_name_list_dialog():
            dlg = NameListDialog(self, self.name_list)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.name_list = dlg.get_names()
        self.name_list_enter_btn.clicked.connect(open_name_list_dialog)
        # --- End name list option ---
        self.mp3_count_checkbox = QtWidgets.QCheckBox("MP3 #")
        self.mp3_count_checkbox.setChecked(False)
        self.mp3_count_edit = QLineEdit(str(DEFAULT_MIN_MP3_COUNT))
        self.mp3_count_edit.setPlaceholderText("MP3")
        self.mp3_count_edit.setValidator(QIntValidator(1, 999, self))
        self.mp3_count_edit.setEnabled(False)
        self.mp3_count_edit.setFixedWidth(40)
        def set_mp3_count_edit_enabled(state):
            # Accept both int and Qt.CheckState for compatibility
            if isinstance(state, int):
                state = Qt.CheckState(state)
            checked = state == Qt.CheckState.Checked
            self.mp3_count_edit.setEnabled(checked)
            if checked:
                self.mp3_count_edit.setStyleSheet("")  # Default style
            else:
                self.mp3_count_edit.setStyleSheet("background-color: #f2f2f2; color: #888;")  # Greyed out
        self.mp3_count_checkbox.stateChanged.connect(set_mp3_count_edit_enabled)
        # Remove mp3_count_edit style logic from update_mp3_checkbox_style
        def update_mp3_checkbox_style(state):
            self.mp3_count_checkbox.setStyleSheet("")  # Always default
        self.mp3_count_checkbox.stateChanged.connect(update_mp3_checkbox_style)
        # Initialize style and enabled state
        update_mp3_checkbox_style(self.mp3_count_checkbox.checkState())
        set_mp3_count_edit_enabled(self.mp3_count_checkbox.checkState())
        self.part1_edit.textChanged.connect(self.update_output_name)
        self.part2_edit.textChanged.connect(self.update_output_name)
        self.folder_edit.textChanged.connect(self.update_output_name)
        part_layout.addSpacing(20)
        part_layout.addWidget(self.name_list_checkbox)
        part_layout.addSpacing(-45)
        part_layout.addWidget(self.name_list_enter_btn)
        # part_layout.addWidget(self.name_list_preview_btn)
        part_layout.addSpacing(20)
        part_layout.addWidget(QLabel("Name:"))
        part_layout.addSpacing(-90)  # Reduce space between label and textbox
        part_layout.addWidget(self.part1_edit)
        part_layout.addSpacing(-10)
        part_layout.addWidget(QLabel("#"))
        part_layout.addSpacing(-120) 
        part_layout.addWidget(self.part2_edit)
        part_layout.addSpacing(15)
        part_layout.addWidget(self.mp3_count_checkbox)
        part_layout.addSpacing(-70)
        part_layout.addWidget(self.mp3_count_edit)
        part_layout.addSpacing(15)
        layout.addLayout(part_layout)

    def create_video_settings(self, layout):
        """Create video settings controls"""
        # Combined layout for codec, resolution, and fps
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(0)  # We'll add custom spacing

        # Codec selection
        settings_layout.addSpacing(30)
        codec_label = QLabel("Codec:")        
        self.codec_combo = QtWidgets.QComboBox()
        self.codec_combo.setFixedWidth(130)
        self.codec_combo.setMinimumHeight(28)
        self.codec_combo.setMaximumHeight(28)
        for label, value in DEFAULT_CODECS:
            self.codec_combo.addItem(label, value)
        self.codec_combo.setCurrentIndex(0)
        settings_layout.addWidget(codec_label)
        settings_layout.addSpacing(5)  # Small space between label and combo
        settings_layout.addWidget(self.codec_combo)
        settings_layout.addSpacing(18)  # Space between groups

        # Video resolution selection
        resolution_label = QLabel("Size:")
        resolution_label.setFixedWidth(35)
        self.resolution_combo = QtWidgets.QComboBox()
        self.resolution_combo.setFixedWidth(140)
        self.resolution_combo.setMinimumHeight(28)
        self.resolution_combo.setMaximumHeight(28)
        for label, value in DEFAULT_RESOLUTIONS:
            self.resolution_combo.addItem(label, value)
        self.resolution_combo.setCurrentIndex(0)
        settings_layout.addWidget(resolution_label)
        settings_layout.addSpacing(3)
        settings_layout.addWidget(self.resolution_combo)
        settings_layout.addSpacing(28)

        # FPS selection
        fps_label = QLabel("FPS:")
        fps_label.setFixedWidth(30)
        self.fps_combo = QtWidgets.QComboBox()
        self.fps_combo.setFixedWidth(120)
        self.fps_combo.setMinimumHeight(28)
        self.fps_combo.setMaximumHeight(28)
        for label, value in DEFAULT_FPS_OPTIONS:
            self.fps_combo.addItem(label, value)
        # Load default FPS from settings
        default_fps = self.settings.value('default_fps', type=int)
        if default_fps is not None:
            fps_index = next((i for i, (label, value) in enumerate(DEFAULT_FPS_OPTIONS) if value == default_fps), 0)
            self.fps_combo.setCurrentIndex(fps_index)
        else:
            self.fps_combo.setCurrentIndex(0)
        settings_layout.addWidget(fps_label)
        settings_layout.addSpacing(6)
        settings_layout.addWidget(self.fps_combo)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        # --- INTRO OVERLAY CONTROLS ---
        self.intro_checkbox = QtWidgets.QCheckBox(" Intro :")
        self.intro_checkbox.setFixedWidth(70)
        self.intro_checkbox.setChecked(True)
        def update_intro_checkbox_style(state):
            self.intro_checkbox.setStyleSheet("")  # Always default color
        self.intro_checkbox.stateChanged.connect(update_intro_checkbox_style)
        update_intro_checkbox_style(self.intro_checkbox.checkState())

        intro_layout = QHBoxLayout()
        intro_layout.setSpacing(4)
        self.intro_edit = ImageDropLineEdit()
        self.intro_edit.setPlaceholderText("Intro image path (*.gif, *.png)")
        self.intro_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
        self.intro_edit.setFixedWidth(125)
        self.intro_path = ""
        def on_intro_changed():
            current_text = self.intro_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.intro_edit.setText(cleaned_text)
            self.intro_path = self.intro_edit.text().strip()
        self.intro_edit.textChanged.connect(on_intro_changed)
        intro_btn = QPushButton("Select")
        intro_btn.setFixedWidth(60)
        def select_intro_image():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Intro Image", "", "Image Files (*.gif *.png *.jpg *.jpeg)")
            if file_path:
                self.intro_edit.setText(file_path)
        intro_btn.clicked.connect(select_intro_image)
        intro_size_label = QLabel("S:")
        intro_size_label.setFixedWidth(18)
        self.intro_size_combo = QtWidgets.QComboBox()
        self.intro_size_combo.setFixedWidth(90)
        for percent in range(5, 101, 5):
            self.intro_size_combo.addItem(f"{percent}%", percent)
        self.intro_size_combo.setCurrentIndex(9)  # Default 50%
        self.intro_size_percent = 50
        def on_intro_size_changed(idx):
            self.intro_size_percent = self.intro_size_combo.itemData(idx)
        self.intro_size_combo.setEditable(False)
        self.intro_size_combo.currentIndexChanged.connect(on_intro_size_changed)
        on_intro_size_changed(self.intro_size_combo.currentIndex())
        # Position option (add Center)
        intro_position_label = QLabel("P:")
        intro_position_label.setFixedWidth(18)
        self.intro_position_combo = QtWidgets.QComboBox()
        self.intro_position_combo.setFixedWidth(130)
        intro_positions = [
            ("Center", "center"),
            ("Top Left", "top_left"),
            ("Top Right", "top_right"),
            ("Bottom Left", "bottom_left"),
            ("Bottom Right", "bottom_right")
        ]
        for label, value in intro_positions:
            self.intro_position_combo.addItem(label, value)
        self.intro_position_combo.setCurrentIndex(0)  # Default Center
        self.intro_position = "center"
        def on_intro_position_changed(idx):
            self.intro_position = self.intro_position_combo.itemData(idx)
        self.intro_position_combo.currentIndexChanged.connect(on_intro_position_changed)
        on_intro_position_changed(self.intro_position_combo.currentIndex())

        # (1) Create all intro widgets first
        combo_width = 130
        intro_effect_label = QLabel("Intro:")
        intro_effect_label.setFixedWidth(40)
        self.intro_effect_combo = QtWidgets.QComboBox()
        self.intro_effect_combo.setFixedWidth(combo_width)
        intro_effect_options = [
            ("Fade in & out", "fadeinout"),
            ("Fade in", "fadein"),
            ("Fade out", "fadeout"),
            ("Zoompan", "zoompan"),
            ("None", "none")
        ]
        for label, value in intro_effect_options:
            self.intro_effect_combo.addItem(label, value)
        self.intro_effect_combo.setCurrentIndex(0)
        self.intro_effect = "fadeinout"
        def on_intro_effect_changed(idx):
            self.intro_effect = self.intro_effect_combo.itemData(idx)
        self.intro_effect_combo.currentIndexChanged.connect(on_intro_effect_changed)
        on_intro_effect_changed(self.intro_effect_combo.currentIndex())

        intro_duration_label = QLabel("For (s): ")
        intro_duration_label.setFixedWidth(45)
        self.intro_duration_edit = QLineEdit("5")
        self.intro_duration_edit.setFixedWidth(40)
        self.intro_duration_edit.setValidator(QIntValidator(1, 999, self))
        self.intro_duration_edit.setPlaceholderText("5")
        self.intro_duration = 5
        def on_intro_duration_changed():
            try:
                self.intro_duration = int(self.intro_duration_edit.text())
            except Exception:
                self.intro_duration = 5
        self.intro_duration_edit.textChanged.connect(on_intro_duration_changed)
        on_intro_duration_changed()

        # (2) Now define set_intro_enabled and connect
        def set_intro_enabled(state):
            enabled = state == Qt.CheckState.Checked
            self.intro_edit.setEnabled(enabled)
            intro_btn.setEnabled(enabled)
            self.intro_size_combo.setEnabled(enabled)
            self.intro_position_combo.setEnabled(enabled)
            self.intro_effect_combo.setEnabled(enabled)
            intro_duration_label.setEnabled(enabled)
            self.intro_duration_edit.setEnabled(enabled)
            if enabled:
                intro_btn.setStyleSheet("")
                self.intro_edit.setStyleSheet("")
                self.intro_size_combo.setStyleSheet("")
                self.intro_position_combo.setStyleSheet("")
                self.intro_effect_combo.setStyleSheet("")
                intro_duration_label.setStyleSheet("")
                self.intro_duration_edit.setStyleSheet("")
                intro_size_label.setStyleSheet("")
                intro_position_label.setStyleSheet("")
                intro_effect_label.setStyleSheet("")
            else:
                grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
                intro_btn.setStyleSheet(grey_btn_style)
                self.intro_edit.setStyleSheet(grey_btn_style)
                self.intro_size_combo.setStyleSheet(grey_btn_style)
                self.intro_position_combo.setStyleSheet(grey_btn_style)
                self.intro_effect_combo.setStyleSheet(grey_btn_style)
                intro_duration_label.setStyleSheet("color: grey;")
                self.intro_duration_edit.setStyleSheet(grey_btn_style)
                intro_size_label.setStyleSheet("color: grey;")
                intro_position_label.setStyleSheet("color: grey;")
                intro_effect_label.setStyleSheet("color: grey;")
        self.intro_checkbox.stateChanged.connect(lambda _: set_intro_enabled(self.intro_checkbox.checkState()))
        set_intro_enabled(self.intro_checkbox.checkState())

        intro_layout = QHBoxLayout()
        intro_layout.setSpacing(4)
        intro_layout.addWidget(self.intro_checkbox)
        intro_layout.addSpacing(10)
        intro_layout.addWidget(self.intro_edit)
        intro_layout.addSpacing(4)
        intro_layout.addWidget(intro_btn)
        intro_layout.addSpacing(4)
        intro_layout.addWidget(intro_position_label)
        intro_layout.addSpacing(0)
        intro_layout.addWidget(self.intro_position_combo)
        intro_layout.addSpacing(6)
        intro_layout.addWidget(intro_size_label)
        intro_layout.addWidget(self.intro_size_combo)
        layout.addLayout(intro_layout)

        # Move PNG overlay checkbox below video settings
        self.overlay_checkbox = QtWidgets.QCheckBox("Overlay 1:")
        self.overlay_checkbox.setFixedWidth(82)
        self.overlay_checkbox.setChecked(True)
        def update_overlay_checkbox_style(state):
            self.overlay_checkbox.setStyleSheet("")  # Always default color
        self.overlay_checkbox.stateChanged.connect(update_overlay_checkbox_style)
        # Initialize style
        update_overlay_checkbox_style(self.overlay_checkbox.checkState())

        # Overlay 1 image input (text, drag & drop, select button)
        overlay1_layout = QHBoxLayout()
        overlay1_layout.setSpacing(4)  # Reduce spacing between widgets
        self.overlay1_edit = ImageDropLineEdit()
        self.overlay1_edit.setPlaceholderText("Overlay 1 image path (*.gif, *.png)")
        self.overlay1_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
        self.overlay1_edit.setFixedWidth(125)  # Make the text box shorter
        self.overlay1_path = ""
        def on_overlay1_changed():
            current_text = self.overlay1_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.overlay1_edit.setText(cleaned_text)
            self.overlay1_path = self.overlay1_edit.text().strip()
        self.overlay1_edit.textChanged.connect(on_overlay1_changed)
        overlay1_btn = QPushButton("Select")
        overlay1_btn.setFixedWidth(60)
        def select_overlay1_image():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Overlay 1 Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.overlay1_edit.setText(file_path)
        overlay1_btn.clicked.connect(select_overlay1_image)
        # Overlay 1 size option (5% to 100%)
        overlay1_size_label = QLabel("S:")
        overlay1_size_label.setFixedWidth(18)
        self.overlay1_size_combo = QtWidgets.QComboBox()
        self.overlay1_size_combo.setFixedWidth(90)
        for percent in range(5, 101, 5):
            self.overlay1_size_combo.addItem(f"{percent}%", percent)
        self.overlay1_size_combo.setCurrentIndex(2)  # Default 15%
        self.overlay1_size_percent = 15
        def on_overlay1_size_changed(idx):
            self.overlay1_size_percent = self.overlay1_size_combo.itemData(idx)
        self.overlay1_size_combo.setEditable(False)
        self.overlay1_size_combo.currentIndexChanged.connect(on_overlay1_size_changed)
        on_overlay1_size_changed(self.overlay1_size_combo.currentIndex())
        # Overlay 1 position option
        overlay1_position_label = QLabel("P:")
        overlay1_position_label.setFixedWidth(18)
        self.overlay1_position_combo = QtWidgets.QComboBox()
        self.overlay1_position_combo.setFixedWidth(130)
        positions = [
            ("Center", "center"),
            ("Top Left", "top_left"),
            ("Top Right", "top_right"),
            ("Bottom Left", "bottom_left"),
            ("Bottom Right", "bottom_right")
        ]
        for label, value in positions:
            self.overlay1_position_combo.addItem(label, value)
        self.overlay1_position_combo.setCurrentIndex(3)  # Default bottom_left
        self.overlay1_position = "bottom_left"
        def on_overlay1_position_changed(idx):
            self.overlay1_position = self.overlay1_position_combo.itemData(idx)
        self.overlay1_position_combo.currentIndexChanged.connect(on_overlay1_position_changed)
        on_overlay1_position_changed(self.overlay1_position_combo.currentIndex())
        # Enable/disable overlay1_edit, overlay1_btn, and overlay1_size_combo based on checkbox
        def set_overlay1_enabled(state):
            enabled = state == Qt.CheckState.Checked
            self.overlay1_edit.setEnabled(enabled)
            overlay1_btn.setEnabled(enabled)
            self.overlay1_size_combo.setEnabled(enabled)
            self.overlay1_position_combo.setEnabled(enabled)
            if enabled:
                overlay1_btn.setStyleSheet("")  # Default style
                self.overlay1_edit.setStyleSheet("")  # Default style
                self.overlay1_size_combo.setStyleSheet("")
                self.overlay1_position_combo.setStyleSheet("")
                overlay1_size_label.setStyleSheet("")  # Default
                overlay1_position_label.setStyleSheet("")
            else:
                grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
                overlay1_btn.setStyleSheet(grey_btn_style)
                self.overlay1_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")  # Lighter grey for textbox
                self.overlay1_size_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.overlay1_position_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                overlay1_size_label.setStyleSheet("color: grey;")
                overlay1_position_label.setStyleSheet("color: grey;")
        self.overlay_checkbox.stateChanged.connect(lambda _: set_overlay1_enabled(self.overlay_checkbox.checkState()))
        set_overlay1_enabled(self.overlay_checkbox.checkState())
        overlay1_layout.addWidget(self.overlay_checkbox)
        overlay1_layout.addWidget(self.overlay1_edit)
        overlay1_layout.addSpacing(6)  # Space before select button
        overlay1_layout.addWidget(overlay1_btn)
        overlay1_layout.addSpacing(4)  # Space before position label
        overlay1_layout.addWidget(overlay1_position_label)
        overlay1_layout.addSpacing(2)
        overlay1_layout.addWidget(self.overlay1_position_combo)
        overlay1_layout.addSpacing(6) 
        overlay1_layout.addWidget(overlay1_size_label)
        overlay1_layout.addWidget(self.overlay1_size_combo)
        layout.addLayout(overlay1_layout)

        # Overlay 2 controls (similar to Overlay 1)
        self.overlay2_checkbox = QtWidgets.QCheckBox("Overlay 2:")
        self.overlay2_checkbox.setFixedWidth(82)
        self.overlay2_checkbox.setChecked(True)
        def update_overlay2_checkbox_style(state):
            self.overlay2_checkbox.setStyleSheet("")  # Always default color
        self.overlay2_checkbox.stateChanged.connect(update_overlay2_checkbox_style)
        update_overlay2_checkbox_style(self.overlay2_checkbox.checkState())

        overlay2_layout = QHBoxLayout()
        overlay2_layout.setSpacing(4)
        self.overlay2_edit = ImageDropLineEdit()
        self.overlay2_edit.setPlaceholderText("Overlay 2 image path (*.gif, *.png)")
        self.overlay2_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
        self.overlay2_edit.setFixedWidth(125)
        self.overlay2_path = ""
        def on_overlay2_changed():
            current_text = self.overlay2_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.overlay2_edit.setText(cleaned_text)
            self.overlay2_path = self.overlay2_edit.text().strip()
        self.overlay2_edit.textChanged.connect(on_overlay2_changed)
        overlay2_btn = QPushButton("Select")
        overlay2_btn.setFixedWidth(60)
        def select_overlay2_image():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Overlay 2 Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.overlay2_edit.setText(file_path)
        overlay2_btn.clicked.connect(select_overlay2_image)
        overlay2_size_label = QLabel("S:")
        overlay2_size_label.setFixedWidth(18)
        self.overlay2_size_combo = QtWidgets.QComboBox()
        self.overlay2_size_combo.setFixedWidth(90)
        for percent in range(5, 101, 5):
            self.overlay2_size_combo.addItem(f"{percent}%", percent)
        self.overlay2_size_combo.setCurrentIndex(2)  # Default 15%
        self.overlay2_size_percent = 15
        def on_overlay2_size_changed(idx):
            self.overlay2_size_percent = self.overlay2_size_combo.itemData(idx)
        self.overlay2_size_combo.setEditable(False)
        self.overlay2_size_combo.currentIndexChanged.connect(on_overlay2_size_changed)
        on_overlay2_size_changed(self.overlay2_size_combo.currentIndex())
        # Overlay 2 position option
        overlay2_position_label = QLabel("P:")
        overlay2_position_label.setFixedWidth(18)
        self.overlay2_position_combo = QtWidgets.QComboBox()
        self.overlay2_position_combo.setFixedWidth(130)
        positions = [
            ("Center", "center"),
            ("Top Left", "top_left"),
            ("Top Right", "top_right"),
            ("Bottom Left", "bottom_left"),
            ("Bottom Right", "bottom_right")
        ]
        for label, value in positions:
            self.overlay2_position_combo.addItem(label, value)
        self.overlay2_position_combo.setCurrentIndex(2)  # Default top_right
        self.overlay2_position = "top_right"
        def on_overlay2_position_changed(idx):
            self.overlay2_position = self.overlay2_position_combo.itemData(idx)
        self.overlay2_position_combo.currentIndexChanged.connect(on_overlay2_position_changed)
        on_overlay2_position_changed(self.overlay2_position_combo.currentIndex())
        def set_overlay2_enabled(state):
            enabled = state == Qt.CheckState.Checked
            self.overlay2_edit.setEnabled(enabled)
            overlay2_btn.setEnabled(enabled)
            self.overlay2_size_combo.setEnabled(enabled)
            self.overlay2_position_combo.setEnabled(enabled)
            if enabled:
                overlay2_btn.setStyleSheet("")
                self.overlay2_edit.setStyleSheet("")
                self.overlay2_size_combo.setStyleSheet("")
                self.overlay2_position_combo.setStyleSheet("")
                overlay2_size_label.setStyleSheet("")
                overlay2_position_label.setStyleSheet("")
            else:
                grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
                overlay2_btn.setStyleSheet(grey_btn_style)
                self.overlay2_edit.setStyleSheet(grey_btn_style)
                self.overlay2_size_combo.setStyleSheet(grey_btn_style)
                self.overlay2_position_combo.setStyleSheet(grey_btn_style)
                overlay2_size_label.setStyleSheet("color: grey;")
                overlay2_position_label.setStyleSheet("color: grey;")
        self.overlay2_checkbox.stateChanged.connect(lambda _: set_overlay2_enabled(self.overlay2_checkbox.checkState()))
        set_overlay2_enabled(self.overlay2_checkbox.checkState())
        overlay2_layout.addWidget(self.overlay2_checkbox)
        overlay2_layout.addWidget(self.overlay2_edit)
        overlay2_layout.addSpacing(6)
        overlay2_layout.addWidget(overlay2_btn)
        overlay2_layout.addSpacing(4)
        overlay2_layout.addWidget(overlay2_position_label)
        overlay2_layout.addSpacing(2)
        overlay2_layout.addWidget(self.overlay2_position_combo)
        overlay2_layout.addSpacing(6)
        overlay2_layout.addWidget(overlay2_size_label)
        overlay2_layout.addWidget(self.overlay2_size_combo)
        layout.addLayout(overlay2_layout)

        # --- EFFECT CONTROL FOR INTRO & OVERLAY (moved below Overlay 2) ---
        combo_width = 130
        edit_width = 40
        effect_label = QLabel("Overlay 1_2:")
        effect_label.setFixedWidth(80)
        self.effect_combo = QtWidgets.QComboBox()
        self.effect_combo.setFixedWidth(combo_width)
        effect_options = [
            ("Fade in & out", "fadeinout"),
            ("Fade in", "fadein"),
            ("Fade out", "fadeout"),
            ("Zoompan", "zoompan"),
            ("None", "none")
        ]
        for label, value in effect_options:
            self.effect_combo.addItem(label, value)
        self.effect_combo.setCurrentIndex(1)
        self.selected_effect = "fadein"
        def on_effect_changed(idx):
            self.selected_effect = self.effect_combo.itemData(idx)
        self.effect_combo.currentIndexChanged.connect(on_effect_changed)
        on_effect_changed(self.effect_combo.currentIndex())

        overlay_duration_label = QLabel("at (s):")
        overlay_duration_label.setFixedWidth(40)
        self.overlay_duration_edit = QLineEdit("5")
        self.overlay_duration_edit.setFixedWidth(edit_width)
        self.overlay_duration_edit.setValidator(QIntValidator(0, 999, self))
        self.overlay_duration_edit.setPlaceholderText("5")
        self.overlay_duration = 5
        def on_overlay_duration_changed():
            try:
                self.overlay_duration = int(self.overlay_duration_edit.text())
            except Exception:
                self.overlay_duration = 5
        self.overlay_duration_edit.textChanged.connect(on_overlay_duration_changed)
        on_overlay_duration_changed()

        effect_layout = QHBoxLayout()
        effect_layout.setContentsMargins(0, 0, 0, 0)
        effect_layout.addSpacing(0)
        effect_layout.addWidget(intro_effect_label)
        effect_layout.addSpacing(-10)
        effect_layout.addWidget(self.intro_effect_combo)
        effect_layout.addSpacing(-10)
        effect_layout.addWidget(intro_duration_label)
        effect_layout.addSpacing(-10)
        effect_layout.addWidget(self.intro_duration_edit)
        effect_layout.addSpacing(12)
        effect_layout.addWidget(effect_label)
        effect_layout.addSpacing(-10)
        effect_layout.addWidget(self.effect_combo)
        effect_layout.addSpacing(-10)
        effect_layout.addWidget(overlay_duration_label)
        effect_layout.addSpacing(-10)
        effect_layout.addWidget(self.overlay_duration_edit)
        effect_layout.addStretch()
        layout.addLayout(effect_layout)

        # --- Overlay effect label greying logic ---
        def update_overlay_effect_label_style():
            if not (self.overlay_checkbox.isChecked() or self.overlay2_checkbox.isChecked()):
                effect_label.setStyleSheet("color: grey;")
                self.effect_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.effect_combo.setEnabled(False)
                overlay_duration_label.setStyleSheet("color: grey;")
                self.overlay_duration_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.overlay_duration_edit.setEnabled(False)
            else:
                effect_label.setStyleSheet("")
                self.effect_combo.setStyleSheet("")
                self.effect_combo.setEnabled(True)
                overlay_duration_label.setStyleSheet("")
                self.overlay_duration_edit.setStyleSheet("")
                self.overlay_duration_edit.setEnabled(True)
        self.overlay_checkbox.stateChanged.connect(update_overlay_effect_label_style)
        self.overlay2_checkbox.stateChanged.connect(update_overlay_effect_label_style)
        update_overlay_effect_label_style()

        # Overlay 3 controls (similar to Overlay 2)
        self.overlay3_checkbox = QtWidgets.QCheckBox("Overlay 3:")
        self.overlay3_checkbox.setFixedWidth(82)
        self.overlay3_checkbox.setChecked(False)
        def update_overlay3_checkbox_style(state):
            self.overlay3_checkbox.setStyleSheet("")  # Always default color
        self.overlay3_checkbox.stateChanged.connect(update_overlay3_checkbox_style)
        update_overlay3_checkbox_style(self.overlay3_checkbox.checkState())

        overlay3_layout = QHBoxLayout()
        overlay3_layout.setSpacing(4)
        self.overlay3_edit = ImageDropLineEdit()
        self.overlay3_edit.setPlaceholderText("Overlay 3 image path (*.gif, *.png)")
        self.overlay3_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
        self.overlay3_edit.setFixedWidth(125)
        self.overlay3_path = ""
        def on_overlay3_changed():
            current_text = self.overlay3_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.overlay3_edit.setText(cleaned_text)
            self.overlay3_path = self.overlay3_edit.text().strip()
        self.overlay3_edit.textChanged.connect(on_overlay3_changed)
        overlay3_btn = QPushButton("Select")
        overlay3_btn.setFixedWidth(60)
        def select_overlay3_image():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Overlay 3 Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.overlay3_edit.setText(file_path)
        overlay3_btn.clicked.connect(select_overlay3_image)
        overlay3_size_label = QLabel("S:")
        overlay3_size_label.setFixedWidth(18)
        self.overlay3_size_combo = QtWidgets.QComboBox()
        self.overlay3_size_combo.setFixedWidth(90)
        for percent in range(5, 101, 5):
            self.overlay3_size_combo.addItem(f"{percent}%", percent)
        self.overlay3_size_combo.setCurrentIndex(2)  # Default 15%
        self.overlay3_size_percent = 15
        def on_overlay3_size_changed(idx):
            self.overlay3_size_percent = self.overlay3_size_combo.itemData(idx)
        self.overlay3_size_combo.setEditable(False)
        self.overlay3_size_combo.currentIndexChanged.connect(on_overlay3_size_changed)
        on_overlay3_size_changed(self.overlay3_size_combo.currentIndex())
        # Overlay 3 position option
        overlay3_position_label = QLabel("P:")
        overlay3_position_label.setFixedWidth(18)
        self.overlay3_position_combo = QtWidgets.QComboBox()
        self.overlay3_position_combo.setFixedWidth(130)
        positions = [
            ("Center", "center"),
            ("Top Left", "top_left"),
            ("Top Right", "top_right"),
            ("Bottom Left", "bottom_left"),
            ("Bottom Right", "bottom_right")
        ]
        for label, value in positions:
            self.overlay3_position_combo.addItem(label, value)
        self.overlay3_position_combo.setCurrentIndex(2)  # Default top_right
        self.overlay3_position = "top_right"
        def on_overlay3_position_changed(idx):
            self.overlay3_position = self.overlay3_position_combo.itemData(idx)
        self.overlay3_position_combo.currentIndexChanged.connect(on_overlay3_position_changed)
        on_overlay3_position_changed(self.overlay3_position_combo.currentIndex())
        def set_overlay3_enabled(state):
            enabled = state == Qt.CheckState.Checked
            self.overlay3_edit.setEnabled(enabled)
            overlay3_btn.setEnabled(enabled)
            self.overlay3_size_combo.setEnabled(enabled)
            self.overlay3_position_combo.setEnabled(enabled)
            if enabled:
                overlay3_btn.setStyleSheet("")
                self.overlay3_edit.setStyleSheet("")
                self.overlay3_size_combo.setStyleSheet("")
                self.overlay3_position_combo.setStyleSheet("")
                overlay3_size_label.setStyleSheet("")
                overlay3_position_label.setStyleSheet("")
            else:
                grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
                overlay3_btn.setStyleSheet(grey_btn_style)
                self.overlay3_edit.setStyleSheet(grey_btn_style)
                self.overlay3_size_combo.setStyleSheet(grey_btn_style)
                self.overlay3_position_combo.setStyleSheet(grey_btn_style)
                overlay3_size_label.setStyleSheet("color: grey;")
                overlay3_position_label.setStyleSheet("color: grey;")
        self.overlay3_checkbox.stateChanged.connect(lambda _: set_overlay3_enabled(self.overlay3_checkbox.checkState()))
        set_overlay3_enabled(self.overlay3_checkbox.checkState())
        overlay3_layout.addWidget(self.overlay3_checkbox)
        overlay3_layout.addWidget(self.overlay3_edit)
        overlay3_layout.addSpacing(6)
        overlay3_layout.addWidget(overlay3_btn)
        overlay3_layout.addSpacing(4)
        overlay3_layout.addWidget(overlay3_position_label)
        overlay3_layout.addSpacing(2)
        overlay3_layout.addWidget(self.overlay3_position_combo)
        overlay3_layout.addSpacing(6)
        overlay3_layout.addWidget(overlay3_size_label)
        overlay3_layout.addWidget(self.overlay3_size_combo)
        layout.addLayout(overlay3_layout)

        # --- SONG TITLE OVERLAY CHECKBOX ---
        self.song_title_checkbox = QtWidgets.QCheckBox("Song Titles:")
        self.song_title_checkbox.setChecked(True)
        def update_song_title_checkbox_style(state):
            self.song_title_checkbox.setStyleSheet("")
        self.song_title_checkbox.stateChanged.connect(update_song_title_checkbox_style)
        update_song_title_checkbox_style(self.song_title_checkbox.checkState())
        
        # Song titles checkbox and controls
        song_title_checkbox_layout = QHBoxLayout()
        song_title_checkbox_layout.setSpacing(4)
        
        # Font control
        song_title_font_label = QLabel("Font:")
        song_title_font_label.setFixedWidth(40)
        self.song_title_font_combo = QtWidgets.QComboBox()
        self.song_title_font_combo.setFixedWidth(120)
        song_title_font_options = [
            ("Default", "default"),
            ("Kantumruy Pro", "KantumruyPro-VariableFont_wght.ttf"),
            ("Kantumruy Pro Italic", "KantumruyPro-Italic-VariableFont_wght.ttf"),
            ("Roboto", "Roboto-VariableFont_wdth,wght.ttf"),
            ("Roboto Italic", "Roboto-Italic-VariableFont_wdth,wght.ttf")
        ]
        for label, value in song_title_font_options:
            self.song_title_font_combo.addItem(label, value)
        self.song_title_font_combo.setCurrentIndex(0)  # Default
        self.song_title_font = "default"
        def on_song_title_font_changed(idx):
            self.song_title_font = self.song_title_font_combo.itemData(idx)
        self.song_title_font_combo.currentIndexChanged.connect(on_song_title_font_changed)
        on_song_title_font_changed(self.song_title_font_combo.currentIndex())
        
        # Font size control (REMOVED DROPDOWN, FIXED TO 220)
        self.song_title_font_size = 220
        # (Remove the font size combo box and related logic)

        # Titles Scale control
        song_title_scale_label = QLabel("Titles Scale:")
        song_title_scale_label.setFixedWidth(80)
        self.song_title_scale_combo = QtWidgets.QComboBox()
        self.song_title_scale_combo.setFixedWidth(86)
        for percent in range(5, 101, 5):
            self.song_title_scale_combo.addItem(f"{percent}%", percent)
        self.song_title_scale_combo.setCurrentIndex(19)  # Default 100%
        self.song_title_scale_percent = 100
        def on_song_title_scale_changed(idx):
            self.song_title_scale_percent = self.song_title_scale_combo.itemData(idx)
        self.song_title_scale_combo.currentIndexChanged.connect(on_song_title_scale_changed)
        on_song_title_scale_changed(self.song_title_scale_combo.currentIndex())
        
        # Color control
        song_title_color_label = QLabel("Color:")
        song_title_color_label.setFixedWidth(40)
        self.song_title_color_btn = QPushButton()
        self.song_title_color_btn.setFixedSize(27, 27)
        self.song_title_color_btn.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 0px; margin: 0px;")
        self.song_title_color = (255, 255, 255)  # Default white
        def on_song_title_color_clicked():
            color = QColorDialog.getColor(QColor(*self.song_title_color), self, "Select Song Title Color")
            if color.isValid():
                self.song_title_color = (color.red(), color.green(), color.blue())
                self.song_title_color_btn.setStyleSheet(f"background-color: rgb{self.song_title_color}; border: 1px solid #ccc; padding: 0px; margin: 0px;")
        self.song_title_color_btn.clicked.connect(on_song_title_color_clicked)
        
        # Background control
        song_title_bg_label = QLabel("BG:")
        song_title_bg_label.setFixedWidth(26)
        self.song_title_bg_combo = QtWidgets.QComboBox()
        self.song_title_bg_combo.setFixedWidth(120)
        bg_options = [
            ("Transparent", "transparent"),
            ("Black", "black"),
            ("White", "white"),
            ("Custom", "custom")
        ]
        for label, value in bg_options:
            self.song_title_bg_combo.addItem(label, value)
        self.song_title_bg_combo.setCurrentIndex(0)  # Default transparent
        self.song_title_bg = "transparent"
        def on_song_title_bg_changed(idx):
            self.song_title_bg = self.song_title_bg_combo.itemData(idx)
            if self.song_title_bg == "custom":
                # Use the color shown in the button (last custom color)
                self.song_title_bg_color = self.last_custom_bg_color
        self.song_title_bg_combo.currentIndexChanged.connect(on_song_title_bg_changed)
        on_song_title_bg_changed(self.song_title_bg_combo.currentIndex())
        
        # Background color control
        self.song_title_bg_color_btn = QPushButton()
        self.song_title_bg_color_btn.setFixedSize(28, 28)
        self.song_title_bg_color_btn.setStyleSheet("background-color: black; border: 1px solid #ccc;")
        self.song_title_bg_color = (0, 0, 0)  # Default black
        
        # Load last custom color from settings
        last_custom_r = self.settings.value('song_title_last_custom_bg_r', 0, type=int)
        last_custom_g = self.settings.value('song_title_last_custom_bg_g', 0, type=int)
        last_custom_b = self.settings.value('song_title_last_custom_bg_b', 0, type=int)
        self.last_custom_bg_color = (last_custom_r, last_custom_g, last_custom_b)
        
        # Ensure internal state matches UI if last custom color is set and mode is custom
        if self.last_custom_bg_color != (0, 0, 0) and self.song_title_bg == "custom":
            self.song_title_bg_color = self.last_custom_bg_color
            self.song_title_bg_color_btn.setStyleSheet(f"background-color: rgb{self.song_title_bg_color}; border: 1px solid #ccc;")
        
        def on_song_title_bg_color_clicked():
            # Use the last custom color as initial, or current if no custom color was picked yet
            if self.last_custom_bg_color != (0, 0, 0):
                initial_color = QColor(*self.last_custom_bg_color)
            else:
                initial_color = QColor(*self.song_title_bg_color)
            color = QColorDialog.getColor(initial_color, self, "Select Background Color")
            if color.isValid():
                self.song_title_bg_color = (color.red(), color.green(), color.blue())
                self.last_custom_bg_color = self.song_title_bg_color  # Remember this custom color
                # Save to settings
                self.settings.setValue('song_title_last_custom_bg_r', color.red())
                self.settings.setValue('song_title_last_custom_bg_g', color.green())
                self.settings.setValue('song_title_last_custom_bg_b', color.blue())
                self.song_title_bg_color_btn.setStyleSheet(f"background-color: rgb{self.song_title_bg_color}; border: 1px solid #ccc;")
                update_bg_color_state()  # Update the state to reflect the new color
        self.song_title_bg_color_btn.clicked.connect(on_song_title_bg_color_clicked)
        
        # Function to update background color button state
        def update_bg_color_state():
            is_custom = self.song_title_bg == "custom"
            is_enabled = self.song_title_checkbox.isChecked()
            self.song_title_bg_color_btn.setEnabled(is_custom and is_enabled)
            
            if not is_enabled:
                self.song_title_bg_color_btn.setStyleSheet("background-color: #f2f2f2; border: 1px solid #cfcfcf;")
            elif not is_custom:
                self.song_title_bg_color_btn.setStyleSheet("background-color: #f2f2f2; border: 1px solid #cfcfcf;")
            else:
                # Use the last custom color when custom is selected, or the current color if no custom color was picked yet
                if self.last_custom_bg_color != (0, 0, 0):
                    self.song_title_bg_color_btn.setStyleSheet(f"background-color: rgb{self.last_custom_bg_color}; border: 1px solid #ccc; padding: 0px; margin: 0px;")
                else:
                    self.song_title_bg_color_btn.setStyleSheet(f"background-color: rgb{self.song_title_bg_color}; border: 1px solid #ccc; padding: 0px; margin: 0px;")
        
        # Connect background dropdown to update color button state
        self.song_title_bg_combo.currentIndexChanged.connect(lambda _: update_bg_color_state())
        
        # Initialize background color button state
        update_bg_color_state()
        
        # Opacity control
        self.song_title_opacity_combo = QtWidgets.QComboBox()
        self.song_title_opacity_combo.setFixedWidth(86)
        opacity_options = [
            (f"{percent}%", percent / 100.0) for percent in range(5, 101, 5)
        ]
        for label, value in opacity_options:
            self.song_title_opacity_combo.addItem(label, value)
        self.song_title_opacity_combo.setCurrentIndex(3)  # Default 20%
        self.song_title_opacity = 0.20
        def on_song_title_opacity_changed(idx):
            self.song_title_opacity = self.song_title_opacity_combo.itemData(idx)
        self.song_title_opacity_combo.currentIndexChanged.connect(on_song_title_opacity_changed)
        on_song_title_opacity_changed(self.song_title_opacity_combo.currentIndex())
        
        # Effect control (moved to next line)
        song_title_effect_layout = QHBoxLayout()
        song_title_effect_layout.setSpacing(4)
        song_title_effect_label = QLabel("Effect:")
        song_title_effect_label.setFixedWidth(50)
        self.song_title_effect_combo = QtWidgets.QComboBox()
        self.song_title_effect_combo.setFixedWidth(100)
        song_title_effect_options = [
            ("Fade in & out", "fadeinout"),
            ("Fade in", "fadein"),
            ("Fade out", "fadeout"),
            ("Zoompan", "zoompan"),
            ("None", "none")
        ]
        for label, value in song_title_effect_options:
            self.song_title_effect_combo.addItem(label, value)
        self.song_title_effect_combo.setCurrentIndex(0)  # Default fadeinout
        self.song_title_effect = "fadeinout"
        def on_song_title_effect_changed(idx):
            self.song_title_effect = self.song_title_effect_combo.itemData(idx)
        self.song_title_effect_combo.currentIndexChanged.connect(on_song_title_effect_changed)
        on_song_title_effect_changed(self.song_title_effect_combo.currentIndex())
        
        # --- Song Title Position Controls (X, Y as percent) ---
        song_title_x_label = QLabel("X:")
        song_title_x_label.setFixedWidth(28)
        self.song_title_x_combo = QtWidgets.QComboBox()
        self.song_title_x_combo.setFixedWidth(80)
        for percent in range(0, 101, 5):
            self.song_title_x_combo.addItem(f"{percent}%", percent)
        self.song_title_x_combo.setCurrentIndex(10)  # Default 50%
        self.song_title_x_percent = 50
        def on_song_title_x_changed(idx):
            self.song_title_x_percent = self.song_title_x_combo.itemData(idx)
        self.song_title_x_combo.currentIndexChanged.connect(on_song_title_x_changed)
        on_song_title_x_changed(self.song_title_x_combo.currentIndex())

        song_title_y_label = QLabel("Y:")
        song_title_y_label.setFixedWidth(28)
        self.song_title_y_combo = QtWidgets.QComboBox()
        self.song_title_y_combo.setFixedWidth(80)
        for percent in range(0, 101, 5):
            self.song_title_y_combo.addItem(f"{percent}%", percent)
        self.song_title_y_combo.setCurrentIndex(4)  # Default 20%
        self.song_title_y_percent = 20
        def on_song_title_y_changed(idx):
            self.song_title_y_percent = self.song_title_y_combo.itemData(idx)
        self.song_title_y_combo.currentIndexChanged.connect(on_song_title_y_changed)
        on_song_title_y_changed(self.song_title_y_combo.currentIndex())

        # --- Song Title Start At (s) ---
        song_title_start_label = QLabel("at (s):")
        song_title_start_label.setFixedWidth(40)
        self.song_title_start_edit = QLineEdit("5")
        self.song_title_start_edit.setFixedWidth(40)
        self.song_title_start_edit.setValidator(QIntValidator(0, 999, self))
        self.song_title_start_edit.setPlaceholderText("5")
        self.song_title_start_at = 5
        def on_song_title_start_changed():
            try:
                self.song_title_start_at = int(self.song_title_start_edit.text())
            except Exception:
                self.song_title_start_at = 5
        self.song_title_start_edit.textChanged.connect(on_song_title_start_changed)
        on_song_title_start_changed()

        # Enable/disable song title controls based on checkbox
        def set_song_title_controls_enabled(state):
            enabled = state == Qt.CheckState.Checked
            self.song_title_effect_combo.setEnabled(enabled)
            self.song_title_font_combo.setEnabled(enabled)
            self.song_title_color_btn.setEnabled(enabled)
            self.song_title_bg_combo.setEnabled(enabled)
            self.song_title_opacity_combo.setEnabled(enabled)
            self.song_title_x_combo.setEnabled(enabled)
            self.song_title_y_combo.setEnabled(enabled)
            self.song_title_start_edit.setEnabled(enabled)
            song_title_effect_label.setStyleSheet("" if enabled else "color: grey;")
            song_title_x_label.setStyleSheet("" if enabled else "color: grey;")
            song_title_y_label.setStyleSheet("" if enabled else "color: grey;")
            song_title_start_label.setStyleSheet("" if enabled else "color: grey;")
            song_title_font_label.setStyleSheet("" if enabled else "color: grey;")
            song_title_color_label.setStyleSheet("" if enabled else "color: grey;")
            song_title_bg_label.setStyleSheet("" if enabled else "color: grey;")
            if not enabled:
                grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
                self.song_title_effect_combo.setStyleSheet(grey_btn_style)
                self.song_title_x_combo.setStyleSheet(grey_btn_style)
                self.song_title_y_combo.setStyleSheet(grey_btn_style)
                self.song_title_start_edit.setStyleSheet(grey_btn_style)
            else:
                self.song_title_effect_combo.setStyleSheet("")
                self.song_title_x_combo.setStyleSheet("")
                self.song_title_y_combo.setStyleSheet("")
                self.song_title_start_edit.setStyleSheet("")
            # Update background color button state
            update_bg_color_state()
        self.song_title_checkbox.stateChanged.connect(lambda _: set_song_title_controls_enabled(self.song_title_checkbox.checkState()))
        set_song_title_controls_enabled(self.song_title_checkbox.checkState())
        
        # First line: checkbox, effect, X, Y, start at
        song_title_checkbox_layout.addSpacing(5)
        song_title_checkbox_layout.addWidget(self.song_title_checkbox)
        song_title_checkbox_layout.addSpacing(5)
        song_title_checkbox_layout.addWidget(song_title_effect_label)
        song_title_checkbox_layout.addWidget(self.song_title_effect_combo)
        song_title_checkbox_layout.addSpacing(5)
        song_title_checkbox_layout.addWidget(song_title_x_label)
        song_title_checkbox_layout.addWidget(self.song_title_x_combo)
        song_title_checkbox_layout.addSpacing(5)
        song_title_checkbox_layout.addWidget(song_title_y_label)
        song_title_checkbox_layout.addWidget(self.song_title_y_combo)
        song_title_checkbox_layout.addSpacing(5)
        song_title_checkbox_layout.addWidget(song_title_start_label)
        song_title_checkbox_layout.addWidget(self.song_title_start_edit)
        song_title_checkbox_layout.addStretch()
        layout.addLayout(song_title_checkbox_layout)
        
        # Second line: font, size, color, bg, opacity
        song_title_controls_layout = QHBoxLayout()
        song_title_controls_layout.setSpacing(2)
        song_title_controls_layout.addWidget(song_title_font_label)        
        song_title_controls_layout.addWidget(self.song_title_font_combo)
        song_title_controls_layout.addSpacing(4)        
        song_title_controls_layout.addWidget(self.song_title_scale_combo) 
        song_title_controls_layout.addWidget(song_title_color_label)
        song_title_controls_layout.addWidget(self.song_title_color_btn)
        song_title_controls_layout.addSpacing(8)
        song_title_controls_layout.addWidget(song_title_bg_label)
        song_title_controls_layout.addWidget(self.song_title_bg_combo)
        song_title_controls_layout.addSpacing(3)
        song_title_controls_layout.addWidget(self.song_title_bg_color_btn)
        song_title_controls_layout.addSpacing(1)
        song_title_controls_layout.addWidget(self.song_title_opacity_combo)
        song_title_controls_layout.addStretch()
        layout.addLayout(song_title_controls_layout)

         # Overlay 4 controls (similar to Overlay 3)
        self.overlay4_checkbox = QtWidgets.QCheckBox("Overlay 4:")
        self.overlay4_checkbox.setFixedWidth(82)
        self.overlay4_checkbox.setChecked(False)
        def update_overlay4_checkbox_style(state):
            self.overlay4_checkbox.setStyleSheet("")  # Always default color
        self.overlay4_checkbox.stateChanged.connect(update_overlay4_checkbox_style)
        update_overlay4_checkbox_style(self.overlay4_checkbox.checkState())

        overlay4_layout = QHBoxLayout()
        overlay4_layout.setSpacing(4)
        self.overlay4_edit = ImageDropLineEdit()
        self.overlay4_edit.setPlaceholderText("Overlay 4 image path (*.gif, *.png)")
        self.overlay4_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
        self.overlay4_edit.setFixedWidth(125)
        self.overlay4_path = ""
        def on_overlay4_changed():
            current_text = self.overlay4_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.overlay4_edit.setText(cleaned_text)
            self.overlay4_path = self.overlay4_edit.text().strip()
        self.overlay4_edit.textChanged.connect(on_overlay4_changed)
        overlay4_btn = QPushButton("Select")
        overlay4_btn.setFixedWidth(60)
        def select_overlay4_image():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Overlay 4 Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.overlay4_edit.setText(file_path)
        overlay4_btn.clicked.connect(select_overlay4_image)
        overlay4_size_label = QLabel("S:")
        overlay4_size_label.setFixedWidth(18)
        self.overlay4_size_combo = QtWidgets.QComboBox()
        self.overlay4_size_combo.setFixedWidth(90)
        for percent in range(5, 101, 5):
            self.overlay4_size_combo.addItem(f"{percent}%", percent)
        self.overlay4_size_combo.setCurrentIndex(2)  # Default 15%
        self.overlay4_size_percent = 15
        def on_overlay4_size_changed(idx):
            self.overlay4_size_percent = self.overlay4_size_combo.itemData(idx)
        self.overlay4_size_combo.setEditable(False)
        self.overlay4_size_combo.currentIndexChanged.connect(on_overlay4_size_changed)
        on_overlay4_size_changed(self.overlay4_size_combo.currentIndex())
        # Overlay 4 position option
        overlay4_position_label = QLabel("P:")
        overlay4_position_label.setFixedWidth(18)
        self.overlay4_position_combo = QtWidgets.QComboBox()
        self.overlay4_position_combo.setFixedWidth(130)
        positions = [
            ("Center", "center"),
            ("Top Left", "top_left"),
            ("Top Right", "top_right"),
            ("Bottom Left", "bottom_left"),
            ("Bottom Right", "bottom_right")
        ]
        for label, value in positions:
            self.overlay4_position_combo.addItem(label, value)
        self.overlay4_position_combo.setCurrentIndex(2)  # Default top_right
        self.overlay4_position = "top_right"
        def on_overlay4_position_changed(idx):
            self.overlay4_position = self.overlay4_position_combo.itemData(idx)
        self.overlay4_position_combo.currentIndexChanged.connect(on_overlay4_position_changed)
        on_overlay4_position_changed(self.overlay4_position_combo.currentIndex())
        def set_overlay4_enabled(state):
            enabled = state == Qt.CheckState.Checked
            self.overlay4_edit.setEnabled(enabled)
            overlay4_btn.setEnabled(enabled)
            self.overlay4_size_combo.setEnabled(enabled)
            self.overlay4_position_combo.setEnabled(enabled)
            if enabled:
                overlay4_btn.setStyleSheet("")
                self.overlay4_edit.setStyleSheet("")
                self.overlay4_size_combo.setStyleSheet("")
                self.overlay4_position_combo.setStyleSheet("")
                overlay4_size_label.setStyleSheet("")
                overlay4_position_label.setStyleSheet("")
            else:
                grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
                overlay4_btn.setStyleSheet(grey_btn_style)
                self.overlay4_edit.setStyleSheet(grey_btn_style)
                self.overlay4_size_combo.setStyleSheet(grey_btn_style)
                self.overlay4_position_combo.setStyleSheet(grey_btn_style)
                overlay4_size_label.setStyleSheet("color: grey;")
                overlay4_position_label.setStyleSheet("color: grey;")
        self.overlay4_checkbox.stateChanged.connect(lambda _: set_overlay4_enabled(self.overlay4_checkbox.checkState()))
        set_overlay4_enabled(self.overlay4_checkbox.checkState())
        overlay4_layout.addWidget(self.overlay4_checkbox)
        overlay4_layout.addWidget(self.overlay4_edit)
        overlay4_layout.addSpacing(6)
        overlay4_layout.addWidget(overlay4_btn)
        overlay4_layout.addSpacing(4)
        overlay4_layout.addWidget(overlay4_position_label)
        overlay4_layout.addSpacing(2)
        overlay4_layout.addWidget(self.overlay4_position_combo)
        overlay4_layout.addSpacing(6)
        overlay4_layout.addWidget(overlay4_size_label)
        overlay4_layout.addWidget(self.overlay4_size_combo)
        layout.addLayout(overlay4_layout)        

        # Overlay 5 controls (similar to Overlay 4)
        self.overlay5_checkbox = QtWidgets.QCheckBox("Overlay 5:")
        self.overlay5_checkbox.setFixedWidth(82)
        self.overlay5_checkbox.setChecked(False)
        def update_overlay5_checkbox_style(state):
            self.overlay5_checkbox.setStyleSheet("")  # Always default color
        self.overlay5_checkbox.stateChanged.connect(update_overlay5_checkbox_style)
        update_overlay5_checkbox_style(self.overlay5_checkbox.checkState())

        overlay5_layout = QHBoxLayout()
        overlay5_layout.setSpacing(4)
        self.overlay5_edit = ImageDropLineEdit()
        self.overlay5_edit.setPlaceholderText("Overlay 5 image path (*.gif, *.png)")
        self.overlay5_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
        self.overlay5_edit.setFixedWidth(125)
        self.overlay5_path = ""
        def on_overlay5_changed():
            current_text = self.overlay5_edit.text()
            cleaned_text = clean_file_path(current_text)
            if cleaned_text != current_text:
                self.overlay5_edit.setText(cleaned_text)
            self.overlay5_path = self.overlay5_edit.text().strip()
        self.overlay5_edit.textChanged.connect(on_overlay5_changed)
        overlay5_btn = QPushButton("Select")
        overlay5_btn.setFixedWidth(60)
        def select_overlay5_image():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Overlay 5 Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.overlay5_edit.setText(file_path)
        overlay5_btn.clicked.connect(select_overlay5_image)
        overlay5_size_label = QLabel("S:")
        overlay5_size_label.setFixedWidth(18)
        self.overlay5_size_combo = QtWidgets.QComboBox()
        self.overlay5_size_combo.setFixedWidth(90)
        for percent in range(5, 101, 5):
            self.overlay5_size_combo.addItem(f"{percent}%", percent)
        self.overlay5_size_combo.setCurrentIndex(2)  # Default 15%
        self.overlay5_size_percent = 15
        def on_overlay5_size_changed(idx):
            self.overlay5_size_percent = self.overlay5_size_combo.itemData(idx)
        self.overlay5_size_combo.setEditable(False)
        self.overlay5_size_combo.currentIndexChanged.connect(on_overlay5_size_changed)
        on_overlay5_size_changed(self.overlay5_size_combo.currentIndex())
        # Overlay 5 position option
        overlay5_position_label = QLabel("P:")
        overlay5_position_label.setFixedWidth(18)
        self.overlay5_position_combo = QtWidgets.QComboBox()
        self.overlay5_position_combo.setFixedWidth(130)
        positions = [
            ("Center", "center"),
            ("Top Left", "top_left"),
            ("Top Right", "top_right"),
            ("Bottom Left", "bottom_left"),
            ("Bottom Right", "bottom_right")
        ]
        for label, value in positions:
            self.overlay5_position_combo.addItem(label, value)
        self.overlay5_position_combo.setCurrentIndex(2)  # Default top_right
        self.overlay5_position = "top_right"
        def on_overlay5_position_changed(idx):
            self.overlay5_position = self.overlay5_position_combo.itemData(idx)
        self.overlay5_position_combo.currentIndexChanged.connect(on_overlay5_position_changed)
        on_overlay5_position_changed(self.overlay5_position_combo.currentIndex())
        def set_overlay5_enabled(state):
            enabled = state == Qt.CheckState.Checked
            self.overlay5_edit.setEnabled(enabled)
            overlay5_btn.setEnabled(enabled)
            self.overlay5_size_combo.setEnabled(enabled)
            self.overlay5_position_combo.setEnabled(enabled)
            if enabled:
                overlay5_btn.setStyleSheet("")
                self.overlay5_edit.setStyleSheet("")
                self.overlay5_size_combo.setStyleSheet("")
                self.overlay5_position_combo.setStyleSheet("")
                overlay5_size_label.setStyleSheet("")
                overlay5_position_label.setStyleSheet("")
            else:
                grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
                overlay5_btn.setStyleSheet(grey_btn_style)
                self.overlay5_edit.setStyleSheet(grey_btn_style)
                self.overlay5_size_combo.setStyleSheet(grey_btn_style)
                self.overlay5_position_combo.setStyleSheet(grey_btn_style)
                overlay5_size_label.setStyleSheet("color: grey;")
                overlay5_position_label.setStyleSheet("color: grey;")
        self.overlay5_checkbox.stateChanged.connect(lambda _: set_overlay5_enabled(self.overlay5_checkbox.checkState()))
        set_overlay5_enabled(self.overlay5_checkbox.checkState())
        overlay5_layout.addWidget(self.overlay5_checkbox)
        overlay5_layout.addWidget(self.overlay5_edit)
        overlay5_layout.addSpacing(6)
        overlay5_layout.addWidget(overlay5_btn)
        overlay5_layout.addSpacing(4)
        overlay5_layout.addWidget(overlay5_position_label)
        overlay5_layout.addSpacing(2)
        overlay5_layout.addWidget(self.overlay5_position_combo)
        overlay5_layout.addSpacing(6)
        overlay5_layout.addWidget(overlay5_size_label)
        overlay5_layout.addWidget(self.overlay5_size_combo)
        layout.addLayout(overlay5_layout)

        # --- EFFECT CONTROL FOR OVERLAY 4_5 (identical for both overlays) ---
        overlay4_5_label = QLabel("Overlay 4_5:")
        overlay4_5_label.setFixedWidth(80)
        self.overlay4_5_effect_combo = QtWidgets.QComboBox()
        self.overlay4_5_effect_combo.setFixedWidth(combo_width)
        for label, value in effect_options:
            self.overlay4_5_effect_combo.addItem(label, value)
        self.overlay4_5_effect_combo.setCurrentIndex(1)
        self.selected_overlay4_5_effect = "fadein"
        def on_overlay4_5_effect_changed(idx):
            self.selected_overlay4_5_effect = self.overlay4_5_effect_combo.itemData(idx)
        self.overlay4_5_effect_combo.currentIndexChanged.connect(on_overlay4_5_effect_changed)
        on_overlay4_5_effect_changed(self.overlay4_5_effect_combo.currentIndex())

        overlay4_5_start_label = QLabel("at (s):")
        overlay4_5_start_label.setFixedWidth(40)
        self.overlay4_5_start_edit = QLineEdit("5")
        self.overlay4_5_start_edit.setFixedWidth(edit_width)
        self.overlay4_5_start_edit.setValidator(QIntValidator(0, 999, self))
        self.overlay4_5_start_edit.setPlaceholderText("5")
        self.overlay4_5_start_at = 5
        def on_overlay4_5_start_changed():
            try:
                self.overlay4_5_start_at = int(self.overlay4_5_start_edit.text())
            except Exception:
                self.overlay4_5_start_at = 5
        self.overlay4_5_start_edit.textChanged.connect(on_overlay4_5_start_changed)
        on_overlay4_5_start_changed()

        overlay4_5_layout = QHBoxLayout()
        overlay4_5_layout.setContentsMargins(0, 0, 0, 0)
        overlay4_5_layout.addSpacing(165)
        overlay4_5_layout.addWidget(overlay4_5_label)
        overlay4_5_layout.addSpacing(-10)
        overlay4_5_layout.addWidget(self.overlay4_5_effect_combo)
        overlay4_5_layout.addSpacing(-10)
        overlay4_5_layout.addWidget(overlay4_5_start_label)
        overlay4_5_layout.addSpacing(-10)
        overlay4_5_layout.addWidget(self.overlay4_5_start_edit)
        overlay4_5_layout.addStretch()
        layout.addLayout(overlay4_5_layout)

        # --- Overlay 4_5 effect greying logic ---
        def update_overlay4_5_effect_label_style():
            if not (self.overlay4_checkbox.isChecked() or self.overlay5_checkbox.isChecked()):
                overlay4_5_label.setStyleSheet("color: grey;")
                self.overlay4_5_effect_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.overlay4_5_effect_combo.setEnabled(False)
                overlay4_5_start_label.setStyleSheet("color: grey;")
                self.overlay4_5_start_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.overlay4_5_start_edit.setEnabled(False)
            else:
                overlay4_5_label.setStyleSheet("")
                self.overlay4_5_effect_combo.setStyleSheet("")
                self.overlay4_5_effect_combo.setEnabled(True)
                overlay4_5_start_label.setStyleSheet("")
                self.overlay4_5_start_edit.setStyleSheet("")
                self.overlay4_5_start_edit.setEnabled(True)
        self.overlay4_checkbox.stateChanged.connect(lambda _: update_overlay4_5_effect_label_style())
        self.overlay5_checkbox.stateChanged.connect(lambda _: update_overlay4_5_effect_label_style())
        update_overlay4_5_effect_label_style()

    def create_action_buttons(self, layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()

        # Add settings button first, before terminal
        button_layout.addSpacing(10)
        self.settings_btn = QPushButton()
        icon_path = os.path.join(PROJECT_ROOT, "src", "sources", "settings.png")
        self.settings_btn.setIcon(QIcon(icon_path))
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setIconSize(self.settings_btn.size())  # Make icon fill button
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setStyleSheet("QPushButton { background: transparent; border: none; padding: 0px; margin: 0px; } QPushButton:pressed { background: transparent; }")
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        button_layout.addWidget(self.settings_btn)

        # Add terminal button next
        button_layout.addSpacing(10)
        self.terminal_btn = QPushButton("💻 Terminal")
        self.terminal_btn.setFixedHeight(35)
        self.terminal_btn.setFixedWidth(100)
        self.terminal_btn.clicked.connect(self.show_terminal)
        button_layout.addWidget(self.terminal_btn)

        # Then add create video button, always after terminal
        button_layout.addSpacing(0)
        self.create_btn = QPushButton("Create Video")
        self.create_btn.setFixedHeight(35)
        self.create_btn.setFixedWidth(350)
        self.create_btn.clicked.connect(self.create_video)
        button_layout.addWidget(self.create_btn)

        # Add placeholder button after create video button
        button_layout.addSpacing(5)
        self.placeholder_btn = QPushButton()
        rocket_icon_path = os.path.join(PROJECT_ROOT, "src", "sources", "rocket.png")
        self.placeholder_btn.setIcon(QIcon(rocket_icon_path))
        self.placeholder_btn.setIconSize(QSize(28, 28))
        self.placeholder_btn.setFixedHeight(32)
        self.placeholder_btn.setFixedWidth(32)
        self.placeholder_btn.setStyleSheet("QPushButton { background: transparent; border: none; padding: 0px; margin: 0px; } QPushButton:pressed { background: transparent; }")
        # self.placeholder_btn.setVisible(self.static_icon.isVisible())  # Ensure always visible
        button_layout.addWidget(self.placeholder_btn)

        button_layout.addStretch()  # Pushes spinner to the far right

        layout.addLayout(button_layout)

    def create_progress_controls(self, layout):
        """Create progress bar and stop button on the same line, with stop button before progress bar. Progress bar should stretch to fill space."""
        progress_row = QtWidgets.QHBoxLayout()
        self.stop_btn = QPushButton()
        self.stop_btn.setFixedHeight(24)
        self.stop_btn.setFixedWidth(24)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        stop_icon_path = os.path.join(PROJECT_ROOT, "src", "sources", "stopbutton.png")
        self.stop_btn.setIcon(QIcon(stop_icon_path))
        self.stop_btn.setIconSize(QSize(22, 22))
        self.stop_btn.setStyleSheet("QPushButton { background: transparent; border: none; } QPushButton:pressed { background: transparent; }")
        self.stop_btn.clicked.connect(self.stop_video_creation)
        progress_row.addWidget(self.stop_btn)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)        
        self.progress_bar.setFormat("Batch: 0/0")
        self.progress_bar.setVisible(False)
        self.progress_bar.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        progress_row.addWidget(self.progress_bar)
        layout.addLayout(progress_row)

    def restore_window_position(self):
        """Restore window position from settings"""
        settings = QSettings('SuperCut', 'SuperCutUI')
        pos = settings.value('window_position')
        if isinstance(pos, QPoint):
            self.move(pos)
        elif isinstance(pos, (tuple, list)) and len(pos) == 2:
            self.move(QPoint(pos[0], pos[1]))
        else:
            # Set initial position to top-left corner (0,0)
            self.move(0, 0)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_window)

    def close_window(self):
        """Wrapper method for close() to fix PyQt slot type error"""
        self.close()

    def show_terminal(self):
        """Show or create the terminal widget"""
        if self.terminal_widget is None:
            self.terminal_widget = TerminalWidget()
            # Connect to the closed signal
            self.terminal_widget.closed.connect(self.on_terminal_closed)
            # Position terminal intelligently based on main window position
            self.position_terminal_widget()
            self.terminal_widget.show_and_raise()
            # Update button text to show terminal is on
            self.terminal_btn.setText("💻 Terminal ON")
        else:
            # Terminal exists, toggle it off
            self.terminal_widget.close()
            self.terminal_widget = None
            # Update button text to show terminal is off
            self.terminal_btn.setText("💻 Terminal")

    def position_terminal_widget(self):
        """Position the terminal widget intelligently based on main window position and screen space"""
        if not self.terminal_widget:
            return
            
        # Get main window position and size
        main_pos = self.pos()
        main_width = self.width()
        main_height = self.height()
        
        # Get terminal widget size
        terminal_width = self.terminal_widget.width()
        terminal_height = self.terminal_widget.height()
        
        # Get screen geometry
        screen = self.screen() if hasattr(self, 'screen') and self.screen() else QApplication.primaryScreen()
        if screen is not None:
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
        else:
            screen_width = 1920
            screen_height = 1080
        
        # Calculate available space on left and right
        space_on_right = screen_width - (main_pos.x() + main_width)
        space_on_left = main_pos.x()
        
        # Determine optimal position
        if space_on_right >= terminal_width + 10:
            # Enough space on the right - position there
            terminal_x = main_pos.x() + main_width + 10
            terminal_y = main_pos.y()
            position_side = "right"
        elif space_on_left >= terminal_width + 10:
            # Enough space on the left - position there
            terminal_x = main_pos.x() - terminal_width - 10
            terminal_y = main_pos.y()
            position_side = "left"
        else:
            # Not enough space on either side, try to fit it
            if space_on_right > space_on_left:
                # More space on right, try to fit there
                terminal_x = main_pos.x() + main_width + 5
                terminal_y = main_pos.y()
                position_side = "right (tight)"
            else:
                # More space on left, try to fit there
                terminal_x = main_pos.x() - terminal_width - 5
                terminal_y = main_pos.y()
                position_side = "left (tight)"
        
        # Ensure terminal doesn't go off-screen vertically
        if terminal_y + terminal_height > screen_height:
            terminal_y = screen_height - terminal_height - 10
        
        if terminal_y < 0:
            terminal_y = 10
        
        # Ensure terminal doesn't go off-screen horizontally
        if terminal_x + terminal_width > screen_width:
            terminal_x = screen_width - terminal_width - 10
        
        if terminal_x < 0:
            terminal_x = 10
        
        # Position the terminal widget
        self.terminal_widget.move(terminal_x, terminal_y)
        
        # Update terminal title to show positioning
        self.terminal_widget.setWindowTitle(f"SuperCut Terminal [{position_side}]")

    def on_terminal_closed(self):
        """Handle terminal widget closed signal"""
        self.terminal_widget = None
        # Reset button text when terminal is closed manually
        self.terminal_btn.setText("💻 Terminal")

    def select_media_sources_folder(self):
        """Select media sources folder"""
        desktop_folder = get_desktop_folder()
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder", desktop_folder)
        if folder:
            self.media_sources_edit.setText(folder)
            if not self.output_folder_manual:
                self.folder_edit.setText(folder)
            self.update_output_name()
        else:
            if not self.output_folder_manual:
                self.folder_edit.setText("")

    def select_output_folder(self):
        """Select output folder"""
        desktop_folder = get_desktop_folder()
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", desktop_folder)
        if folder:
            self.folder_edit.setText(folder)
            self.output_folder_manual = True
            self.update_output_name()

    def update_output_name(self):
        """Update the output filename based on current inputs"""
        if hasattr(self, 'name_list_checkbox') and self.name_list_checkbox.isChecked() and self.name_list:
            # Use first name for preview, do not append number
            part1 = self.name_list[0][:180]
            filename = f"{sanitize_filename(part1)}.mp4"
        else:
            part1 = self.part1_edit.text().strip()
            part2 = self.part2_edit.text().strip()
            folder = self.folder_edit.text().strip() or os.getcwd()
            # Default to 1 if blank or zero
            if not part2 or part2 == '0':
                part2 = '1'
            # Sanitize export name
            part1 = sanitize_filename(part1 or "")
            if part1 and part2:
                filename = f"{part1}_{part2}.mp4"
            else:
                filename = "output.mp4"
        folder = self.folder_edit.text().strip() or os.getcwd()
        self.output_path = os.path.join(folder, filename)

    def create_video(self):
        """Start video creation process"""
        # Step 1: Gather and validate inputs
        # Intro validation
        if self.intro_checkbox.isChecked():
            intro_path = self.intro_edit.text().strip()
            if not intro_path or not os.path.isfile(intro_path) or os.path.splitext(intro_path)[1].lower() not in ['.gif', '.png']:
                QMessageBox.warning(self, "⚠️ Intro Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Intro.", QMessageBox.StandardButton.Ok)
                return
        # Overlay 1 validation
        if self.overlay_checkbox.isChecked():
            overlay_path = self.overlay1_edit.text().strip()
            if not overlay_path or not os.path.isfile(overlay_path) or os.path.splitext(overlay_path)[1].lower() not in ['.gif', '.png']:
                QMessageBox.warning(self, "⚠️ Overlay Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Overlay 1.", QMessageBox.StandardButton.Ok)
                return
        # Overlay 2 validation
        if self.overlay2_checkbox.isChecked():
            overlay2_path = self.overlay2_edit.text().strip()
            if not overlay2_path or not os.path.isfile(overlay2_path) or os.path.splitext(overlay2_path)[1].lower() not in ['.gif', '.png']:
                QMessageBox.warning(self, "⚠️ Overlay 2 Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Overlay 2.", QMessageBox.StandardButton.Ok)
                return
        # Overlay 3 validation
        if self.overlay3_checkbox.isChecked():
            overlay3_path = self.overlay3_edit.text().strip()
            if not overlay3_path or not os.path.isfile(overlay3_path) or os.path.splitext(overlay3_path)[1].lower() not in ['.gif', '.png']:
                QMessageBox.warning(self, "⚠️ Overlay 3 Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Overlay 3.", QMessageBox.StandardButton.Ok)
                return
        # Overlay 4 validation
        if self.overlay4_checkbox.isChecked():
            overlay4_path = self.overlay4_edit.text().strip()
            if not overlay4_path or not os.path.isfile(overlay4_path) or os.path.splitext(overlay4_path)[1].lower() not in ['.gif', '.png']:
                QMessageBox.warning(self, "⚠️ Overlay 4 Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Overlay 4.", QMessageBox.StandardButton.Ok)
                return
        # --- Name list validation ---
        use_name_list = hasattr(self, 'name_list_checkbox') and self.name_list_checkbox.isChecked()
        if use_name_list:
            if not self.name_list:
                QMessageBox.warning(self, "⚠️ Name List Required", "Please enter a name list (one name per line) before processing.", QMessageBox.StandardButton.Ok)
                return
        inputs = self._gather_and_validate_inputs()
        if not inputs:
            return
        media_sources, export_name, number, folder, codec, resolution, fps, original_mp3_files, original_image_files, min_mp3_count = inputs
        # Calculate total batches
        total_batches = min(len(original_image_files), len(original_mp3_files) // min_mp3_count)
        if use_name_list:
            if len(self.name_list) < total_batches:
                QMessageBox.critical(self, "❌ Not Enough Names", f"You provided {len(self.name_list)} names, but {total_batches} are required for all video batches.", QMessageBox.StandardButton.Ok)
                return
        # Step 2: Prepare UI for processing
        self._set_ui_processing_state(True, total_batches=total_batches)
        # Step 3: Set up worker and thread
        self._setup_worker_and_thread(media_sources, export_name, number, folder, codec, resolution, fps, original_mp3_files, original_image_files, min_mp3_count)

    def _gather_and_validate_inputs(self):
        """Gather and validate user inputs. Return tuple or None if invalid."""
        media_sources = self.media_sources_edit.text()
        use_name_list = hasattr(self, 'name_list_checkbox') and self.name_list_checkbox.isChecked()
        if use_name_list:
            export_name = ""  # Will use name list, but pass empty string for validation
        else:
            export_name = self.part1_edit.text().strip()
        number = self.part2_edit.text().strip()
        if not number or number == '0':
            number = '1'
        if not use_name_list:
            export_name = sanitize_filename(export_name or "")
        folder = self.folder_edit.text().strip()
        if not folder:
            QMessageBox.warning(self, "⚠️ Missing Output Folder", "Please select or enter an output folder.", QMessageBox.StandardButton.Ok)
            return None
        codec = self.codec_combo.currentData()
        resolution = self.resolution_combo.currentData()
        fps = self.fps_combo.currentData()
        if self.mp3_count_checkbox.isChecked():
            try:
                min_mp3_count = int(self.mp3_count_edit.text())
                if min_mp3_count < 1:
                    min_mp3_count = DEFAULT_MIN_MP3_COUNT
            except Exception:
                min_mp3_count = DEFAULT_MIN_MP3_COUNT
        else:
            min_mp3_count = DEFAULT_MIN_MP3_COUNT
        if not use_name_list:
            is_valid, error_msg = validate_inputs(media_sources, export_name or "", number)
            if not is_valid:
                QMessageBox.warning(self, "⚠️ Missing Input", error_msg, QMessageBox.StandardButton.Ok)
                return None
        is_valid, error_msg, mp3_files, image_files = validate_media_files(media_sources, min_mp3_count)
        if not is_valid:
            QMessageBox.critical(self, "❌ Error", error_msg)
            return None
        return (media_sources, export_name, number, folder, codec, resolution, fps, set(mp3_files), set(image_files), min_mp3_count)

    def _set_ui_processing_state(self, processing, total_batches=0):
        """Enable/disable UI controls for processing state."""
        self.progress_bar.setMaximum(total_batches)
        self.progress_bar.setValue(0)
        empty_space = " " * 2
        self.progress_bar.setFormat(f"{empty_space}Batch: 0/{total_batches}")
        self.progress_bar.setVisible(processing)
        self.stop_btn.setEnabled(processing)
        self.stop_btn.setVisible(processing)
        if hasattr(self, 'spinner_label'):
            self.spinner_label.setVisible(processing)
        if hasattr(self, 'loading_label'):
            self.loading_label.setVisible(processing)
            movie = self.loading_label.movie()
            if movie is not None:
                if processing:
                    movie.start()
                else:
                    movie.stop()
        if hasattr(self, 'static_icon'):
            self.static_icon.setVisible(not processing)
        if hasattr(self, 'title_placeholder_btn'):
            self.title_placeholder_btn.setVisible(not processing)
        controls = [
            self.create_btn, self.codec_combo, self.resolution_combo, self.fps_combo,
            self.media_sources_edit, self.folder_edit, self.part1_edit, self.part2_edit,
            self.media_sources_select_btn, self.output_folder_select_btn, self.overlay_checkbox
        ]
        for ctrl in controls:
            ctrl.setEnabled(not processing)

        # --- Window resize logic ---
        if processing:
            if not self._expanded_for_progress:
                self._original_size = self.size()
                # Calculate new height: add enough for progress bar + stop button (e.g., 60px)
                extra_height = 40
                new_height = self.height() + extra_height
                self.setFixedSize(self.width(), new_height)
                self._expanded_for_progress = True
        else:
            if self._expanded_for_progress and self._original_size is not None:
                self.setFixedSize(self._original_size)
                self._expanded_for_progress = False

    def _setup_worker_and_thread(self, media_sources, export_name, number, folder, codec, resolution, fps, original_mp3_files, original_image_files, min_mp3_count):
        """Set up the VideoWorker and QThread, connect signals, and start processing."""
        self._thread = QThread()
        use_name_list = hasattr(self, 'name_list_checkbox') and self.name_list_checkbox.isChecked()
        name_list = self.name_list if use_name_list else None
        # Get ffmpeg preset from settings
        preset = self.settings.value('default_ffmpeg_preset', DEFAULT_FFMPEG_PRESET, type=str)
        # Get ffmpeg audio bitrate from settings
        audio_bitrate = self.settings.value('default_ffmpeg_audio_bitrate', DEFAULT_AUDIO_BITRATE, type=str)
        # Get ffmpeg video bitrate from settings
        video_bitrate = self.settings.value('default_ffmpeg_video_bitrate', DEFAULT_VIDEO_BITRATE, type=str)
        # Get ffmpeg maxrate from settings
        maxrate = self.settings.value('default_ffmpeg_maxrate', DEFAULT_MAXRATE, type=str)
        # Get ffmpeg bufsize from settings
        bufsize = self.settings.value('default_ffmpeg_bufsize', DEFAULT_BUFSIZE, type=str)
        # Use overlay_duration as the start time for both overlay 1 and overlay 2
        overlay1_start_at = self.overlay_duration
        overlay2_start_at = self.overlay_duration
        self._worker = VideoWorker(
            media_sources, export_name, number, folder, codec, resolution, fps,
            self.overlay_checkbox.isChecked(), min_mp3_count, self.overlay1_path, self.overlay1_size_percent, self.overlay1_position,
            self.overlay2_checkbox.isChecked(), self.overlay2_path, self.overlay2_size_percent, self.overlay2_position,
            overlay1_start_at, overlay2_start_at,            
            self.overlay3_checkbox.isChecked(), self.overlay3_path, self.overlay3_size_percent, self.overlay3_position,
            self.overlay4_checkbox.isChecked(), self.overlay4_path, self.overlay4_size_percent, self.overlay4_position,
            self.overlay5_checkbox.isChecked(), self.overlay5_path, self.overlay5_size_percent, self.overlay5_position,
            self.intro_checkbox.isChecked(), self.intro_path, self.intro_size_percent, self.intro_position,
            self.selected_effect, self.overlay_duration,
            self.intro_effect, self.intro_duration,
            name_list=name_list,
            preset=preset,
            audio_bitrate=audio_bitrate,
            video_bitrate=video_bitrate,
            maxrate=maxrate,
            bufsize=bufsize,
            use_song_title_overlay=self.song_title_checkbox.isChecked(),
            song_title_effect=self.song_title_effect,
            song_title_font=self.song_title_font,
            song_title_font_size=self.song_title_font_size,
            song_title_color=self.song_title_color,
            song_title_bg=self.song_title_bg,
            song_title_bg_color=self.song_title_bg_color,
            song_title_opacity=self.song_title_opacity,
            song_title_x_percent=self.song_title_x_percent,
            song_title_y_percent=self.song_title_y_percent,
            song_title_start_at=self.song_title_start_at,
            song_title_scale_percent=self.song_title_scale_percent,
            overlay4_effect=self.selected_overlay4_5_effect,
            overlay4_effect_time=self.overlay4_5_start_at,
            overlay5_effect=self.selected_overlay4_5_effect,
            overlay5_effect_time=self.overlay4_5_start_at
            
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_worker_progress)
        self._worker.error.connect(self.on_worker_error)
        self._worker.finished.connect(
            lambda leftover_mp3s, used_images, failed_moves: self.on_worker_finished_with_leftovers(
                leftover_mp3s, used_images, original_image_files, failed_moves
            )
        )
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def on_worker_progress(self, batch_count, total_batches):
        """Handle worker progress updates"""
        if not self.isVisible():
            return
        self.progress_bar.setMaximum(total_batches)
        self.progress_bar.setValue(batch_count)
        self.progress_bar.setFormat(f"Batch: {batch_count}/{total_batches}")
        QtWidgets.QApplication.processEvents()

    def on_worker_error(self, message):
        """Handle worker errors"""
        if not self.isVisible():
            return
        self.progress_bar.setVisible(False)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        if hasattr(self, 'spinner_label'):
            self.spinner_label.setVisible(False)
        if hasattr(self, 'loading_label'):
            self.loading_label.setVisible(False)
            movie = self.loading_label.movie()
            if movie is not None:
                movie.stop()
        if hasattr(self, 'static_icon'):
            self.static_icon.setVisible(True)
        self.create_btn.setEnabled(True)
        self.codec_combo.setEnabled(True)
        self.resolution_combo.setEnabled(True)
        self.fps_combo.setEnabled(True)
        self.media_sources_edit.setEnabled(True)
        self.folder_edit.setEnabled(True)
        self.part1_edit.setEnabled(True)
        self.part2_edit.setEnabled(True)
        self.media_sources_select_btn.setEnabled(True)
        self.output_folder_select_btn.setEnabled(True)
        self.overlay_checkbox.setEnabled(True)
        dlg = ScrollableErrorDialog(self, title="❌ Error", message=message)
        dlg.exec()
        self.cleanup_worker_and_thread()
        self._worker = None
        self._thread = None
        
        if hasattr(self, '_auto_close_on_stop') and self._auto_close_on_stop:
            self._auto_close_on_stop = False
            if hasattr(self, '_stopping_msgbox') and self._stopping_msgbox is not None:
                self._stopping_msgbox.close()
                self._stopping_msgbox.hide()
                QtWidgets.QApplication.processEvents()
                self._stopping_msgbox = None
            self.close()

    def stop_video_creation(self):
        """Stop video creation process"""
        if hasattr(self, "_worker") and self._worker is not None:
            stop_method = getattr(self._worker, 'stop', None)
            if callable(stop_method):
                try:
                    stop_method()
                except RuntimeError:
                    pass  # Worker already deleted
                    
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        
        # Show waiting dialog
        self._stopping_msgbox = PleaseWaitDialog(self)
        self._stopping_msgbox.show()
        
        self.progress_bar.setVisible(False)
        self.create_btn.setEnabled(True)
        self.codec_combo.setEnabled(True)
        self.resolution_combo.setEnabled(True)
        self.fps_combo.setEnabled(True)
        self.media_sources_edit.setEnabled(True)
        self.folder_edit.setEnabled(True)
        self.part1_edit.setEnabled(True)
        self.part2_edit.setEnabled(True)
        self.media_sources_select_btn.setEnabled(True)
        self.output_folder_select_btn.setEnabled(True)
        self.overlay_checkbox.setEnabled(True)
        self._auto_close_on_stop = False
        self._stopped_by_user = True

    def on_worker_finished_with_leftovers(self, leftover_mp3s, used_images, original_image_files, failed_moves=None):
        """Handle worker completion with leftover files"""
        if not self.isVisible():
            return
        self._set_ui_processing_state(False)
        # Calculate leftover images using used_images
        leftover_images = list(set(original_image_files) - set(used_images))
        # Get min_mp3_count from input
        if self.mp3_count_checkbox.isChecked():
            try:
                min_mp3_count = int(self.mp3_count_edit.text())
                if min_mp3_count < 1:
                    min_mp3_count = DEFAULT_MIN_MP3_COUNT
            except Exception:
                min_mp3_count = DEFAULT_MIN_MP3_COUNT
        else:
            min_mp3_count = DEFAULT_MIN_MP3_COUNT
        # Show appropriate dialog
        if hasattr(self, '_stopped_by_user') and self._stopped_by_user:
            self._stopped_by_user = False  # reset for next run
            if hasattr(self, '_stopping_msgbox') and self._stopping_msgbox is not None:
                self._stopping_msgbox.close()
                self._stopping_msgbox.hide()
                QtWidgets.QApplication.processEvents()
                self._stopping_msgbox = None
            batch_count = self.progress_bar.value() if hasattr(self, 'progress_bar') else 0
            total_batches = self.progress_bar.maximum() if hasattr(self, 'progress_bar') else 0
            dlg = StoppedDialog(self, batch_count=batch_count, total_batches=total_batches)
            dlg.exec()
        else:
            # Only show leftover files that still exist
            import os
            real_leftover_mp3s = [f for f in leftover_mp3s if os.path.exists(f)] if leftover_mp3s else []
            real_leftover_images = [f for f in leftover_images if os.path.exists(f)] if leftover_images else []
            # Debug prints for leftovers
            # print("[DEBUG] leftover_mp3s:", leftover_mp3s)
            # print("[DEBUG] used_images:", used_images)
            # print("[DEBUG] original_image_files:", original_image_files)
            # print("[DEBUG] real_leftover_mp3s:", real_leftover_mp3s)
            # print("[DEBUG] real_leftover_images:", real_leftover_images)
            if real_leftover_mp3s or real_leftover_images:
                # Show dialog indicating process is incomplete due to leftovers
                dlg = SuccessWithLeftoverDialog(
                    self,
                    open_folder=self.open_result_folder,
                    leftover_mp3s=real_leftover_mp3s,
                    leftover_images=real_leftover_images,
                    min_mp3_count=min_mp3_count
                )
                # Auto-close after 2 seconds if pending close is set
                if hasattr(self, '_pending_close') and self._pending_close:
                    timer = QTimer(self)
                    timer.singleShot(2000, dlg.close)
                dlg.exec()
            else:
                self.show_success_options(min_mp3_count=min_mp3_count)
        # Show warning if any files failed to move (only if they still exist and were used)
        if failed_moves:
            import os
            # Only warn for files that are both failed to move and were actually used
            used_files = set((used_images or []) + (leftover_mp3s or []))
            still_failed = [f for f in failed_moves if os.path.exists(f) and f in used_files]
            if still_failed:
                QMessageBox.warning(self, "Warning: File Move Failed", f"Some files could not be moved to the bin folder:\n\n" + '\n'.join(still_failed))
        self.clear_inputs()
        self.cleanup_worker_and_thread()
        self._worker = None
        self._thread = None
        # --- Handle pending close after worker finishes ---
        if hasattr(self, '_pending_close') and self._pending_close:
            self._pending_close = False
            if hasattr(self, '_waiting_dialog_on_close') and self._waiting_dialog_on_close is not None:
                self._waiting_dialog_on_close.close()
                self._waiting_dialog_on_close.hide()
                self._waiting_dialog_on_close = None
            QtWidgets.QApplication.processEvents()
            self.close()
        if hasattr(self, '_auto_close_on_stop') and self._auto_close_on_stop:
            self._auto_close_on_stop = False
            if hasattr(self, '_stopping_msgbox') and self._stopping_msgbox is not None:
                self._stopping_msgbox.close()
                self._stopping_msgbox.hide()
                QtWidgets.QApplication.processEvents()
                self._stopping_msgbox = None

    def show_success_options(self, leftover_files=None, leftover_images=None, min_mp3_count=None):
        """Show success dialog with options. All UI updates are performed in the main thread via signals/slots."""
        # Play notification sound
        try:
            QtWidgets.QApplication.beep()
        except RuntimeError as e:
            logger.warning(f"Failed to play notification sound: {e}")
        if min_mp3_count is None:
            if self.mp3_count_checkbox.isChecked():
                try:
                    min_mp3_count = int(self.mp3_count_edit.text())
                    if min_mp3_count < 1:
                        min_mp3_count = DEFAULT_MIN_MP3_COUNT
                except Exception:
                    min_mp3_count = DEFAULT_MIN_MP3_COUNT
            else:
                min_mp3_count = DEFAULT_MIN_MP3_COUNT
        dlg = SuccessDialog(
            self, 
            open_folder=self.open_result_folder, 
            leftover_files=leftover_files, 
            leftover_images=leftover_images,
            min_mp3_count=min_mp3_count
        )
        # Auto-close after 2 seconds if pending close is set
        if hasattr(self, '_pending_close') and self._pending_close:
            timer = QTimer(self)
            timer.singleShot(2000, dlg.close)
        dlg.exec()

    def open_result_folder(self):
        """Open the result folder in file explorer"""
        folder = os.path.dirname(self.output_path)
        open_folder_in_explorer(folder)

    def clear_inputs(self):
        """Clear input fields"""
        self.media_sources_edit.setText("")
        self.folder_edit.setText("")
        self.part2_edit.setText("")

    def closeEvent(self, event):
        """Handle window close event"""
        # Close terminal widget if it exists
        if hasattr(self, 'terminal_widget') and self.terminal_widget is not None:
            self.terminal_widget.close()
            self.terminal_widget = None
        # If a video creation thread is running, warn the user
        if hasattr(self, '_thread') and self._thread is not None and self._thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Quit Program",
                "Video creation is running. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                waiting_dialog = QMessageBox(self)
                waiting_dialog.setWindowTitle("Please Wait")
                waiting_dialog.setText("Waiting for current batch to finish...")
                waiting_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
                waiting_dialog.show()
                # Request stop
                if hasattr(self, "_worker") and self._worker is not None:
                    stop_method = getattr(self._worker, 'stop', None)
                    if callable(stop_method):
                        try:
                            stop_method()
                        except RuntimeError:
                            pass
                # Set pending close flag
                self._pending_close = True
                # Store waiting dialog to close later
                self._waiting_dialog_on_close = waiting_dialog
                event.ignore()
                return
            else:
                event.ignore()
                return
        # Save window position and close as normal
        settings = QSettings('SuperCut', 'SuperCutUI')
        settings.setValue('window_position', self.pos())
        super().closeEvent(event)

    def moveEvent(self, event):
        """Handle window move event to reposition terminal widget"""
        super().moveEvent(event)
        # Reposition terminal widget if it exists and is visible
        if (hasattr(self, 'terminal_widget') and 
            self.terminal_widget is not None and 
            self.terminal_widget.isVisible()):
            self.position_terminal_widget()

    def on_media_folder_changed(self):
        """When media folder is changed, set output folder to same only if output folder is empty"""
        folder = self.media_sources_edit.text().strip()
        if folder and not self.folder_edit.text().strip():
            self.folder_edit.setText(folder)
            self.output_folder_manual = False  # Auto-set, so mark as not manual
            self.update_output_name()

    def on_output_folder_changed(self, text):
        """Reset manual flag if output folder is cleared"""
        if not text.strip():
            self.output_folder_manual = False

    def show_settings_dialog(self):
        dlg = SettingsDialog(self, settings=self.settings, fps_options=DEFAULT_FPS_OPTIONS)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.apply_settings()

    def apply_settings(self):
        # Update FPS combo to reflect new default if not set by user yet
        default_fps = self.settings.value('default_fps', type=int)
        if default_fps is not None:
            idx = next((i for i, (label, value) in enumerate(DEFAULT_FPS_OPTIONS) if value == default_fps), 0)
            self.fps_combo.setCurrentIndex(idx)
        # Apply default intro settings only if enabled
        default_intro_enabled = self.settings.value('default_intro_enabled', True, type=bool)
        if default_intro_enabled:
            default_intro_path = self.settings.value('default_intro_path', '', type=str)
            default_intro_position = self.settings.value('default_intro_position', 'center', type=str)
            default_intro_size = self.settings.value('default_intro_size', 50, type=int)
            if self.intro_checkbox.isChecked():
                if not self.intro_edit.text().strip():
                    self.intro_edit.setText(default_intro_path)
                idx = next((i for i in range(self.intro_position_combo.count()) if self.intro_position_combo.itemData(i) == default_intro_position), 0)
                self.intro_position_combo.setCurrentIndex(idx)
                idx = next((i for i in range(self.intro_size_combo.count()) if self.intro_size_combo.itemData(i) == default_intro_size), 9)
                self.intro_size_combo.setCurrentIndex(idx)
        # Apply default overlay 1 settings if overlay 1 is checked and fields are empty
        default_overlay1_path = self.settings.value('default_overlay1_path', '', type=str)
        default_overlay1_position = self.settings.value('default_overlay1_position', 'bottom_left', type=str)
        default_overlay1_size = self.settings.value('default_overlay1_size', 15, type=int)
        default_overlay1_enabled = self.settings.value('default_overlay1_enabled', True, type=bool)
        if default_overlay1_enabled:
            if self.overlay_checkbox.isChecked():
                if not self.overlay1_edit.text().strip():
                    self.overlay1_edit.setText(default_overlay1_path)
                idx = next((i for i in range(self.overlay1_position_combo.count()) if self.overlay1_position_combo.itemData(i) == default_overlay1_position), 3)
                self.overlay1_position_combo.setCurrentIndex(idx)
                idx = next((i for i in range(self.overlay1_size_combo.count()) if self.overlay1_size_combo.itemData(i) == default_overlay1_size), 2)
                self.overlay1_size_combo.setCurrentIndex(idx)
        # Apply default overlay 2 settings if overlay 2 is checked and fields are empty
        default_overlay2_path = self.settings.value('default_overlay2_path', '', type=str)
        default_overlay2_position = self.settings.value('default_overlay2_position', 'top_right', type=str)
        default_overlay2_size = self.settings.value('default_overlay2_size', 15, type=int)
        default_overlay2_enabled = self.settings.value('default_overlay2_enabled', True, type=bool)
        if default_overlay2_enabled:
            if self.overlay2_checkbox.isChecked():
                if not self.overlay2_edit.text().strip():
                    self.overlay2_edit.setText(default_overlay2_path)
                idx = next((i for i in range(self.overlay2_position_combo.count()) if self.overlay2_position_combo.itemData(i) == default_overlay2_position), 2)
                self.overlay2_position_combo.setCurrentIndex(idx)
                idx = next((i for i in range(self.overlay2_size_combo.count()) if self.overlay2_size_combo.itemData(i) == default_overlay2_size), 2)
                self.overlay2_size_combo.setCurrentIndex(idx)
        # Apply default overlay 3 settings if overlay 3 is checked and fields are empty
        default_overlay3_path = self.settings.value('default_overlay3_path', '', type=str)
        default_overlay3_position = self.settings.value('default_overlay3_position', 'top_right', type=str)
        default_overlay3_size = self.settings.value('default_overlay3_size', 15, type=int)
        default_overlay3_enabled = self.settings.value('default_overlay3_enabled', False, type=bool)
        if default_overlay3_enabled:
            if self.overlay3_checkbox.isChecked():
                if not self.overlay3_edit.text().strip():
                    self.overlay3_edit.setText(default_overlay3_path)
                idx = next((i for i in range(self.overlay3_position_combo.count()) if self.overlay3_position_combo.itemData(i) == default_overlay3_position), 2)
                self.overlay3_position_combo.setCurrentIndex(idx)
                idx = next((i for i in range(self.overlay3_size_combo.count()) if self.overlay3_size_combo.itemData(i) == default_overlay3_size), 2)
                self.overlay3_size_combo.setCurrentIndex(idx)
        # Apply default overlay 4 settings if overlay 4 is checked and fields are empty
        default_overlay4_path = self.settings.value('default_overlay4_path', '', type=str)
        default_overlay4_position = self.settings.value('default_overlay4_position', 'top_right', type=str)
        default_overlay4_size = self.settings.value('default_overlay4_size', 15, type=int)
        default_overlay4_enabled = self.settings.value('default_overlay4_enabled', False, type=bool)
        if default_overlay4_enabled:
            if self.overlay4_checkbox.isChecked():
                if not self.overlay4_edit.text().strip():
                    self.overlay4_edit.setText(default_overlay4_path)
                idx = next((i for i in range(self.overlay4_position_combo.count()) if self.overlay4_position_combo.itemData(i) == default_overlay4_position), 2)
                self.overlay4_position_combo.setCurrentIndex(idx)
                idx = next((i for i in range(self.overlay4_size_combo.count()) if self.overlay4_size_combo.itemData(i) == default_overlay4_size), 2)
                self.overlay4_size_combo.setCurrentIndex(idx)
        self.overlay4_checkbox.setChecked(default_overlay4_enabled)
        # Set intro checkbox state from settings
        self.intro_checkbox.setChecked(default_intro_enabled)
        # Set overlay1 checkbox state from settings
        self.overlay_checkbox.setChecked(default_overlay1_enabled)
        # Set overlay2 checkbox state from settings
        self.overlay2_checkbox.setChecked(default_overlay2_enabled)
        # Set overlay3 checkbox state from settings
        self.overlay3_checkbox.setChecked(default_overlay3_enabled)
        # Set overlay4 checkbox state from settings
        self.overlay4_checkbox.setChecked(default_overlay4_enabled)
        # Set overlay5 checkbox state from settings
        default_overlay5_path = self.settings.value('default_overlay5_path', '', type=str)
        default_overlay5_position = self.settings.value('default_overlay5_position', 'top_right', type=str)
        default_overlay5_size = self.settings.value('default_overlay5_size', 15, type=int)
        default_overlay5_enabled = self.settings.value('default_overlay5_enabled', False, type=bool)
        if default_overlay5_enabled:
            if self.overlay5_checkbox.isChecked():
                if not self.overlay5_edit.text().strip():
                    self.overlay5_edit.setText(default_overlay5_path)
                idx = next((i for i in range(self.overlay5_position_combo.count()) if self.overlay5_position_combo.itemData(i) == default_overlay5_position), 2)
                self.overlay5_position_combo.setCurrentIndex(idx)
                idx = next((i for i in range(self.overlay5_size_combo.count()) if self.overlay5_size_combo.itemData(i) == default_overlay5_size), 2)
                self.overlay5_size_combo.setCurrentIndex(idx)
        self.overlay5_checkbox.setChecked(default_overlay5_enabled)
        # Set list name checkbox state from settings
        default_list_name_enabled = self.settings.value('default_list_name_enabled', False, type=bool)
        if hasattr(self, 'name_list_checkbox'):
            self.name_list_checkbox.setChecked(default_list_name_enabled)
        # Set mp3 # checkbox state from settings
        default_mp3_count_enabled = self.settings.value('default_mp3_count_enabled', False, type=bool)
        if hasattr(self, 'mp3_count_checkbox'):
            self.mp3_count_checkbox.setChecked(default_mp3_count_enabled)
        # Set resolution combo state from settings
        default_resolution = self.settings.value('default_resolution', type=str)
        if default_resolution is not None and hasattr(self, 'resolution_combo'):
            idx = next((i for i, (label, value) in enumerate(DEFAULT_RESOLUTIONS) if value == default_resolution), 0)
            self.resolution_combo.setCurrentIndex(idx)
        if hasattr(self, 'resolution_combo') and hasattr(self, 'resolution_combo') and hasattr(self, 'resolution_combo'):
            # Also update main UI's resolution combo if present
            if hasattr(self, 'resolution_combo'):
                idx = next((i for i, (label, value) in enumerate(DEFAULT_RESOLUTIONS) if value == default_resolution), 0)
                self.resolution_combo.setCurrentIndex(idx)
        if hasattr(self, 'resolution_combo') and hasattr(self, 'resolution_combo'):
            # Update main UI's resolution combo if present
            if hasattr(self, 'resolution_combo'):
                idx = next((i for i, (label, value) in enumerate(DEFAULT_RESOLUTIONS) if value == default_resolution), 0)
                self.resolution_combo.setCurrentIndex(idx)
        # Update main UI's resolution combo if present
        if hasattr(self, 'resolution_combo') and hasattr(self, 'resolution_combo'):
            idx = next((i for i, (label, value) in enumerate(DEFAULT_RESOLUTIONS) if value == default_resolution), 0)
            self.resolution_combo.setCurrentIndex(idx)
        # Update main UI's resolution combo if present
        if hasattr(self, 'resolution_combo'):
            idx = next((i for i, (label, value) in enumerate(DEFAULT_RESOLUTIONS) if value == default_resolution), 0)
            self.resolution_combo.setCurrentIndex(idx)

    def cleanup_worker_and_thread(self):
        """Disconnect all signals and clean up worker and thread objects safely."""
        if hasattr(self, '_worker') and self._worker is not None:
            try:
                self._worker.progress.disconnect(self.on_worker_progress)
            except (TypeError, RuntimeError):
                pass
            try:
                self._worker.error.disconnect(self.on_worker_error)
            except (TypeError, RuntimeError):
                pass
            try:
                self._worker.finished.disconnect()
            except (TypeError, RuntimeError):
                pass
        if hasattr(self, '_thread') and self._thread is not None:
            try:
                self._thread.started.disconnect()
            except (TypeError, RuntimeError):
                pass