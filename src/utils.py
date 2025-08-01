# This file uses PyQt6
import os
import re
import ctypes
import tempfile
import atexit
import gc
import weakref
import io
from typing import Set, Dict, Any, Optional
from src.logger import logger
import shutil
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from PIL import Image, ImageDraw, ImageFont

# Try to import psutil for memory monitoring (optional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

# Global set to track temporary files
TEMP_FILES: Set[str] = set()

# Global registry for memory management
MEMORY_REGISTRY: Dict[str, Any] = {}
WEAK_REFERENCES: Dict[str, weakref.ref] = {}

MIN_FREE_SPACE_BYTES = 100 * 1024 * 1024  # 100MB

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage statistics in MB"""
    if not PSUTIL_AVAILABLE:
        return {"error": "psutil not available"}
    
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / 1024 / 1024
        }
    except Exception as e:
        logger.warning(f"Error getting memory usage: {e}")
        return {"error": str(e)}

def register_for_cleanup(obj: Any, name: str = None) -> str:
    """Register an object for automatic cleanup"""
    if name is None:
        name = f"obj_{id(obj)}"
    
    MEMORY_REGISTRY[name] = obj
    WEAK_REFERENCES[name] = weakref.ref(obj, lambda ref, name=name: _cleanup_callback(name))
    
    logger.debug(f"Registered object '{name}' for cleanup")
    return name

def unregister_from_cleanup(name: str) -> bool:
    """Unregister an object from cleanup"""
    if name in MEMORY_REGISTRY:
        del MEMORY_REGISTRY[name]
        if name in WEAK_REFERENCES:
            del WEAK_REFERENCES[name]
        logger.debug(f"Unregistered object '{name}' from cleanup")
        return True
    return False

def _cleanup_callback(name: str):
    """Callback when a registered object is garbage collected"""
    if name in MEMORY_REGISTRY:
        del MEMORY_REGISTRY[name]
    logger.debug(f"Object '{name}' was garbage collected")

def force_garbage_collection() -> Dict[str, Any]:
    """Force garbage collection and return statistics"""
    try:
        # Get memory usage before GC
        before_stats = get_memory_usage()
        
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory usage after GC
        after_stats = get_memory_usage()
        
        return {
            "collected_objects": collected,
            "before": before_stats,
            "after": after_stats,
            "freed_mb": before_stats.get("rss_mb", 0) - after_stats.get("rss_mb", 0)
        }
    except Exception as e:
        logger.warning(f"Error during garbage collection: {e}")
        return {"error": str(e)}

def cleanup_large_objects() -> Dict[str, Any]:
    """Clean up large objects and return statistics"""
    try:
        # Get memory usage before cleanup
        before_stats = get_memory_usage()
        
        # Clear large objects from registry
        large_objects = []
        for name, obj in list(MEMORY_REGISTRY.items()):
            if hasattr(obj, '__sizeof__'):
                size = obj.__sizeof__()
                if size > 1024 * 1024:  # 1MB threshold
                    large_objects.append((name, size))
                    unregister_from_cleanup(name)
        
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory usage after cleanup
        after_stats = get_memory_usage()
        
        return {
            "large_objects_cleaned": len(large_objects),
            "large_objects_details": large_objects,
            "collected_objects": collected,
            "before": before_stats,
            "after": after_stats,
            "freed_mb": before_stats.get("rss_mb", 0) - after_stats.get("rss_mb", 0)
        }
    except Exception as e:
        logger.warning(f"Error during large object cleanup: {e}")
        return {"error": str(e)}

def get_memory_registry_stats() -> Dict[str, Any]:
    """Get statistics about registered objects"""
    try:
        total_size = 0
        object_types = {}
        
        for name, obj in MEMORY_REGISTRY.items():
            obj_type = type(obj).__name__
            object_types[obj_type] = object_types.get(obj_type, 0) + 1
            
            if hasattr(obj, '__sizeof__'):
                total_size += obj.__sizeof__()
        
        return {
            "total_objects": len(MEMORY_REGISTRY),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / 1024 / 1024,
            "object_types": object_types
        }
    except Exception as e:
        logger.warning(f"Error getting memory registry stats: {e}")
        return {"error": str(e)}

def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters: <>:"/\\|?* and normalize"""
    if not name:
        return "untitled"
    
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure it's not empty after sanitization
    if not sanitized:
        return "untitled"
    
    # Limit length to prevent filesystem issues
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized

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
        # Convert /C:/path to C:/path (Windows absolute path)
        if len(path) > 2 and path[1] == ':' and path[2] == '/':
            path = path[1:]
        # Convert /path to path (relative path)
        elif len(path) > 1:
            path = path[1:]
    
    # Handle Windows paths that might have backslashes converted to forward slashes
    if os.name == 'nt' and ':' in path and path.count(':') == 1:
        # This looks like a Windows path, ensure proper format
        drive_part, rest = path.split(':', 1)
        if rest.startswith('/'):
            # Convert C:/path to C:\path
            path = drive_part + ':' + rest.replace('/', '\\')
    
    # Normalize the path
    return os.path.normpath(path)

