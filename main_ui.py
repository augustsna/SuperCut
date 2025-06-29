import os
import sys
import threading
import time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings, QThread
from PyQt5.QtGui import QIntValidator, QIcon

from config import (
    WINDOW_SIZE, WINDOW_TITLE, ICON_PATH, STYLE_SHEET,
    DEFAULT_CODECS, DEFAULT_RESOLUTIONS, DEFAULT_FPS_OPTIONS,
    DEFAULT_EXPORT_NAME, DEFAULT_START_NUMBER, DEFAULT_FPS,
    DEFAULT_RESOLUTION, DEFAULT_CODEC, check_ffmpeg_installation
)
from utils import (
    sanitize_filename, get_desktop_folder, open_folder_in_explorer,
    validate_inputs, validate_media_files
)
from ui_components import (
    FolderDropLineEdit, WaitingDialog, PleaseWaitDialog, 
    StoppedDialog, SuccessDialog
)
from video_worker import VideoWorker

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
        
        self.init_ui()
        self.restore_window_position()
        self.setup_shortcuts()

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
        
        folder_layout.addWidget(label_output)
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)

    def create_export_inputs(self, layout):
        """Create export name and number inputs"""
        part_layout = QHBoxLayout()
        
        self.part1_edit = QLineEdit(DEFAULT_EXPORT_NAME)
        self.part1_edit.setPlaceholderText("Export Name")
        
        self.part2_edit = QLineEdit(DEFAULT_START_NUMBER)
        self.part2_edit.setPlaceholderText("12345")
        self.part2_edit.setValidator(QIntValidator(1, 9999999, self))
        
        self.part1_edit.textChanged.connect(self.update_output_name)
        self.part2_edit.textChanged.connect(self.update_output_name)
        
        part_layout.addWidget(QLabel("Export name:"))
        part_layout.addWidget(self.part1_edit)
        part_layout.addWidget(QLabel("Number:"))
        part_layout.addWidget(self.part2_edit)
        layout.addLayout(part_layout)

    def create_video_settings(self, layout):
        """Create video settings controls"""
        # Codec selection
        codec_layout = QHBoxLayout()
        codec_label = QLabel("Video Codec:")
        codec_label.setFixedWidth(90)
        
        self.codec_combo = QtWidgets.QComboBox()
        self.codec_combo.setFixedWidth(140)
        self.codec_combo.setMinimumHeight(28)
        self.codec_combo.setMaximumHeight(28)
        
        for label, value in DEFAULT_CODECS:
            self.codec_combo.addItem(label, value)
        self.codec_combo.setCurrentIndex(0)
        
        codec_layout.addWidget(codec_label)
        codec_layout.addWidget(self.codec_combo)
        codec_layout.addStretch()
        layout.addLayout(codec_layout)

        # Video resolution selection
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Video Size:")
        resolution_label.setFixedWidth(90)
        
        self.resolution_combo = QtWidgets.QComboBox()
        self.resolution_combo.setFixedWidth(140)
        self.resolution_combo.setMinimumHeight(28)
        self.resolution_combo.setMaximumHeight(28)
        
        for label, value in DEFAULT_RESOLUTIONS:
            self.resolution_combo.addItem(label, value)
        self.resolution_combo.setCurrentIndex(0)
        
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addStretch()
        layout.addLayout(resolution_layout)

        # FPS selection
        fps_layout = QHBoxLayout()
        fps_label = QLabel("FPS:")
        fps_label.setFixedWidth(90)
        
        self.fps_combo = QtWidgets.QComboBox()
        self.fps_combo.setFixedWidth(140)
        self.fps_combo.setMinimumHeight(28)
        self.fps_combo.setMaximumHeight(28)
        
        for label, value in DEFAULT_FPS_OPTIONS:
            self.fps_combo.addItem(label, value)
        self.fps_combo.setCurrentIndex(0)
        
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_combo)
        fps_layout.addStretch()
        layout.addLayout(fps_layout)

    def create_action_buttons(self, layout):
        """Create action buttons"""
        self.create_btn = QPushButton("🚀 Create Video")
        self.create_btn.setFixedHeight(35)
        self.create_btn.clicked.connect(self.create_video)
        layout.addWidget(self.create_btn)

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
        if pos:
            self.move(pos)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)

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
        # Get input values
        media_sources = self.media_sources_edit.text()
        export_name = self.part1_edit.text().strip()
        number = self.part2_edit.text().strip()
        
        # Default to 1 if blank or zero
        if not number or number == '0':
            number = '1'
        
        # Sanitize export name
        export_name = sanitize_filename(export_name)
        
        folder = self.folder_edit.text().strip() or os.getcwd()
        codec = self.codec_combo.currentData()
        resolution = self.resolution_combo.currentData()
        fps = self.fps_combo.currentData()

        # Validate inputs
        is_valid, error_msg = validate_inputs(media_sources, export_name, number)
        if not is_valid:
            QMessageBox.warning(self, "⚠️ Missing Input", error_msg, QMessageBox.Ok)
            return

        # Validate media files
        is_valid, error_msg, mp3_files, image_files = validate_media_files(media_sources)
        if not is_valid:
            QMessageBox.critical(self, "❌ Error", error_msg)
            return

        # Calculate total batches
        total_batches = min(len(image_files), len(mp3_files) // 3)
        self.progress_bar.setMaximum(total_batches)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"Batch: 0/{total_batches}")
        self.progress_bar.setVisible(True)

        # Track original files for leftovers
        original_mp3_files = set(mp3_files)
        original_image_files = set(image_files)

        # Show waiting dialog
        self.waiting_dialog = WaitingDialog(self)
        self.waiting_dialog.show()
        QtWidgets.QApplication.processEvents()
        
        # Enable stop button
        self.stop_btn.setEnabled(True)
        self.stop_btn.setVisible(True)
        self.create_btn.setEnabled(False)

        # Set up worker and thread
        self._thread = QThread()
        self._worker = VideoWorker(media_sources, export_name, number, folder, codec, resolution, fps)
        self._worker.moveToThread(self._thread)
        
        # Connect signals
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_worker_progress)
        self._worker.error.connect(self.on_worker_error)
        self._worker.finished.connect(
            lambda leftover_mp3s: self.on_worker_finished_with_leftovers(
                leftover_mp3s, original_mp3_files, original_image_files
            )
        )
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        
        # Start processing
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
        self.waiting_dialog.close()
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        self.create_btn.setEnabled(True)
        QMessageBox.critical(self, "❌ Error", message)
        self._worker = None
        self._thread = None
        
        if hasattr(self, '_auto_close_on_stop') and self._auto_close_on_stop:
            self._auto_close_on_stop = False
            if hasattr(self, '_stopping_msgbox') and self._stopping_msgbox is not None:
                self._stopping_msgbox.close()
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
        
        if hasattr(self, "waiting_dialog") and self.waiting_dialog is not None:
            self.waiting_dialog.close()
            
        self.progress_bar.setVisible(False)
        self.create_btn.setEnabled(True)
        self._auto_close_on_stop = False
        self._stopped_by_user = True

    def on_worker_finished_with_leftovers(self, leftover_mp3s, original_mp3_files, original_image_files):
        """Handle worker completion with leftover files"""
        self.progress_bar.setVisible(False)
        self.waiting_dialog.close()
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        self.create_btn.setEnabled(True)
        
        # Calculate leftover images
        used_mp3s = set(original_mp3_files) - set(leftover_mp3s)
        used_images = set()
        folder = self.media_sources_edit.text().strip()
        for img in original_image_files:
            if not os.path.exists(os.path.join(folder, img)):
                used_images.add(img)
        leftover_images = list(original_image_files - used_images)
        
        # Show appropriate dialog
        if hasattr(self, '_stopped_by_user') and self._stopped_by_user:
            self._stopped_by_user = False  # reset for next run

            # Close PleaseWaitDialog if open
            if hasattr(self, '_stopping_msgbox') and self._stopping_msgbox is not None:
                self._stopping_msgbox.close()
                self._stopping_msgbox = None

            batch_count = self.progress_bar.value() if hasattr(self, 'progress_bar') else 0
            total_batches = self.progress_bar.maximum() if hasattr(self, 'progress_bar') else 0
            dlg = StoppedDialog(self, batch_count=batch_count, total_batches=total_batches)
            dlg.exec_()
        else:
            if leftover_mp3s or leftover_images:
                self.show_success_options(leftover_files=leftover_mp3s, leftover_images=leftover_images)
            else:
                self.show_success_options()
                
        self.clear_inputs()
        self._worker = None
        self._thread = None
        
        if hasattr(self, '_auto_close_on_stop') and self._auto_close_on_stop:
            self._auto_close_on_stop = False
            if hasattr(self, '_stopping_msgbox') and self._stopping_msgbox is not None:
                self._stopping_msgbox.close()
                self._stopping_msgbox = None

    def show_success_options(self, leftover_files=None, leftover_images=None):
        """Show success dialog with options"""
        # Play notification sound
        try:
            if sys.platform.startswith('win'):
                QtWidgets.QApplication.beep()
            else:
                QtWidgets.QApplication.beep()
        except Exception:
            pass
            
        dlg = SuccessDialog(
            self, 
            open_folder=self.open_result_folder, 
            leftover_files=leftover_files, 
            leftover_images=leftover_images
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