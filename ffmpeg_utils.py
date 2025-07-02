import os
import json
import subprocess
import tempfile
import time
import re
import sys
from typing import Optional, Tuple
from config import FFMPEG_BINARY, FFPROBE_BINARY, VIDEO_SETTINGS
from logger import logger
from utils import has_enough_disk_space, create_temp_file

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
    use_overlay: bool = False
) -> Tuple[bool, Optional[str]]:
    """Create video from image and audio using ffmpeg with progress tracking. Returns (success, error_message)."""
    temp_png_path = None
    try:
        # Estimate required output file size
        audio_duration = get_audio_duration(audio_path)
        video_bitrate_str = VIDEO_SETTINGS["video_bitrate"]
        if video_bitrate_str.lower().endswith('m'):
            video_bitrate = int(float(video_bitrate_str[:-1]) * 1024 * 1024)
        elif video_bitrate_str.lower().endswith('k'):
            video_bitrate = int(float(video_bitrate_str[:-1]) * 1024)
        else:
            video_bitrate = int(video_bitrate_str)
        audio_bitrate_str = VIDEO_SETTINGS["audio_bitrate"]
        if audio_bitrate_str.lower().endswith('k'):
            audio_bitrate = int(float(audio_bitrate_str[:-1]) * 1024)
        else:
            audio_bitrate = int(audio_bitrate_str)
        total_bitrate = video_bitrate + audio_bitrate
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

        # Accept only PNG image files
        if not image_path_for_ffmpeg.lower().endswith('.png'):
            msg = f"Error: Only PNG image files are accepted. Provided: {image_path_for_ffmpeg}"
            logger.error(msg)
            return False, msg
        
        width, height = map(int, resolution.split('x'))
        
        # Build ffmpeg command
        cmd = [
            FFMPEG_BINARY,         
            "-loop", "1",
            "-i", image_path_for_ffmpeg,
            "-i", audio_path
        ]
        if use_overlay:
            cmd.extend(["-i", os.path.join("sources", "overlay1.png")])

        # Filter complex
        if use_overlay:
            filter_complex = f"[0:v]scale={width}:{height}[bg];[bg][2:v]overlay=0:0,format={VIDEO_SETTINGS['pixel_format']}[vout]"
            cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]", "-map", "1:a"])
        else:
            filter_complex = f"[0:v]scale={width}:{height},format={VIDEO_SETTINGS['pixel_format']}[vout]"
            cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]", "-map", "1:a"])

        cmd.extend(["-c:v", codec, "-preset", VIDEO_SETTINGS["preset"]])       

        if codec == "h264_nvenc":
            cmd.extend(["-rc", "vbr_hq"])

        # Video settings
        cmd.extend([   
            "-b:v", VIDEO_SETTINGS["video_bitrate"],
            "-maxrate", VIDEO_SETTINGS["max_bitrate"],
            "-bufsize", VIDEO_SETTINGS["buffer_size"]     
        ])

        # Audio settings
        cmd.extend([   
            "-c:a", VIDEO_SETTINGS["audio_codec"],
            "-b:a", VIDEO_SETTINGS["audio_bitrate"],
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
                        while (now - last_update) < 0.3:
                            interp_seconds = last_seconds + (now - last_update)
                            if interp_seconds > audio_duration:
                                interp_seconds = audio_duration
                            print_progress(interp_seconds)
                            time.sleep(0.3)
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
    from utils import create_temp_file
    
    output_path = create_temp_file(suffix=".mp3")
    
    if merge_mp3s_with_ffmpeg(selected_mp3s, output_path):
        duration = get_audio_duration(output_path)
        return output_path, duration
    else:
        return None, 0.0