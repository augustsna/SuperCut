import os
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDesktopWidget, QDialog, QComboBox, QDialogButtonBox, QFormLayout
)
from PyQt5.QtCore import Qt, QSettings, QThread, QPoint, QSize
from PyQt5.QtGui import QIntValidator, QIcon, QPixmap, QMovie, QImage
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
    PROJECT_ROOT
)
from src.utils import (
    sanitize_filename, get_desktop_folder, open_folder_in_explorer,
    validate_inputs, validate_media_files
)
from src.ui_components import FolderDropLineEdit, WaitingDialog, PleaseWaitDialog, StoppedDialog, SuccessDialog, ScrollableErrorDialog, ImageDropLineEdit
from src.video_worker import VideoWorker
from src.terminal_widget import TerminalWidget

import time
import threading

class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None, fps_options=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.settings = settings
        self.fps_options = fps_options or [("24", 24)]
        self.selected_fps = None
        main_layout = QtWidgets.QVBoxLayout(self)
        # Add Settings label at the top
        settings_label = QLabel("Settings")
        settings_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        settings_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(settings_label)
        # Add Default button below Settings label
        self.reset_btn = QPushButton("Default")
        self.reset_btn.setFixedSize(100, 28)
        self.reset_btn.setStyleSheet("QPushButton { background: white; border: 1px solid #ccc; color: #333; } QPushButton:hover { background: #f5f5f5; }")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn_layout = QHBoxLayout()
        reset_btn_layout.addStretch()
        reset_btn_layout.addWidget(self.reset_btn)
        reset_btn_layout.addStretch()
        main_layout.addLayout(reset_btn_layout)
        form_layout = QFormLayout()
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
        form_layout.addRow("Default FPS:", self.fps_combo)
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
        form_layout.addRow("Default Intro Path:", intro_path_layout)
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
        form_layout.addRow("Default Intro Position:", self.default_intro_position_combo)
        # --- Default Intro Size ---
        self.default_intro_size_combo = QComboBox()
        self.default_intro_size_combo.setFixedWidth(120)
        for percent in range(5, 101, 5):
            self.default_intro_size_combo.addItem(f"{percent}%", percent)
        if self.settings is not None:
            default_intro_size = self.settings.value('default_intro_size', 50, type=int)
            idx = (default_intro_size // 5) - 1 if 5 <= default_intro_size <= 100 else 9
            self.default_intro_size_combo.setCurrentIndex(idx)
        form_layout.addRow("Default Intro Size:", self.default_intro_size_combo)
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
        form_layout.addRow("Default Overlay 1 Path:", overlay1_path_layout)
        # --- Default Overlay 1 Position ---
        self.default_overlay1_position_combo = QComboBox()
        self.default_overlay1_position_combo.setFixedWidth(120)
        for label, value in intro_positions:
            self.default_overlay1_position_combo.addItem(label, value)
        if self.settings is not None:
            default_overlay1_position = self.settings.value('default_overlay1_position', 'bottom_left', type=str)
            idx = next((i for i, (label, value) in enumerate(intro_positions) if value == default_overlay1_position), 3)
            self.default_overlay1_position_combo.setCurrentIndex(idx)
        form_layout.addRow("Default Overlay 1 Position:", self.default_overlay1_position_combo)
        # --- Default Overlay 1 Size ---
        self.default_overlay1_size_combo = QComboBox()
        self.default_overlay1_size_combo.setFixedWidth(120)
        for percent in range(5, 101, 5):
            self.default_overlay1_size_combo.addItem(f"{percent}%", percent)
        if self.settings is not None:
            default_overlay1_size = self.settings.value('default_overlay1_size', 15, type=int)
            idx = (default_overlay1_size // 5) - 1 if 5 <= default_overlay1_size <= 100 else 2
            self.default_overlay1_size_combo.setCurrentIndex(idx)
        form_layout.addRow("Default Overlay 1 Size:", self.default_overlay1_size_combo)
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
        form_layout.addRow("Default Overlay 2 Path:", overlay2_path_layout)
        # --- Default Overlay 2 Position ---
        self.default_overlay2_position_combo = QComboBox()
        self.default_overlay2_position_combo.setFixedWidth(120)
        for label, value in intro_positions:
            self.default_overlay2_position_combo.addItem(label, value)
        if self.settings is not None:
            default_overlay2_position = self.settings.value('default_overlay2_position', 'top_right', type=str)
            idx = next((i for i, (label, value) in enumerate(intro_positions) if value == default_overlay2_position), 2)
            self.default_overlay2_position_combo.setCurrentIndex(idx)
        form_layout.addRow("Default Overlay 2 Position:", self.default_overlay2_position_combo)
        # --- Default Overlay 2 Size ---
        self.default_overlay2_size_combo = QComboBox()
        self.default_overlay2_size_combo.setFixedWidth(120)
        for percent in range(5, 101, 5):
            self.default_overlay2_size_combo.addItem(f"{percent}%", percent)
        if self.settings is not None:
            default_overlay2_size = self.settings.value('default_overlay2_size', 15, type=int)
            idx = (default_overlay2_size // 5) - 1 if 5 <= default_overlay2_size <= 100 else 2
            self.default_overlay2_size_combo.setCurrentIndex(idx)
        form_layout.addRow("Default Overlay 2 Size:", self.default_overlay2_size_combo)
        # Center the form layout in the dialog
        form_widget = QtWidgets.QWidget()
        form_widget.setLayout(form_layout)
        form_layout_container = QtWidgets.QVBoxLayout()
        form_layout_container.addWidget(form_widget, alignment=Qt.AlignCenter)
        main_layout.addLayout(form_layout_container)
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
        self.setFixedSize(450, 520)
    def accept(self):
        self.selected_fps = self.fps_combo.currentData()
        if self.settings is not None:
            self.settings.setValue('default_fps', self.selected_fps)
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
        self.default_intro_path_edit.setText("")
        self.default_intro_position_combo.setCurrentIndex(0)  # Center
        idx_intro_size = (50 // 5) - 1  # 50% size
        self.default_intro_size_combo.setCurrentIndex(idx_intro_size)
        # Overlay 1
        self.default_overlay1_path_edit.setText("")
        self.default_overlay1_position_combo.setCurrentIndex(3)  # Bottom Left
        idx_overlay1_size = (15 // 5) - 1  # 15% size
        self.default_overlay1_size_combo.setCurrentIndex(idx_overlay1_size)
        # Overlay 2
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
        self.text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        if initial_names:
            self.set_names(initial_names)
        layout.addWidget(self.text_edit)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
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
        layout.addSpacing(-5)
        title_widget = QtWidgets.QWidget()
        title_widget.setFixedHeight(75)
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        # Add PNG logo in front of SuperCut title
        title_icon = QLabel()
        title_icon.setPixmap(QtGui.QPixmap(os.path.join(PROJECT_ROOT, "src", "sources", "icon.png")).scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title_label = QLabel("SuperCut")
        title_label.setStyleSheet("font-size: 35px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        static_icon = QLabel()
        static_icon.setPixmap(QtGui.QPixmap(os.path.join(PROJECT_ROOT, "src", "sources", "static.png")))
        static_icon.setVisible(True)  # Show by default
        self.static_icon = static_icon  # Store as instance variable for later control
        spinner_label = QLabel()
        spinner_movie = QtGui.QMovie(os.path.join(PROJECT_ROOT, "src", "sources", "spinner.gif"))
        spinner_label.setMovie(spinner_movie)       
        spinner_movie.start()
        spinner_label.setVisible(False)  # Hide by default
        self.spinner_label = spinner_label  # Store as instance variable for later control
        # Add loading.gif after spinner gif
        loading_label = QLabel()
        loading_movie = QtGui.QMovie(os.path.join(PROJECT_ROOT, "src", "sources", "loading.gif"))
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
        title_layout.addWidget(spinner_label, alignment=Qt.AlignVCenter)
        title_layout.addWidget(loading_label, alignment=Qt.AlignVCenter)
        
        title_layout.addStretch()
        title_widget.setLayout(title_layout)
        layout.addWidget(title_widget)
        # Add spacer below title bar to prevent overlap
        layout.addSpacing(0)
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
        self.name_list_enter_btn.setEnabled(self.name_list_checkbox.isChecked())  # Sync with checkbox state
        # Set initial style for name_list_enter_btn
        if not self.name_list_checkbox.isChecked():
            self.name_list_enter_btn.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
        else:
            self.name_list_enter_btn.setStyleSheet("")
        self.name_list = []  # Store the name list
        self.name_list_dialog = None
        def on_name_list_checkbox(state):
            enabled = state == Qt.Checked
            self.part1_edit.setEnabled(not enabled)
            self.part2_edit.setEnabled(not enabled)
            if enabled:
                self.name_list_checkbox.setStyleSheet("")
                self.name_list_enter_btn.setStyleSheet("")
                self.name_list_enter_btn.setEnabled(True)
                # Grey out name and number text boxes
                self.part1_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.part2_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
            else:
                self.name_list_checkbox.setStyleSheet("")
                self.name_list_enter_btn.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.name_list_enter_btn.setEnabled(False)
                # Restore default style for name and number text boxes
                self.part1_edit.setStyleSheet("")
                self.part2_edit.setStyleSheet("")
            if not enabled:
                self.name_list = []
        self.name_list_checkbox.stateChanged.connect(on_name_list_checkbox)
        # Apply logic for initial state
        on_name_list_checkbox(self.name_list_checkbox.checkState())
        def open_name_list_dialog():
            dlg = NameListDialog(self, self.name_list)
            if dlg.exec_() == QDialog.Accepted:
                self.name_list = dlg.get_names()
        self.name_list_enter_btn.clicked.connect(open_name_list_dialog)
        # --- End name list option ---
        self.mp3_count_checkbox = QtWidgets.QCheckBox("MP3 #")
        self.mp3_count_checkbox.setChecked(False)
        self.mp3_count_edit = QLineEdit(str(DEFAULT_MIN_MP3_COUNT))
        self.mp3_count_edit.setPlaceholderText("MP3")
        self.mp3_count_edit.setValidator(QIntValidator(1, 999, self))
        self.mp3_count_edit.setEnabled(False)
        self.mp3_count_edit.setFixedWidth(50)
        self.mp3_count_checkbox.stateChanged.connect(lambda state: self.mp3_count_edit.setEnabled(state == Qt.Checked))
        # Set label color grey when unchecked, black when checked
        def update_mp3_checkbox_style(state):
            if state == Qt.Checked:
                self.mp3_count_checkbox.setStyleSheet("")  # Default
                self.mp3_count_edit.setStyleSheet("")  # Default
            else:
                self.mp3_count_checkbox.setStyleSheet("color: grey;")
                self.mp3_count_edit.setStyleSheet("background-color: #f2f2f2; color: #888;")  # Lighter grey for textbox
        self.mp3_count_checkbox.stateChanged.connect(update_mp3_checkbox_style)
        # Initialize style
        update_mp3_checkbox_style(self.mp3_count_checkbox.checkState())
        self.part1_edit.textChanged.connect(self.update_output_name)
        self.part2_edit.textChanged.connect(self.update_output_name)
        self.folder_edit.textChanged.connect(self.update_output_name)
        part_layout.addSpacing(20)
        part_layout.addWidget(self.name_list_checkbox)
        part_layout.addSpacing(-50)
        part_layout.addWidget(self.name_list_enter_btn)
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
        self.intro_checkbox.setFixedWidth(65)
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
            self.intro_path = self.intro_edit.text().strip()
        self.intro_edit.textChanged.connect(on_intro_changed)
        intro_btn = QPushButton("Select")
        intro_btn.setFixedWidth(60)
        def select_intro_image():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Intro Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.intro_edit.setText(file_path)
        intro_btn.clicked.connect(select_intro_image)
        intro_size_label = QLabel("S:")
        intro_size_label.setFixedWidth(18)
        self.intro_size_combo = QtWidgets.QComboBox()
        self.intro_size_combo.setFixedWidth(90)
        for percent in range(5, 101, 5):
            self.intro_size_combo.addItem(str(percent), percent)
        self.intro_size_combo.setCurrentIndex(1)  # Default 10%
        self.intro_size_percent = 10
        def on_intro_size_changed(idx):
            self.intro_size_percent = self.intro_size_combo.itemData(idx)
            if idx >= 0:
                self.intro_size_combo.setEditText(f"{self.intro_size_percent}%")
        self.intro_size_combo.setEditable(True)
        self.intro_size_combo.lineEdit().setReadOnly(True)
        self.intro_size_combo.lineEdit().setAlignment(Qt.AlignCenter)
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
            enabled = state == Qt.Checked
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
                self.intro_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.intro_size_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.intro_position_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.intro_effect_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                intro_duration_label.setStyleSheet("color: grey;")
                self.intro_duration_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                intro_size_label.setStyleSheet("color: grey;")
                intro_position_label.setStyleSheet("color: grey;")
                intro_effect_label.setStyleSheet("color: grey;")
        self.intro_checkbox.stateChanged.connect(set_intro_enabled)
        set_intro_enabled(self.intro_checkbox.checkState())

        intro_layout = QHBoxLayout()
        intro_layout.setSpacing(4)
        intro_layout.addWidget(self.intro_checkbox)
        intro_layout.addSpacing(10)
        intro_layout.addWidget(self.intro_edit)
        intro_layout.addSpacing(6)
        intro_layout.addWidget(intro_btn)
        intro_layout.addSpacing(0)
        intro_layout.addWidget(intro_position_label)
        intro_layout.addWidget(self.intro_position_combo)
        intro_layout.addSpacing(6)
        intro_layout.addWidget(intro_size_label)
        intro_layout.addWidget(self.intro_size_combo)
        layout.addLayout(intro_layout)

        # Move PNG overlay checkbox below video settings
        self.overlay_checkbox = QtWidgets.QCheckBox("Overlay 1:")
        self.overlay_checkbox.setFixedWidth(80)
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
            self.overlay1_size_combo.addItem(str(percent), percent)
        self.overlay1_size_combo.setCurrentIndex(1)  # Default 10%
        self.overlay1_size_percent = 10
        def on_overlay1_size_changed(idx):
            self.overlay1_size_percent = self.overlay1_size_combo.itemData(idx)
            # Set display text with %
            if idx >= 0:
                self.overlay1_size_combo.setEditText(f"{self.overlay1_size_percent}%")
        self.overlay1_size_combo.setEditable(True)
        self.overlay1_size_combo.lineEdit().setReadOnly(True)
        self.overlay1_size_combo.lineEdit().setAlignment(Qt.AlignCenter)
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
        self.overlay1_position_combo.setCurrentIndex(0)  # Default Center
        self.overlay1_position = "center"
        def on_overlay1_position_changed(idx):
            self.overlay1_position = self.overlay1_position_combo.itemData(idx)
        self.overlay1_position_combo.currentIndexChanged.connect(on_overlay1_position_changed)
        on_overlay1_position_changed(self.overlay1_position_combo.currentIndex())
        # Enable/disable overlay1_edit, overlay1_btn, and overlay1_size_combo based on checkbox
        def set_overlay1_enabled(state):
            enabled = state == Qt.Checked
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
        self.overlay_checkbox.stateChanged.connect(set_overlay1_enabled)
        set_overlay1_enabled(self.overlay_checkbox.checkState())
        overlay1_layout.addWidget(self.overlay_checkbox)
        overlay1_layout.addWidget(self.overlay1_edit)
        overlay1_layout.addSpacing(6)  # Space before select button
        overlay1_layout.addWidget(overlay1_btn)
        overlay1_layout.addSpacing(6)  # Space before position label
        overlay1_layout.addWidget(overlay1_position_label)
        overlay1_layout.addWidget(self.overlay1_position_combo)
        overlay1_layout.addSpacing(6) 
        overlay1_layout.addWidget(overlay1_size_label)
        overlay1_layout.addWidget(self.overlay1_size_combo)
        layout.addLayout(overlay1_layout)

        # Overlay 2 controls (similar to Overlay 1)
        self.overlay2_checkbox = QtWidgets.QCheckBox("Overlay 2:")
        self.overlay2_checkbox.setFixedWidth(80)
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
            self.overlay2_size_combo.addItem(str(percent), percent)
        self.overlay2_size_combo.setCurrentIndex(1)  # Default 10%
        self.overlay2_size_percent = 10
        def on_overlay2_size_changed(idx):
            self.overlay2_size_percent = self.overlay2_size_combo.itemData(idx)
            # Set display text with %
            if idx >= 0:
                self.overlay2_size_combo.setEditText(f"{self.overlay2_size_percent}%")
        self.overlay2_size_combo.setEditable(True)
        self.overlay2_size_combo.lineEdit().setReadOnly(True)
        self.overlay2_size_combo.lineEdit().setAlignment(Qt.AlignCenter)
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
        self.overlay2_position_combo.setCurrentIndex(0)  # Default Center
        self.overlay2_position = "center"
        def on_overlay2_position_changed(idx):
            self.overlay2_position = self.overlay2_position_combo.itemData(idx)
        self.overlay2_position_combo.currentIndexChanged.connect(on_overlay2_position_changed)
        on_overlay2_position_changed(self.overlay2_position_combo.currentIndex())
        def set_overlay2_enabled(state):
            enabled = state == Qt.Checked
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
                self.overlay2_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.overlay2_size_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                self.overlay2_position_combo.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
                overlay2_size_label.setStyleSheet("color: grey;")
                overlay2_position_label.setStyleSheet("color: grey;")
        self.overlay2_checkbox.stateChanged.connect(set_overlay2_enabled)
        set_overlay2_enabled(self.overlay2_checkbox.checkState())
        overlay2_layout.addWidget(self.overlay2_checkbox)
        overlay2_layout.addWidget(self.overlay2_edit)
        overlay2_layout.addSpacing(6)
        overlay2_layout.addWidget(overlay2_btn)
        overlay2_layout.addSpacing(6)
        overlay2_layout.addWidget(overlay2_position_label)
        overlay2_layout.addWidget(self.overlay2_position_combo)
        overlay2_layout.addSpacing(6)
        overlay2_layout.addWidget(overlay2_size_label)
        overlay2_layout.addWidget(self.overlay2_size_combo)
        layout.addLayout(overlay2_layout)

        # --- EFFECT CONTROL FOR INTRO & OVERLAY ---
        
        combo_width = 130
        edit_width = 50

        effect_label = QLabel("Overlay:")
        effect_label.setFixedWidth(55)
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
        effect_layout.addSpacing(20)
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
        # Add extra vertical spacing before the action buttons
        layout.addSpacing(6)

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
        self.progress_bar.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
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
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close_window)

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
        desktop = QDesktopWidget()
        screen_geometry = desktop.screenGeometry(self)
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
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
                QMessageBox.warning(self, "⚠️ Intro Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Intro.", QMessageBox.Ok)
                return
        # Overlay 1 validation
        if self.overlay_checkbox.isChecked():
            overlay_path = self.overlay1_edit.text().strip()
            if not overlay_path or not os.path.isfile(overlay_path) or os.path.splitext(overlay_path)[1].lower() not in ['.gif', '.png']:
                QMessageBox.warning(self, "⚠️ Overlay Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Overlay 1.", QMessageBox.Ok)
                return
        # Overlay 2 validation
        if self.overlay2_checkbox.isChecked():
            overlay2_path = self.overlay2_edit.text().strip()
            if not overlay2_path or not os.path.isfile(overlay2_path) or os.path.splitext(overlay2_path)[1].lower() not in ['.gif', '.png']:
                QMessageBox.warning(self, "⚠️ Overlay 2 Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Overlay 2.", QMessageBox.Ok)
                return
        # --- Name list validation ---
        use_name_list = hasattr(self, 'name_list_checkbox') and self.name_list_checkbox.isChecked()
        if use_name_list:
            if not self.name_list:
                QMessageBox.warning(self, "⚠️ Name List Required", "Please enter a name list (one name per line) before processing.", QMessageBox.Ok)
                return
        inputs = self._gather_and_validate_inputs()
        if not inputs:
            return
        media_sources, export_name, number, folder, codec, resolution, fps, original_mp3_files, original_image_files, min_mp3_count = inputs
        # Calculate total batches
        total_batches = min(len(original_image_files), len(original_mp3_files) // min_mp3_count)
        if use_name_list:
            if len(self.name_list) < total_batches:
                QMessageBox.critical(self, "❌ Not Enough Names", f"You provided {len(self.name_list)} names, but {total_batches} are required for all video batches.", QMessageBox.Ok)
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
            QMessageBox.warning(self, "⚠️ Missing Output Folder", "Please select or enter an output folder.", QMessageBox.Ok)
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
                QMessageBox.warning(self, "⚠️ Missing Input", error_msg, QMessageBox.Ok)
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
            if processing:
                self.loading_label.movie().start()
            else:
                self.loading_label.movie().stop()
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
        self._worker = VideoWorker(
            media_sources, export_name, number, folder, codec, resolution, fps,
            self.overlay_checkbox.isChecked(), min_mp3_count, self.overlay1_path, self.overlay1_size_percent, self.overlay1_position,
            self.overlay2_checkbox.isChecked(), self.overlay2_path, self.overlay2_size_percent, self.overlay2_position,
            self.intro_checkbox.isChecked(), self.intro_path, self.intro_size_percent, self.intro_position,
            self.selected_effect, self.overlay_duration,
            self.intro_effect, self.intro_duration,
            name_list=name_list
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_worker_progress)
        self._worker.error.connect(self.on_worker_error)
        self._worker.finished.connect(
            lambda leftover_mp3s, used_images, failed_moves: self.on_worker_finished_with_leftovers(
                leftover_mp3s, used_images, original_mp3_files, original_image_files, failed_moves
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
            self.loading_label.movie().stop()
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
        dlg.exec_()
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

    def on_worker_finished_with_leftovers(self, leftover_mp3s, used_images, original_mp3_files, original_image_files, failed_moves=None):
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
            dlg.exec_()
        else:
            if leftover_mp3s or leftover_images:
                self.show_success_options(leftover_files=leftover_mp3s, leftover_images=leftover_images, min_mp3_count=min_mp3_count)
            else:
                self.show_success_options(min_mp3_count=min_mp3_count)
        # Show warning if any files failed to move
        if failed_moves:
            QMessageBox.warning(self, "Warning: File Move Failed", f"Some files could not be moved to the bin folder:\n\n" + '\n'.join(failed_moves))
        self.clear_inputs()
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
        dlg.exec_()

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
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Show waiting dialog
                waiting_dialog = QMessageBox(self)
                waiting_dialog.setWindowTitle("Please Wait")
                waiting_dialog.setText("Waiting for current batch to finish...")
                waiting_dialog.setStandardButtons(QMessageBox.NoButton)
                waiting_dialog.show()
                
                # Request stop
                if hasattr(self, "_worker") and self._worker is not None:
                    stop_method = getattr(self._worker, 'stop', None)
                    if callable(stop_method):
                        try:
                            stop_method()
                        except RuntimeError:
                            pass
                            
                # Wait for thread to finish in a background thread, then close app after 3s
                def wait_and_close():
                    if self._thread is not None:
                        self._thread.wait()
                    time.sleep(3)
                    waiting_dialog.close()
                    app_instance = QApplication.instance()
                    if app_instance is not None:
                        app_instance.quit()
                        
                threading.Thread(target=wait_and_close, daemon=True).start()
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
        if dlg.exec_() == QDialog.Accepted:
            self.apply_settings()

    def apply_settings(self):
        # Update FPS combo to reflect new default if not set by user yet
        default_fps = self.settings.value('default_fps', type=int)
        if default_fps is not None:
            idx = next((i for i, (label, value) in enumerate(DEFAULT_FPS_OPTIONS) if value == default_fps), 0)
            self.fps_combo.setCurrentIndex(idx)
        # Apply default intro settings if intro is checked and fields are empty
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
        if self.overlay2_checkbox.isChecked():
            if not self.overlay2_edit.text().strip():
                self.overlay2_edit.setText(default_overlay2_path)
            idx = next((i for i in range(self.overlay2_position_combo.count()) if self.overlay2_position_combo.itemData(i) == default_overlay2_position), 2)
            self.overlay2_position_combo.setCurrentIndex(idx)
            idx = next((i for i in range(self.overlay2_size_combo.count()) if self.overlay2_size_combo.itemData(i) == default_overlay2_size), 2)
            self.overlay2_size_combo.setCurrentIndex(idx)

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

def main():
    """Main application entry point"""
    # Ensure console output is visible
    print("Starting SuperCut Video Maker...")
    print("Console output will be visible here during video processing.")
    
    app = QApplication(sys.argv)
    app.setApplicationName("SuperCut")
    app.setApplicationVersion("1.0")
    
    # Check FFmpeg installation
    ffmpeg_ok, error_msg = check_ffmpeg_installation()
    if not ffmpeg_ok:
        print(f"Warning: FFmpeg not found. {error_msg or 'The application will attempt to extract it on first use.'}")
    
    window = SuperCutUI()
    window.show()
    
    print("Application started successfully!")
    print("You can now use the GUI to create videos.")
    print("Console output will show during video processing...")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()