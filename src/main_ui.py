# This file uses PyQt6
import os
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QDialog, QComboBox, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, QSettings, QThread, QPoint, QSize
from PyQt6.QtGui import QIntValidator, QIcon, QPixmap, QMovie, QImage, QShortcut, QKeySequence
from src.logger import logger
from src.worker_manager import setup_worker_and_thread, stop_video_creation, cleanup_worker_and_thread
from src.settings_manager import show_settings_dialog, apply_settings
from src.overlay_manager import create_intro_overlay_controls
from src.terminal_manager import show_terminal, position_terminal_widget
from src.progress_manager import create_progress_controls
from .input_manager import on_media_folder_changed, on_output_folder_changed
from .window_manager import restore_window_position, setup_shortcuts, close_window, closeEvent, moveEvent
from .ui_builder import create_folder_inputs, create_export_inputs
from .action_buttons import create_action_buttons
from .success_manager import show_success_options
from .leftover_manager import cleanup_leftovers
from .settings_dialog_manager import show_settings_dialog_ui, apply_settings_ui
from .input_clear_manager import clear_inputs
from .result_folder_manager import open_result_folder

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
    validate_inputs, validate_media_files,
    select_media_sources_folder, select_output_folder, update_output_name, gather_and_validate_inputs
)
from src.ui_components import (
    FolderDropLineEdit, WaitingDialog, PleaseWaitDialog, StoppedDialog, SuccessDialog, ScrollableErrorDialog, ImageDropLineEdit,
    SettingsDialog, NameListDialog
)
from src.video_worker import VideoWorker
from src.terminal_widget import TerminalWidget

import time
import threading

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
        
        # Bind input manager methods
        self.on_media_folder_changed = on_media_folder_changed.__get__(self)
        self.on_output_folder_changed = on_output_folder_changed.__get__(self)
        self.clear_inputs = clear_inputs.__get__(self)

        # Bind window manager methods
        self.restore_window_position = restore_window_position.__get__(self)
        self.setup_shortcuts = setup_shortcuts.__get__(self)
        self.close_window = close_window.__get__(self)

        # Bind success manager methods
        self.show_success_options = show_success_options.__get__(self)

        # Bind cleanup leftovers method
        self.cleanup_leftovers = cleanup_leftovers.__get__(self)

        # Bind settings dialog methods
        self.show_settings_dialog = show_settings_dialog_ui.__get__(self)
        self.apply_settings = apply_settings_ui.__get__(self)

        # Call bound methods after binding
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
        layout.addSpacing(0)
        # --- End program title ---

        # Add UI components
        create_folder_inputs(self, layout, FolderDropLineEdit, PROJECT_ROOT)
        create_export_inputs(self, layout, DEFAULT_EXPORT_NAME, DEFAULT_START_NUMBER, DEFAULT_MIN_MP3_COUNT, QIntValidator, NameListDialog)
        self.create_video_settings(layout)
        create_action_buttons(self, layout, PROJECT_ROOT)
        # Use progress_manager for progress bar and stop button
        progress_controls = create_progress_controls(self)
        self.stop_btn = progress_controls['stop_btn']
        self.progress_bar = progress_controls['progress_bar']
        layout.addLayout(progress_controls['progress_row'])
        
        self.setLayout(layout)
        self.update_output_name()
        # Apply intro defaults on startup
        self.apply_settings()
        # Connect text change for media_sources_edit and folder_edit
        self.media_sources_edit.textChanged.connect(self.on_media_folder_changed)
        self.folder_edit.textChanged.connect(self.update_output_name)
        self.folder_edit.textChanged.connect(self.on_output_folder_changed)

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

        # --- Intro and Overlay controls (moved to overlay_manager) ---
        overlay_controls = create_intro_overlay_controls(self)
        # Assign all returned widgets to self for later use
        for key, widget in overlay_controls.items():
            setattr(self, key, widget)
        # Connect overlay1 default button to set_overlay1_defaults
        if hasattr(self, 'overlay1_default_button'):
            from src.settings_manager import set_overlay1_defaults
            self.overlay1_default_button.clicked.connect(lambda: set_overlay1_defaults(self))
        # Add layouts to main layout if present
        if 'intro_layout' in overlay_controls:
            layout.addLayout(overlay_controls['intro_layout'])
        if 'overlay1_layout' in overlay_controls:
            layout.addLayout(overlay_controls['overlay1_layout'])
        if 'overlay2_layout' in overlay_controls:
            layout.addLayout(overlay_controls['overlay2_layout'])
        if 'effect_layout' in overlay_controls:
            layout.addLayout(overlay_controls['effect_layout'])
        if 'spacing' in overlay_controls:
            layout.addSpacing(overlay_controls['spacing'])

    def show_terminal(self):
        show_terminal(self)

    def position_terminal_widget(self):
        position_terminal_widget(self)

    def select_media_sources_folder(self):
        """Select media sources folder (now uses utils)"""
        select_media_sources_folder(
            self,
            self.media_sources_edit,
            self.folder_edit,
            self.output_folder_manual,
            self.update_output_name
        )

    def select_output_folder(self):
        """Select output folder (now uses utils)"""
        def set_manual(val):
            self.output_folder_manual = val
        select_output_folder(
            self,
            self.folder_edit,
            self.update_output_name,
            set_manual
        )

    def update_output_name(self):
        """Update the output filename based on current inputs (now uses utils)"""
        def set_output_path(path):
            self.output_path = path
        update_output_name(
            self.name_list_checkbox,
            self.name_list,
            self.part1_edit,
            self.part2_edit,
            self.folder_edit,
            set_output_path
        )

    def _gather_and_validate_inputs(self):
        """Gather and validate user inputs. Return tuple or None if invalid. (now uses utils)"""
        return gather_and_validate_inputs(
            self,
            self.media_sources_edit,
            self.name_list_checkbox,
            self.name_list,
            self.part1_edit,
            self.part2_edit,
            self.folder_edit,
            self.codec_combo,
            self.resolution_combo,
            self.fps_combo,
            self.mp3_count_checkbox,
            self.mp3_count_edit,
            DEFAULT_MIN_MP3_COUNT
        )
        return None

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

    def _setup_worker_and_thread(self, *args, **kwargs):
        setup_worker_and_thread(self, *args, **kwargs)

    def stop_video_creation(self):
        stop_video_creation(self)

    def cleanup_worker_and_thread(self):
        cleanup_worker_and_thread(self)

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
            dlg.exec()
        else:
            if leftover_mp3s or leftover_images:
                self.show_success_options(leftover_files=leftover_mp3s, leftover_images=leftover_images, min_mp3_count=min_mp3_count)
            else:
                self.show_success_options(min_mp3_count=min_mp3_count)
        # Show warning if any files failed to move
        if failed_moves:
            QMessageBox.warning(self, "Warning: File Move Failed", f"Some files could not be moved to the bin folder:\n\n" + '\n'.join(failed_moves))
        # Clear inputs using imported function
        clear_inputs(self)
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
                # Show waiting dialog
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
        show_settings_dialog(self, DEFAULT_FPS_OPTIONS)

    def apply_settings(self):
        apply_settings(self, DEFAULT_FPS_OPTIONS)