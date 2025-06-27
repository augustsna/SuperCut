import os
import sys
import random
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QApplication, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QDialog, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings
from moviepy import ImageClip, AudioFileClip, concatenate_audioclips
import subprocess
import shutil
from PyQt5.QtGui import QIntValidator, QIcon, QMovie
import tempfile

# Set FFMPEG paths (use local ffmpeg folder)
os.environ["FFMPEG_BINARY"] = os.path.abspath("ffmpeg/ffmpeg.exe")
os.environ["FFPLAY_BINARY"] = os.path.abspath("ffmpeg/ffplay.exe")

# Check if ffmpeg exists
if not os.path.exists(os.environ["FFMPEG_BINARY"]):
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "FFmpeg Not Found", "Could not find ffmpeg/ffmpeg.exe. Please ensure ffmpeg is present in the ffmpeg folder.")
    sys.exit(1)

def make_video(image_path, audio_path, output_path):
    audio = AudioFileClip(audio_path)
    image = ImageClip(image_path).with_duration(audio.duration).resized(height=720)
    video = image.with_audio(audio)
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

def merge_random_mp3s(folder_path, count=3):
    mp3_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]
    if len(mp3_files) < count:
        raise Exception(f"Not enough mp3 files in folder (found {len(mp3_files)}, need {count})")
    selected = random.sample(mp3_files, count)
    clips = [AudioFileClip(f) for f in selected]
    final_clip = concatenate_audioclips(clips)
    return final_clip, selected

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
        self.movie = QMovie("spinner.gif")
        self.spinner.setMovie(self.movie)
        layout.addWidget(self.spinner)
        self.movie.start()

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
        self.media_sources_edit = QLineEdit()
        self.media_sources_edit.setReadOnly(True)
        self.media_sources_edit.setMinimumWidth(folder_row_style["edit_min_width"])
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
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        self.folder_edit.setMinimumWidth(folder_row_style["edit_min_width"])
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
        create_btn = QPushButton("🚀 Create Video")
        create_btn.setFixedHeight(35)
        create_btn.clicked.connect(self.create_video)
        layout.addWidget(create_btn)

        # Add progress bar (hidden by default)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Batch: 0/0")
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.output_folder_manual = False
        self.folder_edit.setText("")
        self.update_output_name()

    def build_file_input(self, label_text, action, attr_name):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        edit = QLineEdit()
        button = QPushButton("Browse")
        button.setFixedWidth(80)
        button.clicked.connect(action)
        layout.addWidget(label)
        layout.addWidget(edit)
        layout.addWidget(button)
        setattr(self, attr_name, edit)
        return layout

    def select_media_sources_folder(self):
        desktop_folder = os.path.join(os.path.expanduser("~"), "Desktop")
        folder = QFileDialog.getExistingDirectory(self, "Select Media Folder", desktop_folder)
        if folder:
            self.media_sources_edit.setText(folder)
            if not self.output_folder_manual:
                self.folder_edit.setText(folder)
            self.update_output_name()

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", os.getcwd())
        if folder:
            self.folder_edit.setText(folder)
            self.output_folder_manual = True
            self.update_output_name()

    def update_output_name(self):
        part1 = self.part1_edit.text().strip()
        part2 = self.part2_edit.text().strip()
        folder = self.folder_edit.text().strip() or os.getcwd()
        if part1 and part2:
            filename = f"{part1}_{part2}.mp4"
        else:
            filename = "output.mp4"
        self.output_path = os.path.join(folder, filename)

    def create_video(self):
        media_sources = self.media_sources_edit.text()
        export_name = self.part1_edit.text().strip()
        number = self.part2_edit.text().strip()
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
        # Only show waiting dialog after all checks pass
        waiting_dialog = WaitingDialog(self)
        waiting_dialog.show()
        QtWidgets.QApplication.processEvents()
        try:
            mp3_files = [os.path.join(media_sources, f) for f in os.listdir(media_sources) if f.lower().endswith('.mp3')]
            image_files = [f for f in os.listdir(media_sources) if f.lower().endswith((".jpg", ".png"))]
            if not image_files:
                waiting_dialog.close()
                QMessageBox.critical(self, "❌ Error", "No image files found in the media folder.")
                return
            if not mp3_files or len(mp3_files) < 3:
                waiting_dialog.close()
                raise Exception("Not enough mp3 files in folder (need at least 3 to start batch processing)")
            # Prepare for batch processing
            try:
                start_number = int(number)
            except Exception:
                start_number = 1
            current_number = start_number
            used_images = set()
            total_batches = len(mp3_files) // 3
            self.progress_bar.setMaximum(total_batches)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(f"Batch: 0/{total_batches}")
            self.progress_bar.setVisible(True)
            QtWidgets.QApplication.processEvents()
            batch_count = 0
            while len(mp3_files) >= 3:
                # Pick 3 mp3s
                selected_mp3s = random.sample(mp3_files, 3)
                # Pick an image (random, but try to avoid repeats until all are used)
                available_images = [img for img in image_files if img not in used_images]
                if not available_images:
                    used_images = set()
                    available_images = image_files[:]
                selected_image = os.path.join(media_sources, random.choice(available_images))
                used_images.add(os.path.basename(selected_image))
                # Merge and create video
                merged_clip, _ = merge_random_mp3s(media_sources, 3)
                output_filename = f"{export_name}_{current_number}.mp4"
                out = os.path.join(folder, output_filename)
                # Use tempfile for audio_path
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    audio_path = tmp.name
                    merged_clip.write_audiofile(audio_path)
                try:
                    make_video(selected_image, audio_path, out)
                    merged_clip.close()
                finally:
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                # Write log file in media folder
                output_base_name = os.path.splitext(output_filename)[0]
                log_path = os.path.join(media_sources, f"{output_base_name}.log")
                with open(log_path, "w", encoding="utf-8") as logf:
                    logf.write(f"Output video: {out}\n")
                    logf.write(f"Image used: {selected_image}\n")
                    logf.write("MP3s used:\n")
                    for mp3 in selected_mp3s:
                        logf.write(f"  {mp3}\n")
                # Move log file to bin folder
                bin_folder = os.path.join(media_sources, "bin")
                os.makedirs(bin_folder, exist_ok=True)
                shutil.move(log_path, os.path.join(bin_folder, f"{output_base_name}.log"))
                # Move used mp3s and image to bin folder
                output_base = os.path.splitext(os.path.basename(out))[0]
                for idx, mp3 in enumerate(selected_mp3s, 1):
                    new_name = f"{output_base}+{idx}.mp3"
                    try:
                        shutil.move(mp3, os.path.join(bin_folder, new_name))
                        mp3_files.remove(mp3)
                    except Exception as move_err:
                        print(f"Failed to move {mp3}: {move_err}")
                # Move used image to bin folder and rename as output name
                try:
                    img_ext = os.path.splitext(selected_image)[1]
                    img_new_name = f"{output_base}{img_ext}"
                    shutil.move(selected_image, os.path.join(bin_folder, img_new_name))
                    image_files.remove(os.path.basename(selected_image))
                except Exception as move_err:
                    print(f"Failed to move {selected_image}: {move_err}")
                current_number += 1
                batch_count += 1
                self.progress_bar.setValue(batch_count)
                self.progress_bar.setFormat(f"Batch: {batch_count}/{total_batches}")
                QtWidgets.QApplication.processEvents()
            self.progress_bar.setVisible(False)
            # After loop, show message about leftovers
            left_mp3 = len(mp3_files)
            if left_mp3 > 0:
                self.show_success_options(leftover_files=mp3_files)
                self.clear_inputs()
            else:
                self.show_success_options()
                self.clear_inputs()
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "❌ Error", str(e))
        finally:
            waiting_dialog.close()

    def show_success_options(self, leftover_files=None):
        # Play notification sound at 10% volume (Windows only, if pycaw is available)
        try:
            if sys.platform.startswith('win'):
                # pycaw/comtypes not installed, just play beep
                QtWidgets.QApplication.beep()
            else:
                QtWidgets.QApplication.beep()
        except Exception:
            pass
        class SuccessDialog(QDialog):
            def __init__(self, parent=None, open_folder=None, leftover_files=None):
                super().__init__(parent)
                self.open_folder = open_folder
                self.setWindowTitle("Task Completed")
                self.setFixedSize(370, 220 if leftover_files else 170)
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
                # Use only color, no outline or shadow
                icon.setStyleSheet("font-size: 28px; color: #4BB543; border: none; background: transparent;")
                vbox.addWidget(icon)

                # Main message
                msg = QLabel("Video created successfully!")
                msg.setObjectName("msgLabel")
                msg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                vbox.addWidget(msg)

                # Leftover files section
                if leftover_files:
                    leftover_label = QLabel(f"{len(leftover_files)} MP3 file(s) left over (not enough for a group):")
                    leftover_label.setObjectName("leftoverLabel")
                    leftover_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                    vbox.addWidget(leftover_label)
                    file_list = QLabel("\n".join([os.path.basename(f) for f in leftover_files]))
                    file_list.setObjectName("fileListLabel")
                    file_list.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                    vbox.addWidget(file_list)

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

        dlg = SuccessDialog(self, open_folder=self.open_result_folder, leftover_files=leftover_files)
        dlg.exec_()

    def open_log_file(self):
        # Try to open log from media folder if possible
        log_path = os.path.join(self.media_sources_edit.text(), "output.log")
        if os.path.exists(log_path):
            if sys.platform.startswith('win'):
                os.startfile(log_path)
            elif sys.platform.startswith('darwin'):
                subprocess.call(['open', log_path])
            else:
                subprocess.call(['xdg-open', log_path])
        else:
            QMessageBox.information(self, "Log Not Found", "No log file found.")

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
        self.part1_edit.setText("")
        self.part2_edit.setText("")

    def closeEvent(self, event):
        settings = QSettings('SuperCut', 'SuperCutUI')
        settings.setValue('window_position', self.pos())
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SuperCutUI()
    window.show()
    sys.exit(app.exec_())
