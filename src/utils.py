# This file uses PyQt6
import os
import re
import ctypes
import tempfile
import atexit
from typing import Set
from src.logger import logger
import shutil
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from PIL import Image, ImageDraw, ImageFont

# Global set to track temporary files
TEMP_FILES: Set[str] = set()

MIN_FREE_SPACE_BYTES = 100 * 1024 * 1024  # 100MB

def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters: <>:"/\\|?*"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def clean_file_path(path: str) -> str:
    """Clean file path by removing file:/// prefix and normalizing the path"""
    if not path:
        return path
    
    # Remove file:/// prefix if present
    if path.startswith('file:///'):
        path = path[7:]  # Remove 'file:///'
    elif path.startswith('file://'):
        path = path[7:]  # Remove 'file://'
    elif path.startswith('file:'):
        path = path[5:]  # Remove 'file:'
    
    # Handle Windows paths that might have extra slashes
    if os.name == 'nt' and path.startswith('/'):
        # Convert /C:/path to C:/path
        if len(path) > 2 and path[1] == ':' and path[2] == '/':
            path = path[1:]
        # Convert /path to path (relative path)
        elif len(path) > 1:
            path = path[1:]
    
    # Normalize the path
    return os.path.normpath(path)

def get_desktop_folder() -> str:
    """Get the desktop folder path"""
    return os.path.join(os.path.expanduser("~"), "Desktop")

def set_low_priority():
    """Set process priority to below normal (Windows only)"""
    try:
        p = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.SetPriorityClass(p, 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS
    except AttributeError as e:
        logger.warning(f"ctypes.windll not available: {e}")
    except OSError as e:
        logger.warning(f"OS error setting low priority: {e}")

def has_enough_disk_space(path: str, required_bytes: int) -> bool:
    """Check if the filesystem containing 'path' has at least required_bytes free."""
    try:
        usage = shutil.disk_usage(os.path.abspath(path))
        return usage.free >= required_bytes
    except FileNotFoundError:
        logger.warning(f"Disk usage path not found: {path}")
        return False
    except PermissionError:
        logger.warning(f"No permission to check disk usage for {path}.")
        return False
    except OSError as e:
        logger.warning(f"OS error checking disk space for {path}: {e}")
        return False

def create_temp_file(suffix: str = "", prefix: str = "") -> str:
    """Create a temporary file and track it for cleanup. Checks for minimum free disk space."""
    unique_prefix = "supercut_"
    temp_dir = tempfile.gettempdir()
    if not has_enough_disk_space(temp_dir, MIN_FREE_SPACE_BYTES):
        logger.error(f"Not enough disk space to create temp file in {temp_dir}. At least {MIN_FREE_SPACE_BYTES // (1024*1024)}MB required.")
        raise OSError(f"Not enough disk space to create temp file in {temp_dir}.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=unique_prefix) as tmp:
        temp_path = tmp.name
        TEMP_FILES.add(temp_path)
        return temp_path

def cleanup_temp_files():
    """Clean up all tracked temporary files that start with our unique prefix.
    Note: This only runs on normal interpreter exit. If the app is killed abruptly (e.g., SIGKILL), temp files may remain. Consider providing a manual cleanup utility if this is a concern.
    """
    unique_prefix = "supercut_"
    for file_path in list(TEMP_FILES):
        try:
            if os.path.exists(file_path) and os.path.basename(file_path).startswith(unique_prefix):
                os.remove(file_path)
        except FileNotFoundError:
            logger.warning(f"Temp file {file_path} not found for removal.")
        except PermissionError:
            logger.warning(f"No permission to remove temp file {file_path}.")
        except OSError as e:
            logger.warning(f"OS error removing temp file {file_path}: {e}")
        TEMP_FILES.discard(file_path)
    TEMP_FILES.clear()

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
    from src.config import AUDIO_EXTENSIONS
    return get_file_extension(filename) in AUDIO_EXTENSIONS

def is_image_file(filename: str) -> bool:
    """Check if a file is an image file"""
    from src.config import IMAGE_EXTENSIONS
    return get_file_extension(filename) in IMAGE_EXTENSIONS

def is_video_file(filename: str) -> bool:
    """Check if a file is a video file"""
    from src.config import VIDEO_EXTENSIONS
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
    import os
    # Check media_sources is not empty and is a valid directory
    if not media_sources:
        return False, "Please select the media folder."
    if not os.path.isdir(media_sources):
        return False, f"Media folder does not exist: {media_sources}"
    # Check export_name is not empty and is a valid filename (no path separators)
    if not export_name:
        return False, "Please enter an export name."
    if any(sep in export_name for sep in (os.sep, os.altsep) if sep):
        return False, "Export name cannot contain path separators."
    # Check number is a positive integer
    if not number:
        return False, "Please enter a number."
    try:
        num = int(number)
        if num <= 0:
            return False, "Number must be a positive integer."
    except ValueError:
        return False, "Number must be a valid integer."
    return True, ""

def validate_media_files(media_sources: str, min_mp3_count: int = 3) -> tuple[bool, str, list, list]:
    """Validate media files and return (is_valid, error_message, mp3_files, image_files)"""
    mp3_files = get_files_by_type(media_sources, "audio")
    image_files = get_files_by_type(media_sources, "image")
    if not image_files:
        return False, "No image files found in the media folder.", [], []
    if not mp3_files or len(mp3_files) < min_mp3_count:
        return False, f"Not enough mp3 files in folder (need at least {min_mp3_count} to start batch processing)", [], []
    return True, "", mp3_files, image_files

def extract_mp3_title(mp3_path):
    """
    Extract the song title from an MP3 file's metadata.
    Returns the title as a string, or the filename (without extension) if not found.
    """
    try:
        audio = MP3(mp3_path, ID3=EasyID3)
        title = audio.get('title', None)
        if title and isinstance(title, list):
            return title[0]
        elif title:
            return title
    except Exception:
        pass
    # Fallback: use filename without extension
    import os
    return os.path.splitext(os.path.basename(mp3_path))[0]

def create_song_title_png(title, output_path, width=400, height=40, font_size=12, font_name="default", color=(255, 255, 255)):
    """
    Create a PNG image with the song title text at the top-left.
    Args:
        title (str): The song title to render.
        output_path (str): Where to save the PNG.
        width (int): Width of the image.
        height (int): Height of the image.
        font_size (int): Font size for the title.
        font_name (str): Font filename or "default" for system font.
        color (tuple): RGB color tuple for the text.
    """
    from src.config import PROJECT_ROOT
    
    # Create a transparent image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to load custom font if specified
    font = None
    if font_name != "default":
        try:
            font_path = os.path.join(PROJECT_ROOT, "src", "sources", "font", font_name)
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            logger.warning(f"Failed to load custom font {font_name}: {e}")
    
    # Fallback to system font if custom font failed
    if font is None:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
    
    # Draw text at (8, 8) for padding
    draw.text((8, 8), title, font=font, fill=(*color, 255))
    img.save(output_path, 'PNG')

# Register cleanup function to run at exit
atexit.register(cleanup_temp_files) 