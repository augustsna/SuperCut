import os
import re
import ctypes
import tempfile
import atexit
from typing import Set
from logger import logger

# Global set to track temporary files
TEMP_FILES: Set[str] = set()

def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters: <>:"/\\|?*"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def get_desktop_folder() -> str:
    """Get the desktop folder path"""
    return os.path.join(os.path.expanduser("~"), "Desktop")

def set_low_priority():
    """Set process priority to below normal (Windows only)"""
    try:
        p = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.SetPriorityClass(p, 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS
    except Exception as e:
        logger.warning(f"Failed to set low priority: {e}")

def create_temp_file(suffix: str = "", prefix: str = "") -> str:
    """Create a temporary file and track it for cleanup"""
    unique_prefix = "supercut_"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=unique_prefix) as tmp:
        temp_path = tmp.name
        TEMP_FILES.add(temp_path)
        return temp_path

def cleanup_temp_files():
    """Clean up all tracked temporary files that start with our unique prefix"""
    unique_prefix = "supercut_"
    for file_path in list(TEMP_FILES):
        try:
            if os.path.exists(file_path) and os.path.basename(file_path).startswith(unique_prefix):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to remove temp file {file_path}: {e}")
        TEMP_FILES.discard(file_path)

def open_folder_in_explorer(folder_path: str):
    """Open a folder in the system's file explorer"""
    import sys
    import subprocess
    
    if sys.platform.startswith('win'):
        os.startfile(folder_path)
    elif sys.platform.startswith('darwin'):
        subprocess.call(['open', folder_path])
    else:
        subprocess.call(['xdg-open', folder_path])

def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename"""
    return os.path.splitext(filename)[1].lower()

def is_audio_file(filename: str) -> bool:
    """Check if a file is an audio file"""
    from config import AUDIO_EXTENSIONS
    return get_file_extension(filename) in AUDIO_EXTENSIONS

def is_image_file(filename: str) -> bool:
    """Check if a file is an image file"""
    from config import IMAGE_EXTENSIONS
    return get_file_extension(filename) in IMAGE_EXTENSIONS

def is_video_file(filename: str) -> bool:
    """Check if a file is a video file"""
    from config import VIDEO_EXTENSIONS
    return get_file_extension(filename) in VIDEO_EXTENSIONS

def get_files_by_type(folder_path: str, file_type: str) -> list:
    """Get all files of a specific type from a folder. Always return full file paths."""
    if not os.path.exists(folder_path):
        return []
    files = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            if file_type == "audio" and is_audio_file(filename):
                files.append(file_path)
            elif file_type == "image" and is_image_file(filename):
                files.append(file_path)  # Return full path for images
            elif file_type == "video" and is_video_file(filename):
                files.append(file_path)
    return files

def format_time(seconds: int) -> str:
    """Format seconds into HH:MM:SS format"""
    import time
    return time.strftime('%H:%M:%S', time.gmtime(seconds)) if seconds > 0 else "--:--:--"

def validate_inputs(media_sources: str, export_name: str, number: str) -> tuple[bool, str]:
    """Validate user inputs and return (is_valid, error_message)"""
    if not media_sources:
        return False, "Please select the media folder."
    if not export_name:
        return False, "Please enter an export name."
    if not number:
        return False, "Please enter a number."
    return True, ""

def validate_media_files(media_sources: str) -> tuple[bool, str, list, list]:
    """Validate media files and return (is_valid, error_message, mp3_files, image_files)"""
    mp3_files = get_files_by_type(media_sources, "audio")
    image_files = get_files_by_type(media_sources, "image")
    
    if not image_files:
        return False, "No image files found in the media folder.", [], []
    if not mp3_files or len(mp3_files) < 3:
        return False, "Not enough mp3 files in folder (need at least 3 to start batch processing)", [], []
    
    return True, "", mp3_files, image_files

# Register cleanup function to run at exit
atexit.register(cleanup_temp_files) 