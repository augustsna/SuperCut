import os
import sys
import random
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QApplication, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QDialog, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings, QObject, QThread, pyqtSignal
from moviepy import AudioFileClip, ImageClip, concatenate_audioclips
import subprocess
import shutil
from PyQt5.QtGui import QIntValidator, QIcon, QMovie
import tempfile
import ctypes
import re

# Set FFMPEG paths (use local ffmpeg folder)
os.environ["FFMPEG_BINARY"] = os.path.abspath("C:/SuperCut/ffmpeg/bin/ffmpeg.exe")
os.environ["FFPLAY_BINARY"] = os.path.abspath("C:/SuperCut/ffmpeg/bin/ffplay.exe")

# Check if ffmpeg exists
if not os.path.exists(os.environ["FFMPEG_BINARY"]):
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "FFmpeg Not Found", "Could not find C:/SuperCut/ffmpeg/bin/ffmpeg.exe. Please ensure ffmpeg is present in the ffmpeg folder.")
    sys.exit(1)

def make_video(image_path, audio_path, output_path):
    audio = AudioFileClip(audio_path)
    image = ImageClip(image_path).with_duration(audio.duration).resized(height=720)
    video = image.with_audio(audio)
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    audio.close()
    image.close()

def merge_random_mp3s(selected_mp3s):
    clips = [AudioFileClip(f) for f in selected_mp3s]
    final_clip = concatenate_audioclips(clips)
    # Do NOT close the clips here! Return them for later cleanup.
    return final_clip, clips

class WaitingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Running...")
        self.setModal(True)
        self.setFixedSize(180, 120)
        layout = QVBoxLayout(self)
        self.label = QLabel("Creating video, wait...")
        font = self.label.font()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gif_path = os.path.join(os.path.dirname(__file__), "sources/spinner.gif")
        self.movie = QMovie(gif_path)
        self.spinner.setMovie(self.movie)
        layout.addWidget(self.spinner)
        self.movie.start()

class VideoWorker(QObject):
    progress = pyqtSignal(int, int)  # batch_count, total_batches
    error = pyqtSignal(str)
    finished = pyqtSignal(list)  # leftover_files

    def __init__(self, media_sources, export_name, number, folder):
        super().__init__()
        self.media_sources = media_sources
        self.export_name = export_name
        self.number = number
        self.folder = folder
        self._stop = False  # Add stop flag

    def stop(self):
        self._stop = True

    def run(self):
        set_low_priority()
        try:
            mp3_files = [os.path.join(self.media_sources, f) for f in os.listdir(self.media_sources) if f.lower().endswith('.mp3')]
            image_files = [f for f in os.listdir(self.media_sources) if f.lower().endswith((".jpg", ".png"))]
            if not image_files:
                self.error.emit("No image files found in the media folder.")
                return
            if not mp3_files or len(mp3_files) < 3:
                self.error.emit("Not enough mp3 files in folder (need at least 3 to start batch processing)")
                return
            try:
                start_number = int(self.number)
            except Exception:
                start_number = 1
            current_number = start_number
            used_images = set()
            total_batches = len(mp3_files) // 3
            batch_count = 0
            while len(mp3_files) >= 3:
                if self._stop:
                    self.finished.emit(mp3_files)
                    return
                selected_mp3s = random.sample(mp3_files, 3)
                available_images = [img for img in image_files if img not in used_images]
                if not available_images:
                    used_images = set()
                    available_images = image_files[:]
                selected_image_name = random.choice(available_images)
                selected_image = os.path.join(self.media_sources, selected_image_name)
                used_images.add(selected_image_name)
                # Merge and create video
                clips = [AudioFileClip(f) for f in selected_mp3s]
                final_clip = concatenate_audioclips(clips)
                output_filename = f"{self.export_name}_{current_number}.mp4"
                out = os.path.join(self.folder, output_filename)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    audio_path = tmp.name
                    final_clip.write_audiofile(audio_path)
                try:
                    audio = AudioFileClip(audio_path)
                    image = ImageClip(selected_image).with_duration(audio.duration).resized(height=720)
                    video = image.with_audio(audio)
                    video.write_videofile(out, fps=24, codec="libx264", audio_codec="aac")
                    audio.close()
                    image.close()
                finally:
                    final_clip.close()
                    for clip in clips:
                        clip.close()
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                # Write log file in media folder
                output_base_name = os.path.splitext(output_filename)[0]
                log_path = os.path.join(self.media_sources, f"{output_base_name}.log")
                with open(log_path, "w", encoding="utf-8") as logf:
                    logf.write(f"Output video: {out}\n")
                    logf.write(f"Image used: {selected_image}\n")
                    logf.write("MP3s used:\n")
                    for mp3 in selected_mp3s:
                        logf.write(f"  {mp3}\n")
                bin_folder = os.path.join(self.media_sources, "bin")
                os.makedirs(bin_folder, exist_ok=True)
                shutil.move(log_path, os.path.join(bin_folder, f"{output_base_name}.log"))
                output_base = os.path.splitext(os.path.basename(out))[0]
                for idx, mp3 in enumerate(selected_mp3s, 1):
                    new_name = f"{output_base}+{idx}.mp3"
                    try:
                        shutil.move(mp3, os.path.join(bin_folder, new_name))
                        mp3_files.remove(mp3)
                    except Exception as move_err:
                        print(f"Failed to move {mp3}: {move_err}")
                try:
                    img_ext = os.path.splitext(selected_image)[1]
                    img_new_name = f"{output_base}{img_ext}"
                    shutil.move(selected_image, os.path.join(bin_folder, img_new_name))
                    image_files.remove(selected_image_name)
                except Exception as move_err:
                    print(f"Failed to move {selected_image}: {move_err}")
                current_number += 1
                batch_count += 1
                self.progress.emit(batch_count, total_batches)
            left_mp3 = len(mp3_files)
            self.finished.emit(mp3_files if left_mp3 > 0 else [])
        except Exception as e:
            self.error.emit(str(e))

