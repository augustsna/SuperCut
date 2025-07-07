# This file uses PyQt6
import os
import re
import ctypes
import tempfile
import atexit
from typing import Set
from src.logger import logger
import shutil
from PyQt6.QtWidgets import QFileDialog, QMessageBox

# Global set to track temporary files
TEMP_FILES: Set[str] = set()

MIN_FREE_SPACE_BYTES = 100 * 1024 * 1024  # 100MB

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

def select_media_sources_folder(parent, media_sources_edit, folder_edit, output_folder_manual, update_output_name_func):
    """Select media sources folder (refactored for utils)"""
    desktop_folder = get_desktop_folder()
    folder = QFileDialog.getExistingDirectory(parent, "Select Media Folder", desktop_folder)
    if folder:
        media_sources_edit.setText(folder)
        if not output_folder_manual:
            folder_edit.setText(folder)
        update_output_name_func()
        return folder
    else:
        if not output_folder_manual:
            folder_edit.setText("")
        return None

def select_output_folder(parent, folder_edit, update_output_name_func, set_output_folder_manual):
    """Select output folder (refactored for utils)"""
    desktop_folder = get_desktop_folder()
    folder = QFileDialog.getExistingDirectory(parent, "Select Output Folder", desktop_folder)
    if folder:
        folder_edit.setText(folder)
        set_output_folder_manual(True)
        update_output_name_func()
        return folder
    return None

def update_output_name(name_list_checkbox, name_list, part1_edit, part2_edit, folder_edit, set_output_path_func):
    """Update the output filename based on current inputs (refactored for utils)"""
    if name_list_checkbox.isChecked() and name_list:
        part1 = name_list[0][:180]
        filename = f"{sanitize_filename(part1)}.mp4"
    else:
        part1 = part1_edit.text().strip()
        part2 = part2_edit.text().strip()
        folder = folder_edit.text().strip() or os.getcwd()
        if not part2 or part2 == '0':
            part2 = '1'
        part1 = sanitize_filename(part1 or "")
        if part1 and part2:
            filename = f"{part1}_{part2}.mp4"
        else:
            filename = "output.mp4"
    folder = folder_edit.text().strip() or os.getcwd()
    output_path = os.path.join(folder, filename)
    set_output_path_func(output_path)
    return output_path

def gather_and_validate_inputs(
    parent,
    media_sources_edit,
    name_list_checkbox,
    name_list,
    part1_edit,
    part2_edit,
    folder_edit,
    codec_combo,
    resolution_combo,
    fps_combo,
    mp3_count_checkbox,
    mp3_count_edit,
    DEFAULT_MIN_MP3_COUNT
):
    """Gather and validate user inputs. Return tuple or None if invalid. (refactored for utils)"""
    media_sources = media_sources_edit.text()
    use_name_list = name_list_checkbox.isChecked() if name_list_checkbox else False
    if use_name_list:
        export_name = ""
    else:
        export_name = part1_edit.text().strip()
    number = part2_edit.text().strip()
    if not number or number == '0':
        number = '1'
    if not use_name_list:
        export_name = sanitize_filename(export_name or "")
    folder = folder_edit.text().strip()
    if not folder:
        QMessageBox.warning(parent, "⚠️ Missing Output Folder", "Please select or enter an output folder.", QMessageBox.StandardButton.Ok)
        return None
    codec = codec_combo.currentData()
    resolution = resolution_combo.currentData()
    fps = fps_combo.currentData()
    if mp3_count_checkbox.isChecked():
        try:
            min_mp3_count = int(mp3_count_edit.text())
            if min_mp3_count < 1:
                min_mp3_count = DEFAULT_MIN_MP3_COUNT
        except Exception:
            min_mp3_count = DEFAULT_MIN_MP3_COUNT
    else:
        min_mp3_count = DEFAULT_MIN_MP3_COUNT
    if not use_name_list:
        is_valid, error_msg = validate_inputs(media_sources, export_name or "", number)
        if not is_valid:
            QMessageBox.warning(parent, "⚠️ Missing Input", error_msg, QMessageBox.StandardButton.Ok)
            return None
    is_valid, error_msg, mp3_files, image_files = validate_media_files(media_sources, min_mp3_count)
    if not is_valid:
        QMessageBox.critical(parent, "❌ Error", error_msg)
        return None
    return (media_sources, export_name, number, folder, codec, resolution, fps, set(mp3_files), set(image_files), min_mp3_count)

# Register cleanup function to run at exit
atexit.register(cleanup_temp_files)