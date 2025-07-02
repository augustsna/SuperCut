import os
import sys
import threading
import time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDesktopWidget
)
from PyQt5.QtCore import Qt, QSettings, QThread, QPoint
from PyQt5.QtGui import QIntValidator, QIcon
from logger import logger

# Force console output to be visible
sys.stdout.flush()
sys.stderr.flush()

from config import (
    WINDOW_SIZE, WINDOW_TITLE, ICON_PATH, STYLE_SHEET,
    DEFAULT_CODECS, DEFAULT_RESOLUTIONS, DEFAULT_FPS_OPTIONS,
    DEFAULT_EXPORT_NAME, DEFAULT_START_NUMBER, DEFAULT_FPS,
    DEFAULT_RESOLUTION, DEFAULT_CODEC, check_ffmpeg_installation,
    DEFAULT_MIN_MP3_COUNT
)
from utils import (
    sanitize_filename, get_desktop_folder, open_folder_in_explorer,
    validate_inputs, validate_media_files
)
from ui_components import FolderDropLineEdit, WaitingDialog, PleaseWaitDialog, StoppedDialog, SuccessDialog, ScrollableErrorDialog, ImageDropLineEdit
from video_worker import VideoWorker
from terminal_widget import TerminalWidget

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
        
        # Add UI components
        self.create_folder_inputs(layout)
        self.create_export_inputs(layout)
        self.create_video_settings(layout)
        self.create_action_buttons(layout)
        self.create_progress_controls(layout)
        
        self.setLayout(layout)
        self.update_output_name()
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
        label_output.setFixedWidth(folder_row_style["label_width"])
        
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
        self.part2_edit = QLineEdit(DEFAULT_START_NUMBER)
        self.part2_edit.setPlaceholderText("12345")
        self.part2_edit.setValidator(QIntValidator(1, 9999999, self))
        self.mp3_count_checkbox = QtWidgets.QCheckBox("MP3 Per Video")
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
        part_layout.addWidget(QLabel("Export Name:"))
        part_layout.addWidget(self.part1_edit)
        part_layout.addWidget(QLabel("Number:"))
        part_layout.addWidget(self.part2_edit)
        part_layout.addWidget(self.mp3_count_checkbox)
        part_layout.addWidget(self.mp3_count_edit)
        layout.addLayout(part_layout)

    def create_video_settings(self, layout):
        """Create video settings controls"""
        # Combined layout for codec, resolution, and fps
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(0)  # We'll add custom spacing

        # Codec selection
        codec_label = QLabel("Codec:")
        codec_label.setFixedWidth(50)
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
        self.fps_combo.setFixedWidth(100)
        self.fps_combo.setMinimumHeight(28)
        self.fps_combo.setMaximumHeight(28)
        for label, value in DEFAULT_FPS_OPTIONS:
            self.fps_combo.addItem(label, value)
        # Restore last used FPS from settings if available
        last_fps = self.settings.value('last_fps', type=int)
        if last_fps is not None:
            fps_index = next((i for i, (label, value) in enumerate(DEFAULT_FPS_OPTIONS) if value == last_fps), 0)
            self.fps_combo.setCurrentIndex(fps_index)
        else:
            default_fps_index = next((i for i, (label, value) in enumerate(DEFAULT_FPS_OPTIONS) if value == 24), 0)
            self.fps_combo.setCurrentIndex(default_fps_index)
        self.fps_combo.currentIndexChanged.connect(self.save_fps_setting)
        settings_layout.addWidget(fps_label)
        settings_layout.addSpacing(6)
        settings_layout.addWidget(self.fps_combo)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        # Move PNG overlay checkbox below video settings
        self.overlay_checkbox = QtWidgets.QCheckBox("Overlay 1")
        self.overlay_checkbox.setChecked(False)
        # Set label color grey when unchecked, black when checked
        def update_overlay_checkbox_style(state):
            if state == Qt.Checked:
                self.overlay_checkbox.setStyleSheet("")  # Default
            else:
                self.overlay_checkbox.setStyleSheet("color: grey;")
        self.overlay_checkbox.stateChanged.connect(update_overlay_checkbox_style)
        # Initialize style
        update_overlay_checkbox_style(self.overlay_checkbox.checkState())

        # Overlay 1 image input (text, drag & drop, select button)
        overlay1_layout = QHBoxLayout()
        self.overlay1_edit = ImageDropLineEdit()
        self.overlay1_edit.setPlaceholderText("Overlay 1 image path (*.gif, *.png)")
        self.overlay1_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
        self.overlay1_path = ""
        def on_overlay1_changed():
            self.overlay1_path = self.overlay1_edit.text().strip()
        self.overlay1_edit.textChanged.connect(on_overlay1_changed)
        overlay1_btn = QPushButton("Select Image")
        overlay1_btn.setFixedWidth(110)
        def select_overlay1_image():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Overlay 1 Image", "", "Image Files (*.gif *.png)")
            if file_path:
                self.overlay1_edit.setText(file_path)
        overlay1_btn.clicked.connect(select_overlay1_image)
        # Enable/disable overlay1_edit and overlay1_btn based on checkbox
        def set_overlay1_enabled(state):
            enabled = state == Qt.Checked
            self.overlay1_edit.setEnabled(enabled)
            overlay1_btn.setEnabled(enabled)
            if enabled:
                overlay1_btn.setStyleSheet("")  # Default style
                self.overlay1_edit.setStyleSheet("")  # Default style
            else:
                overlay1_btn.setStyleSheet("background-color: #e0e0e0; color: #888;")  # Lighter grey
                self.overlay1_edit.setStyleSheet("background-color: #f2f2f2; color: #888;")  # Lighter grey for textbox
        self.overlay_checkbox.stateChanged.connect(set_overlay1_enabled)
        # Initialize enabled state on startup
        set_overlay1_enabled(self.overlay_checkbox.checkState())
        overlay1_layout.addWidget(self.overlay_checkbox)
        overlay1_layout.addWidget(self.overlay1_edit)
        overlay1_layout.addWidget(overlay1_btn)
        layout.addLayout(overlay1_layout)

    def create_action_buttons(self, layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()

        # Add terminal button first, fixed to the left
        self.terminal_btn = QPushButton("💻 Terminal")
        self.terminal_btn.setFixedHeight(35)
        self.terminal_btn.setFixedWidth(100)
        self.terminal_btn.clicked.connect(self.show_terminal)
        button_layout.addWidget(self.terminal_btn)

        # Then add create video button, always after terminal
        self.create_btn = QPushButton("🚀 Create Video")
        self.create_btn.setFixedHeight(35)
        self.create_btn.setFixedWidth(380)
        self.create_btn.clicked.connect(self.create_video)
        button_layout.addWidget(self.create_btn)

        button_layout.addStretch()  # Pushes spinner to the far right

        # Add spinner widget (always visible)
        self.running_widget = QtWidgets.QWidget()
        running_layout = QHBoxLayout(self.running_widget)
        running_layout.setContentsMargins(0, 0, 0, 0)
        running_layout.setSpacing(0)
        # Spinner GIF only
        self.spinner_label = QLabel()
        self.spinner_movie = QtGui.QMovie(os.path.join(os.path.dirname(__file__), "sources/spinner.gif"))
        self.spinner_label.setMovie(self.spinner_movie)
        self.spinner_label.setFixedSize(35, 35)
        running_layout.addWidget(self.spinner_label)
        self.running_widget.setFixedHeight(40)
        self.running_widget.setFixedWidth(50)
        self.running_widget.setVisible(True)
        button_layout.addWidget(self.running_widget)

        layout.addLayout(button_layout)

    def create_progress_controls(self, layout):
        """Create progress bar and stop button"""
        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Batch: 0/0")
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Stop button
        self.stop_btn = QPushButton("🛑 Stop")
        self.stop_btn.setFixedHeight(24)
        self.stop_btn.setFixedWidth(70)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.stop_video_creation)
        layout.addWidget(self.stop_btn)

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
        part1 = self.part1_edit.text().strip()
        part2 = self.part2_edit.text().strip()
        folder = self.folder_edit.text().strip() or os.getcwd()
        
        # Default to 1 if blank or zero
        if not part2 or part2 == '0':
            part2 = '1'
        
        # Sanitize export name
        part1 = sanitize_filename(part1)
        
        if part1 and part2:
            filename = f"{part1}_{part2}.mp4"
        else:
            filename = "output.mp4"
            
        self.output_path = os.path.join(folder, filename)

    def create_video(self):
        """Start video creation process"""
        # Step 1: Gather and validate inputs
        # Overlay 1 validation
        if self.overlay_checkbox.isChecked():
            overlay_path = self.overlay1_edit.text().strip()
            if not overlay_path or not os.path.isfile(overlay_path) or os.path.splitext(overlay_path)[1].lower() not in ['.gif', '.png']:
                QMessageBox.warning(self, "⚠️ Overlay Image Required", "Please provide a valid GIF or PNG file (*.gif, *.png) for Overlay 1.", QMessageBox.Ok)
                return
        inputs = self._gather_and_validate_inputs()
        if not inputs:
            return
        media_sources, export_name, number, folder, codec, resolution, fps, original_mp3_files, original_image_files, min_mp3_count = inputs

        # Step 2: Prepare UI for processing
        self._set_ui_processing_state(True, total_batches=min(len(original_image_files), len(original_mp3_files) // min_mp3_count))

        # Step 3: Set up worker and thread
        self._setup_worker_and_thread(media_sources, export_name, number, folder, codec, resolution, fps, original_mp3_files, original_image_files, min_mp3_count)

    def _gather_and_validate_inputs(self):
        """Gather and validate user inputs. Return tuple or None if invalid."""
        media_sources = self.media_sources_edit.text()
        export_name = self.part1_edit.text().strip()
        number = self.part2_edit.text().strip()
        if not number or number == '0':
            number = '1'
        export_name = sanitize_filename(export_name)
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
        is_valid, error_msg = validate_inputs(media_sources, export_name, number)
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
        self.progress_bar.setFormat(f"Batch: 0/{total_batches}")
        self.progress_bar.setVisible(processing)
        self.stop_btn.setEnabled(processing)
        self.stop_btn.setVisible(processing)
        self.running_widget.setVisible(processing)
        if processing:
            self.spinner_movie.start()
        else:
            self.spinner_movie.stop()
        controls = [
            self.create_btn, self.codec_combo, self.resolution_combo, self.fps_combo,
            self.media_sources_edit, self.folder_edit, self.part1_edit, self.part2_edit,
            self.media_sources_select_btn, self.output_folder_select_btn, self.overlay_checkbox
        ]
        for ctrl in controls:
            ctrl.setEnabled(not processing)

    def _setup_worker_and_thread(self, media_sources, export_name, number, folder, codec, resolution, fps, original_mp3_files, original_image_files, min_mp3_count):
        """Set up the VideoWorker and QThread, connect signals, and start processing."""
        self._thread = QThread()
        self._worker = VideoWorker(media_sources, export_name, number, folder, codec, resolution, fps, self.overlay_checkbox.isChecked(), min_mp3_count, self.overlay1_path)
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
        self.progress_bar.setMaximum(total_batches)
        self.progress_bar.setValue(batch_count)
        self.progress_bar.setFormat(f"Batch: {batch_count}/{total_batches}")
        QtWidgets.QApplication.processEvents()

    def on_worker_error(self, message):
        """Handle worker errors"""
        self.progress_bar.setVisible(False)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        self.running_widget.setVisible(False)
        self.spinner_movie.stop()
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
        self.progress_bar.setVisible(False)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        self.running_widget.setVisible(False)
        self.spinner_movie.stop()
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
        # Save FPS setting on close
        if hasattr(self, 'fps_combo'):
            self.save_fps_setting()
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

    def save_fps_setting(self):
        """Save the currently selected FPS to settings"""
        fps = self.fps_combo.currentData()
        self.settings.setValue('last_fps', fps)

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