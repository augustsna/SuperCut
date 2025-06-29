import os
import json
import subprocess
import tempfile
import time
import re
import sys
from typing import Optional, Tuple
from config import FFMPEG_BINARY, FFPROBE_BINARY, VIDEO_SETTINGS

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
    except Exception as e:
        print(f"Error getting duration for {file_path}: {e}")
        return 0.0

def merge_mp3s_with_ffmpeg(input_files: list, output_file: str) -> bool:
    """Merge multiple MP3 files using ffmpeg"""
    try:
        # Create a file list for ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for file_path in input_files:
                f.write(f"file '{file_path}'\n")
            file_list_path = f.name
        
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
        os.unlink(file_list_path)
        return True
    except Exception as e:
        print(f"Error merging MP3s: {e}")
        return False

def create_video_with_ffmpeg(
    image_path: str, 
    audio_path: str, 
    output_path: str, 
    resolution: str, 
    fps: int, 
    codec: str
) -> bool:
    """Create video from image and audio using ffmpeg with progress tracking"""
    try:
        width, height = map(int, resolution.split('x'))
        
        # Build ffmpeg command
        cmd = [
            FFMPEG_BINARY,
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", codec,
            "-c:a", VIDEO_SETTINGS["audio_codec"],
            "-b:a", VIDEO_SETTINGS["audio_bitrate"],
            "-ar", VIDEO_SETTINGS["audio_sample_rate"],
            "-ac", VIDEO_SETTINGS["audio_channels"],
            "-vf", f"scale={width}:{height}",
            "-r", str(fps),
            "-shortest",
            "-y"
        ]
        
        # Add codec-specific settings
        if codec in ("libx264", "h264_nvenc"):
            cmd.extend(["-preset", "slow", "-profile:v", "high", "-level:v", "4.2"])
        
        # Add common video settings
        cmd.extend([
            "-movflags", "+faststart",
            "-b:v", VIDEO_SETTINGS["video_bitrate"],
            "-maxrate", VIDEO_SETTINGS["max_bitrate"],
            "-bufsize", VIDEO_SETTINGS["buffer_size"],
            "-pix_fmt", VIDEO_SETTINGS["pixel_format"],
            "-g", VIDEO_SETTINGS["gop_size"],
            "-bf", VIDEO_SETTINGS["bframes"]
        ])
        
        if codec == "h264_nvenc":
            cmd.extend(["-rc", "vbr_hq"])
        
        cmd.append(output_path)

        # Get audio duration for progress calculation
        audio_duration = get_audio_duration(audio_path)
        total_frames = int(audio_duration * fps)
        
        # Start ffmpeg process
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)

        # Progress tracking
        start_time = time.time()
        last_seconds = 0.0
        last_update = time.time()
        
        def print_progress(seconds: float):
            """Print progress information"""
            current_frame = int(seconds * fps)
            percent = min(100.0, (current_frame / total_frames) * 100) if total_frames > 0 else 0
            elapsed = time.time() - start_time
            speed = (current_frame / elapsed) if elapsed > 0 else 0
            remaining_frames = total_frames - current_frame
            eta_sec = int(remaining_frames / speed) if speed > 0 else 0
            eta_str = time.strftime('%H:%M:%S', time.gmtime(eta_sec)) if eta_sec > 0 else "--:--:--"
            
            sys.stdout.write(
                f"\r  {percent:5.1f}% | Frame: {current_frame}/{total_frames} | ETA: {eta_str} "
            )
            sys.stdout.flush()

        # Read ffmpeg output and track progress
        seconds = 0.0
        while True:
            if process.stderr is None:
                break
            line = process.stderr.readline()
            if not line:
                break
                
            # Parse time from ffmpeg output
            match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
            if match:
                h, m, s = map(float, match.groups())
                seconds = h * 3600 + m * 60 + s
                last_seconds = seconds
                last_update = time.time()
                print_progress(seconds)
                
                # Interpolate progress every 0.1s until next ffmpeg update
                now = time.time()
                while (now - last_update) < 0.3:  # Interpolate for 0.3s
                    interp_seconds = last_seconds + (now - last_update)
                    if interp_seconds > audio_duration:
                        interp_seconds = audio_duration
                    print_progress(interp_seconds)
                    time.sleep(0.1)
                    now = time.time()
                    
        process.wait()
        
        # Final progress update
        sys.stdout.write(
            f"\r  100.0% | Frame: {total_frames}/{total_frames} | ETA: 00:00:00 \n"
        )
        sys.stdout.flush()

        return process.returncode == 0
    except Exception as e:
        print(f"Error creating video: {e}")
        return False

def merge_random_mp3s(selected_mp3s: list) -> Tuple[Optional[str], float]:
    """Merge MP3 files using ffmpeg - returns output path and duration"""
    from utils import create_temp_file
    
    output_path = create_temp_file(suffix=".mp3")
    
    if merge_mp3s_with_ffmpeg(selected_mp3s, output_path):
        duration = get_audio_duration(output_path)
        return output_path, duration
    else:
        return None, 0.0 