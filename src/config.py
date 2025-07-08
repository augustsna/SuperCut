# This file uses PyQt6
import os
import sys

# Project root is one level up from this file
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# FFmpeg Configuration
FFMPEG_BASE_PATH = "C:/SuperCut/ffmpeg/bin"
FFMPEG_BINARY = os.path.abspath(os.path.join(FFMPEG_BASE_PATH, "ffmpeg.exe"))
FFPLAY_BINARY = os.path.abspath(os.path.join(FFMPEG_BASE_PATH, "ffplay.exe"))
FFPROBE_BINARY = os.path.abspath(os.path.join(FFMPEG_BASE_PATH, "ffprobe.exe"))

# Set environment variables
os.environ["FFMPEG_BINARY"] = FFMPEG_BINARY
os.environ["FFPLAY_BINARY"] = FFPLAY_BINARY

# UI Configuration
WINDOW_SIZE = (640, 560)
WINDOW_TITLE = "SuperCut Magic Maker"
ICON_PATH = os.path.join(PROJECT_ROOT, "src", "sources", "icon.png")
STYLE_SHEET = os.path.join(PROJECT_ROOT, "src", "sources", "style.qss") if os.path.exists(os.path.join(PROJECT_ROOT, "src", "sources", "style.qss")) else """
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
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
        color: #333;
        font-family: 'Segoe UI', sans-serif;                               
    }
    QComboBox:hover {
        border: 2px solid #4687f4;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left: 1px solid #ccc;
    }
    QComboBox::down-arrow {
        image: url(src/sources/down_arrow.svg);
        width: 16px;
        height: 16px;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        selection-background-color: #3f92e3;
        border: 1px solid #ccc;
        outline: none;
    }
    QCheckBox {
        spacing: 8px;
        font-size: 13px;
        color: #333;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 6px;
        border: 1px solid #ccc;
        background: transparent;
    }
    QCheckBox::indicator:hover {
        border: 1px solid #357ABD;
    }
    QCheckBox::indicator:checked {
        background: transparent;
        border: 1px solid #ccc;
        image: url(src/sources/black_tick.svg);
    }
    QCheckBox::indicator:unchecked {
        background: transparent;
        border: 1px solid #ccc;
    }
"""

# Video Configuration
DEFAULT_CODECS = [
    ("H.264 NVENC", "h264_nvenc"),
    ("H.264 libx264", "libx264")
]

DEFAULT_RESOLUTIONS = [
    ("Full HD (1080p)", "1920x1080"),
    ("4K UHD (2160p)", "3840x2160"),
    ("Vertical (9:16)", "1080x1920"),
    ("Square (1:1)", "1080x1080")
]

DEFAULT_FPS_OPTIONS = [
    ("24 FPS", 24),
    ("30 FPS", 30),
    ("60 FPS", 60)
]

# File Extensions
AUDIO_EXTENSIONS = ['.mp3']
IMAGE_EXTENSIONS = ['.jpg', '.png']
VIDEO_EXTENSIONS = ['.mp4']

# Default Values
DEFAULT_EXPORT_NAME = "Output"
DEFAULT_START_NUMBER = "1"
DEFAULT_FPS = 24
DEFAULT_RESOLUTION = "1920x1080"
DEFAULT_CODEC = "h264_nvenc"
DEFAULT_MIN_MP3_COUNT = 3

# Video Encoding Settings
VIDEO_SETTINGS = {
    "audio_codec": "aac",
    "audio_bitrate": "384k",
    "audio_sample_rate": "48000",
    "audio_channels": "2",
    "video_bitrate": "12M",
    "max_bitrate": "16M",
    "buffer_size": "24M",
    "pixel_format": "yuv420p",
    "gop_size": "120",
    "bframes": "2",
    "preset": "slow",
    "profile": "high",
    "level": "4.2",
}

# FFmpeg Preset Options
DEFAULT_FFMPEG_PRESETS = [
    ("Ultrafast", "ultrafast"),
    ("Superfast", "superfast"),
    ("Veryfast", "veryfast"),
    ("Faster", "faster"),
    ("Fast", "fast"),
    ("Medium", "medium"),
    ("Slow", "slow"),
    ("Slower", "slower"),
    ("Veryslow", "veryslow")
]
DEFAULT_FFMPEG_PRESET = "slow"

# FFmpeg Audio Bitrate Options
DEFAULT_AUDIO_BITRATE_OPTIONS = [
    ("96 kbps", "96k"),
    ("128 kbps", "128k"),
    ("192 kbps", "192k"),
    ("256 kbps", "256k"),
    ("320 kbps", "320k"),
    ("384 kbps", "384k"),
    ("512 kbps", "512k")
]
DEFAULT_AUDIO_BITRATE = "384k"

# FFmpeg Video Bitrate Options
DEFAULT_VIDEO_BITRATE_OPTIONS = [
    ("1 Mbps", "1M"),
    ("2 Mbps", "2M"),
    ("4 Mbps", "4M"),
    ("6 Mbps", "6M"),
    ("8 Mbps", "8M"),
    ("12 Mbps", "12M"),
    ("16 Mbps", "16M"),
    ("20 Mbps", "20M"),
    ("25 Mbps", "25M"),
    ("30 Mbps", "30M")
]
DEFAULT_VIDEO_BITRATE = "12M"

# FFmpeg Maxrate Options
DEFAULT_MAXRATE_OPTIONS = [
    ("2 Mbps", "2M"),
    ("4 Mbps", "4M"),
    ("6 Mbps", "6M"),
    ("8 Mbps", "8M"),
    ("12 Mbps", "12M"),
    ("16 Mbps", "16M"),
    ("20 Mbps", "20M"),
    ("25 Mbps", "25M"),
    ("30 Mbps", "30M"),
    ("40 Mbps", "40M")
]
DEFAULT_MAXRATE = "16M"

def check_ffmpeg_installation():
    """Check if FFmpeg is properly installed"""
    if not os.path.exists(FFMPEG_BINARY):
        return False, f"Could not find {FFMPEG_BINARY}. Please ensure ffmpeg is present in the ffmpeg folder."
    return True, None