def validate_file_path(path: str, file_type: str = None) -> tuple[bool, str]:
    """Validate file path and return (is_valid, error_message)"""
    if not path:
        return False, "File path is empty."
    
    # Clean the path first
    cleaned_path = clean_file_path(path)
    
    # Check if file exists
    if not os.path.exists(cleaned_path):
        return False, f"File does not exist: {cleaned_path}"
    
    # Check if it's actually a file (not a directory)
    if not os.path.isfile(cleaned_path):
        return False, f"Path is not a file: {cleaned_path}"
    
    # Check if file is readable
    if not os.access(cleaned_path, os.R_OK):
        return False, f"No permission to read file: {cleaned_path}"
    
    # Check file size (prevent processing empty or extremely large files)
    try:
        file_size = os.path.getsize(cleaned_path)
        if file_size == 0:
            return False, f"File is empty: {cleaned_path}"
        if file_size > 1024 * 1024 * 1024:  # 1GB limit
            return False, f"File is too large (>1GB): {cleaned_path}"
    except OSError:
        return False, f"Cannot access file size: {cleaned_path}"
    
    # Validate file type if specified
    if file_type:
        if file_type == "audio" and not is_audio_file(cleaned_path):
            return False, f"File is not a valid audio file: {cleaned_path}"
        elif file_type == "image" and not is_image_file(cleaned_path):
            return False, f"File is not a valid image file: {cleaned_path}"
        elif file_type == "video" and not is_video_file(cleaned_path):
            return False, f"File is not a valid video file: {cleaned_path}"
        elif file_type == "overlay" and not is_overlay_file(cleaned_path):
            return False, f"File is not a valid overlay file: {cleaned_path}"
    
    return True, ""

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

def is_overlay_file(filename: str) -> bool:
    """Check if a file is a valid overlay file (image or video)"""
    return is_image_file(filename) or is_video_file(filename)

def is_video_valid(path):
    """Check if a video file is valid using ffprobe"""
    try:
        import subprocess
        result = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', path], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

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

def validate_numeric_input(value: str, min_val: int = None, max_val: int = None, 
                          allow_float: bool = False) -> tuple[bool, str, float]:
    """Validate numeric input and return (is_valid, error_message, numeric_value)"""
    if not value:
        return False, "Value is empty.", 0
    
    try:
        if allow_float:
            num_val = float(value)
        else:
            num_val = int(value)
    except ValueError:
        return False, f"Value '{value}' is not a valid number.", 0
    
    # Check bounds if specified
    if min_val is not None and num_val < min_val:
        return False, f"Value must be at least {min_val}.", 0
    
    if max_val is not None and num_val > max_val:
        return False, f"Value must be at most {max_val}.", 0
    
    return True, "", num_val

def validate_inputs(media_sources: str, export_name: str, number: str) -> tuple[bool, str]:
    """Validate user inputs and return (is_valid, error_message)"""
    import os
    
    # Check media_sources is not empty and is a valid directory
    if not media_sources:
        return False, "Please select the media folder."
    
    if not os.path.isdir(media_sources):
        return False, f"Media folder does not exist: {media_sources}"
    
    # Check if directory is readable
    if not os.access(media_sources, os.R_OK):
        return False, f"No permission to read media folder: {media_sources}"
    
    # Check export_name is not empty and is a valid filename
    if not export_name:
        return False, "Please enter an export name."
    
    # Sanitize and validate export name
    sanitized_name = sanitize_filename(export_name)
    if sanitized_name == "untitled" and export_name.strip():
        return False, "Export name contains only invalid characters."
    
    # Check for path separators
    if any(sep in export_name for sep in (os.sep, os.altsep) if sep):
        return False, "Export name cannot contain path separators."
    
    # Check for reserved filenames (Windows)
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                     'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                     'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    if sanitized_name.upper() in reserved_names:
        return False, f"Export name '{sanitized_name}' is a reserved system name."
    
    # Check number is a positive integer with reasonable bounds
    if not number:
        return False, "Please enter a number."
    
    try:
        num = int(number)
        if num <= 0:
            return False, "Number must be a positive integer."
        if num > 999999:
            return False, "Number must be less than 1,000,000."
    except ValueError:
        return False, "Number must be a valid integer."
    
    return True, ""

