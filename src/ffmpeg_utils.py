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

def create_video_with_ffmpeg(
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
    extra_overlays: Optional[List[dict]] = None,  # List of dicts: {path, start, duration, fade}
    song_title_effect: str = "fadeinout",
    song_title_font: str = "default",
    song_title_font_size: int = 32,
    song_title_color: tuple = (255, 255, 255),
    song_title_bg: str = "transparent",
    song_title_bg_color: tuple = (0, 0, 0),
    song_title_opacity: float = 1.0,
    song_title_scale_percent: int = 100,
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
    overlay1_start_at: int = 0,
    overlay2_start_at: int = 0
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
        input_idx = 2
        if use_intro and intro_path and ext_intro in ['.gif', '.png']:
            if ext_intro == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", intro_path])
            elif ext_intro == '.png':
                cmd.extend(["-loop", "1", "-i", intro_path])
            else:
                cmd.extend(["-i", intro_path])
            intro_idx = input_idx
            input_idx += 1
        if use_overlay and overlay1_path and ext1 in ['.gif', '.png']:
            if ext1 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay1_path])
            elif ext1 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay1_path])
            else:
                cmd.extend(["-i", overlay1_path])
            overlay1_idx = input_idx
            input_idx += 1
        if use_overlay2 and overlay2_path and ext2 in ['.gif', '.png']:
            if ext2 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay2_path])
            elif ext2 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay2_path])
            else:
                cmd.extend(["-i", overlay2_path])
            overlay2_idx = input_idx
            input_idx += 1
        if use_overlay3 and overlay3_path and ext3 in ['.gif', '.png']:
            if ext3 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay3_path])
            elif ext3 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay3_path])
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
        if use_overlay8 and overlay8_path and ext8 in ['.gif', '.png']:
            if ext8 == '.gif':
                cmd.extend(["-stream_loop", "-1", "-i", overlay8_path])
            elif ext8 == '.png':
                cmd.extend(["-loop", "1", "-i", overlay8_path])
            else:
                cmd.extend(["-i", overlay8_path])
            overlay8_idx = input_idx
            input_idx += 1
        # --- Add extra overlays (song titles) as inputs ---
        extra_overlay_indices = []
        if extra_overlays:
            for overlay in extra_overlays:
                cmd.extend(["-loop", "1", "-i", overlay['path']])
                extra_overlay_indices.append(input_idx)
                input_idx += 1
        # --- End Song Title Overlay Filter Graph ---
        # Build filter graph with correct indices
        overlays_present = use_intro or use_overlay or use_overlay2 or use_overlay3 or use_overlay4 or use_overlay5 or use_overlay6 or use_overlay7 or use_overlay8 or bool(extra_overlays)
        if overlays_present:
            scale_factor_intro = intro_size_percent / 100.0
            owi = f"iw*{scale_factor_intro:.3f}"
            ohi = f"ih*{scale_factor_intro:.3f}"
            scale_factor1 = overlay1_size_percent / 100.0
            ow1 = f"iw*{scale_factor1:.3f}"
            oh1 = f"ih*{scale_factor1:.3f}"
            scale_factor2 = overlay2_size_percent / 100.0
            ow2 = f"iw*{scale_factor2:.3f}"
            oh2 = f"ih*{scale_factor2:.3f}"
            scale_factor3 = overlay3_size_percent / 100.0
            ow3 = f"iw*{scale_factor3:.3f}"
            oh3 = f"ih*{scale_factor3:.3f}"
            scale_factor4 = overlay4_size_percent / 100.0
            ow4 = f"iw*{scale_factor4:.3f}"
            oh4 = f"ih*{scale_factor4:.3f}"
            scale_factor5 = overlay5_size_percent / 100.0
            ow5 = f"iw*{scale_factor5:.3f}"
            oh5 = f"ih*{scale_factor5:.3f}"
            scale_factor6 = overlay6_size_percent / 100.0
            ow6 = f"iw*{scale_factor6:.3f}"
            oh6 = f"ih*{scale_factor6:.3f}"
            scale_factor7 = overlay7_size_percent / 100.0
            ow7 = f"iw*{scale_factor7:.3f}"
            oh7 = f"ih*{scale_factor7:.3f}"
            scale_factor8 = overlay8_size_percent / 100.0
            ow8 = f"iw*{scale_factor8:.3f}"
            oh8 = f"ih*{scale_factor8:.3f}"
            position_map = {
                "top_left": ("0", "0"),
                "top_right": (f"W-w", "0"),
                "bottom_left": ("0", f"H-h"),
                "bottom_right": (f"W-w", f"H-h"),
                "center": ("(W-w)/2", "(H-h)/2")
            }
            # Calculate intro position using X and Y percentages
            ox_intro = f"(W-w)*{intro_x_percent}/100" if intro_x_percent != 0 else "0"
            oy_intro = f"(H-h)*(1-({intro_y_percent}/100))" if intro_y_percent != 100 else "0"
            ox1 = f"(W-w)*{overlay1_x_percent}/100" if overlay1_x_percent != 0 else "0"
            oy1 = f"(H-h)*(1-({overlay1_y_percent}/100))" if overlay1_y_percent != 100 else "0"
            ox2 = f"(W-w)*{overlay2_x_percent}/100" if overlay2_x_percent != 0 else "0"
            oy2 = f"(H-h)*(1-({overlay2_y_percent}/100))" if overlay2_y_percent != 100 else "0"
            ox3 = f"(W-w)*{overlay3_x_percent}/100" if overlay3_x_percent != 0 else "0"
            oy3 = f"(H-h)*(1-({overlay3_y_percent}/100))" if overlay3_y_percent != 100 else "0"
            ox4 = f"(W-w)*{overlay4_x_percent}/100" if overlay4_x_percent != 0 else "0"
            oy4 = f"(H-h)*(1-({overlay4_y_percent}/100))" if overlay4_y_percent != 100 else "0"
            ox5 = f"(W-w)*{overlay5_x_percent}/100" if overlay5_x_percent != 0 else "0"
            oy5 = f"(H-h)*(1-({overlay5_y_percent}/100))" if overlay5_y_percent != 100 else "0"
            ox6 = f"(W-w)*{overlay6_x_percent}/100" if overlay6_x_percent != 0 else "0"
            oy6 = f"(H-h)*(1-({overlay6_y_percent}/100))" if overlay6_y_percent != 100 else "0"
            ox7 = f"(W-w)*{overlay7_x_percent}/100" if overlay7_x_percent != 0 else "0"
            oy7 = f"(H-h)*(1-({overlay7_y_percent}/100))" if overlay7_y_percent != 100 else "0"
            ox8 = f"(W-w)*{overlay8_x_percent}/100" if overlay8_x_percent != 0 else "0"
            oy8 = f"(H-h)*(1-({overlay8_y_percent}/100))" if overlay8_y_percent != 100 else "0"
            filter_bg = f"[0:v]scale={int(width*1.03)}:{int(height*1.03)},crop={width}:{height}[bg]"

            # Effect logic for overlays
            def overlay_effect_chain(idx, scale_expr, label, effect, effect_time, ext, duration=None):
                if idx is None:
                    return ""
                
                # Debug effect chain parameters
                if label == "ol8":
                    print(f"Effect Chain Debug - {label}: effect_time={effect_time}, effect={effect}, duration={duration}")
                
                chain = f"[{idx}:v]"
                if ext == ".gif":
                    chain += "fps=30,"
                chain += "format=rgba,"
                fade_alpha = ":alpha=1" if ext == ".png" else ""
                if effect == "fadeinout":
                    fadein_duration = 1.5
                    fadeout_duration = 1.5
                    # Calculate hold duration based on total duration
                    if duration is not None:
                        hold_duration = max(0, duration - fadein_duration - fadeout_duration)
                    else:
                        hold_duration = 5  # Fallback to 5 seconds if no duration provided
                    fadein_end = effect_time + fadein_duration
                    fadeout_start = fadein_end + hold_duration
                    chain += f"fade=t=in:st={effect_time}:d={fadein_duration}{fade_alpha},fade=t=out:st={fadeout_start}:d={fadeout_duration}{fade_alpha},"
                elif effect == "fadein":
                    chain += f"fade=t=in:st={effect_time}:d=1{fade_alpha},"
                elif effect == "fadeout":
                    chain += f"fade=t=out:st={effect_time}:d=1{fade_alpha},"
                elif effect == "zoompan":
                    chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
                chain += f"scale={scale_expr}[{label}]"
                return chain

            def intro_effect_chain(idx, scale_expr, label, effect, duration, start_at, ext):
                if idx is None:
                    return ""
                chain = f"[{idx}:v]"
                if ext == ".gif":
                    chain += "fps=30,"
                chain += "format=rgba,"
                fade_alpha = ":alpha=1" if ext == ".png" else ""
                if effect == "fadein":
                    chain += f"fade=t=in:st={start_at}:d=1{fade_alpha},"
                elif effect == "fadeout":
                    # Use duration if provided, otherwise use default calculation
                    if duration is not None:
                        fadeout_start = start_at + duration - 1.5
                    else:
                        fadeout_start = start_at + 6 - 1.5  # Default 6 seconds
                    chain += f"fade=t=out:st={fadeout_start}:d=1.5{fade_alpha},"
                elif effect == "fadeinout":
                    # Use duration if provided, otherwise use default calculation
                    if duration is not None:
                        fadeout_start = start_at + duration - 1.5
                    else:
                        fadeout_start = start_at + 6 - 1.5  # Default 6 seconds
                    chain += f"fade=t=in:st={start_at}:d=1.5{fade_alpha},fade=t=out:st={fadeout_start}:d=1.5{fade_alpha},"
                elif effect == "zoompan":
                    chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
                chain += f"scale={scale_expr}[{label}]"
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
            
            # Debug overlay8 parameters
            print(f"FFmpeg Debug - Overlay8: start_time={overlay8_start_time}, duration={overlay8_duration}, effect={overlay8_effect}")
            
            filter_overlay8 = overlay_effect_chain(overlay8_idx, f"{ow8}:{oh8}", "ol8", overlay8_effect, overlay8_start_time, ext8, overlay8_actual_duration) if overlay8_idx is not None else ""
            # --- Song Title Overlay Filter Graph ---
            filter_chains = []
            overlay_labels = []
            if extra_overlays:
                for i, overlay in enumerate(extra_overlays):
                    idx = extra_overlay_indices[i]
                    start = overlay.get('start', 0)
                    duration = overlay.get('duration', 0)
                    x_percent = overlay.get('x_percent', 0)
                    y_percent = overlay.get('y_percent', 0)
                    
                    # Check if this is an overlay8 popup overlay (has size_percent and effect)
                    is_overlay8_popup = 'size_percent' in overlay and 'effect' in overlay
                    
                    if is_overlay8_popup:
                        # Overlay8 popup overlay - use its own scaling and effects
                        size_percent = overlay.get('size_percent', 100)
                        effect = overlay.get('effect', 'fadein')
                        scale_factor = size_percent / 100.0
                        scale_expr = f"iw*{scale_factor:.3f}:ih*{scale_factor:.3f}"
                        label = f"popupol{i+1}"
                        
                        # Calculate x/y as expressions based on percent
                        x_expr = f"(W-w)*{x_percent}/100" if x_percent != 0 else "0"
                        y_expr = f"(H-h)*(1-({y_percent}/100))" if y_percent != 100 else "0"
                        
                        # Build effect chain for overlay8 popup
                        chain = f"[{idx}:v]"
                        ext = os.path.splitext(overlay.get('path', ''))[1].lower()
                        if ext == ".gif":
                            chain += "fps=30,"
                        chain += "format=rgba,"
                        
                        # Apply effect based on overlay8 effect
                        fade_alpha = ":alpha=1" if ext == ".png" else ""
                        if effect == "fadeinout":
                            fadein_duration = 1.5
                            fadeout_duration = 1.5
                            hold_duration = max(0, duration - fadein_duration - fadeout_duration)
                            fadein_end = start + fadein_duration
                            fadeout_start = fadein_end + hold_duration
                            chain += f"fade=t=in:st={start}:d={fadein_duration}{fade_alpha},fade=t=out:st={fadeout_start}:d={fadeout_duration}{fade_alpha},"
                        elif effect == "fadein":
                            chain += f"fade=t=in:st={start}:d=1{fade_alpha},"
                        elif effect == "fadeout":
                            chain += f"fade=t=out:st={start}:d=1{fade_alpha},"
                        elif effect == "zoompan":
                            chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
                        
                        chain += f"scale={scale_expr}[{label}]"
                        filter_chains.append(chain)
                        overlay_labels.append((label, start, duration, x_expr, y_expr))
                        
                    else:
                        # Song title overlay - use existing logic
                        scale = song_title_scale_percent / 100.0 if song_title_scale_percent else 1.0
                        scaled_w = round(1920 * scale)
                        scaled_h = round(240 * scale)
                        label = f"songol{i+1}"
                        
                        # Calculate x/y as expressions based on percent
                        x_expr = f"(W-w)*{x_percent}/100" if x_percent != 0 else "0"
                        # For Y: 0% = bottom, 100% = top
                        y_expr = f"(H-h)*(1-({y_percent}/100))" if y_percent != 100 else "0"
                        chain = f"[{idx}:v]format=rgba,scale={scaled_w}:{scaled_h}"
                        
                        # Apply song title effect based on song_title_effect parameter
                        if song_title_effect == "fadeinout":
                            chain += f",fade=t=in:st={start}:d=1:alpha=1,fade=t=out:st={start+duration-1}:d=1:alpha=1"
                        elif song_title_effect == "fadein":
                            chain += f",fade=t=in:st={start}:d=1:alpha=1"
                        elif song_title_effect == "fadeout":
                            chain += f",fade=t=out:st={start+duration-1}:d=1:alpha=1"
                        elif song_title_effect == "zoompan":
                            chain += f",zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        # For "none" effect, no additional effects are applied
                        
                        chain += f"[{label}]"
                        filter_chains.append(chain)
                        overlay_labels.append((label, start, duration, x_expr, y_expr))
            # --- End Song Title Overlay Filter Graph ---
            filter_graph = filter_bg
            last_label = "[bg]"
            # Overlay 1
            if filter_overlay1:
                filter_graph += f";{filter_overlay1}"
                # Use duration control like overlay8 if duration full checkbox is not checked
                if overlay1_2_duration_full_checkbox_checked:
                    # Full duration - show for entire video
                    filter_graph += f";[bg][ol1]overlay={ox1}:{oy1}:enable='gte(t,{overlay1_start_at})'[tmp1]"
                else:
                    # Limited duration - show for specified duration
                    filter_graph += f";[bg][ol1]overlay={ox1}:{oy1}:enable='between(t,{overlay1_start_at},{overlay1_start_at+overlay1_2_duration})'[tmp1]"
                last_label = "[tmp1]"
            # Overlay 2
            if filter_overlay2:
                filter_graph += f";{filter_overlay2}"
                # Use duration control like overlay8 if duration full checkbox is not checked
                if overlay1_2_duration_full_checkbox_checked:
                    # Full duration - show for entire video
                    filter_graph += f";{last_label}[ol2]overlay={ox2}:{oy2}:enable='gte(t,{overlay2_start_at})'[tmp2]"
                else:
                    # Limited duration - show for specified duration
                    filter_graph += f";{last_label}[ol2]overlay={ox2}:{oy2}:enable='between(t,{overlay2_start_at},{overlay2_start_at+overlay1_2_duration})'[tmp2]"
                last_label = "[tmp2]"
            # Overlay 3
            if filter_overlay3:
                filter_graph += f";{filter_overlay3}"
                filter_graph += f";{last_label}[ol3]overlay={ox3}:{oy3}[tmp3]"
                last_label = "[tmp3]"
            # Overlay 4
            if filter_overlay4:
                filter_graph += f";{filter_overlay4}"
                # Use duration control like overlay8 if duration full checkbox is not checked
                if overlay4_duration_full_checkbox_checked:
                    # Full duration - show for entire video
                    filter_graph += f";{last_label}[ol4]overlay={ox4}:{oy4}:enable='gte(t,{overlay4_start_time})'[tmp4]"
                else:
                    # Limited duration - show for specified duration
                    filter_graph += f";{last_label}[ol4]overlay={ox4}:{oy4}:enable='between(t,{overlay4_start_time},{overlay4_start_time+overlay4_duration})'[tmp4]"
                last_label = "[tmp4]"
            # Overlay 5
            if filter_overlay5:
                filter_graph += f";{filter_overlay5}"
                # Use duration control like overlay8 if duration full checkbox is not checked
                if overlay5_duration_full_checkbox_checked:
                    # Full duration - show for entire video
                    filter_graph += f";{last_label}[ol5]overlay={ox5}:{oy5}:enable='gte(t,{overlay5_start_time})'[tmp5]"
                else:
                    # Limited duration - show for specified duration
                    filter_graph += f";{last_label}[ol5]overlay={ox5}:{oy5}:enable='between(t,{overlay5_start_time},{overlay5_start_time+overlay5_duration})'[tmp5]"
                last_label = "[tmp5]"
            # Overlay 6
            if filter_overlay6:
                filter_graph += f";{filter_overlay6}"
                # Use duration control like overlay8 if duration full checkbox is not checked
                if overlay6_duration_full_checkbox_checked:
                    # Full duration - show for entire video
                    filter_graph += f";{last_label}[ol6]overlay={ox6}:{oy6}:enable='gte(t,{overlay6_start_time})'[tmp6]"
                else:
                    # Limited duration - show for specified duration
                    filter_graph += f";{last_label}[ol6]overlay={ox6}:{oy6}:enable='between(t,{overlay6_start_time},{overlay6_start_time+overlay6_duration})'[tmp6]"
                last_label = "[tmp6]"
            # Overlay 7
            if filter_overlay7:
                filter_graph += f";{filter_overlay7}"
                # Use duration control like overlay8 if duration full checkbox is not checked
                if overlay7_duration_full_checkbox_checked:
                    # Full duration - show for entire video
                    filter_graph += f";{last_label}[ol7]overlay={ox7}:{oy7}:enable='gte(t,{overlay7_start_time})'[tmp7]"
                else:
                    # Limited duration - show for specified duration
                    filter_graph += f";{last_label}[ol7]overlay={ox7}:{oy7}:enable='between(t,{overlay7_start_time},{overlay7_start_time+overlay7_duration})'[tmp7]"
                last_label = "[tmp7]"
            # Overlay 8
            if filter_overlay8:
                filter_graph += f";{filter_overlay8}"
                # Use duration control like intro if duration full checkbox is not checked
                if overlay8_duration_full_checkbox_checked:
                    # Full duration - show for entire video
                    filter_graph += f";{last_label}[ol8]overlay={ox8}:{oy8}:enable='gte(t,{overlay8_start_time})'[tmp8]"
                else:
                    # Limited duration - show for specified duration
                    filter_graph += f";{last_label}[ol8]overlay={ox8}:{oy8}:enable='between(t,{overlay8_start_time},{overlay8_start_time+overlay8_duration})'[tmp8]"
                last_label = "[tmp8]"
            # Intro
            if filter_intro:
                filter_graph += f";{filter_intro}"
                # Use duration control like overlays if duration full checkbox is not checked
                if intro_duration_full_checkbox_checked:
                    # Full duration - show for entire video
                    filter_graph += f";{last_label}[oi]overlay={ox_intro}:{oy_intro}:enable='gte(t,{intro_start_at})'[v1]"
                else:
                    # Limited duration - show for specified duration
                    filter_graph += f";{last_label}[oi]overlay={ox_intro}:{oy_intro}:enable='between(t,{intro_start_at},{intro_start_at+intro_duration})'[v1]"
                last_label = "[v1]"
            # Extra overlays
            if filter_chains:
                filter_graph += ";" + ";".join(filter_chains)
                for i, (label, start, duration, x_expr, y_expr) in enumerate(overlay_labels):
                    enable_expr = f"between(t,{start},{start+duration})"
                    out_label = f"songtmp{i+1}" if i < len(overlay_labels)-1 else "vout"
                    filter_graph += f";{last_label}[{label}]overlay={x_expr}:{y_expr}:enable='{enable_expr}'[{out_label}]"
                    last_label = f"[{out_label}]"
            else:
                filter_graph += f";{last_label}format={VIDEO_SETTINGS['pixel_format']}[vout]"
        else:
            filter_graph = f"[0:v]scale={int(width*1.03)}:{int(height*1.03)},crop={width}:{height},format={VIDEO_SETTINGS['pixel_format']}[vout]"
        cmd.extend(["-filter_complex", filter_graph, "-map", "[vout]", "-map", "1:a"])

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

        # Display FFmpeg command with output video name
        video_name = os.path.basename(output_path)        
        print(f"📝 FFMPEG COMMAND:")        
        display_cmd = ['✨ ffmpeg'] + cmd[1:]
        print(f"  {' '.join(display_cmd)} ✨")           

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