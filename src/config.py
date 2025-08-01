# This file uses PyQt6
import os
import sys
import json
from datetime import datetime

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
WINDOW_SIZE = (660, 660)
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
        padding: 6px 8px;
        background-color: white;
        font-size: 13px;
        line-height: 1.4;
    }
    QLineEdit:hover {
        border: 2px solid #4a90e2;
        background-color: #ffffff;
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
        border: none;
        width: 0px;
    }
    QComboBox::down-arrow {
        image: none;
        border: none;
        width: 0px;
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
        background: #ffffff;
    }
    QCheckBox::indicator:hover {
        border: 1px solid #357ABD;
    }
    QCheckBox::indicator:checked {
        background: #ffffff;
        border: 1px solid #ccc;
        image: url(src/sources/black_tick.svg);
    }
    QCheckBox::indicator:unchecked {
        background: #ffffff;
        border: 1px solid #ccc;
    }
    QCheckBox:disabled {
        color: #888;
    }
    QCheckBox::indicator:disabled {
        background: #f2f2f2;
        border: 1px solid #cfcfcf;
    }
    QScrollBar:vertical {
        background: rgba(240, 240, 240, 0.20);
        width: 12px;
        border-radius: 6px;
        margin: 0px;
        position: absolute;
        right: 0px;
    }
    QScrollBar::handle:vertical {
        background: rgba(192, 192, 192, 0.20);
        border-radius: 6px;
        min-height: 20px;
        margin: 0px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(160, 160, 160, 0.35);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: rgba(240, 240, 240, 0.35);
        height: 12px;
        border-radius: 6px;
        margin: 0px;
        position: absolute;
        bottom: 0px;
    }
    QScrollBar::handle:horizontal {
        background: rgba(192, 192, 192, 0.35);
        border-radius: 6px;
        min-width: 20px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgba(160, 160, 160, 0.35);
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    QScrollBar::sub-control:corner {
        background: transparent;        
    }
    
    QPlainTextEdit {
        border: 1px solid #ccc;
        border-radius: 6px;
        padding: 6px 8px;
        background-color: white;
        font-size: 13px;
        line-height: 1.4;
    }
    
"""

# Video Configuration
DEFAULT_CODECS = [
    ("H.264 NVENC", "h264_nvenc")
]

DEFAULT_RESOLUTIONS = [
    ("1080p", "1920x1080"),
    ("4K 2160p", "3840x2160"),
    ("9:16", "1080x1920"),
    ("Square", "1080x1080")
]

DEFAULT_FPS_OPTIONS = [
    ("24", 24),
    ("30", 30),
    ("60", 60)
]

# File Extensions
AUDIO_EXTENSIONS = ['.mp3']
IMAGE_EXTENSIONS = ['.jpg', '.png', '.gif']
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
    "pixel_format": "yuv420p", # yuv420p is the default pixel format for most videos #nv12 is the pixel format for GPU processing
    "gop_size": "120",
    "bframes": "2",
    "preset": "slow",
    "profile": "high",
    "level": "4.2",
}

# FFmpeg Preset Options
DEFAULT_FFMPEG_PRESETS = [    
    ("Fast", "fast"),
    ("Medium", "medium"),
    ("Slow", "slow")    
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

# Layer Order Configuration
def get_config_file_path():
    """Get the path to the user configuration file"""
    config_dir = os.path.join(PROJECT_ROOT, "config")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "user_settings.json")

def save_layer_order(layer_order):
    """Save layer order to configuration file"""
    config_file = get_config_file_path()
    try:
        # Load existing config or create new one
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Save layer order
        config['layer_order'] = layer_order
        
        # Write back to file
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        

        return True
    except Exception as e:

        return False

def load_layer_order():
    """Load layer order from configuration file"""
    config_file = get_config_file_path()
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                layer_order = config.get('layer_order')
                if layer_order:
            
                    return layer_order
    except Exception as e:
        pass

    return None

# FFmpeg bufsize Options
DEFAULT_BUFSIZE_OPTIONS = [
    ("4 Mbps", "4M"),
    ("8 Mbps", "8M"),
    ("12 Mbps", "12M"),
    ("16 Mbps", "16M"),
    ("24 Mbps", "24M"),
    ("32 Mbps", "32M"),
    ("40 Mbps", "40M"),
    ("48 Mbps", "48M"),
    ("64 Mbps", "64M")
]
DEFAULT_BUFSIZE = "24M"

def check_ffmpeg_installation():
    """Check if FFmpeg is properly installed"""
    if not os.path.exists(FFMPEG_BINARY):
        return False, f"Could not find {FFMPEG_BINARY}. Please ensure ffmpeg is present in the ffmpeg folder."
    return True, None

def get_templates_dir():
    """Get the path to the templates directory"""
    templates_dir = os.path.join(PROJECT_ROOT, "config", "templates")
    os.makedirs(templates_dir, exist_ok=True)
    return templates_dir

def save_template(template_data, template_name):
    """Save template to JSON file"""
    templates_dir = get_templates_dir()
    template_file = os.path.join(templates_dir, f"{template_name}.json")
    
    try:
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving template: {e}")
        return False

def load_template(template_name):
    """Load template from JSON file"""
    templates_dir = get_templates_dir()
    template_file = os.path.join(templates_dir, f"{template_name}.json")
    
    try:
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading template {template_name}: {e}")
    
    return None

def get_available_templates():
    """Get list of all available templates"""
    templates_dir = get_templates_dir()
    templates = []
    
    try:
        if os.path.exists(templates_dir):
            for file in os.listdir(templates_dir):
                if file.endswith('.json'):
                    template_name = file[:-5]  # Remove .json
                    template_data = load_template(template_name)
                    if template_data:
                        templates.append(template_data)
    except Exception as e:
        print(f"Error loading templates: {e}")
    
    return templates

def delete_template(template_name):
    """Delete a template file"""
    templates_dir = get_templates_dir()
    template_file = os.path.join(templates_dir, f"{template_name}.json")
    
    try:
        if os.path.exists(template_file):
            os.remove(template_file)
            return True
    except Exception as e:
        print(f"Error deleting template {template_name}: {e}")
    
    return False

def get_template_categories():
    """Get template categories configuration"""
    categories_file = os.path.join(PROJECT_ROOT, "config", "template_categories.json")
    
    default_categories = {
        "categories": {
            "music": {
                "name": "Music",
                "description": "Templates for music videos and audio content",
                "icon": "🎵",
                "color": "#4a90e2"
            },
            "gaming": {
                "name": "Gaming",
                "description": "Templates for gaming highlights and streams",
                "icon": "🎮",
                "color": "#e24a4a"
            },
            "business": {
                "name": "Business",
                "description": "Templates for professional presentations",
                "icon": "💼",
                "color": "#4ae24a"
            },
            "social": {
                "name": "Social Media",
                "description": "Templates for social media content",
                "icon": "📱",
                "color": "#e24ae2"
            },
            "custom": {
                "name": "Custom",
                "description": "User-created custom templates",
                "icon": "⚙️",
                "color": "#e2e24a"
            }
        }
    }
    
    try:
        if os.path.exists(categories_file):
            with open(categories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default categories file
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(default_categories, f, indent=2, ensure_ascii=False)
            return default_categories
    except Exception as e:
        print(f"Error loading template categories: {e}")
        return default_categories