def is_image_valid(path):
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False

def is_mp3_valid(path):
    try:
        MP3(path)
        return True
    except Exception:
        return False

def validate_media_files(media_sources: str, min_mp3_count: int = 3) -> tuple[bool, str, list, list]:
    """Validate media files and return (is_valid, error_message, mp3_files, image_files)"""
    import os
    
    # Validate media sources directory
    if not os.path.exists(media_sources):
        return False, f"Media sources directory does not exist: {media_sources}", [], []
    
    if not os.path.isdir(media_sources):
        return False, f"Media sources path is not a directory: {media_sources}", [], []
    
    if not os.access(media_sources, os.R_OK):
        return False, f"No permission to read media sources directory: {media_sources}", [], []
    
    # Get files by type
    mp3_files = get_files_by_type(media_sources, "audio")
    image_files = get_files_by_type(media_sources, "image")
    
    # Validate minimum count
    if min_mp3_count < 1:
        return False, "Minimum MP3 count must be at least 1.", [], []
    
    # Filter out corrupt files and validate each file
    valid_mp3s = []
    invalid_mp3s = []
    
    for mp3_file in mp3_files:
        is_valid, error_msg = validate_file_path(mp3_file, "audio")
        if is_valid and is_mp3_valid(mp3_file):
            valid_mp3s.append(mp3_file)
        else:
            invalid_mp3s.append(mp3_file)
    
    valid_images = []
    invalid_images = []
    
    for image_file in image_files:
        is_valid, error_msg = validate_file_path(image_file, "image")
        if is_valid and is_image_valid(image_file):
            valid_images.append(image_file)
        else:
            invalid_images.append(image_file)
    
    # Check for valid images
    if not valid_images:
        if invalid_images:
            return False, f"No valid image files found. {len(invalid_images)} invalid/corrupt image files detected.", [], []
        else:
            return False, "No image files found in the media folder.", [], []
    
    # Check for valid MP3s
    if not valid_mp3s:
        if invalid_mp3s:
            return False, f"No valid MP3 files found. {len(invalid_mp3s)} invalid/corrupt MP3 files detected.", [], []
        else:
            return False, "No MP3 files found in the media folder.", [], []
    
    if len(valid_mp3s) < min_mp3_count:
        return False, f"Not enough valid MP3 files in folder (need at least {min_mp3_count}, found {len(valid_mp3s)})", [], []
    
    return True, "", valid_mp3s, valid_images

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

