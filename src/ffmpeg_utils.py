# This file uses PyQt6
import os
import json
import subprocess
import tempfile
import time
import re
import sys
from typing import Optional, List, Tuple
from src.config import FFMPEG_BINARY, FFPROBE_BINARY, VIDEO_SETTINGS
from src.logger import logger
from src.utils import has_enough_disk_space, create_temp_file

def get_audio_duration(file_path: str) -> float:
    """Get audio duration using ffprobe"""
    try:
        cmd = [
            FFPROBE_BINARY,
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Error getting duration for {file_path}: {e}")
        return 0.0

def merge_mp3s_with_ffmpeg(input_files: list, output_file: str) -> bool:
    """Merge multiple MP3 files using ffmpeg and convert to AAC/M4A format"""
    try:
        # Create a file list for ffmpeg
        file_list_path = create_temp_file(suffix='.txt')
        with open(file_list_path, 'w') as f:
            for file_path in input_files:
                f.write(f"file '{file_path}'\n")
        
        # Use ffmpeg to concatenate and convert to AAC
        cmd = [
            FFMPEG_BINARY,
            "-f", "concat",
            "-safe", "0",
            "-i", file_list_path,
            "-c:a", "aac",        # Convert to AAC codec
            "-b:a", "384k",       # High quality bitrate matching video settings
            output_file,
            "-y"  # Overwrite output file
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Clean up file list
        if file_list_path and os.path.exists(file_list_path):
            try:
                os.unlink(file_list_path)
            except FileNotFoundError:
                logger.warning(f"Temp file list {file_list_path} not found for removal.")
            except PermissionError:
                logger.warning(f"No permission to remove temp file list {file_list_path}.")
            except OSError as e:
                logger.warning(f"OS error removing temp file list {file_list_path}: {e}")
        return True
    except (subprocess.CalledProcessError, OSError, ValueError) as e:
        logger.error(f"Error merging MP3s: {e}")
        return False

def create_video_with_ffmpeg( # pyright: ignore[reportGeneralTypeIssues]
    image_path: str, 
    audio_path: str, 
    output_path: str, 
    resolution: str, 
    fps: int, 
    codec: str,
    use_overlay: bool = False,
    overlay1_path: str = "",
    overlay1_size_percent: int = 100,
    overlay1_x_percent: int = 0,
    overlay1_y_percent: int = 75,
    use_overlay2: bool = False,
    overlay2_path: str = "",
    overlay2_size_percent: int = 10,
    overlay2_x_percent: int = 75,
    overlay2_y_percent: int = 0,
    use_overlay3: bool = False,
    overlay3_path: str = "",
    overlay3_size_percent: int = 10,
    overlay3_x_percent: int = 75,
    overlay3_y_percent: int = 0,
    use_overlay4: bool = False,
    overlay4_path: str = "",
    overlay4_size_percent: int = 10,
    overlay4_x_percent: int = 75,
    overlay4_y_percent: int = 0,
    use_overlay5: bool = False,
    overlay5_path: str = "",
    overlay5_size_percent: int = 10,
    overlay5_x_percent: int = 75,
    overlay5_y_percent: int = 0,
    use_overlay6: bool = False,
    overlay6_path: str = "",
    overlay6_size_percent: int = 10,
    overlay6_x_percent: int = 75,
    overlay6_y_percent: int = 0,
    use_overlay7: bool = False,
    overlay7_path: str = "",
    overlay7_size_percent: int = 10,
    overlay7_x_percent: int = 75,
    overlay7_y_percent: int = 0,
    use_overlay8: bool = False,
    overlay8_path: str = "",
    overlay8_size_percent: int = 10,
    overlay8_x_percent: int = 75,
    overlay8_y_percent: int = 0,
    use_overlay9: bool = False,
    overlay9_path: str = "",
    overlay9_size_percent: int = 10,
    overlay9_x_percent: int = 75,
    overlay9_y_percent: int = 0,
    use_overlay10: bool = False,
    overlay10_path: str = "",
    overlay10_size_percent: int = 10,
    overlay10_x_percent: int = 75,
    overlay10_y_percent: int = 0,
    use_intro: bool = False,
    intro_path: str = "",
    intro_size_percent: int = 10,
    intro_x_percent: int = 50,
    intro_y_percent: int = 50,
    overlay1_2_effect: str = "fadein",
    overlay1_2_start_time: int = 5,
    overlay1_2_duration: int = 6,
    overlay1_2_duration_full_checkbox_checked: bool = False,
    intro_effect: str = "fadeout",
    intro_duration: int = 6,
    intro_start_at: int = 0,
    intro_duration_full_checkbox_checked: bool = False,
    preset: str = "slow",
    audio_bitrate: str = "384k",
    video_bitrate: str = "12M",
    maxrate: str = "16M",
    bufsize: str = "24M",
    extra_overlays: Optional[List[dict]] = None,  # List of dicts: {path, start, duration, x_percent, y_percent, size_percent, effect, type}
    song_title_effect: str = "fadeinout",
    song_title_font: str = "default",
    song_title_font_size: int = 32,
    song_title_color: tuple = (255, 255, 255),
    song_title_bg: str = "transparent",
    song_title_bg_color: tuple = (0, 0, 0),
    song_title_opacity: float = 1.0,
    song_title_scale_percent: int = 100,
    # --- Add song title text effect parameters ---
    song_title_text_effect: str = "none",
    song_title_text_effect_color: tuple = (0, 0, 0),
    song_title_text_effect_intensity: int = 20,
    overlay3_effect: str = "fadein",
    overlay3_start_time: int = 5,
    overlay4_effect: str = "fadein",
    overlay4_start_time: int = 5,
    overlay4_duration: int = 6,
    overlay4_duration_full_checkbox_checked: bool = False,
    overlay5_effect: str = "fadein",
    overlay5_start_time: int = 5,
    overlay5_duration: int = 6,
    overlay5_duration_full_checkbox_checked: bool = False,
    overlay6_effect: str = "fadein",
    overlay6_start_time: int = 5,
    overlay6_duration: int = 6,
    overlay6_duration_full_checkbox_checked: bool = False,
    overlay7_effect: str = "fadein",
    overlay7_start_time: int = 5,
    overlay7_duration: int = 6,
    overlay7_duration_full_checkbox_checked: bool = False,
    overlay8_effect: str = "fadein",
    overlay8_start_time: int = 5,
    overlay8_duration: int = 6,
    overlay8_duration_full_checkbox_checked: bool = False,
    overlay8_intervals: Optional[list] = None,  # NEW: list of (start, duration)
    overlay9_effect: str = "fadein",
    overlay9_start_time: int = 5,
    overlay9_duration: int = 6,
    overlay9_duration_full_checkbox_checked: bool = False,
    overlay9_intervals: Optional[list] = None,  # NEW: list of (start, duration)
    overlay10_effect: str = "fadein",
    overlay10_start_time: int = 5,
    overlay10_duration: int = 6,
    overlay10_start_time_percent: int = 0,
    overlay10_intervals: Optional[list] = None,  # NEW: list of (start, duration)
    # --- Add frame box parameters ---
    use_frame_box: bool = False,
    frame_box_path: str = "",
    frame_box_size_percent: int = 50,
    frame_box_x_percent: int = 0,
    frame_box_y_percent: int = 0,
    frame_box_effect: str = "fadein",
    frame_box_start_time: int = 5,
    frame_box_duration: int = 6,
    frame_box_duration_full_checkbox_checked: bool = True,
    frame_box_pad_left: int = 12,
    frame_box_pad_right: int = 12,
    frame_box_pad_top: int = 12,
    frame_box_pad_bottom: int = 12,
    # --- Add frame box custom image parameters ---
    use_frame_box_custom_image: bool = False,
    frame_box_custom_image_path: str = "",
    # --- Add frame mp3cover parameters ---
    use_frame_mp3cover: bool = False,
    frame_mp3cover_path: str = "",
    frame_mp3cover_size_percent: int = 50,
    frame_mp3cover_x_percent: int = 0,
    frame_mp3cover_y_percent: int = 0,
    frame_mp3cover_effect: str = "fadein",
    frame_mp3cover_start_time: int = 5,
    frame_mp3cover_duration: int = 6,
    frame_mp3cover_duration_full_checkbox_checked: bool = True,
    overlay1_start_at: int = 0,
    overlay2_start_at: int = 0,
    # --- Background layer parameters are now handled in advance during image preprocessing ---
    # --- Add soundwave overlay parameters ---
    use_soundwave_overlay: bool = False,
    soundwave_overlay_path: str = "",
    soundwave_size_percent: int = 50,
    soundwave_x_percent: int = 50,
    soundwave_y_percent: int = 50,
    # --- Add layer order parameter ---
    layer_order: Optional[List[str]] = None,
    # --- Add filter complex alt mode parameter ---
    filter_complex_alt_mode: bool = False
) -> Tuple[bool, Optional[str]]:
    temp_png_path = None
    try:
        # If input is JPG, convert to PNG using ffmpeg
        if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
            temp_png_path = create_temp_file(suffix='.png', prefix='supercut_')
            convert_cmd = [
                FFMPEG_BINARY,
                '-y',
                '-i', image_path,
                temp_png_path
            ]
            result = subprocess.run(convert_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                msg = f"Error converting JPG to PNG: {result.stderr}"
                logger.error(msg)
                return False, msg
            image_path_for_ffmpeg = temp_png_path
        else:
            image_path_for_ffmpeg = image_path

        # Accept PNG and GIF image files
        if not (image_path_for_ffmpeg.lower().endswith('.png') or image_path_for_ffmpeg.lower().endswith('.gif')):
            msg = f"Error: Only PNG and GIF image files are accepted. Provided: {image_path_for_ffmpeg}"
            logger.error(msg)
            return False, msg
        
        width, height = map(int, resolution.split('x'))
        
        # Build ffmpeg command with dynamic inputs
        cmd = [
            FFMPEG_BINARY,
            "-i", image_path_for_ffmpeg,
            "-i", audio_path
        ]
        
        # Add loop parameter based on image type
        if image_path_for_ffmpeg.lower().endswith('.gif'):
            cmd.insert(1, "-stream_loop")
            cmd.insert(2, "-1")
        else:
            cmd.insert(1, "-loop")
            cmd.insert(2, "1")
        ext1 = os.path.splitext(overlay1_path)[1].lower() if overlay1_path else ''
        ext2 = os.path.splitext(overlay2_path)[1].lower() if overlay2_path else ''
        ext3 = os.path.splitext(overlay3_path)[1].lower() if overlay3_path else ''
        ext4 = os.path.splitext(overlay4_path)[1].lower() if overlay4_path else ''
        ext5 = os.path.splitext(overlay5_path)[1].lower() if overlay5_path else ''
        ext6 = os.path.splitext(overlay6_path)[1].lower() if overlay6_path else ''
        ext7 = os.path.splitext(overlay7_path)[1].lower() if overlay7_path else ''
        ext8 = os.path.splitext(overlay8_path)[1].lower() if overlay8_path else ''
        ext9 = os.path.splitext(overlay9_path)[1].lower() if overlay9_path else ''
        ext10 = os.path.splitext(overlay10_path)[1].lower() if overlay10_path else ''
        ext_frame_box = os.path.splitext(frame_box_path)[1].lower() if frame_box_path else ''
        ext_frame_mp3cover = os.path.splitext(frame_mp3cover_path)[1].lower() if frame_mp3cover_path else ''
        ext_intro = os.path.splitext(intro_path)[1].lower() if intro_path else ''
        intro_idx = None
        overlay1_idx = None
        overlay2_idx = None
        overlay3_idx = None
        overlay4_idx = None
        overlay5_idx = None
        overlay6_idx = None
        overlay7_idx = None
        overlay8_idx = None
        overlay9_idx = None
        overlay10_idx = None
        frame_box_idx = None
        frame_mp3cover_idx = None
        input_idx = 2
        if use_intro and intro_path and ext_intro in ['.gif', '.png', '.mp4', '.mov', '.mkv']:
            if ext_intro == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", intro_path])
            elif ext_intro == '.png':
                cmd.extend(["-loop", "1", "-i", intro_path])
            elif ext_intro in ['.mp4', '.mov', '.mkv']:
                # For video files, loop infinitely and handle timing
                cmd.extend(["-stream_loop", "-1", "-i", intro_path])
            else:
                cmd.extend(["-i", intro_path])
            intro_idx = input_idx
            input_idx += 1
        if use_overlay and overlay1_path and ext1 in ['.gif', '.png', '.mp4', '.mov', '.mkv']:
            if ext1 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay1_path])
            elif ext1 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay1_path])
            elif ext1 in ['.mp4', '.mov', '.mkv']:
                # For MP4 overlays, start from the beginning at the overlay1_start_at time
                # Use -itsoffset to delay the overlay input
                cmd.extend(["-itsoffset", str(overlay1_start_at), "-stream_loop", "-1", "-i", overlay1_path])
            else:
                cmd.extend(["-i", overlay1_path])
            overlay1_idx = input_idx
            input_idx += 1
        if use_overlay2 and overlay2_path and ext2 in ['.gif', '.png', '.mp4', '.mov', '.mkv']:
            if ext2 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay2_path])
            elif ext2 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay2_path])
            elif ext2 in ['.mp4', '.mov', '.mkv']:
                # For video files, loop infinitely and handle timing
                cmd.extend(["-stream_loop", "-1", "-i", overlay2_path])
            else:
                cmd.extend(["-i", overlay2_path])
            overlay2_idx = input_idx
            input_idx += 1
        if use_overlay3 and overlay3_path and ext3 in ['.gif', '.png', '.jpg', '.jpeg', '.mp4', '.mov', '.mkv']:
            if ext3 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay3_path])
            elif ext3 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay3_path])
            elif ext3 in ['.mp4', '.mov', '.mkv']:
                # For video files, loop infinitely and handle timing
                cmd.extend(["-stream_loop", "-1", "-i", overlay3_path])
            else:
                cmd.extend(["-i", overlay3_path])
            overlay3_idx = input_idx
            input_idx += 1
        if use_overlay4 and overlay4_path and ext4 in ['.gif', '.png']:
            if ext4 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay4_path])
            elif ext4 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay4_path])
            else:
                cmd.extend(["-i", overlay4_path])
            overlay4_idx = input_idx
            input_idx += 1
        if use_overlay5 and overlay5_path and ext5 in ['.gif', '.png']:
            if ext5 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay5_path])
            elif ext5 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay5_path])
            else:
                cmd.extend(["-i", overlay5_path])
            overlay5_idx = input_idx
            input_idx += 1
        if use_overlay6 and overlay6_path and ext6 in ['.gif', '.png']:
            if ext6 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay6_path])
            elif ext6 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay6_path])
            else:
                cmd.extend(["-i", overlay6_path])
            overlay6_idx = input_idx
            input_idx += 1
        if use_overlay7 and overlay7_path and ext7 in ['.gif', '.png']:
            if ext7 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay7_path])
            elif ext7 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay7_path])
            else:
                cmd.extend(["-i", overlay7_path])
            overlay7_idx = input_idx
            input_idx += 1
        if use_overlay8 and overlay8_path and ext8 in ['.gif', '.png', '.mp4', '.mov', '.mkv']:
            if ext8 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay8_path])
            elif ext8 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay8_path])
            elif ext8 in ['.mp4', '.mov', '.mkv']:
                # For video files, loop infinitely and handle timing
                cmd.extend(["-stream_loop", "-1", "-i", overlay8_path])
            else:
                cmd.extend(["-i", overlay8_path])
            overlay8_idx = input_idx
            input_idx += 1
        if use_overlay9 and overlay9_path and ext9 in ['.gif', '.png', '.mp4', '.mov', '.mkv']:
            if ext9 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay9_path])
            elif ext9 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay9_path])
            elif ext9 in ['.mp4', '.mov', '.mkv']:
                # For video files, loop infinitely and handle timing
                cmd.extend(["-stream_loop", "-1", "-i", overlay9_path])
            else:
                cmd.extend(["-i", overlay9_path])
            overlay9_idx = input_idx
            input_idx += 1
        if use_overlay10 and overlay10_path and ext10 in ['.gif', '.png', '.mp4', '.mov', '.mkv']:
            if ext10 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay10_path])
            elif ext10 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay10_path])
            elif ext10 in ['.mp4', '.mov', '.mkv']:
                # For video files, loop infinitely and handle timing
                cmd.extend(["-stream_loop", "-1", "-i", overlay10_path])
            else:
                cmd.extend(["-i", overlay10_path])
            overlay10_idx = input_idx
            input_idx += 1
        if use_frame_box and frame_box_path and ext_frame_box in ['.gif', '.png']:
            if ext_frame_box == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", frame_box_path])
            elif ext_frame_box == '.png':
                cmd.extend(["-loop", "1", "-i", frame_box_path])
            else:
                cmd.extend(["-i", frame_box_path])
            frame_box_idx = input_idx
            input_idx += 1
        if use_frame_mp3cover and frame_mp3cover_path and ext_frame_mp3cover in ['.gif', '.png', '.mp4', '.mov', '.mkv']:
            if ext_frame_mp3cover == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", frame_mp3cover_path])
            elif ext_frame_mp3cover == '.png':
                cmd.extend(["-loop", "1", "-i", frame_mp3cover_path])
            elif ext_frame_mp3cover in ['.mp4', '.mov', '.mkv']:
                # For video files, loop infinitely and handle timing
                cmd.extend(["-stream_loop", "-1", "-i", frame_mp3cover_path])
            else:
                cmd.extend(["-i", frame_mp3cover_path])
            frame_mp3cover_idx = input_idx
            input_idx += 1
        # --- Add extra overlays (song titles) as inputs ---
        extra_overlay_indices = []
        if extra_overlays:
            for overlay in extra_overlays:
                cmd.extend(["-loop", "1", "-i", overlay['path']])
                extra_overlay_indices.append(input_idx)
                input_idx += 1
        
        # --- Add soundwave overlay as separate input ---
        soundwave_idx = None
        if use_soundwave_overlay and soundwave_overlay_path:
            cmd.extend(["-stream_loop", "-1", "-i", soundwave_overlay_path])
            soundwave_idx = input_idx
            input_idx += 1
        # --- End Song Title Overlay Filter Graph ---
        # Build filter graph with correct indices
        overlays_present = use_intro or use_overlay or use_overlay2 or use_overlay3 or use_overlay4 or use_overlay5 or use_overlay6 or use_overlay7 or use_overlay8 or use_overlay9 or use_overlay10 or use_frame_box or use_frame_mp3cover or bool(extra_overlays) or use_soundwave_overlay
        if overlays_present:
            # Check if intro is preprocessed (only for non-GIF images)
            intro_filename = os.path.basename(intro_path) if intro_path else ""
            is_intro_preprocessed = intro_filename.startswith("supercut_")
            intro_ext = os.path.splitext(intro_path)[1].lower() if intro_path else ""
            is_intro_gif = intro_ext == '.gif'
            is_intro_video = intro_path and intro_ext in ['.mp4', '.mov', '.mkv']
            
            if is_intro_preprocessed and not is_intro_gif:
                # Intro is preprocessed non-GIF image - use original size
                owi = "iw"
                ohi = "ih"
            elif is_intro_gif or is_intro_video:
                # Intro is GIF or video - apply scaling in FFmpeg
                scale_factor_intro = intro_size_percent / 100.0
                owi = f"iw*{scale_factor_intro:.3f}"
                ohi = f"ih*{scale_factor_intro:.3f}"
            else:
                # Intro is non-preprocessed image - apply scaling in FFmpeg
                scale_factor_intro = intro_size_percent / 100.0
                owi = f"iw*{scale_factor_intro:.3f}"
                ohi = f"ih*{scale_factor_intro:.3f}"
            
            # Check if overlay1 is preprocessed (only for non-GIF images)
            overlay1_filename = os.path.basename(overlay1_path) if overlay1_path else ""
            is_overlay1_preprocessed = overlay1_filename.startswith("supercut_")
            overlay1_ext = os.path.splitext(overlay1_path)[1].lower() if overlay1_path else ""
            is_overlay1_gif = overlay1_ext == '.gif'
            is_overlay1_video = overlay1_path and overlay1_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay1_preprocessed and not is_overlay1_gif:
                # Overlay1 is preprocessed non-GIF image - use original size
                ow1 = "iw"
                oh1 = "ih"
            elif is_overlay1_gif or is_overlay1_video:
                # Overlay1 is GIF or video - apply scaling in FFmpeg
                scale_factor1 = overlay1_size_percent / 100.0
                ow1 = f"iw*{scale_factor1:.3f}"
                oh1 = f"ih*{scale_factor1:.3f}"
            else:
                # Overlay1 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor1 = overlay1_size_percent / 100.0
                ow1 = f"iw*{scale_factor1:.3f}"
                oh1 = f"ih*{scale_factor1:.3f}"
            
            # Check if overlay2 is preprocessed (only for non-GIF images)
            overlay2_filename = os.path.basename(overlay2_path) if overlay2_path else ""
            is_overlay2_preprocessed = overlay2_filename.startswith("supercut_")
            overlay2_ext = os.path.splitext(overlay2_path)[1].lower() if overlay2_path else ""
            is_overlay2_gif = overlay2_ext == '.gif'
            is_overlay2_video = overlay2_path and overlay2_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay2_preprocessed and not is_overlay2_gif:
                # Overlay2 is preprocessed non-GIF image - use original size
                ow2 = "iw"
                oh2 = "ih"
            elif is_overlay2_gif or is_overlay2_video:
                # Overlay2 is GIF or video - apply scaling in FFmpeg
                scale_factor2 = overlay2_size_percent / 100.0
                ow2 = f"iw*{scale_factor2:.3f}"
                oh2 = f"ih*{scale_factor2:.3f}"
            else:
                # Overlay2 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor2 = overlay2_size_percent / 100.0
                ow2 = f"iw*{scale_factor2:.3f}"
                oh2 = f"ih*{scale_factor2:.3f}"
            
            # Check if overlay3 is preprocessed (only for non-GIF images)
            overlay3_filename = os.path.basename(overlay3_path) if overlay3_path else ""
            is_overlay3_preprocessed = overlay3_filename.startswith("supercut_")
            overlay3_ext = os.path.splitext(overlay3_path)[1].lower() if overlay3_path else ""
            is_overlay3_gif = overlay3_ext == '.gif'
            is_overlay3_video = overlay3_path and overlay3_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay3_preprocessed and not is_overlay3_gif:
                # Overlay3 is preprocessed non-GIF image - use original size
                ow3 = "iw"
                oh3 = "ih"
            elif is_overlay3_gif or is_overlay3_video:
                # Overlay3 is GIF or video - apply scaling in FFmpeg
                scale_factor3 = overlay3_size_percent / 100.0
                ow3 = f"iw*{scale_factor3:.3f}"
                oh3 = f"ih*{scale_factor3:.3f}"
            else:
                # Overlay3 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor3 = overlay3_size_percent / 100.0
                ow3 = f"iw*{scale_factor3:.3f}"
                oh3 = f"ih*{scale_factor3:.3f}"
            
            # Check if overlay4 is preprocessed (only for non-GIF images)
            overlay4_filename = os.path.basename(overlay4_path) if overlay4_path else ""
            is_overlay4_preprocessed = overlay4_filename.startswith("supercut_")
            overlay4_ext = os.path.splitext(overlay4_path)[1].lower() if overlay4_path else ""
            is_overlay4_gif = overlay4_ext == '.gif'
            is_overlay4_video = overlay4_path and overlay4_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay4_preprocessed and not is_overlay4_gif:
                # Overlay4 is preprocessed non-GIF image - use original size
                ow4 = "iw"
                oh4 = "ih"
            elif is_overlay4_gif or is_overlay4_video:
                # Overlay4 is GIF or video - apply scaling in FFmpeg
                scale_factor4 = overlay4_size_percent / 100.0
                ow4 = f"iw*{scale_factor4:.3f}"
                oh4 = f"ih*{scale_factor4:.3f}"
            else:
                # Overlay4 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor4 = overlay4_size_percent / 100.0
                ow4 = f"iw*{scale_factor4:.3f}"
                oh4 = f"ih*{scale_factor4:.3f}"
            
            # Check if overlay5 is preprocessed (only for non-GIF images)
            overlay5_filename = os.path.basename(overlay5_path) if overlay5_path else ""
            is_overlay5_preprocessed = overlay5_filename.startswith("supercut_")
            overlay5_ext = os.path.splitext(overlay5_path)[1].lower() if overlay5_path else ""
            is_overlay5_gif = overlay5_ext == '.gif'
            is_overlay5_video = overlay5_path and overlay5_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay5_preprocessed and not is_overlay5_gif:
                # Overlay5 is preprocessed non-GIF image - use original size
                ow5 = "iw"
                oh5 = "ih"
            elif is_overlay5_gif or is_overlay5_video:
                # Overlay5 is GIF or video - apply scaling in FFmpeg
                scale_factor5 = overlay5_size_percent / 100.0
                ow5 = f"iw*{scale_factor5:.3f}"
                oh5 = f"ih*{scale_factor5:.3f}"
            else:
                # Overlay5 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor5 = overlay5_size_percent / 100.0
                ow5 = f"iw*{scale_factor5:.3f}"
                oh5 = f"ih*{scale_factor5:.3f}"
            
            # Check if overlay6 is preprocessed (only for non-GIF images)
            overlay6_filename = os.path.basename(overlay6_path) if overlay6_path else ""
            is_overlay6_preprocessed = overlay6_filename.startswith("supercut_")
            overlay6_ext = os.path.splitext(overlay6_path)[1].lower() if overlay6_path else ""
            is_overlay6_gif = overlay6_ext == '.gif'
            is_overlay6_video = overlay6_path and overlay6_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay6_preprocessed and not is_overlay6_gif:
                # Overlay6 is preprocessed non-GIF image - use original size
                ow6 = "iw"
                oh6 = "ih"
            elif is_overlay6_gif or is_overlay6_video:
                # Overlay6 is GIF or video - apply scaling in FFmpeg
                scale_factor6 = overlay6_size_percent / 100.0
                ow6 = f"iw*{scale_factor6:.3f}"
                oh6 = f"ih*{scale_factor6:.3f}"
            else:
                # Overlay6 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor6 = overlay6_size_percent / 100.0
                ow6 = f"iw*{scale_factor6:.3f}"
                oh6 = f"ih*{scale_factor6:.3f}"
            
            # Check if overlay7 is preprocessed (only for non-GIF images)
            overlay7_filename = os.path.basename(overlay7_path) if overlay7_path else ""
            is_overlay7_preprocessed = overlay7_filename.startswith("supercut_")
            overlay7_ext = os.path.splitext(overlay7_path)[1].lower() if overlay7_path else ""
            is_overlay7_gif = overlay7_ext == '.gif'
            is_overlay7_video = overlay7_path and overlay7_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay7_preprocessed and not is_overlay7_gif:
                # Overlay7 is preprocessed non-GIF image - use original size
                ow7 = "iw"
                oh7 = "ih"
            elif is_overlay7_gif or is_overlay7_video:
                # Overlay7 is GIF or video - apply scaling in FFmpeg
                scale_factor7 = overlay7_size_percent / 100.0
                ow7 = f"iw*{scale_factor7:.3f}"
                oh7 = f"ih*{scale_factor7:.3f}"
            else:
                # Overlay7 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor7 = overlay7_size_percent / 100.0
                ow7 = f"iw*{scale_factor7:.3f}"
                oh7 = f"ih*{scale_factor7:.3f}"
            
            # Check if overlay8 is preprocessed (only for non-GIF images)
            overlay8_filename = os.path.basename(overlay8_path) if overlay8_path else ""
            is_overlay8_preprocessed = overlay8_filename.startswith("supercut_")
            overlay8_ext = os.path.splitext(overlay8_path)[1].lower() if overlay8_path else ""
            is_overlay8_gif = overlay8_ext == '.gif'
            is_overlay8_video = overlay8_path and overlay8_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay8_preprocessed and not is_overlay8_gif:
                # Overlay8 is preprocessed non-GIF image - use original size
                ow8 = "iw"
                oh8 = "ih"
            elif is_overlay8_gif or is_overlay8_video:
                # Overlay8 is GIF or video - apply scaling in FFmpeg
                scale_factor8 = overlay8_size_percent / 100.0
                ow8 = f"iw*{scale_factor8:.3f}"
                oh8 = f"ih*{scale_factor8:.3f}"
            else:
                # Overlay8 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor8 = overlay8_size_percent / 100.0
                ow8 = f"iw*{scale_factor8:.3f}"
                oh8 = f"ih*{scale_factor8:.3f}"
            
            # Check if overlay9 is preprocessed (only for non-GIF images)
            overlay9_filename = os.path.basename(overlay9_path) if overlay9_path else ""
            is_overlay9_preprocessed = overlay9_filename.startswith("supercut_")
            overlay9_ext = os.path.splitext(overlay9_path)[1].lower() if overlay9_path else ""
            is_overlay9_gif = overlay9_ext == '.gif'
            is_overlay9_video = overlay9_path and overlay9_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay9_preprocessed and not is_overlay9_gif:
                # Overlay9 is preprocessed non-GIF image - use original size
                ow9 = "iw"
                oh9 = "ih"
            elif is_overlay9_gif or is_overlay9_video:
                # Overlay9 is GIF or video - apply scaling in FFmpeg
                scale_factor9 = overlay9_size_percent / 100.0
                ow9 = f"iw*{scale_factor9:.3f}"
                oh9 = f"ih*{scale_factor9:.3f}"
            else:
                # Overlay9 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor9 = overlay9_size_percent / 100.0
                ow9 = f"iw*{scale_factor9:.3f}"
                oh9 = f"ih*{scale_factor9:.3f}"
            # Check if overlay10 is preprocessed (only for non-GIF images)
            overlay10_filename = os.path.basename(overlay10_path) if overlay10_path else ""
            is_overlay10_preprocessed = overlay10_filename.startswith("supercut_")
            overlay10_ext = os.path.splitext(overlay10_path)[1].lower() if overlay10_path else ""
            is_overlay10_gif = overlay10_ext == '.gif'
            is_overlay10_video = overlay10_path and overlay10_ext in ['.mp4', '.mov', '.mkv']
            
            if is_overlay10_preprocessed and not is_overlay10_gif:
                # Overlay10 is preprocessed non-GIF image - use original size
                ow10 = "iw"
                oh10 = "ih"
            elif is_overlay10_gif or is_overlay10_video:
                # Overlay10 is GIF or video - apply scaling in FFmpeg
                scale_factor10 = overlay10_size_percent / 100.0
                ow10 = f"iw*{scale_factor10:.3f}"
                oh10 = f"ih*{scale_factor10:.3f}"
            else:
                # Overlay10 is non-preprocessed image - apply scaling in FFmpeg
                scale_factor10 = overlay10_size_percent / 100.0
                ow10 = f"iw*{scale_factor10:.3f}"
                oh10 = f"ih*{scale_factor10:.3f}"
            # Framebox is pre-scaled, use original dimensions
            ow_frame_box = "iw"
            oh_frame_box = "ih"
            
            # Check if frame_mp3cover is preprocessed (only for non-GIF images)
            frame_mp3cover_filename = os.path.basename(frame_mp3cover_path) if frame_mp3cover_path else ""
            is_frame_mp3cover_preprocessed = frame_mp3cover_filename.startswith("supercut_")
            frame_mp3cover_ext = os.path.splitext(frame_mp3cover_path)[1].lower() if frame_mp3cover_path else ""
            is_frame_mp3cover_gif = frame_mp3cover_ext == '.gif'
            is_frame_mp3cover_video = frame_mp3cover_path and frame_mp3cover_ext in ['.mp4', '.mov', '.mkv']
            
            if is_frame_mp3cover_preprocessed and not is_frame_mp3cover_gif:
                # Frame_mp3cover is preprocessed non-GIF image - use original size
                ow_frame_mp3cover = "iw"
                oh_frame_mp3cover = "ih"
            elif is_frame_mp3cover_gif or is_frame_mp3cover_video:
                # Frame_mp3cover is GIF or video - apply scaling in FFmpeg
                scale_factor_frame_mp3cover = frame_mp3cover_size_percent / 100.0
                ow_frame_mp3cover = f"iw*{scale_factor_frame_mp3cover:.3f}"
                oh_frame_mp3cover = f"ih*{scale_factor_frame_mp3cover:.3f}"
            else:
                # Frame_mp3cover is non-preprocessed image - apply scaling in FFmpeg
                scale_factor_frame_mp3cover = frame_mp3cover_size_percent / 100.0
                ow_frame_mp3cover = f"iw*{scale_factor_frame_mp3cover:.3f}"
                oh_frame_mp3cover = f"ih*{scale_factor_frame_mp3cover:.3f}"
            # --- Add soundwave scale and position calculations ---
            scale_factor_soundwave = soundwave_size_percent / 100.0
            ow_soundwave = f"iw*{scale_factor_soundwave:.3f}"
            oh_soundwave = f"ih*{scale_factor_soundwave:.3f}"
            ox_soundwave = f"(W-w)*({soundwave_x_percent}/100)" if soundwave_x_percent != 0 else "0"
            oy_soundwave = f"(H-h)*(1-({soundwave_y_percent}/100))" if soundwave_y_percent != 100 else "0"
            position_map = {
                "top_left": ("0", "0"),
                "top_right": (f"W-w", "0"),
                "bottom_left": ("0", f"H-h"),
                "bottom_right": (f"W-w", f"H-h"),
                "center": ("(W-w)/2", "(H-h)/2")
            }
            # Pre-calculate intro position for better performance
            def precalculate_intro_position(video_width, video_height, intro_width, intro_height, x_percent, y_percent):
                """Pre-calculate intro overlay position to avoid real-time calculations"""
                if x_percent == 0:
                    x_pos = 0
                else:
                    x_pos = int((video_width - intro_width) * (x_percent / 100))
                
                if y_percent == 100:
                    y_pos = 0
                else:
                    y_pos = int((video_height - intro_height) * (1 - (y_percent / 100)))
                
                return x_pos, y_pos
            
            # Calculate intro dimensions (assuming intro is scaled by intro_size_percent)
            # For testing, we'll use estimated dimensions based on size percentage
            estimated_intro_width = int(width * (intro_size_percent / 100))
            estimated_intro_height = int(height * (intro_size_percent / 100))
            
            # Pre-calculate intro position
            intro_x_pos, intro_y_pos = precalculate_intro_position(
                video_width=width, 
                video_height=height,
                intro_width=estimated_intro_width,
                intro_height=estimated_intro_height,
                x_percent=intro_x_percent,
                y_percent=intro_y_percent
            )
            
            # Use pre-calculated values instead of dynamic expressions
            ox_intro = str(intro_x_pos)
            oy_intro = str(intro_y_pos)
            


            
            # 🚀 PRE-CALCULATION OPTIMIZATION: All overlay positions
            def precalculate_overlay_position(video_width, video_height, overlay_width, overlay_height, x_percent, y_percent):
                """Pre-calculate overlay position to avoid real-time calculations"""
                if x_percent == 0:
                    x_pos = 0
                else:
                    x_pos = int((video_width - overlay_width) * (x_percent / 100))
                
                if y_percent == 100:
                    y_pos = 0
                else:
                    y_pos = int((video_height - overlay_height) * (1 - (y_percent / 100)))
                
                return x_pos, y_pos
            
            # 🚀 PRE-CALCULATION OPTIMIZATION: Get actual overlay dimensions
            def get_actual_overlay_dimensions(overlay_path, size_percent):
                """Get actual overlay dimensions from preprocessed images and videos"""
                # Check if overlay path is empty or invalid
                if not overlay_path or overlay_path.strip() == "":
                    base_size = 200  # Estimated base size for empty paths
                    return int(base_size * (size_percent / 100)), int(base_size * (size_percent / 100))
                
                # Check file type
                file_ext = os.path.splitext(overlay_path)[1].lower()
                is_video = file_ext in ['.mp4', '.mov', '.mkv']
                is_gif = file_ext == '.gif'
                
                try:
                    if is_video or is_gif:
                        # For video/GIF files, try to get dimensions with FFprobe
                        try:
                            import subprocess
                            from src.config import FFPROBE_BINARY
                            ffprobe = FFPROBE_BINARY
                            
                            cmd = [
                                ffprobe,
                                '-v', 'quiet',
                                '-print_format', 'json',
                                '-show_streams',
                                '-select_streams', 'v:0',
                                overlay_path
                            ]
                            
                            result = subprocess.run(cmd, capture_output=True, text=True)
                            if result.returncode == 0:
                                import json
                                data = json.loads(result.stdout)
                                if 'streams' in data and len(data['streams']) > 0:
                                    stream = data['streams'][0]
                                    actual_width = int(stream.get('width', 200))
                                    actual_height = int(stream.get('height', 200))
                                    # Apply size_percent for video/GIF files
                                    scaled_width = int(actual_width * (size_percent / 100))
                                    scaled_height = int(actual_height * (size_percent / 100))
                                    return scaled_width, scaled_height
                        except Exception as e:
                            # Fallback to estimated dimensions for video/GIF
                            print(f"⚠️ FFprobe failed for {overlay_path}: {e}")
                            base_size = 200  # Estimated base size for video/GIF
                            return int(base_size * (size_percent / 100)), int(base_size * (size_percent / 100))
                    
                    # Only try PIL for image files (not video/GIF)
                    if not is_video and not is_gif:
                        from PIL import Image
                        with Image.open(overlay_path) as img:
                            # For preprocessed images, use the actual dimensions directly
                            # The preprocessing already applied the size_percent scaling
                            actual_width, actual_height = img.size
                            return actual_width, actual_height
                except Exception as e:
                    # Fallback to estimated dimensions if all methods fail
                    print(f"⚠️ Could not get actual dimensions for {overlay_path}: {e}")
                    base_size = 200  # Estimated base size
                    return int(base_size * (size_percent / 100)), int(base_size * (size_percent / 100))
            
            # Pre-calculate all overlay positions using actual dimensions
            overlay1_width, overlay1_height = get_actual_overlay_dimensions(overlay1_path, overlay1_size_percent)
            ox1, oy1 = precalculate_overlay_position(width, height, overlay1_width, overlay1_height, overlay1_x_percent, overlay1_y_percent)
            
            overlay2_width, overlay2_height = get_actual_overlay_dimensions(overlay2_path, overlay2_size_percent)
            ox2, oy2 = precalculate_overlay_position(width, height, overlay2_width, overlay2_height, overlay2_x_percent, overlay2_y_percent)
            
            overlay3_width, overlay3_height = get_actual_overlay_dimensions(overlay3_path, overlay3_size_percent)
            ox3, oy3 = precalculate_overlay_position(width, height, overlay3_width, overlay3_height, overlay3_x_percent, overlay3_y_percent)
            
            overlay4_width, overlay4_height = get_actual_overlay_dimensions(overlay4_path, overlay4_size_percent)
            ox4, oy4 = precalculate_overlay_position(width, height, overlay4_width, overlay4_height, overlay4_x_percent, overlay4_y_percent)
            
            overlay5_width, overlay5_height = get_actual_overlay_dimensions(overlay5_path, overlay5_size_percent)
            ox5, oy5 = precalculate_overlay_position(width, height, overlay5_width, overlay5_height, overlay5_x_percent, overlay5_y_percent)
            
            overlay6_width, overlay6_height = get_actual_overlay_dimensions(overlay6_path, overlay6_size_percent)
            ox6, oy6 = precalculate_overlay_position(width, height, overlay6_width, overlay6_height, overlay6_x_percent, overlay6_y_percent)
            
            overlay7_width, overlay7_height = get_actual_overlay_dimensions(overlay7_path, overlay7_size_percent)
            ox7, oy7 = precalculate_overlay_position(width, height, overlay7_width, overlay7_height, overlay7_x_percent, overlay7_y_percent)
            
            overlay8_width, overlay8_height = get_actual_overlay_dimensions(overlay8_path, overlay8_size_percent)
            ox8, oy8 = precalculate_overlay_position(width, height, overlay8_width, overlay8_height, overlay8_x_percent, overlay8_y_percent)
            
            overlay9_width, overlay9_height = get_actual_overlay_dimensions(overlay9_path, overlay9_size_percent)
            ox9, oy9 = precalculate_overlay_position(width, height, overlay9_width, overlay9_height, overlay9_x_percent, overlay9_y_percent)
            
            overlay10_width, overlay10_height = get_actual_overlay_dimensions(overlay10_path, overlay10_size_percent)
            ox10, oy10 = precalculate_overlay_position(width, height, overlay10_width, overlay10_height, overlay10_x_percent, overlay10_y_percent)
            
            # Pre-calculate frame box positions using actual dimensions
            frame_box_width, frame_box_height = get_actual_overlay_dimensions(frame_box_path, frame_box_size_percent)
            base_frame_x, base_frame_y = precalculate_overlay_position(width, height, frame_box_width, frame_box_height, frame_box_x_percent, frame_box_y_percent)
            ox_frame_box = base_frame_x + frame_box_pad_left
            oy_frame_box = base_frame_y + frame_box_pad_top
            
            # Pre-calculate frame mp3cover positions using actual dimensions
            frame_mp3cover_width, frame_mp3cover_height = get_actual_overlay_dimensions(frame_mp3cover_path, frame_mp3cover_size_percent)
            ox_frame_mp3cover, oy_frame_mp3cover = precalculate_overlay_position(width, height, frame_mp3cover_width, frame_mp3cover_height, frame_mp3cover_x_percent, frame_mp3cover_y_percent)
            

            
            # Check if background is preprocessed (already correct size)
            # Background is always PNG, so no need to check for GIF
            bg_filename = os.path.basename(image_path_for_ffmpeg)
            is_bg_preprocessed = bg_filename.startswith("supercut_")
            
            if is_bg_preprocessed:
                # Background is preprocessed PNG - no scaling needed
                filter_bg = f"[0:v]null[bg]"
            else:
                # Background needs scaling to target resolution
                filter_bg = f"[0:v]scale={width}:{height}[bg]"

            # Effect logic for overlays
            def overlay_effect_chain(idx, scale_expr, label, effect, effect_time, ext, duration=None):
                if idx is None:
                    return ""
                chain = f"[{idx}:v]"
                if ext == ".gif":
                    chain += "fps=30,"
                elif ext in [".mp4", ".mov", ".mkv"]:
                    pass
                chain += "format=rgba"
                # Special case for overlay8, overlay9, and overlay10 with effect 'null'
                if label in ["ol8", "ol9", "ol10"] and effect == "null":
                    chain += ",null[" + label + "]"
                    return chain
                chain += ","
                fade_alpha = ":alpha=1" if ext == ".png" else ""
                if effect == "fadeinout":
                    fadein_duration = 1.5
                    fadeout_duration = 1.5
                    if duration is not None:
                        hold_duration = max(0, duration - fadein_duration - fadeout_duration)
                    else:
                        hold_duration = 5
                    fadein_end = effect_time + fadein_duration
                    fadeout_start = fadein_end + hold_duration
                    if scale_expr != "iw:ih":
                        chain += f"fade=t=in:st={effect_time}:d={fadein_duration}{fade_alpha},fade=t=out:st={fadeout_start}:d={fadeout_duration}{fade_alpha},"
                    else:
                        chain += f"fade=t=in:st={effect_time}:d={fadein_duration}{fade_alpha},fade=t=out:st={fadeout_start}:d={fadeout_duration}{fade_alpha}"
                elif effect == "fadein":
                    if scale_expr != "iw:ih":
                        chain += f"fade=t=in:st={effect_time}:d=1{fade_alpha},"
                    else:
                        chain += f"fade=t=in:st={effect_time}:d=1{fade_alpha}"
                elif effect == "fadeout":
                    if scale_expr != "iw:ih":
                        chain += f"fade=t=out:st={effect_time}:d=1{fade_alpha},"
                    else:
                        chain += f"fade=t=out:st={effect_time}:d=1{fade_alpha}"
                elif effect == "zoompan":
                    if scale_expr != "iw:ih":
                        chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
                    else:
                        chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                if scale_expr != "iw:ih":
                    chain += f"scale={scale_expr}"
                chain += f"[{label}]"
                return chain

            def intro_effect_chain(idx, scale_expr, label, effect, duration, start_at, ext):
                if idx is None:
                    return ""
                chain = f"[{idx}:v]"
                if ext == ".gif":
                    chain += "fps=30,"
                elif ext in [".mp4", ".mov", ".mkv"]:
                    # For video overlays, we need to handle them differently
                    # Videos already have their own fps, so we don't force fps=30
                    # Video files are now looped infinitely like GIFs
                    pass
                chain += "format=rgba,"
                fade_alpha = ":alpha=1" if ext == ".png" else ""
                if effect == "fadein":
                    # Add comma only if scale operation will follow
                    if scale_expr != "iw:ih":
                        chain += f"fade=t=in:st={start_at}:d=1{fade_alpha},"
                    else:
                        chain += f"fade=t=in:st={start_at}:d=1{fade_alpha}"
                elif effect == "fadeout":
                    # Use duration if provided, otherwise use default calculation
                    if duration is not None:
                        fadeout_start = start_at + duration - 1.5
                    else:
                        fadeout_start = start_at + 6 - 1.5  # Default 6 seconds
                    # Add comma only if scale operation will follow
                    if scale_expr != "iw:ih":
                        chain += f"fade=t=out:st={fadeout_start}:d=1.5{fade_alpha},"
                    else:
                        chain += f"fade=t=out:st={fadeout_start}:d=1.5{fade_alpha}"
                elif effect == "fadeinout":
                    # Use duration if provided, otherwise use default calculation
                    if duration is not None:
                        fadeout_start = start_at + duration - 1.5
                    else:
                        fadeout_start = start_at + 6 - 1.5  # Default 6 seconds
                    # Add comma only if scale operation will follow
                    if scale_expr != "iw:ih":
                        chain += f"fade=t=in:st={start_at}:d=1.5{fade_alpha},fade=t=out:st={fadeout_start}:d=1.5{fade_alpha},"
                    else:
                        chain += f"fade=t=in:st={start_at}:d=1.5{fade_alpha},fade=t=out:st={fadeout_start}:d=1.5{fade_alpha}"
                elif effect == "zoompan":
                    # Add comma only if scale operation will follow
                    if scale_expr != "iw:ih":
                        chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
                    else:
                        chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                # Add scale operation only if necessary
                if scale_expr != "iw:ih":
                    chain += f"scale={scale_expr}"
                chain += f"[{label}]"
                return chain

            # Calculate duration for intro based on full duration checkbox
            intro_actual_duration = None
            if not intro_duration_full_checkbox_checked:
                intro_actual_duration = intro_duration
            
            filter_intro = intro_effect_chain(intro_idx, f"{owi}:{ohi}", "oi", intro_effect, intro_actual_duration, intro_start_at, ext_intro) if intro_idx is not None else ""
            # Calculate duration for overlay1_2 based on full duration checkbox
            overlay1_2_actual_duration = None
            if not overlay1_2_duration_full_checkbox_checked:
                overlay1_2_actual_duration = overlay1_2_duration
            
            filter_overlay1 = overlay_effect_chain(overlay1_idx, f"{ow1}:{oh1}", "ol1", overlay1_2_effect, overlay1_2_start_time, ext1, overlay1_2_actual_duration) if overlay1_idx is not None else ""
            filter_overlay2 = overlay_effect_chain(overlay2_idx, f"{ow2}:{oh2}", "ol2", overlay1_2_effect, overlay1_2_start_time, ext2, overlay1_2_actual_duration) if overlay2_idx is not None else ""
            filter_overlay3 = overlay_effect_chain(overlay3_idx, f"{ow3}:{oh3}", "ol3", overlay3_effect, overlay3_start_time, ext3) if overlay3_idx is not None else ""
            # Calculate duration for overlay4_5 based on full duration checkbox
            overlay4_actual_duration = None
            overlay5_actual_duration = None
            if not overlay4_duration_full_checkbox_checked:
                overlay4_actual_duration = overlay4_duration
            if not overlay5_duration_full_checkbox_checked:
                overlay5_actual_duration = overlay5_duration
            
            filter_overlay4 = overlay_effect_chain(overlay4_idx, f"{ow4}:{oh4}", "ol4", overlay4_effect, overlay4_start_time, ext4, overlay4_actual_duration) if overlay4_idx is not None else ""
            filter_overlay5 = overlay_effect_chain(overlay5_idx, f"{ow5}:{oh5}", "ol5", overlay5_effect, overlay5_start_time, ext5, overlay5_actual_duration) if overlay5_idx is not None else ""
            # Calculate duration for overlay6_7 based on full duration checkbox
            overlay6_actual_duration = None
            overlay7_actual_duration = None
            if not overlay6_duration_full_checkbox_checked:
                overlay6_actual_duration = overlay6_duration
            if not overlay7_duration_full_checkbox_checked:
                overlay7_actual_duration = overlay7_duration
            
            filter_overlay6 = overlay_effect_chain(overlay6_idx, f"{ow6}:{oh6}", "ol6", overlay6_effect, overlay6_start_time, ext6, overlay6_actual_duration) if overlay6_idx is not None else ""
            filter_overlay7 = overlay_effect_chain(overlay7_idx, f"{ow7}:{oh7}", "ol7", overlay7_effect, overlay7_start_time, ext7, overlay7_actual_duration) if overlay7_idx is not None else ""
            # Calculate duration for overlay8 based on full duration checkbox
            overlay8_actual_duration = None
            if not overlay8_duration_full_checkbox_checked:
                overlay8_actual_duration = overlay8_duration
            
            filter_overlay8 = overlay_effect_chain(overlay8_idx, f"{ow8}:{oh8}", "ol8", overlay8_effect, overlay8_start_time, ext8, overlay8_actual_duration) if overlay8_idx is not None else ""
            # Calculate duration for overlay9 based on full duration checkbox
            overlay9_actual_duration = None
            if not overlay9_duration_full_checkbox_checked:
                overlay9_actual_duration = overlay9_duration
            
            filter_overlay9 = overlay_effect_chain(overlay9_idx, f"{ow9}:{oh9}", "ol9", overlay9_effect, overlay9_start_time, ext9, overlay9_actual_duration) if overlay9_idx is not None else ""
            filter_overlay10 = overlay_effect_chain(overlay10_idx, f"{ow10}:{oh10}", "ol10", overlay10_effect, overlay10_start_time, ext10, overlay10_duration) if overlay10_idx is not None else ""
            # Calculate duration for frame box based on full duration checkbox
            frame_box_actual_duration = None
            if not frame_box_duration_full_checkbox_checked:
                frame_box_actual_duration = frame_box_duration
            
            filter_frame_box = overlay_effect_chain(frame_box_idx, "iw:ih", "ol_frame_box", frame_box_effect, frame_box_start_time, ext_frame_box, frame_box_actual_duration) if frame_box_idx is not None else ""
            # Calculate duration for frame mp3cover based on full duration checkbox
            frame_mp3cover_actual_duration = None
            if not frame_mp3cover_duration_full_checkbox_checked:
                frame_mp3cover_actual_duration = frame_mp3cover_duration
            
            filter_frame_mp3cover = overlay_effect_chain(frame_mp3cover_idx, f"{ow_frame_mp3cover}:{oh_frame_mp3cover}", "ol_frame_mp3cover", frame_mp3cover_effect, frame_mp3cover_start_time, ext_frame_mp3cover, frame_mp3cover_actual_duration) if frame_mp3cover_idx is not None else ""
            # --- Song Title and MP3 Cover Overlay Filter Graph ---
            song_title_chains = []
            song_title_labels = []
            mp3_cover_chains = []
            mp3_cover_labels = []
            
            # Separate counters for each overlay type
            song_title_counter = 0
            mp3_cover_counter = 0
            
            if extra_overlays:
                for i, overlay in enumerate(extra_overlays):
                    idx = extra_overlay_indices[i]
                    start = overlay.get('start', 0)
                    duration = overlay.get('duration', 0)
                    x_percent = overlay.get('x_percent', 0)
                    y_percent = overlay.get('y_percent', 0)
                    size_percent = overlay.get('size_percent', 100)
                    effect = overlay.get('effect', 'fadein')
                    
                    overlay_path = overlay.get('path', '')
                    overlay_filename = os.path.basename(overlay_path) if overlay_path else ""
                    overlay_ext = os.path.splitext(overlay_path)[1].lower() if overlay_path else ""
                    
                    # Get overlay type directly from the overlay data FIRST
                    # Supported types: 'song_title', 'mp3_cover'
                    overlay_type = overlay.get('type', 'unknown')
                    
                    # 🚀 PRE-CALCULATION OPTIMIZATION: Song title and MP3 cover positions
                    # Get actual overlay dimensions from the image files
                    if not overlay_path or overlay_path.strip() == "":
                        # Handle empty overlay paths
                        if overlay_type == 'song_title':
                            overlay_width = int(300 * (size_percent / 100))
                            overlay_height = int(100 * (size_percent / 100))
                        else:  # mp3_cover
                            overlay_width = int(200 * (size_percent / 100))
                            overlay_height = int(200 * (size_percent / 100))
                    else:
                        try:
                            from PIL import Image
                            with Image.open(overlay_path) as img:
                                # For preprocessed images, use the actual dimensions directly
                                # The preprocessing already applied the size_percent scaling
                                overlay_width, overlay_height = img.size
                        except Exception as e:
                            # Fallback to estimated dimensions if PIL fails
                            print(f"⚠️ Could not get actual dimensions for {overlay_path}: {e}")
                            if overlay_type == 'song_title':
                                overlay_width = int(300 * (size_percent / 100))
                                overlay_height = int(100 * (size_percent / 100))
                            else:  # mp3_cover
                                overlay_width = int(200 * (size_percent / 100))
                                overlay_height = int(200 * (size_percent / 100))
                    
                    # Pre-calculate positions
                    if x_percent == 0:
                        x_pos = 0
                    else:
                        x_pos = int((width - overlay_width) * (x_percent / 100))
                    
                    if y_percent == 100:
                        y_pos = 0
                    else:
                        y_pos = int((height - overlay_height) * (1 - (y_percent / 100)))
                    
                    # Use pre-calculated positions instead of expressions
                    x_expr = str(x_pos)
                    y_expr = str(y_pos)
                    
                    # Process based on explicit type
                    if overlay_type == 'song_title':
                        # This is a song title overlay
                        song_title_counter += 1
                        label = f"songol{song_title_counter}"
                        
                        # Build song title effect chain
                        chain = f"[{idx}:v]format=rgba"
                        
                        # Apply effect
                        fade_alpha = ":alpha=1" if overlay_ext == ".png" else ""
                        if effect == "fadeinout":
                            fadein_duration = 1.5
                            fadeout_duration = 1.5
                            hold_duration = max(0, duration - fadein_duration - fadeout_duration)
                            fadein_end = start + fadein_duration
                            fadeout_start = fadein_end + hold_duration
                            chain += f",fade=t=in:st={start}:d={fadein_duration}{fade_alpha},fade=t=out:st={fadeout_start}:d={fadeout_duration}{fade_alpha}"
                        elif effect == "fadein":
                            chain += f",fade=t=in:st={start}:d=1{fade_alpha}"
                        elif effect == "fadeout":
                            chain += f",fade=t=out:st={start}:d=1{fade_alpha}"
                        elif effect == "zoompan":
                            chain += f",zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        
                        # 🚀 PRE-CALCULATION OPTIMIZATION: Scale factor for song titles
                        # Use actual dimensions instead of estimated ones
                        if size_percent != 100:
                            # Use the already calculated overlay_width and overlay_height
                            chain += f",scale={overlay_width}:{overlay_height}"
                        
                        chain += f"[{label}]"
                        song_title_chains.append(chain)
                        song_title_labels.append((label, start, duration, x_expr, y_expr))
                        
                    elif overlay_type == 'mp3_cover':
                        # This is an MP3 cover overlay
                        mp3_cover_counter += 1
                        label = f"mp3cover.ol{mp3_cover_counter}"
                        
                        # Build MP3 cover effect chain
                        chain = f"[{idx}:v]format=rgba"
                        
                        # Apply effect
                        fade_alpha = ":alpha=1" if overlay_ext == ".png" else ""
                        if effect == "fadeinout":
                            fadein_duration = 1.5
                            fadeout_duration = 1.5
                            hold_duration = max(0, duration - fadein_duration - fadeout_duration)
                            fadein_end = start + fadein_duration
                            fadeout_start = fadein_end + hold_duration
                            chain += f",fade=t=in:st={start}:d={fadein_duration}{fade_alpha},fade=t=out:st={fadeout_start}:d={fadeout_duration}{fade_alpha}"
                        elif effect == "fadein":
                            chain += f",fade=t=in:st={start}:d=1{fade_alpha}"
                        elif effect == "fadeout":
                            chain += f",fade=t=out:st={start}:d=1{fade_alpha}"
                        elif effect == "zoompan":
                            chain += f",zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        
                        # 🚀 PRE-CALCULATION OPTIMIZATION: Scale factor for MP3 covers
                        # Use actual dimensions instead of estimated ones
                        if size_percent != 100:
                            # Use the already calculated overlay_width and overlay_height
                            chain += f",scale={overlay_width}:{overlay_height}"
                        
                        chain += f"[{label}]"
                        mp3_cover_chains.append(chain)
                        mp3_cover_labels.append((label, start, duration, x_expr, y_expr))
                        
                    else:
                        # Unknown overlay type - skip or handle as needed
                        print(f"⚠️ Unknown overlay type: {overlay_type} for {overlay_filename}")
                        continue
            
            # Keep chains separate since they're handled individually in the layer processing
            # filter_chains = song_title_chains + mp3_cover_chains  # Removed to prevent duplicates
            # overlay_labels = song_title_labels + mp3_cover_labels  # Removed to prevent duplicates
            

            # --- End Song Title and MP3 Cover Overlay Filter Graph ---
            
            
            # Build filter graph based on layer order
            filter_graph = filter_bg
            last_label = "[bg]"
            
            # Define layer configurations for custom ordering
            layer_configs = {
                'background': {'filter': None, 'label': '[bg]'},  # Background is handled in advance
                'overlay1': {
                    'filter': filter_overlay1,
                    'overlay': f"[ol1]overlay={ox1}:{oy1}",
                    'duration_control': overlay1_2_duration_full_checkbox_checked,
                    'start_time': overlay1_start_at,
                    'duration': overlay1_2_duration
                },
                'overlay2': {
                    'filter': filter_overlay2,
                    'overlay': f"[ol2]overlay={ox2}:{oy2}",
                    'duration_control': overlay1_2_duration_full_checkbox_checked,
                    'start_time': overlay2_start_at,
                    'duration': overlay1_2_duration
                },
                'overlay3': {
                    'filter': filter_overlay3,
                    'overlay': f"[ol3]overlay={ox3}:{oy3}",
                    'duration_control': None,
                    'start_time': None,
                    'duration': None
                },
                'overlay4': {
                    'filter': filter_overlay4,
                    'overlay': f"[ol4]overlay={ox4}:{oy4}",
                    'duration_control': overlay4_duration_full_checkbox_checked,
                    'start_time': overlay4_start_time,
                    'duration': overlay4_duration
                },
                'overlay5': {
                    'filter': filter_overlay5,
                    'overlay': f"[ol5]overlay={ox5}:{oy5}",
                    'duration_control': overlay5_duration_full_checkbox_checked,
                    'start_time': overlay5_start_time,
                    'duration': overlay5_duration
                },
                'overlay6': {
                    'filter': filter_overlay6,
                    'overlay': f"[ol6]overlay={ox6}:{oy6}",
                    'duration_control': overlay6_duration_full_checkbox_checked,
                    'start_time': overlay6_start_time,
                    'duration': overlay6_duration
                },
                'overlay7': {
                    'filter': filter_overlay7,
                    'overlay': f"[ol7]overlay={ox7}:{oy7}",
                    'duration_control': overlay7_duration_full_checkbox_checked,
                    'start_time': overlay7_start_time,
                    'duration': overlay7_duration
                },
                'overlay8': {
                    'filter': filter_overlay8,
                    'overlay': f"[ol8]overlay={ox8}:{oy8}",
                    'duration_control': overlay8_duration_full_checkbox_checked,
                    'start_time': overlay8_start_time,
                    'duration': overlay8_duration,
                    'intervals': overlay8_intervals  # NEW
                },
                'overlay9': {
                    'filter': filter_overlay9,
                    'overlay': f"[ol9]overlay={ox9}:{oy9}",
                    'duration_control': overlay9_duration_full_checkbox_checked,
                    'start_time': overlay9_start_time,
                    'duration': overlay9_duration,
                    'intervals': overlay9_intervals  # NEW
                },
                'overlay10': {
                    'filter': filter_overlay10,
                    'overlay': f"[ol10]overlay={ox10}:{oy10}",
                    'duration_control': False,  # Always limited duration
                    'start_time': overlay10_start_time,
                    'duration': overlay10_duration,
                    'intervals': overlay10_intervals  # NEW
                },
                'mp3_cover_overlay': {
                    'filter': None,  # Handled in extra_overlays like song_titles
                    'overlay': None,  # Handled in extra_overlays like song_titles
                    'duration_control': None,
                    'start_time': None,
                    'duration': None
                },
                'frame_box': {
                    'filter': filter_frame_box,
                    'overlay': f"[ol_frame_box]overlay={ox_frame_box}:{oy_frame_box}",
                    'duration_control': frame_box_duration_full_checkbox_checked,
                    'start_time': frame_box_start_time,
                    'duration': frame_box_duration
                },
                'frame_mp3cover': {
                    'filter': filter_frame_mp3cover,
                    'overlay': f"[ol_frame_mp3cover]overlay={ox_frame_mp3cover}:{oy_frame_mp3cover}",
                    'duration_control': frame_mp3cover_duration_full_checkbox_checked,
                    'start_time': frame_mp3cover_start_time,
                    'duration': frame_mp3cover_duration
                },
                'intro': {
                    'filter': filter_intro,
                    'overlay': f"[oi]overlay={ox_intro}:{oy_intro}",
                    'duration_control': intro_duration_full_checkbox_checked,
                    'start_time': intro_start_at,
                    'duration': intro_duration
                },
                'song_titles': {
                    'filter': None,  # Handled separately in special case
                    'overlay': None,  # Handled separately
                    'duration_control': None,
                    'start_time': None,
                    'duration': None
                },
                'soundwave': {
                    'filter': None,  # Handled separately
                    'overlay': None,
                    'duration_control': None,
                    'start_time': None,
                    'duration': None
                }
            }
            
            # Use the exact layer order from layer manager if provided
            if layer_order:
    
                # Use the exact order provided by layer manager, only filter out non-existent layers
                final_order = [layer for layer in layer_order if layer in layer_configs]
                # Add any missing layers that exist in configs but not in layer_order
                missing_layers = [layer for layer in layer_configs.keys() if layer not in final_order]
                final_order.extend(missing_layers)
            else:
    
                final_order = ['background', 'overlay1', 'overlay2', 'overlay3', 'overlay4', 'overlay5',
                             'overlay6', 'overlay7', 'overlay8', 'overlay9', 'overlay10',
                             'intro', 'frame_box', 'frame_mp3cover', 'mp3_cover_overlay', 'song_titles', 'soundwave']
            
            # Build filter graph with proper 2-grouping: input processing first, then overlay applications
            # But ensure the order within each group matches the overlay application order
            input_processing_filters = []
            overlay_application_filters = []
            
            # Alternative approach: when filter_complex_alt_mode is True, don't use 2-grouping
            # Instead, process each overlay immediately after its input processing
            if filter_complex_alt_mode:
                # Alternative approach: process each overlay immediately after its input processing
                # This avoids the 2-grouping approach and processes overlays one by one
                # We still need to define overlay_application_filters for compatibility
                overlay_application_filters = []
                print(f"🔧 Filter Complex Alt Mode: ON")
            else:
                # Original approach: 2-grouping with input processing first, then overlay applications
                pass
            
            # First pass: collect all filters in the EXACT order they will be applied in overlays
            for layer_id in final_order:
                if layer_id == 'background':
                    continue  # Background is already the base
                
                config = layer_configs.get(layer_id)
                if not config:
                    continue
                
                # Handle song titles (special case)
                if layer_id == 'song_titles' and song_title_chains:
                    input_processing_filters.extend(song_title_chains)
                    continue
                
                # Handle MP3 cover overlays (special case)
                if layer_id == 'mp3_cover_overlay' and mp3_cover_chains:
                    input_processing_filters.extend(mp3_cover_chains)
                    continue
                
                # Handle soundwave (special case)
                if layer_id == 'soundwave' and use_soundwave_overlay and soundwave_idx is not None:
                    input_processing_filters.append(f"[{soundwave_idx}:v]format=yuva420p[soundwave]")
                    continue
                
                # Handle regular overlays
                if config['filter']:
                    input_processing_filters.append(config['filter'])
                    
                    # Prepare overlay application
                    if layer_id == 'overlay8' and config.get('intervals'):
                        # Build combined enable expression for all intervals
                        intervals = config['intervals']
                        enable_expr = "+".join([
                            f"between(t,{start},{start+duration})" for start, duration in intervals if duration > 0
                        ])
                        overlay_application_filters.append((f"{config['overlay']}:enable='{enable_expr}'[tmp_{layer_id}]", f"tmp_{layer_id}"))
                    elif layer_id == 'overlay9' and config.get('intervals'):
                        # Build combined enable expression for all intervals
                        intervals = config['intervals']
                        enable_expr = "+".join([
                            f"between(t,{start},{start+duration})" for start, duration in intervals if duration > 0
                        ])
                        overlay_application_filters.append((f"{config['overlay']}:enable='{enable_expr}'[tmp_{layer_id}]", f"tmp_{layer_id}"))
                    elif layer_id == 'overlay10' and config.get('intervals'):
                        # Build combined enable expression for all intervals
                        intervals = config['intervals']
                        enable_expr = "+".join([
                            f"between(t,{start},{start+duration})" for start, duration in intervals if duration > 0
                        ])
                        overlay_application_filters.append((f"{config['overlay']}:enable='{enable_expr}'[tmp_{layer_id}]", f"tmp_{layer_id}"))
                    elif config['duration_control'] is None:
                        # No duration control (like overlay3)
                        overlay_application_filters.append((f"{config['overlay']}[tmp_{layer_id}]", None))
                    elif config['duration_control']:
                        # Full duration
                        overlay_application_filters.append((f"{config['overlay']}:enable='gte(t,{config['start_time']})'[tmp_{layer_id}]", f"tmp_{layer_id}"))
                    else:
                        # Time-based enable expressions
                        end_time = config['start_time'] + config['duration']
                        overlay_application_filters.append((f"{config['overlay']}:enable='between(t,{config['start_time']},{end_time})'[tmp_{layer_id}]", f"tmp_{layer_id}"))
            
            # Build the filter graph based on the selected approach
            if filter_complex_alt_mode:
                # Alternative approach: process each overlay immediately after its input processing
                filter_graph = filter_bg
                last_label = "[bg]"
                
                # Process each layer in order, applying overlays immediately after input processing
                for layer_id in final_order:
                    if layer_id == 'background':
                        continue  # Background is already the base
                    
                    config = layer_configs.get(layer_id)
                    if not config:
                        continue
                    
                    # Handle song titles (special case)
                    if layer_id == 'song_titles' and song_title_chains:
                        # Add song title input processing
                        filter_graph += ";" + ";".join(song_title_chains)
                        # Apply song title overlays immediately
                        if song_title_labels:
                            for i, (label, start, duration, x_expr, y_expr) in enumerate(song_title_labels):
                                end_time = start + duration
                                enable_expr = f"between(t,{start},{end_time})"
                                is_last_song = (i == len(song_title_labels)-1) and not mp3_cover_chains and not (use_soundwave_overlay and soundwave_idx is not None)
                                out_label = f"songtmp{i+1}" if i < len(song_title_labels)-1 else "songtmp_final"
                                filter_graph += f";{last_label}[{label}]overlay={x_expr}:{y_expr}:enable='{enable_expr}'[{out_label}]"
                                last_label = f"[{out_label}]"
                        continue
                    
                    # Handle MP3 cover overlays (special case)
                    if layer_id == 'mp3_cover_overlay' and mp3_cover_chains:
                        # Add MP3 cover input processing
                        filter_graph += ";" + ";".join(mp3_cover_chains)
                        # Apply MP3 cover overlays immediately
                        if mp3_cover_labels:
                            for i, (label, start, duration, x_expr, y_expr) in enumerate(mp3_cover_labels):
                                end_time = start + duration
                                enable_expr = f"between(t,{start},{end_time})"
                                current_layer_index = final_order.index('mp3_cover_overlay')
                                layers_after_mp3 = final_order[current_layer_index + 1:]
                                has_layers_after = any(layer in layers_after_mp3 for layer in ['song_titles', 'soundwave'])
                                is_last_mp3 = (i == len(mp3_cover_labels)-1) and not has_layers_after
                                out_label = f"mp3covertmp{i+1}" if i < len(mp3_cover_labels)-1 else "mp3covertmp_final"
                                filter_graph += f";{last_label}[{label}]overlay={x_expr}:{y_expr}:enable='{enable_expr}'[{out_label}]"
                                last_label = f"[{out_label}]"
                        continue
                    
                    # Handle soundwave (special case)
                    if layer_id == 'soundwave' and use_soundwave_overlay and soundwave_idx is not None:
                        # Add soundwave input processing
                        filter_graph += f";[{soundwave_idx}:v]format=yuva420p[soundwave]"
                        # Apply soundwave overlay immediately
                        current_layer_index = final_order.index('soundwave')
                        is_last_layer = (current_layer_index == len(final_order) - 1)
                        out_label = "soundwave_final"
                        filter_graph += f";{last_label}[soundwave]overlay={ox_soundwave}:{oy_soundwave}[{out_label}]"
                        last_label = f"[{out_label}]"
                        continue
                    
                    # Handle regular overlays
                    if config['filter']:
                        # Add input processing filter
                        filter_graph += f";{config['filter']}"
                        
                        # Apply overlay immediately
                        if layer_id == 'overlay8' and config.get('intervals'):
                            # Build combined enable expression for all intervals
                            intervals = config['intervals']
                            enable_expr = "+".join([
                                f"between(t,{start},{start+duration})" for start, duration in intervals if duration > 0
                            ])
                            input_label = config['overlay'].split(']')[0] + ']' if ']' in config['overlay'] else config['overlay']
                            output_label = f"tmp_{layer_id}"
                            overlay_params = config['overlay'].split('overlay=')[1]
                            filter_graph += f";{last_label}{input_label}overlay={overlay_params}:enable='{enable_expr}'[{output_label}]"
                            last_label = f"[{output_label}]"
                        elif layer_id == 'overlay9' and config.get('intervals'):
                            # Build combined enable expression for all intervals
                            intervals = config['intervals']
                            enable_expr = "+".join([
                                f"between(t,{start},{start+duration})" for start, duration in intervals if duration > 0
                            ])
                            input_label = config['overlay'].split(']')[0] + ']' if ']' in config['overlay'] else config['overlay']
                            output_label = f"tmp_{layer_id}"
                            overlay_params = config['overlay'].split('overlay=')[1]
                            filter_graph += f";{last_label}{input_label}overlay={overlay_params}:enable='{enable_expr}'[{output_label}]"
                            last_label = f"[{output_label}]"
                        elif config['duration_control'] is None:
                            # No duration control (like overlay3)
                            # Extract the input label from the overlay filter (e.g., "[ol1]" from "[ol1]overlay={ox1}:{oy1}")
                            input_label = config['overlay'].split(']')[0] + ']' if ']' in config['overlay'] else config['overlay']
                            output_label = f"tmp_{layer_id}"
                            filter_graph += f";{last_label}{input_label}overlay={config['overlay'].split('overlay=')[1]}[{output_label}]"
                            last_label = f"[{output_label}]"
                        elif config['duration_control']:
                            # Full duration
                            input_label = config['overlay'].split(']')[0] + ']' if ']' in config['overlay'] else config['overlay']
                            output_label = f"tmp_{layer_id}"
                            overlay_params = config['overlay'].split('overlay=')[1]
                            filter_graph += f";{last_label}{input_label}overlay={overlay_params}:enable='gte(t,{config['start_time']})'[{output_label}]"
                            last_label = f"[{output_label}]"
                        else:
                            # Time-based enable expressions
                            end_time = config['start_time'] + config['duration']
                            input_label = config['overlay'].split(']')[0] + ']' if ']' in config['overlay'] else config['overlay']
                            output_label = f"tmp_{layer_id}"
                            overlay_params = config['overlay'].split('overlay=')[1]
                            filter_graph += f";{last_label}{input_label}overlay={overlay_params}:enable='between(t,{config['start_time']},{end_time})'[{output_label}]"
                            last_label = f"[{output_label}]"
                
                # Handle final output for alternative mode - always add format filter
                if last_label != "[vout_final]":
                    filter_graph += f";{last_label}format={VIDEO_SETTINGS['pixel_format']}[vout_final]"
                    final_output_label = "[vout_final]"
                else:
                    final_output_label = last_label
            else:
                # Original approach: 2-grouping with input processing first, then overlay applications
                filter_graph = filter_bg
                last_label = "[bg]"
                
                # 1. Add all input processing filters in the same order as overlay applications
                if input_processing_filters:
                    filter_graph += ";" + ";".join(input_processing_filters)
                
                # 2. Add overlay applications in the same order as layer_order
                for layer_id in final_order:
                    if layer_id == 'background':
                        continue  # Background is already the base
                    
                    config = layer_configs.get(layer_id)
                    if not config:
                        continue
                    
                    # Handle song titles (special case)
                    if layer_id == 'song_titles' and song_title_labels:
                        for i, (label, start, duration, x_expr, y_expr) in enumerate(song_title_labels):
                            # 🚀 PRE-CALCULATION OPTIMIZATION: Time-based enable expressions
                            # Pre-calculate end time instead of real-time addition
                            end_time = start + duration
                            enable_expr = f"between(t,{start},{end_time})"
                            is_last_song = (i == len(song_title_labels)-1) and not mp3_cover_chains and not (use_soundwave_overlay and soundwave_idx is not None)
                            out_label = f"songtmp{i+1}" if i < len(song_title_labels)-1 else "songtmp_final"
                            filter_graph += f";{last_label}[{label}]overlay={x_expr}:{y_expr}:enable='{enable_expr}'[{out_label}]"
                            last_label = f"[{out_label}]"
                        continue
                    
                    # Handle MP3 cover overlays (special case)
                    if layer_id == 'mp3_cover_overlay' and mp3_cover_labels:
                        for i, (label, start, duration, x_expr, y_expr) in enumerate(mp3_cover_labels):
                            # 🚀 PRE-CALCULATION OPTIMIZATION: Time-based enable expressions
                            # Pre-calculate end time instead of real-time addition
                            end_time = start + duration
                            enable_expr = f"between(t,{start},{end_time})"
                            # Check if this is the last MP3 cover AND if there are layers after mp3_cover_overlay in the order
                            current_layer_index = final_order.index('mp3_cover_overlay')
                            layers_after_mp3 = final_order[current_layer_index + 1:]
                            has_layers_after = any(layer in layers_after_mp3 for layer in ['song_titles', 'soundwave'])
                            is_last_mp3 = (i == len(mp3_cover_labels)-1) and not has_layers_after
                            out_label = f"mp3covertmp{i+1}" if i < len(mp3_cover_labels)-1 else "mp3covertmp_final"
                            filter_graph += f";{last_label}[{label}]overlay={x_expr}:{y_expr}:enable='{enable_expr}'[{out_label}]"
                            last_label = f"[{out_label}]"
                        continue
                    
                    # Handle soundwave (special case)
                    if layer_id == 'soundwave' and use_soundwave_overlay and soundwave_idx is not None:
                        # Check if soundwave is the last layer in the order
                        current_layer_index = final_order.index('soundwave')
                        is_last_layer = (current_layer_index == len(final_order) - 1)
                        out_label = "soundwave_final"
                        filter_graph += f";{last_label}[soundwave]overlay={ox_soundwave}:{oy_soundwave}[{out_label}]"
                        last_label = f"[{out_label}]"
                        continue
                    
                    # Handle regular overlays
                    if config['filter']:
                        # Find the corresponding overlay filter
                        for overlay_filter, tmp_label in overlay_application_filters:
                            if f"tmp_{layer_id}" in overlay_filter or layer_id in overlay_filter:
                                filter_graph += f";{last_label}{overlay_filter}"
                                if tmp_label:
                                    last_label = f"[{tmp_label}]"
                                else:
                                    # Extract the output label from the overlay filter
                                    if "[" in overlay_filter and "]" in overlay_filter.split("[")[-1]:
                                        output_label = overlay_filter.split("[")[-1].split("]")[0]
                                        last_label = f"[{output_label}]"
                                break
            
            # Handle final output - add format filter if not already added (only for original mode)
            if not filter_complex_alt_mode:
                if song_title_chains or mp3_cover_chains or (use_soundwave_overlay and soundwave_idx is not None):
                    # Song titles, MP3 covers, or soundwave were processed - they should have created [vout]
                    # But if they didn't (e.g., songtmp_final), we need to add format filter
                    if last_label != "[vout]" and not last_label.endswith("_final]"):
                        filter_graph += f";{last_label}format={VIDEO_SETTINGS['pixel_format']}[vout_final]"
                        final_output_label = "[vout_final]"
                    elif last_label == "[vout]":
                        # [vout] already exists but needs format filter
                        filter_graph += f";[vout]format={VIDEO_SETTINGS['pixel_format']}[vout_final]"
                        final_output_label = "[vout_final]"
                    else:
                        # Check if we need to add format to _final labels
                        if last_label.endswith("_final]"):
                            filter_graph += f";{last_label}format={VIDEO_SETTINGS['pixel_format']}[vout_final]"
                            final_output_label = "[vout_final]"
                        else:
                            final_output_label = last_label if last_label != "[bg]" else "[vout_final]"
                else:
                    # No song titles, MP3 covers, or soundwave - add format filter
                    filter_graph += f";{last_label}format={VIDEO_SETTINGS['pixel_format']}[vout_final]"
                    final_output_label = "[vout_final]"
        else:
            # Check if background is preprocessed (already correct size)
            # Background is always PNG, so no need to check for GIF
            bg_filename = os.path.basename(image_path_for_ffmpeg)
            is_bg_preprocessed = bg_filename.startswith("supercut_")
            
            # Show alt mode status for background-only videos too
            if filter_complex_alt_mode:
                print(f"🔧 Filter Complex Alt Mode: ON (background-only video)")
            
            if is_bg_preprocessed:
                # Background is preprocessed PNG - no scaling needed
                filter_graph = f"[0:v]format={VIDEO_SETTINGS['pixel_format']}[vout_final]"
            else:
                # Background needs scaling to target resolution
                filter_graph = f"[0:v]scale={width}:{height},format={VIDEO_SETTINGS['pixel_format']}[vout_final]"
            # For simple background-only videos, the output is always [vout_final]
            final_output_label = "[vout_final]"
        
        cmd.extend(["-filter_complex", filter_graph, "-map", final_output_label, "-map", "1:a"])

        cmd.extend(["-c:v", codec, "-preset", preset])       

        # Rate control based on input image type
        if image_path_for_ffmpeg.lower().endswith('.gif'):
            cmd.extend(["-rc", "vbr", "-cq", "19"])
        elif image_path_for_ffmpeg.lower().endswith('.png'):
            cmd.extend(["-rc", "cbr"])        

        # Video settings
        video_bitrate_str = str(video_bitrate)
        maxrate_str = str(maxrate)
        buffer_size_str = str(bufsize)
        audio_bitrate_str = str(audio_bitrate)
        cmd.extend([   
            "-b:v", video_bitrate_str,
            "-maxrate", maxrate_str,
            "-bufsize", buffer_size_str     
        ])

        # Audio settings
        cmd.extend([   
            "-c:a", VIDEO_SETTINGS["audio_codec"],
            "-b:a", audio_bitrate_str,
            "-ar", VIDEO_SETTINGS["audio_sample_rate"],
            "-ac", VIDEO_SETTINGS["audio_channels"]
        ])
       
        cmd.extend([
            "-r", str(fps),
            "-g", VIDEO_SETTINGS["gop_size"],
            "-bf", VIDEO_SETTINGS["bframes"],
            "-profile:v", VIDEO_SETTINGS["profile"],
            "-level:v", VIDEO_SETTINGS["level"],
            "-movflags", "+faststart", 
            "-shortest",
            "-y"
        ])              
        
        cmd.append(output_path)

        # Display raw FFmpeg command for debugging performance bottlenecks
        print(f"🔧 RAW FFMPEG COMMAND (for performance analysis):")
        raw_cmd = " ".join(cmd)
        print(raw_cmd)
        print()

        audio_duration = get_audio_duration(audio_path)
        total_frames = int(audio_duration * fps)
        
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)

        start_time = time.time()
        last_seconds = 0.0
        last_update = time.time()
        current_its = "--"
        def print_progress(seconds: float):
            current_frame = int(seconds * fps)
            percent = min(100.0, (current_frame / total_frames) * 100) if total_frames > 0 else 0
            elapsed = time.time() - start_time
            speed = (current_frame / elapsed) if elapsed > 0 else 0
            remaining_frames = total_frames - current_frame
            eta_sec = int(remaining_frames / speed) if speed > 0 else 0
            eta_str = time.strftime('%H:%M:%S', time.gmtime(eta_sec)) if eta_sec > 0 else "--:--:--"
            sys.stdout.write(
                f"\r  {percent:5.1f}% | Frame: {current_frame}/{total_frames} | ETA: {eta_str} | it/s: {current_its} 🚀 "
            )
            sys.stdout.flush()
        try:
            if process.stderr is not None:
                for line in process.stderr:
                    its_patterns = [
                        r'speed=(\d+\.?\d*)x',
                        r'fps=(\d+\.?\d*)',
                        r'(\d+\.?\d*)\s*it/s',
                    ]
                    for pattern in its_patterns:
                        match = re.search(pattern, line)
                        if match:
                            try:
                                its_value = float(match.group(1))
                                current_its = f"{its_value:0.3f}"
                                break
                            except ValueError:
                                continue
                    match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                    if match:
                        h, m, s = map(float, match.groups())
                        seconds = h * 3600 + m * 60 + s
                        last_seconds = seconds
                        last_update = time.time()
                        print_progress(seconds)
                        now = time.time()
                        while (now - last_update) < 0.2:
                            interp_seconds = last_seconds + (now - last_update)
                            if interp_seconds > audio_duration:
                                interp_seconds = audio_duration
                            print_progress(interp_seconds)
                            time.sleep(0.1)
                            now = time.time()
        except Exception as e:
            msg = f"Error reading ffmpeg output: {e}"
            logger.error(msg)
            return False, msg
        finally:
            if process.stderr is not None:
                process.stderr.close()
            process.wait()
            sys.stdout.flush()
        sys.stdout.write(
            f"\r  100.0% | Frame: {total_frames}/{total_frames} | ETA: 00:00:00 | it/s: {current_its} 🚀\n"
        )
        sys.stdout.flush()
        if process.returncode != 0:
            msg = f"FFmpeg failed with return code {process.returncode}."
            logger.error(msg)
            return False, msg
        return True, None
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        msg = f"Error creating video: {e}"
        logger.error(msg)
        return False, msg
    finally:
        if temp_png_path and os.path.exists(temp_png_path):
            try:
                os.unlink(temp_png_path)
            except FileNotFoundError:
                logger.warning(f"Temp PNG {temp_png_path} not found for removal.")
            except PermissionError:
                logger.warning(f"No permission to remove temp PNG {temp_png_path}.")
            except OSError as e:
                logger.warning(f"OS error removing temp PNG {temp_png_path}: {e}")





def merge_random_mp3s(selected_mp3s: list) -> Tuple[Optional[str], float]:
    """Merge MP3 files using ffmpeg - returns output path and duration"""
    from src.utils import create_temp_file
    
    output_path = create_temp_file(suffix=".m4a")  # Changed from .mp3 to .m4a
    
    if merge_mp3s_with_ffmpeg(selected_mp3s, output_path):
        duration = get_audio_duration(output_path)
        return output_path, duration
    else:
        return None, 0.0 