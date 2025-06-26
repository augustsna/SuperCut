import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
import sys
from moviepy import ImageClip, AudioFileClip

# Set FFMPEG paths (use local ffmpeg folder)
os.environ["FFMPEG_BINARY"] = os.path.abspath("ffmpeg/ffmpeg.exe")
os.environ["FFPLAY_BINARY"] = os.path.abspath("ffmpeg/ffplay.exe")

def make_video(image_path, audio_path, output_path):
    audio = AudioFileClip(audio_path)
    image = ImageClip(image_path).with_duration(audio.duration)
    image = image.resized(height=720)
    video = image.with_audio(audio)
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

class SuperCutUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperCut Video Maker")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image
        img_layout = QHBoxLayout()
        self.img_edit = QLineEdit()
        img_btn = QPushButton("Browse Image")
        img_btn.clicked.connect(self.browse_image)
        img_layout.addWidget(QLabel("Image:"))
        img_layout.addWidget(self.img_edit)
        img_layout.addWidget(img_btn)
        layout.addLayout(img_layout)

        # Audio
        audio_layout = QHBoxLayout()
        self.audio_edit = QLineEdit()
        audio_btn = QPushButton("Browse Audio")
        audio_btn.clicked.connect(self.browse_audio)
        audio_layout.addWidget(QLabel("Audio:"))
        audio_layout.addWidget(self.audio_edit)
        audio_layout.addWidget(audio_btn)
        layout.addLayout(audio_layout)

        # Output
        out_layout = QHBoxLayout()
        self.out_edit = QLineEdit("output.mp4")
        out_btn = QPushButton("Save As")
        out_btn.clicked.connect(self.save_output)
        out_layout.addWidget(QLabel("Output:"))
        out_layout.addWidget(self.out_edit)
        out_layout.addWidget(out_btn)
        layout.addLayout(out_layout)

        # Create button
        create_btn = QPushButton("Create Video")
        create_btn.clicked.connect(self.create_video)
        layout.addWidget(create_btn)

        self.setLayout(layout)

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.jpg *.png)")
        if path:
            self.img_edit.setText(path)

    def browse_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Audio", "", "Audio Files (*.mp3 *.wav)")
        if path:
            self.audio_edit.setText(path)

    def save_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Output", "output.mp4", "MP4 Files (*.mp4)")
        if path:
            self.out_edit.setText(path)

    def create_video(self):
        img = self.img_edit.text()
        audio = self.audio_edit.text()
        out = self.out_edit.text()
        try:
            make_video(img, audio, out)
            QMessageBox.information(self, "Success", "Video created successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SuperCutUI()
    window.show()
    sys.exit(app.exec_())