def create_song_title_png(title, output_path, width=400, height=40, font_size=12, font_name="default", color=(255, 255, 255), bg="transparent", bg_color=(0, 0, 0), opacity=1.0, text_effect="none", text_effect_color=(0, 0, 0), text_effect_intensity=20, bottom_padding=0):
    """
    Create a PNG image with the song title text at the top-left, with optional extra transparent space at the bottom.
    Args:
        title (str): The song title to render.
        output_path (str): Where to save the PNG.
        width (int): Width of the image.
        height (int): Height of the image (text area only; total image will be height+bottom_padding).
        font_size (int): Font size for the title.
        font_name (str): Font filename or "default" for system font.
        color (tuple): RGB color tuple for the text.
        bg (str): Background type ("transparent", "black", "white", "custom")
        bg_color (tuple): RGB color tuple for custom background.
        opacity (float): Opacity value (0.0 to 1.0).
        text_effect (str): Text effect type ("none", "outline", "outward_stroke", "inward_stroke", "shadow", "glow")
        text_effect_color (tuple): RGB color tuple for text effect.
        text_effect_intensity (int): Intensity of the text effect (0-100).
        bottom_padding (int): Extra transparent pixels to add at the bottom.
    """
    from src.config import PROJECT_ROOT
    
    # Register for memory management
    img_name = register_for_cleanup(None, f"song_title_img_{id(title)}")
    
    try:
        total_height = height + bottom_padding
        # Create image with background
        if bg == "transparent":
            img = Image.new('RGBA', (width, total_height), (0, 0, 0, 0))
        elif bg == "black":
            img = Image.new('RGBA', (width, total_height), (0, 0, 0, int(255 * opacity)))
        elif bg == "white":
            img = Image.new('RGBA', (width, total_height), (255, 255, 255, int(255 * opacity)))
        elif bg == "custom":
            img = Image.new('RGBA', (width, total_height), (*bg_color, int(255 * opacity)))
        else:
            img = Image.new('RGBA', (width, total_height), (0, 0, 0, 0))
        
        # Register the image for cleanup
        register_for_cleanup(img, img_name)
        
        draw = ImageDraw.Draw(img)
        font = None
        if font_name != "default":
            try:
                font_path = os.path.join(PROJECT_ROOT, "src", "sources", "font", font_name)
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    logger.warning(f"Font file not found: {font_path}")
            except Exception as e:
                logger.warning(f"Failed to load custom font {font_name}: {e}")
        if font is None:
            try:
                # Try to use KantumruyPro as fallback for better Khmer support
                fallback_font_path = os.path.join(PROJECT_ROOT, "src", "sources", "font", "KantumruyPro-VariableFont_wght.ttf")
                if os.path.exists(fallback_font_path):
                    font = ImageFont.truetype(fallback_font_path, font_size)
                else:
                    font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
        # Calculate text position (centered in the original area, not including padding)
        try:
            text_x, text_y = width // 2, height // 2
            anchor = 'mm'
        except TypeError:
            text_bbox = draw.textbbox((0, 0), title, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2
            anchor = None
        # Apply text effects
        if text_effect != "none":
            effect_intensity = max(1, text_effect_intensity // 10)
            if text_effect == "outline":
                for dx in range(-effect_intensity, effect_intensity + 1):
                    for dy in range(-effect_intensity, effect_intensity + 1):
                        if dx != 0 or dy != 0:
                            if anchor:
                                draw.text((text_x + dx, text_y + dy), title, font=font, fill=(*text_effect_color, 255), anchor=anchor)
                            else:
                                draw.text((text_x + dx, text_y + dy), title, font=font, fill=(*text_effect_color, 255))
            elif text_effect == "outward_stroke":
                for dx in range(-effect_intensity * 2, effect_intensity * 2 + 1):
                    for dy in range(-effect_intensity * 2, effect_intensity * 2 + 1):
                        if anchor:
                            draw.text((text_x + dx, text_y + dy), title, font=font, fill=(*text_effect_color, 255), anchor=anchor)
                        else:
                            draw.text((text_x + dx, text_y + dy), title, font=font, fill=(*text_effect_color, 255))
            elif text_effect == "inward_stroke":
                for dx in range(-effect_intensity // 2, effect_intensity // 2 + 1):
                    for dy in range(-effect_intensity // 2, effect_intensity // 2 + 1):
                        if anchor:
                            draw.text((text_x + dx, text_y + dy), title, font=font, fill=(*text_effect_color, 255), anchor=anchor)
                        else:
                            draw.text((text_x + dx, text_y + dy), title, font=font, fill=(*text_effect_color, 255))
            elif text_effect == "shadow":
                shadow_x = text_x + effect_intensity
                shadow_y = text_y + effect_intensity
                if anchor:
                    draw.text((shadow_x, shadow_y), title, font=font, fill=(*text_effect_color, 128), anchor=anchor)
                else:
                    draw.text((shadow_x, shadow_y), title, font=font, fill=(*text_effect_color, 128))
            elif text_effect == "glow":
                for i in range(effect_intensity, 0, -1):
                    opacity_factor = 255 // (effect_intensity + 1) * i
                    glow_color = (*text_effect_color, opacity_factor)
                    for dx in range(-i, i + 1):
                        for dy in range(-i, i + 1):
                            if anchor:
                                draw.text((text_x + dx, text_y + dy), title, font=font, fill=glow_color, anchor=anchor)
                            else:
                                draw.text((text_x + dx, text_y + dy), title, font=font, fill=glow_color)
        # Draw main text
        if anchor:
            draw.text((text_x, text_y), title, font=font, fill=(*color, 255), anchor=anchor)
        else:
            draw.text((text_x, text_y), title, font=font, fill=(*color, 255))
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"Error creating song title image: {e}")
        raise
    finally:
        # Ensure cleanup
        unregister_from_cleanup(img_name)

# Register cleanup function to run at exit
atexit.register(cleanup_temp_files)

def merge_images_with_position(background_path, overlay_path, output_path, position="bottom_center", overlay_size_percent=100):
    """
    Merge two images with the overlay positioned according to the position parameter.
    
    Args:
        background_path (str): Path to the background image
        overlay_path (str): Path to the overlay image
        output_path (str): Path where the merged image will be saved
        position (str): Position of overlay ("bottom_center", "bottom_left", "bottom_right", "top_center", "top_left", "top_right")
        overlay_size_percent (int): Size of overlay as percentage of background (1-100)
    """
    from PIL import Image
    
    # Open images
    with Image.open(background_path) as bg_img:
        with Image.open(overlay_path) as overlay_img:
            # Convert to RGBA if needed
            if bg_img.mode != 'RGBA':
                bg_img = bg_img.convert('RGBA')
            if overlay_img.mode != 'RGBA':
                overlay_img = overlay_img.convert('RGBA')
            
            bg_width, bg_height = bg_img.size
            overlay_width, overlay_height = overlay_img.size
            
            # Special scaling for framebox caption PNG mode
            # If PNG width is larger than background height, scale PNG width to match background height
            # and scale PNG height proportionally based on the width decrease
            if overlay_width > bg_height:
                # Calculate the scale factor to make PNG width equal to background height
                scale_factor = bg_height / overlay_width
                new_width = int(overlay_width * scale_factor)
                new_height = int(overlay_height * scale_factor)
                overlay_img = overlay_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                overlay_width, overlay_height = overlay_img.size
            # Regular percentage-based scaling (only if not already scaled by the special logic above)
            elif overlay_size_percent != 100:
                new_width = int(overlay_width * overlay_size_percent / 100)
                new_height = int(overlay_height * overlay_size_percent / 100)
                overlay_img = overlay_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                overlay_width, overlay_height = overlay_img.size
            
            # Calculate position with 10px spacing from edges to avoid cutoff
            spacing = 10
            if position == "bottom_center":
                x = (bg_width - overlay_width) // 2
                y = bg_height - overlay_height - spacing
            elif position == "bottom_left":
                x = spacing
                y = bg_height - overlay_height - spacing
            elif position == "bottom_right":
                x = bg_width - overlay_width - spacing
                y = bg_height - overlay_height - spacing
            elif position == "top_center":
                x = (bg_width - overlay_width) // 2
                y = spacing
            elif position == "top_left":
                x = spacing
                y = spacing
            elif position == "top_right":
                x = bg_width - overlay_width - spacing
                y = spacing
            else:  # Default to bottom_center
                x = (bg_width - overlay_width) // 2
                y = bg_height - overlay_height - spacing
            
            # Create new image with background
            result = Image.new('RGBA', (bg_width, bg_height), (0, 0, 0, 0))
            result.paste(bg_img, (0, 0))
            
            # Paste overlay at calculated position
            result.paste(overlay_img, (x, y), overlay_img)
            
            # Save result
            result.save(output_path, 'PNG') 

def extract_mp3_cover_with_ffmpeg(mp3_path, output_path):
    """
    Extract cover image from MP3 file using FFmpeg directly.
    This is much faster than using mutagen for metadata extraction.
    
    Args:
        mp3_path: Path to the MP3 file
        output_path: Where to save the extracted cover image
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from src.config import FFMPEG_BINARY
        import subprocess
        
        # Try different stream mappings as cover art can be at different indexes
        stream_mappings = ["0:v:0", "0:1", "0:2", "0:v"]
        
        for stream_map in stream_mappings:
            # Use FFmpeg to extract the cover image
            # Try different stream mappings to find the cover art
            cmd = [
                FFMPEG_BINARY,
                "-i", mp3_path,
                "-map", stream_map,
                "-c", "copy",
                output_path,
                "-y"  # Overwrite output file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check if file was actually created and has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
            
        # If all mappings failed, log the last error
        logger.debug(f"FFmpeg failed to extract cover from {mp3_path} with all stream mappings")
        return False
            
    except Exception as e:
        logger.debug(f"Failed to extract cover with FFmpeg from {mp3_path}: {e}")
        return False

def extract_mp3_cover_image(mp3_path):
    """
    Extract cover image from MP3 file's metadata using FFmpeg (optimized version).
    Returns the image data as bytes, or None if not found.
    """
    temp_cover_path = None
    try:
        # Create a temporary file for FFmpeg extraction
        temp_cover_path = create_temp_file(suffix='.png', prefix='mp3cover_')
        
        # Try FFmpeg extraction first (faster)
        if extract_mp3_cover_with_ffmpeg(mp3_path, temp_cover_path):
            # Read the extracted file as bytes
            with open(temp_cover_path, 'rb') as f:
                cover_data = f.read()
            return cover_data
        else:
            # Fallback to mutagen if FFmpeg fails
            try:
                audio = MP3(mp3_path, ID3=ID3)
                
                # Look for attached picture frames
                if audio.tags:
                    for key in audio.tags:
                        if key.startswith('APIC'):
                            apic = audio.tags[key]
                            if hasattr(apic, 'data') and apic.data:
                                return apic.data
                        
            except Exception as e:
                logger.debug(f"Mutagen fallback failed for {mp3_path}: {e}")
            
            return None
            
    except Exception as e:
        logger.debug(f"Failed to extract cover from {mp3_path}: {e}")
        return None
    finally:
        # Ensure temp file is cleaned up if it exists
        # Note: create_temp_file already registers files for cleanup, but this is extra safety
        if temp_cover_path and os.path.exists(temp_cover_path):
            try:
                os.unlink(temp_cover_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"Failed to remove temporary cover file: {e}")

def create_framed_cover_image(cover_data_or_path, output_path, frame_width=10, frame_color=(255, 255, 255)):
    """
    Create a PNG image with a colored frame overlaid on the cover image.
    The frame overlays on top of the cover, cutting off edges based on frame size.
    
    Args:
        cover_data_or_path: Either bytes (cover image data) or str (path to default image)
        output_path: Where to save the framed PNG
        frame_width: Width of the frame in pixels (default 10px)
        frame_color: RGB tuple for frame color (default white)
    """
    try:
        # Load the image using context manager
        if isinstance(cover_data_or_path, bytes):
            # Cover image from MP3 metadata
            from io import BytesIO
            with Image.open(BytesIO(cover_data_or_path)) as img:
                # Convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Keep original size - frame will overlay on top
                original_width, original_height = img.size
                
                # Create a copy of the original image to work with
                framed_img = img.copy()
        else:
            # Default cover image from file path
            with Image.open(cover_data_or_path) as img:
                # Convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Keep original size - frame will overlay on top
                original_width, original_height = img.size
                
                # Create a copy of the original image to work with
                framed_img = img.copy()
        
        # Create a drawing context to draw the frame overlay
        draw = ImageDraw.Draw(framed_img)
        
        # Draw frame borders as overlay (cutting into the image)
        frame_color_with_alpha = (*frame_color, 255)
        
        # Top border
        if frame_width > 0:
            draw.rectangle([0, 0, original_width-1, frame_width-1], fill=frame_color_with_alpha)
        
        # Bottom border  
        if frame_width > 0:
            draw.rectangle([0, original_height-frame_width, original_width-1, original_height-1], fill=frame_color_with_alpha)
        
        # Left border
        if frame_width > 0:
            draw.rectangle([0, frame_width, frame_width-1, original_height-frame_width-1], fill=frame_color_with_alpha)
        
        # Right border
        if frame_width > 0:
            draw.rectangle([original_width-frame_width, frame_width, original_width-1, original_height-frame_width-1], fill=frame_color_with_alpha)
        
        # Save as PNG
        framed_img.save(output_path, 'PNG')
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create framed cover image: {e}")
        return False

def extract_and_frame_mp3_cover(mp3_path, output_path, default_cover_path="src/sources/mp3cover/mp3cover.png", frame_width=10, frame_color=(255, 255, 255)):
    """
    Extract cover image from MP3 file using optimized FFmpeg method and create a framed version.
    If no cover exists in MP3, use the default cover image.
    
    Args:
        mp3_path: Path to the MP3 file
        output_path: Where to save the framed cover PNG
        default_cover_path: Path to default cover image if MP3 has no cover
        frame_width: Width of the frame in pixels
        frame_color: RGB tuple for frame color
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Try to extract cover from MP3 using optimized FFmpeg method
    cover_data = extract_mp3_cover_image(mp3_path)
    
    if cover_data:
        # Use extracted cover
        return create_framed_cover_image(cover_data, output_path, frame_width, frame_color)
    else:
        # Use default cover if exists
        if os.path.exists(default_cover_path):
            return create_framed_cover_image(default_cover_path, output_path, frame_width, frame_color)
        else:
            logger.warning(f"No cover found in MP3 and default cover not found at {default_cover_path}")
            return False

def preprocess_background_image(image_path: str, resolution: str, scale_percent: int = 103, crop_position: str = "center", effect: str = "none", intensity: int = 50) -> str:
    """
    Preprocess background image with advanced scaling and cropping.
    
    Args:
        image_path: Path to the original background image
        resolution: Target resolution (e.g., "1920x1080")
        scale_percent: Scale percentage (default 103 for 103%)
        crop_position: Crop position ("center", "left", "right", "top", "bottom", "top_left", "top_right", "bottom_left", "bottom_right")
        effect: Background effect ("none", "gaussian_blur", "sharpen", "vignette")
        intensity: Effect intensity (0-100)
    
    Returns:
        Path to the processed temporary image file
    """
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Parse target resolution
        target_width, target_height = map(int, resolution.split('x'))
        
        # Calculate scaled dimensions
        scale_factor = scale_percent / 100.0
        scaled_width = int(target_width * scale_factor)
        scaled_height = int(target_height * scale_factor)
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        # Calculate crop x/y offsets based on position
        if crop_position == "center":
            crop_x = f"(in_w-out_w)/2"
            crop_y = f"(in_h-out_h)/2"
        elif crop_position == "left":
            crop_x = "0"
            crop_y = f"(in_h-out_h)/2"
        elif crop_position == "right":
            crop_x = f"in_w-out_w"
            crop_y = f"(in_h-out_h)/2"
        elif crop_position == "top":
            crop_x = f"(in_w-out_w)/2"
            crop_y = "0"
        elif crop_position == "bottom":
            crop_x = f"(in_w-out_w)/2"
            crop_y = f"in_h-out_h"
        elif crop_position == "top_left":
            crop_x = "0"
            crop_y = "0"
        elif crop_position == "top_right":
            crop_x = f"in_w-out_w"
            crop_y = "0"
        elif crop_position == "bottom_left":
            crop_x = "0"
            crop_y = f"in_h-out_h"
        elif crop_position == "bottom_right":
            crop_x = f"in_w-out_w"
            crop_y = f"in_h-out_h"
        else:
            # Default to center
            crop_x = f"(in_w-out_w)/2"
            crop_y = f"(in_h-out_h)/2"
        
        # Build filter string
        filter_str = f"scale={scaled_width}:{scaled_height}:flags=lanczos,crop={target_width}:{target_height}:{crop_x}:{crop_y}"
        
        # Add effect filters if specified
        if effect != "none":
            intensity_factor = intensity / 100.0
            if effect == "gaussian_blur":
                sigma = intensity_factor * 10  # 0-10 range
                filter_str += f",gblur=sigma={sigma:.2f}"
            elif effect == "sharpen":
                amount = intensity_factor * 2  # 0-2 range
                filter_str += f",unsharp=3:3:1.5:3:3:{amount:.2f}"
            elif effect == "vignette":
                filter_str += f",vignette={intensity_factor:.2f}"
        
        # Use FFmpeg for scaling, cropping, and effects
        cmd = [
            FFMPEG_BINARY,
            '-y',  # Overwrite output file
            '-i', image_path,
            '-vf', filter_str,
            temp_processed_path
        ]
        
        # Execute FFmpeg command
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg preprocessing failed: {result.stderr}")
            # Fallback to original image
            return image_path
        
        logger.info(f"Background image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing background image: {e}")
        # Fallback to original image
        return image_path

def preprocess_overlay1_image(image_path: str, size_percent: int = 100) -> str:
    """
    Preprocess overlay1 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay1 file
        size_percent: Scale percentage (default 100 for 100%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay1 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay1 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay1 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay1 image: {e}")
        # Fallback to original image
        return image_path

def preprocess_overlay2_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay2 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay2 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay2 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay2 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay2 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay2 image: {e}")
        # Fallback to original image
        return image_path


def preprocess_overlay3_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay3 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay3 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay3 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay3 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay3 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay3 image: {e}")
        # Fallback to original image
        return image_path


def preprocess_overlay4_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay4 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay4 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay4 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay4 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay4 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay4 image: {e}")
        # Fallback to original image
        return image_path


def preprocess_overlay5_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay5 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay5 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay5 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay5 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay5 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay5 image: {e}")
        # Fallback to original image
        return image_path


def preprocess_overlay6_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay6 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay6 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay6 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay6 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay6 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay6 image: {e}")
        # Fallback to original image
        return image_path


def preprocess_overlay7_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay7 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay7 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay7 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay7 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay7 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay7 image: {e}")
        # Fallback to original image
        return image_path


def preprocess_intro_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess intro image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original intro file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Intro video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg intro preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Intro image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing intro image: {e}")
        # Fallback to original image
        return image_path

def preprocess_overlay8_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay8 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay8 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay8 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay8 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay8 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay8 image: {e}")
        # Fallback to original image
        return image_path


def preprocess_overlay9_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay9 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay9 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay9 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay9 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay9 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay9 image: {e}")
        # Fallback to original image
        return image_path


def preprocess_framebox_image(image_path: str, size_percent: int = 50) -> str:
    """
    Preprocess framebox image with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG/JPEG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original framebox file
        size_percent: Scale percentage (default 50 for 50%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Framebox video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG/JPEG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg framebox preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Framebox image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing framebox image: {e}")
        # Fallback to original image
        return image_path


def preprocess_frame_mp3cover_image(image_path: str, size_percent: int = 50) -> str:
    """
    Preprocess frame_mp3cover image with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG/JPEG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original frame_mp3cover file
        size_percent: Scale percentage (default 50 for 50%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Frame_mp3cover video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG/JPEG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg frame_mp3cover preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Frame_mp3cover image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing frame_mp3cover image: {e}")
        # Fallback to original image
        return image_path


def preprocess_overlay10_image(image_path: str, size_percent: int = 10) -> str:
    """
    Preprocess overlay10 image/video with advanced scaling.
    For GIF files: No preprocessing, handled directly by FFmpeg.
    For video files: No preprocessing, handled directly by FFmpeg.
    For static images (PNG/JPG): Scale with high quality Lanczos filtering.
    
    Args:
        image_path: Path to the original overlay10 file
        size_percent: Scale percentage (default 10 for 10%)
    
    Returns:
        Path to the processed temporary file or original path if no preprocessing
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = size_percent / 100.0
        
        # Check file type
        file_ext = os.path.splitext(image_path)[1].lower()
        is_gif = file_ext == '.gif'
        is_video = file_ext in ['.mp4', '.mov', '.mkv']
        is_image = file_ext in ['.png', '.jpg', '.jpeg']
        
        # For video files, don't preprocess - let FFmpeg handle scaling
        if is_video:
            logger.info(f"Overlay10 video file detected: {os.path.basename(image_path)} - using original path")
            return image_path
        
        # Create temporary file for processed image
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        if is_gif:
            # GIFs are no longer preprocessed - return original path for FFmpeg to handle directly
            logger.info(f"GIF file detected: {os.path.basename(image_path)} - skipping preprocessing, will be handled directly by FFmpeg")
            return image_path
        else:
            # Regular scaling for PNG/JPG files
            filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
            
            cmd = [
                FFMPEG_BINARY,
                '-y',  # Overwrite output file
                '-i', image_path,
                '-vf', filter_str,
                temp_processed_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg overlay10 preprocessing failed: {result.stderr}")
                # Fallback to original image
                return image_path
        
        logger.info(f"Overlay10 image preprocessed: {os.path.basename(image_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing overlay10 image: {e}")
        # Fallback to original image
        return image_path

def preprocess_song_title_png(png_path: str, scale_percent: int = 100) -> str:
    """
    Preprocess song title PNG with scaling only (like other overlays).
    For PNG files: Scale with high quality Lanczos filtering.
    
    Args:
        png_path: Path to the original song title PNG (has supercut_ prefix)
        scale_percent: Scale percentage (default 100 for 100%)
    
    Returns:
        Path to the processed temporary PNG file (with supercut_ prefix for cleanup)
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = scale_percent / 100.0
        
        # No scaling needed
        if scale_factor == 1.0:
            return png_path
        
        # Create temporary file for processed image with supercut_ prefix
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        # Simple scaling with Lanczos (like other overlays)
        filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
        
        # Run FFmpeg
        cmd = [
            FFMPEG_BINARY,
            '-y',  # Overwrite output file
            '-i', png_path,
            '-vf', filter_str,
            temp_processed_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Song title preprocessing failed: {result.stderr}")
            return png_path  # Fallback to original
        
        logger.info(f"Song title preprocessed: {os.path.basename(png_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing song title PNG: {e}")
        return png_path  # Fallback to original

def preprocess_mp3_cover_png(png_path: str, scale_percent: int = 20) -> str:
    """
    Preprocess MP3 cover PNG with scaling only (like other overlays).
    For PNG files: Scale with high quality Lanczos filtering.
    
    Args:
        png_path: Path to the original MP3 cover PNG (has supercut_ prefix)
        scale_percent: Scale percentage (default 20 for 20%)
    
    Returns:
        Path to the processed temporary PNG file (with supercut_ prefix for cleanup)
    """
    try:
        import subprocess
        from src.config import FFMPEG_BINARY
        from src.logger import logger
        
        # Calculate scale factor
        scale_factor = scale_percent / 100.0
        
        # No scaling needed
        if scale_factor == 1.0:
            return png_path
        
        # Create temporary file for processed PNG
        temp_processed_path = create_temp_file(suffix='.png', prefix='supercut_')
        
        # Scale with high quality Lanczos filtering
        filter_str = f"scale=iw*{scale_factor:.3f}:ih*{scale_factor:.3f}:flags=lanczos"
        
        cmd = [
            FFMPEG_BINARY,
            '-y',  # Overwrite output file
            '-i', png_path,
            '-vf', filter_str,
            temp_processed_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg MP3 cover preprocessing failed: {result.stderr}")
            # Fallback to original PNG
            return png_path
        
        logger.info(f"MP3 cover PNG preprocessed: {os.path.basename(png_path)} -> {os.path.basename(temp_processed_path)}")
        return temp_processed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing MP3 cover PNG: {e}")
        # Fallback to original PNG
        return png_path