class FolderDropLineEdit(QLineEdit):
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

class SuperCutUI(QWidget):
    def __init__(self):
        super().__init__()
        # Set window icon from sources/icon.ico
        self.setWindowIcon(QIcon('sources/icon.ico'))
        self.setWindowTitle("SuperCut Video Maker")
        self.setFixedSize(500, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QLabel {
                color: #333;
                padding-right: 5px;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px;
                background-color: white;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        self.output_folder_manual = False
        self.init_ui()
        # Restore window position
        settings = QSettings('SuperCut', 'SuperCutUI')
        pos = settings.value('window_position')
        if pos:
            self.move(pos)
        # Add Ctrl+W shortcut to close main window
        QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Media Folder input (used for both images and mp3s)
        folder_row_style = {
            "label_width": 90,
            "edit_min_width": 220,
            "btn_width": 110
        }

        media_sources_layout = QHBoxLayout()
        label_media = QLabel("Media Folder:")
        label_media.setFixedWidth(folder_row_style["label_width"])
        # --- Use FolderDropLineEdit for drag & drop support ---
        self.media_sources_edit = FolderDropLineEdit()
        self.media_sources_edit.setReadOnly(False)
        self.media_sources_edit.setMinimumWidth(folder_row_style["edit_min_width"])
        self.media_sources_edit.setPlaceholderText("Drag & drop or click Select Folder")
        # Optionally, keep the tooltip for accessibility:
        self.media_sources_edit.setToolTip("Drag and drop a folder here or click 'Select Folder'")
        media_sources_btn = QPushButton("Select Folder")
        media_sources_btn.setFixedWidth(folder_row_style["btn_width"])
        media_sources_btn.clicked.connect(self.select_media_sources_folder)
        media_sources_layout.addWidget(label_media)
        media_sources_layout.addWidget(self.media_sources_edit)
        media_sources_layout.addWidget(media_sources_btn)
        layout.addLayout(media_sources_layout)

        # Output folder selection (same style and alignment as media folder)
        folder_layout = QHBoxLayout()
        label_output = QLabel("Output Folder:")
        label_output.setFixedWidth(folder_row_style["label_width"])
        # --- Optionally, add drag & drop for output folder too ---
        self.folder_edit = FolderDropLineEdit()
        self.folder_edit.setReadOnly(False)
        self.folder_edit.setMinimumWidth(folder_row_style["edit_min_width"])
        self.folder_edit.setPlaceholderText("Drag & drop or click Select Folder")  # <-- Add this line
        self.folder_edit.setToolTip("Drag and drop a folder here or click 'Select Folder'")
        folder_btn = QPushButton("Select Folder")
        folder_btn.setFixedWidth(folder_row_style["btn_width"])
        folder_btn.clicked.connect(self.select_output_folder)
        folder_layout.addWidget(label_output)
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)

        # Part 1 and Part 2 fields (now below output folder)
        part_layout = QHBoxLayout()
        self.part1_edit = QLineEdit("Ragged")
        self.part1_edit.setPlaceholderText("Export Name")
        self.part2_edit = QLineEdit("")
        self.part2_edit.setPlaceholderText("12345")
        self.part2_edit.setValidator(QIntValidator(1, 9999999, self))
        self.part1_edit.textChanged.connect(self.update_output_name)
        self.part2_edit.textChanged.connect(self.update_output_name)
        part_layout.addWidget(QLabel("Export name:"))
        part_layout.addWidget(self.part1_edit)
        part_layout.addWidget(QLabel("Number:"))
        part_layout.addWidget(self.part2_edit)
        layout.addLayout(part_layout)

        # Create button
        self.create_btn = QPushButton("🚀 Create Video")
        self.create_btn.setFixedHeight(35)
        self.create_btn.clicked.connect(self.create_video)
        layout.addWidget(self.create_btn)

        # Add progress bar (hidden by default)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Batch: 0/0")
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Stop button (directly below progress bar, small, hidden by default)
        self.stop_btn = QPushButton("🛑 Stop")
        self.stop_btn.setFixedHeight(24)
        self.stop_btn.setFixedWidth(70)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.stop_video_creation)
        layout.addWidget(self.stop_btn)

        self.setLayout(layout)
        self.output_folder_manual = False
        self.folder_edit.setText("")
        self.update_output_name()

    def select_media_sources_folder(self):
        desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder", desktop_folder)
        if folder:
            self.media_sources_edit.setText(folder)
            if not self.output_folder_manual:
                self.folder_edit.setText(folder)
            self.update_output_name()
        else:
            self.folder_edit.setText("")

    def select_output_folder(self):
        # Open at Desktop by default
        desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", desktop_folder)
        if folder:
            self.folder_edit.setText(folder)
            self.output_folder_manual = True
            self.update_output_name()

    def sanitize_filename(self, name):
        # Remove invalid filename characters: <>:"/\|?*
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def update_output_name(self):
        part1 = self.part1_edit.text().strip()
        part2 = self.part2_edit.text().strip()
        folder = self.folder_edit.text().strip() or os.getcwd()
        # Default to 1 if blank or zero
        if not part2 or part2 == '0':
            part2 = '1'
        # Sanitize export name
        part1 = self.sanitize_filename(part1)
        if part1 and part2:
            filename = f"{part1}_{part2}.mp4"
        else:
            filename = "output.mp4"
        self.output_path = os.path.join(folder, filename)

    def create_video(self):
        media_sources = self.media_sources_edit.text()
        export_name = self.part1_edit.text().strip()
        number = self.part2_edit.text().strip()
        # Default to 1 if blank or zero
        if not number or number == '0':
            number = '1'
        # Sanitize export name
        export_name = self.sanitize_filename(export_name)
        folder = self.folder_edit.text().strip() or os.getcwd()
        if not media_sources:
            QMessageBox.warning(self, "⚠️ Missing Input", "Please select the media folder.", QMessageBox.Ok)
            return
        if not export_name:
            QMessageBox.warning(self, "⚠️ Missing Input", "Please enter an export name.", QMessageBox.Ok)
            return
        if not number:
            QMessageBox.warning(self, "⚠️ Missing Input", "Please enter a number.", QMessageBox.Ok)
            return

        # Check for media before showing waiting dialog
        mp3_files = [os.path.join(media_sources, f) for f in os.listdir(media_sources) if f.lower().endswith('.mp3')]
        image_files = [f for f in os.listdir(media_sources) if f.lower().endswith((".jpg", ".png"))]
        if not image_files:
            QMessageBox.critical(self, "❌ Error", "No image files found in the media folder.")
            return
        if not mp3_files or len(mp3_files) < 3:
            QMessageBox.critical(self, "❌ Error", "Not enough mp3 files in folder (need at least 3 to start batch processing)")
            return

        # Calculate total batches: min(images, mp3s // 3)
        total_batches = min(len(image_files), len(mp3_files) // 3)
        self.progress_bar.setMaximum(total_batches)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"Batch: 0/{total_batches}")
        self.progress_bar.setVisible(True)

        # Track original files for leftovers
        original_mp3_files = set(mp3_files)
        original_image_files = set(image_files)

        self.waiting_dialog = WaitingDialog(self)
        self.waiting_dialog.show()
        QtWidgets.QApplication.processEvents()
        self.stop_btn.setEnabled(True)
        self.stop_btn.setVisible(True)
        self.create_btn.setEnabled(False)

        # Set up worker and thread
        self._thread = QThread()
        self._worker = VideoWorker(media_sources, export_name, number, folder)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.on_worker_progress)
        self._worker.error.connect(self.on_worker_error)
        self._worker.finished.connect(lambda leftover_mp3s: self.on_worker_finished_with_leftovers(leftover_mp3s, original_mp3_files, original_image_files))
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def on_worker_progress(self, batch_count, total_batches):
        self.progress_bar.setMaximum(total_batches)
        self.progress_bar.setValue(batch_count)
        self.progress_bar.setFormat(f"Batch: {batch_count}/{total_batches}")
        QtWidgets.QApplication.processEvents()

    def on_worker_error(self, message):
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
        if hasattr(self, "_worker") and self._worker is not None:
            stop_method = getattr(self._worker, 'stop', None)
            if callable(stop_method):
                try:
                    stop_method()
                except RuntimeError:
                    pass  # Worker already deleted
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        # Show a dialog to inform the user to wait for the current batch to finish
        class PleaseWaitDialog(QDialog):
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
        self._stopping_msgbox = PleaseWaitDialog(self)
        self._stopping_msgbox.show()
        if hasattr(self, "waiting_dialog") and self.waiting_dialog is not None:
            self.waiting_dialog.close()
        self.progress_bar.setVisible(False)
        self.create_btn.setEnabled(True)
        self._auto_close_on_stop = False
        self._stopped_by_user = True  # <-- Add this flag

    def on_worker_finished_with_leftovers(self, leftover_mp3s, original_mp3_files, original_image_files):
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
        # Show stopped dialog if stopped by user, otherwise show success dialog
        if hasattr(self, '_stopped_by_user') and self._stopped_by_user:
            self._stopped_by_user = False  # reset for next run

            # Close PleaseWaitDialog if open
            if hasattr(self, '_stopping_msgbox') and self._stopping_msgbox is not None:
                self._stopping_msgbox.close()
                self._stopping_msgbox = None

            class StoppedDialog(QDialog):
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

                    icon = QLabel("📛")
                    icon.setObjectName("iconLabel")
                    icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                    layout.addWidget(icon)

                    msg = QLabel("Video creation was stopped.")
                    msg.setObjectName("msgLabel")
                    msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                    layout.addWidget(msg)

                    # Batch info
                    batch_count = self.parent().progress_bar.value() if hasattr(self.parent(), 'progress_bar') else 0
                    total_batches = self.parent().progress_bar.maximum() if hasattr(self.parent(), 'progress_bar') else 0
                    unsuccessful = max(0, total_batches - batch_count)
                    batch_info = QLabel(f"Batches completed: {batch_count} / {total_batches}<br>Unsuccessful: {unsuccessful}")
                    batch_info.setObjectName("batchLabel")
                    batch_info.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                    batch_info.setTextFormat(Qt.TextFormat.RichText)
                    layout.addWidget(batch_info)

                    ok_btn = QPushButton("OK")
                    ok_btn.setDefault(True)
                    ok_btn.clicked.connect(self.accept)

                    btn_row = QHBoxLayout()
                    btn_row.addStretch()
                    btn_row.addWidget(ok_btn)
                    btn_row.addStretch()
                    layout.addLayout(btn_row)

                    QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)

                    self.adjustSize()  # 👈 Auto-fit the dialog to content

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
        # Play notification sound at 10% volume (Windows only, if pycaw is available)
        try:
            if sys.platform.startswith('win'):
                QtWidgets.QApplication.beep()
            else:
                QtWidgets.QApplication.beep()
        except Exception:
            pass
        class SuccessDialog(QDialog):
            def __init__(self, parent=None, open_folder=None, leftover_files=None, leftover_images=None):
                super().__init__(parent)
                self.open_folder = open_folder
                self.setWindowTitle("Task Completed")
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

                # Large icon
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
                    leftover_label = QLabel(f"{len(leftover_files)} MP3 files left over (not enough for a group):")
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

                QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)

            def on_folder(self):
                if self.open_folder:
                    self.open_folder()

        dlg = SuccessDialog(self, open_folder=self.open_result_folder, leftover_files=leftover_files, leftover_images=leftover_images)
        dlg.exec_()

    def open_result_folder(self):
        folder = os.path.dirname(self.output_path)
        if sys.platform.startswith('win'):
            os.startfile(folder)
        elif sys.platform.startswith('darwin'):
            subprocess.call(['open', folder])
        else:
            subprocess.call(['xdg-open', folder])

    def clear_inputs(self):
        self.media_sources_edit.setText("")
        self.folder_edit.setText("")
        self.part2_edit.setText("")

    def closeEvent(self, event):
        settings = QSettings('SuperCut', 'SuperCutUI')
        settings.setValue('window_position', self.pos())
        # Fix: Only call isRunning if self._thread is not None
        if hasattr(self, '_thread') and self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()
        super().closeEvent(event)

def set_low_priority():
    try:
        p = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.SetPriorityClass(p, 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS
    except Exception:
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SuperCutUI()
    window.show()
    sys.exit(app.exec_())
