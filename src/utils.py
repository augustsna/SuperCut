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
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
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
    mp3_files = get_files_by_type(media_sources, "audio")
    image_files = get_files_by_type(media_sources, "image")
    # Filter out corrupt files
    valid_mp3s = [f for f in mp3_files if is_mp3_valid(f)]
    valid_images = [f for f in image_files if is_image_valid(f)]
    if not valid_images:
        return False, "No valid (non-corrupt) image files found in the media folder.", [], []
    if not valid_mp3s or len(valid_mp3s) < min_mp3_count:
        return False, f"Not enough valid (non-corrupt) mp3 files in folder (need at least {min_mp3_count})", [], []
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
    img.save(output_path, 'PNG')

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

def extract_mp3_cover_image(mp3_path):
    """
    Extract cover image from MP3 file's metadata.
    Returns the image data as bytes, or None if not found.
    """
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
        logger.debug(f"Failed to extract cover from {mp3_path}: {e}")
    
    return None

def create_framed_cover_image(cover_data_or_path, output_path, frame_width=10, frame_color=(255, 255, 255)):
    """
    Create a PNG image with a colored frame around the cover image.
    
    Args:
        cover_data_or_path: Either bytes (cover image data) or str (path to default image)
        output_path: Where to save the framed PNG
        frame_width: Width of the frame in pixels (default 10px)
        frame_color: RGB tuple for frame color (default white)
    """
    try:
        # Load the image
        if isinstance(cover_data_or_path, bytes):
            # Cover image from MP3 metadata
            from io import BytesIO
            img = Image.open(BytesIO(cover_data_or_path))
        else:
            # Default cover image from file path
            img = Image.open(cover_data_or_path)
        
        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Calculate new size with frame
        original_width, original_height = img.size
        new_width = original_width + (frame_width * 2)
        new_height = original_height + (frame_width * 2)
        
        # Create new image with colored background (frame)
        framed_img = Image.new('RGBA', (new_width, new_height), (*frame_color, 255))
        
        # Paste the original image centered in the frame
        framed_img.paste(img, (frame_width, frame_width), img if img.mode == 'RGBA' else None)
        
        # Save as PNG
        framed_img.save(output_path, 'PNG')
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create framed cover image: {e}")
        return False

def extract_and_frame_mp3_cover(mp3_path, output_path, default_cover_path="src/sources/mp3cover/mp3cover.png", frame_width=10, frame_color=(255, 255, 255)):
    """
    Extract cover image from MP3 file and create a framed version.
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
    # Try to extract cover from MP3
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