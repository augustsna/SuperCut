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
    """Merge multiple MP3 files using ffmpeg"""
    try:
        # Create a file list for ffmpeg
        file_list_path = create_temp_file(suffix='.txt')
        with open(file_list_path, 'w') as f:
            for file_path in input_files:
                f.write(f"file '{file_path}'\n")
        
        # Use ffmpeg to concatenate
        cmd = [
            FFMPEG_BINARY,
            "-f", "concat",
            "-safe", "0",
            "-i", file_list_path,
            "-c", "copy",
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
    overlay1_position: str = "top_left",
    use_overlay2: bool = False,
    overlay2_path: str = "",
    overlay2_size_percent: int = 10,
    overlay2_position: str = "top_left",
    use_overlay3: bool = False,
    overlay3_path: str = "",
    overlay3_size_percent: int = 10,
    overlay3_position: str = "top_left",
    use_overlay4: bool = False,
    overlay4_path: str = "",
    overlay4_size_percent: int = 10,
    overlay4_position: str = "top_left",
    use_overlay5: bool = False,
    overlay5_path: str = "",
    overlay5_size_percent: int = 10,
    overlay5_position: str = "top_left",
    use_intro: bool = False,
    intro_path: str = "",
    intro_size_percent: int = 10,
    intro_position: str = "center",
    effect: str = "fadein",
    effect_time: int = 5,
    intro_effect: str = "fadeout",
    intro_duration: int = 5,
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
    song_title_opacity: float = 1.0
) -> Tuple[bool, Optional[str]]:
    if extra_overlays is None:
        extra_overlays = []
    temp_png_path = None
    try:
        # Debug: Print all file paths
        print("[DEBUG] Background image:", image_path)
        print("[DEBUG] Audio path:", audio_path)
        print("[DEBUG] Output path:", output_path)
        print("[DEBUG] Overlay 1 path:", overlay1_path)
        print("[DEBUG] Overlay 2 path:", overlay2_path)
        print("[DEBUG] Overlay Effect:", effect)
        print("[DEBUG] Overlay Effect Start Time:", effect_time)
        # Estimate required output file size
        audio_duration = get_audio_duration(audio_path)
        # Use the provided video_bitrate instead of VIDEO_SETTINGS['video_bitrate']
        video_bitrate_str = str(video_bitrate)
        maxrate_str = str(maxrate)
        buffer_size_str = str(bufsize)
        # Convert bitrate strings to int for calculation
        if video_bitrate_str.lower().endswith('m'):
            video_bitrate_int = int(float(video_bitrate_str[:-1]) * 1024 * 1024)
        elif video_bitrate_str.lower().endswith('k'):
            video_bitrate_int = int(float(video_bitrate_str[:-1]) * 1024)
        else:
            video_bitrate_int = int(video_bitrate_str)
        audio_bitrate_str = str(audio_bitrate)
        if audio_bitrate_str.lower().endswith('k'):
            audio_bitrate_int = int(float(audio_bitrate_str[:-1]) * 1024)
        else:
            audio_bitrate_int = int(audio_bitrate_str)
        total_bitrate = video_bitrate_int + audio_bitrate_int
        estimated_size = int((total_bitrate / 8) * audio_duration)  # bytes
        min_required = max(estimated_size * 2, 100 * 1024 * 1024)  # at least 2x estimated, or 100MB
        output_dir = os.path.dirname(os.path.abspath(output_path)) or os.getcwd()
        if not has_enough_disk_space(output_dir, min_required):
            msg = f"❌ Not enough disk space to create output video in {output_dir}. At least {min_required // (1024*1024)}MB required."
            logger.error(msg)
            print(msg)
            return False, msg
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
        ext_intro = os.path.splitext(intro_path)[1].lower() if intro_path else ''
        intro_idx = None
        overlay1_idx = None
        overlay2_idx = None
        overlay3_idx = None
        overlay4_idx = None
        overlay5_idx = None
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
        # --- Add extra overlays (song titles) as inputs ---
        extra_overlay_indices = []
        if extra_overlays:
            print("[DEBUG] extra_overlays (inputs):", extra_overlays)
            for overlay in extra_overlays:
                cmd.extend(["-loop", "1", "-i", overlay['path']])
                extra_overlay_indices.append(input_idx)
                input_idx += 1
        # --- End Song Title Overlay Filter Graph ---
        # Build filter graph with correct indices
        overlays_present = use_intro or use_overlay or use_overlay2 or use_overlay3 or use_overlay4 or use_overlay5 or bool(extra_overlays)
        print("[DEBUG] overlays_present:", overlays_present)
        print("[DEBUG] extra_overlays (filter graph):", extra_overlays)
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
            position_map = {
                "top_left": ("0", "0"),
                "top_right": (f"W-w", "0"),
                "bottom_left": ("0", f"H-h"),
                "bottom_right": (f"W-w", f"H-h"),
                "center": ("(W-w)/2", "(H-h)/2")
            }
            ox_intro, oy_intro = position_map.get(intro_position, ("(W-w)/2", "(H-h)/2"))
            ox1, oy1 = position_map.get(overlay1_position, ("0", "0"))
            ox2, oy2 = position_map.get(overlay2_position, ("0", "0"))
            ox3, oy3 = position_map.get(overlay3_position, ("0", "0"))
            ox4, oy4 = position_map.get(overlay4_position, ("0", "0"))
            ox5, oy5 = position_map.get(overlay5_position, ("0", "0"))
            filter_bg = f"[0:v]scale={int(width*1.03)}:{int(height*1.03)},crop={width}:{height}[bg]"

            # Effect logic for overlays
            def overlay_effect_chain(idx, scale_expr, label, effect, effect_time, ext):
                if idx is None:
                    return ""
                chain = f"[{idx}:v]"
                if ext == ".gif":
                    chain += "fps=30,"
                chain += "format=rgba,"
                fade_alpha = ":alpha=1" if ext == ".png" else ""
                if effect == "fadeinout":
                    chain += f"fade=t=in:st={effect_time}:d=1.5{fade_alpha},fade=t=out:st={effect_time+1.5}:d=1.5{fade_alpha},"
                elif effect == "fadein":
                    chain += f"fade=t=in:st={effect_time}:d=1{fade_alpha},"
                elif effect == "fadeout":
                    chain += f"fade=t=out:st={effect_time}:d=1{fade_alpha},"
                elif effect == "zoompan":
                    chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
                chain += f"scale={scale_expr}[{label}]"
                return chain

            def intro_effect_chain(idx, scale_expr, label, effect, duration, ext):
                if idx is None:
                    return ""
                chain = f"[{idx}:v]"
                if ext == ".gif":
                    chain += "fps=30,"
                chain += "format=rgba,"
                fade_alpha = ":alpha=1" if ext == ".png" else ""
                if effect == "fadein":
                    chain += f"fade=t=in:st=0:d=1{fade_alpha},"
                elif effect == "fadeout":
                    chain += f"fade=t=out:st={duration-1.5}:d=1.5{fade_alpha},"
                elif effect == "fadeinout":
                    chain += f"fade=t=in:st=0:d=1.5{fade_alpha},fade=t=out:st={duration-1.5}:d=1.5{fade_alpha},"
                elif effect == "zoompan":
                    chain += f"zoompan=z='min(1.5,zoom+0.005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',"
                chain += f"scale={scale_expr}[{label}]"
                return chain

            filter_intro = intro_effect_chain(intro_idx, f"{owi}:{ohi}", "oi", intro_effect, intro_duration, ext_intro) if intro_idx is not None else ""
            filter_overlay1 = overlay_effect_chain(overlay1_idx, f"{ow1}:{oh1}", "ol1", effect, effect_time, ext1) if overlay1_idx is not None else ""
            filter_overlay2 = overlay_effect_chain(overlay2_idx, f"{ow2}:{oh2}", "ol2", effect, effect_time, ext2) if overlay2_idx is not None else ""
            filter_overlay3 = overlay_effect_chain(overlay3_idx, f"{ow3}:{oh3}", "ol3", effect, effect_time, ext3) if overlay3_idx is not None else ""
            filter_overlay4 = overlay_effect_chain(overlay4_idx, f"{ow4}:{oh4}", "ol4", effect, effect_time, ext4) if overlay4_idx is not None else ""
            filter_overlay5 = overlay_effect_chain(overlay5_idx, f"{ow5}:{oh5}", "ol5", effect, effect_time, ext5) if overlay5_idx is not None else ""
            # --- Song Title Overlay Filter Graph ---
            filter_chains = []
            overlay_labels = []
            if extra_overlays:
                for i, overlay in enumerate(extra_overlays):
                    idx = extra_overlay_indices[i]
                    label = f"songol{i+1}"
                    start = overlay.get('start', 0)
                    duration = overlay.get('duration', 0)
                    x_percent = overlay.get('x_percent', 0)
                    y_percent = overlay.get('y_percent', 0)
                    # Calculate x/y as expressions based on percent
                    x_expr = f"(W-w)*{x_percent}/100" if x_percent != 0 else "0"
                    # For Y: 0% = bottom, 100% = top
                    y_expr = f"(H-h)*(1-({y_percent}/100))" if y_percent != 100 else "0"
                    chain = f"[{idx}:v]format=rgba,scale=1920:240"
                    
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
            print("[DEBUG] filter_chains:", filter_chains)
            print("[DEBUG] overlay_labels:", overlay_labels)
            # --- End Song Title Overlay Filter Graph ---
            # Compose overlays: Overlay 2, then Overlay 3, then Overlay 1, then Intro, then song title overlays
            filter_complex = f"[0:v]scale={int(width*1.03)}:{int(height*1.03)},crop={width}:{height}[bg];"
            if overlays_present:
                # Build filter chains for intro/overlay1/overlay2/overlay3
                if use_intro or use_overlay or use_overlay2 or use_overlay3 or use_overlay4 or use_overlay5:
                    filter_complex += filter_intro + ";" if filter_intro else ""
                    filter_complex += filter_overlay1 + ";" if filter_overlay1 else ""
                    filter_complex += filter_overlay2 + ";" if filter_overlay2 else ""
                    filter_complex += filter_overlay3 + ";" if filter_overlay3 else ""
                    filter_complex += filter_overlay4 + ";" if filter_overlay4 else ""
                    filter_complex += filter_overlay5 + ";" if filter_overlay5 else ""
                    bg_ref = "[bg]"
                    if overlay2_idx is not None:
                        filter_complex += f"{bg_ref}[ol2]overlay={ox2}:{oy2}:enable='gte(t,5)'[tmp2];"
                        bg_ref = "[tmp2]"
                    if overlay3_idx is not None:
                        filter_complex += f"{bg_ref}[ol3]overlay={ox3}:{oy3}:enable='gte(t,5)'[tmp3];"
                        bg_ref = "[tmp3]"
                    if overlay4_idx is not None:
                        filter_complex += f"{bg_ref}[ol4]overlay={ox4}:{oy4}:enable='gte(t,5)'[tmp4];"
                        bg_ref = "[tmp4]"
                    if overlay5_idx is not None:
                        filter_complex += f"{bg_ref}[ol5]overlay={ox5}:{oy5}:enable='gte(t,5)'[tmp5];"
                        bg_ref = "[tmp5]"
                    if overlay1_idx is not None:
                        filter_complex += f"{bg_ref}[ol1]overlay={ox1}:{oy1}:enable='gte(t,5)'[tmp1];"
                        bg_ref = "[tmp1]"
                    if intro_idx is not None:
                        filter_complex += f"{bg_ref}[oi]overlay={ox_intro}:{oy_intro}:enable='lte(t,{intro_duration})'[v1];"
                        bg_ref = "[v1]"
                else:
                    bg_ref = "[bg]"
                # Add song title overlay filter chains
                if filter_chains:
                    filter_complex += ";".join(filter_chains) + ";"
                # Chain song title overlays
                if overlay_labels:
                    for i, (label, start, duration, x_expr, y_expr) in enumerate(overlay_labels):
                        enable_expr = f"between(t,{start},{start+duration})"
                        out_label = f"songtmp{i+1}" if i < len(overlay_labels)-1 else "vout"
                        filter_complex += f"{bg_ref}[{label}]overlay={x_expr}:{y_expr}:enable='{enable_expr}'[{out_label}];"
                        bg_ref = f"[{out_label}]"
                else:
                    filter_complex += f"{bg_ref}format={VIDEO_SETTINGS['pixel_format']}[vout]"
            else:
                filter_complex = f"[0:v]scale={int(width*1.03)}:{int(height*1.03)},crop={width}:{height},format={VIDEO_SETTINGS['pixel_format']}[vout]"
            # --- Debug print for filter_complex ---
            print("[DEBUG] filter_complex:")
            print(filter_complex)
        else:
            filter_complex = f"[0:v]scale={int(width*1.03)}:{int(height*1.03)},crop={width}:{height},format={VIDEO_SETTINGS['pixel_format']}[vout]"
            # --- Debug print for filter_complex ---
            print("[DEBUG] filter_complex:")
            print(filter_complex)
        cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]", "-map", "1:a"])

        cmd.extend(["-c:v", codec, "-preset", preset])       

        # Rate control based on input image type
        if image_path_for_ffmpeg.lower().endswith('.gif'):
            cmd.extend(["-rc", "vbr", "-cq", "19"])
        elif image_path_for_ffmpeg.lower().endswith('.png'):
            cmd.extend(["-rc", "cbr"])        

        # Video settings
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
        logger.info(f"FFmpeg Video Creation Command for {video_name}:")
        print(f"FFmpeg Video Creation Command for {video_name}:")
        display_cmd = ['ffmpeg'] + cmd[1:]
        logger.info(f"  {' '.join(display_cmd)}")
        print(f"  {' '.join(display_cmd)}")
        logger.info("")
        print("")

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
                f"\r  {percent:5.1f}% | Frame: {current_frame}/{total_frames} | ETA: {eta_str} | it/s: {current_its} "
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
            f"\r  100.0% | Frame: {total_frames}/{total_frames} | ETA: 00:00:00 | it/s: {current_its} \n"
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
    
    output_path = create_temp_file(suffix=".mp3")
    
    if merge_mp3s_with_ffmpeg(selected_mp3s, output_path):
        duration = get_audio_duration(output_path)
        return output_path, duration
    else:
        return None, 0.0 