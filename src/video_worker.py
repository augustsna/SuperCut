# This file uses PyQt6
import os
import random
import shutil
from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Optional
from src.ffmpeg_utils import merge_random_mp3s, create_video_with_ffmpeg
from src.utils import set_low_priority, create_temp_file
import time
from src.logger import logger

class VideoWorker(QObject):
    """Worker class for processing video creation in background thread. Supports GIF overlay for Overlay 1. Optionally supports a name list for output naming."""
    progress = pyqtSignal(int, int)  # batch_count, total_batches
    error = pyqtSignal(str)
    finished = pyqtSignal(list, list, list)  # leftover_mp3s, used_images, failed_moves

    def __init__(self, media_sources: str, export_name: str, number: str, 
                 folder: str, codec: str = "libx264", resolution: str = "1920x1080", fps: int = 24, use_overlay: bool = False, min_mp3_count: int = 3, overlay1_path: str = "", overlay1_size_percent: int = 100, overlay1_x_percent: int = 0, overlay1_y_percent: int = 75,
                 use_overlay2: bool = False, overlay2_path: str = "", overlay2_size_percent: int = 10, overlay2_x_percent: int = 75, overlay2_y_percent: int = 0,
                 overlay1_start_at: int = 0, overlay2_start_at: int = 0,
                 use_overlay3: bool = False, overlay3_path: str = "", overlay3_size_percent: int = 10, overlay3_x_percent: int = 75, overlay3_y_percent: int = 0,
                 use_overlay4: bool = False, overlay4_path: str = "", overlay4_size_percent: int = 10, overlay4_x_percent: int = 75, overlay4_y_percent: int = 0,
                 use_overlay5: bool = False, overlay5_path: str = "", overlay5_size_percent: int = 10, overlay5_x_percent: int = 75, overlay5_y_percent: int = 0,
                 use_intro: bool = False, intro_path: str = "", intro_size_percent: int = 10, intro_x_percent: int = 50, intro_y_percent: int = 50,
                 overlay1_2_effect: str = "fadein", overlay1_2_start_time: int = 5, overlay1_2_duration: int = 6, overlay1_2_duration_full_checkbox_checked: bool = False, overlay1_2_start_from: int = 0, overlay1_2_start_at_checkbox_checked: bool = True,
                 intro_effect: str = "fadeout", intro_duration: int = 6, intro_start_at: int = 0, intro_start_from: int = 0, intro_start_checkbox_checked: bool = False, intro_duration_full_checkbox_checked: bool = False,
                 name_list: Optional[List[str]] = None,
                 preset: str = "slow",
                 audio_bitrate: str = "384k",
                 video_bitrate: str = "12M",
                 maxrate: str = "16M",
                 bufsize: str = "24M",
                 use_song_title_overlay: bool = True,
                 song_title_effect: str = "fadeinout",
                 song_title_font: str = "default",
                 song_title_font_size: int = 32,
                 song_title_color: tuple = (255, 255, 255),
                 song_title_bg: str = "transparent",
                 song_title_bg_color: tuple = (0, 0, 0),
                 song_title_opacity: float = 1.0,
                 song_title_x_percent: int = 25,
                 song_title_y_percent: int = 25,
                 song_title_start_at: int = 5,
                 song_title_scale_percent: int = 100,
                 overlay4_effect: str = "fadein", overlay4_start_time: int = 5, overlay4_duration: int = 6, overlay4_duration_full_checkbox_checked: bool = False,
                 overlay5_effect: str = "fadein", overlay5_start_time: int = 5, overlay5_duration: int = 6, overlay5_duration_full_checkbox_checked: bool = False, overlay4_5_start_from: int = 0, overlay4_5_start_at_checkbox_checked: bool = True,
                 # --- Add overlay6, overlay7, overlay6_7 effect ---
                 use_overlay6: bool = False, overlay6_path: str = "", overlay6_size_percent: int = 10, overlay6_x_percent: int = 75, overlay6_y_percent: int = 0,
                 use_overlay7: bool = False, overlay7_path: str = "", overlay7_size_percent: int = 10, overlay7_x_percent: int = 75, overlay7_y_percent: int = 0,
                 overlay6_effect: str = "fadein", overlay6_start_time: int = 5, overlay6_duration: int = 6, overlay6_duration_full_checkbox_checked: bool = False, overlay6_7_start_from: int = 0, overlay6_7_start_at_checkbox_checked: bool = True,
                 overlay7_effect: str = "fadein", overlay7_start_time: int = 5, overlay7_duration: int = 6, overlay7_duration_full_checkbox_checked: bool = False,
                 # --- Add overlay8, overlay8 effect ---
                 use_overlay8: bool = False, overlay8_path: str = "", overlay8_size_percent: int = 10, overlay8_x_percent: int = 75, overlay8_y_percent: int = 0,
                 overlay8_effect: str = "fadein", overlay8_start_time: int = 5, overlay8_start_from: int = 0, overlay8_duration: int = 6, overlay8_duration_full_checkbox_checked: bool = False, overlay8_start_at_checkbox_checked: bool = True, overlay8_popup_start_at: int = 5, overlay8_popup_interval: int = 10, overlay8_popup_checkbox_checked: bool = False):
        super().__init__()
        self.media_sources = media_sources
        self.export_name = export_name
        self.number = number
        self.folder = folder
        self.codec = codec
        self.resolution = resolution
        self.fps = fps
        self.use_overlay = use_overlay
        self.min_mp3_count = min_mp3_count
        self.overlay1_path = overlay1_path  # Should be a GIF or PNG file if used
        self.overlay1_size_percent = overlay1_size_percent
        self.overlay1_x_percent = overlay1_x_percent
        self.overlay1_y_percent = overlay1_y_percent
        self.use_overlay2 = use_overlay2
        self.overlay2_path = overlay2_path
        self.overlay2_size_percent = overlay2_size_percent
        self.overlay2_x_percent = overlay2_x_percent
        self.overlay2_y_percent = overlay2_y_percent
        self.overlay1_start_at = overlay1_start_at
        self.overlay2_start_at = overlay2_start_at
        self.use_overlay3 = use_overlay3
        self.overlay3_path = overlay3_path
        self.overlay3_size_percent = overlay3_size_percent
        self.overlay3_x_percent = overlay3_x_percent
        self.overlay3_y_percent = overlay3_y_percent
        self.use_overlay4 = use_overlay4
        self.overlay4_path = overlay4_path
        self.overlay4_size_percent = overlay4_size_percent
        self.overlay4_x_percent = overlay4_x_percent
        self.overlay4_y_percent = overlay4_y_percent
        self.use_overlay5 = use_overlay5
        self.overlay5_path = overlay5_path
        self.overlay5_size_percent = overlay5_size_percent
        self.overlay5_x_percent = overlay5_x_percent
        self.overlay5_y_percent = overlay5_y_percent
        self.use_intro = use_intro
        self.intro_path = intro_path
        self.intro_size_percent = intro_size_percent
        self.intro_x_percent = intro_x_percent
        self.intro_y_percent = intro_y_percent
        self.overlay1_2_effect = overlay1_2_effect
        self.overlay1_2_start_time = overlay1_2_start_time
        self.overlay1_2_duration = overlay1_2_duration
        self.overlay1_2_duration_full_checkbox_checked = overlay1_2_duration_full_checkbox_checked
        self.overlay1_2_start_from = overlay1_2_start_from
        self.overlay1_2_start_at_checkbox_checked = overlay1_2_start_at_checkbox_checked
        self.intro_effect = intro_effect
        self.intro_duration = intro_duration
        self.intro_start_at = intro_start_at
        self.intro_start_from = intro_start_from
        self.intro_start_checkbox_checked = intro_start_checkbox_checked
        self.intro_duration_full_checkbox_checked = intro_duration_full_checkbox_checked
        self.name_list = name_list if name_list is not None else []
        self.preset = preset
        self.audio_bitrate = audio_bitrate
        self.video_bitrate = video_bitrate
        self.maxrate = maxrate
        self.bufsize = bufsize
        self._stop = False
        self._used_images = set()
        self.use_song_title_overlay = use_song_title_overlay
        self.song_title_effect = song_title_effect
        self.song_title_font = song_title_font
        self.song_title_font_size = song_title_font_size
        self.song_title_color = song_title_color
        self.song_title_bg = song_title_bg
        self.song_title_bg_color = song_title_bg_color
        self.song_title_opacity = song_title_opacity
        self.song_title_x_percent = song_title_x_percent
        self.song_title_y_percent = song_title_y_percent
        self.song_title_start_at = song_title_start_at
        self.song_title_scale_percent = song_title_scale_percent
        self.overlay4_effect = overlay4_effect
        self.overlay4_start_time = overlay4_start_time
        self.overlay4_duration = overlay4_duration
        self.overlay4_duration_full_checkbox_checked = overlay4_duration_full_checkbox_checked
        self.overlay5_effect = overlay5_effect
        self.overlay5_start_time = overlay5_start_time
        self.overlay5_duration = overlay5_duration
        self.overlay5_duration_full_checkbox_checked = overlay5_duration_full_checkbox_checked
        self.overlay4_5_start_from = overlay4_5_start_from
        self.overlay4_5_start_at_checkbox_checked = overlay4_5_start_at_checkbox_checked
        self.use_overlay6 = use_overlay6
        self.overlay6_path = overlay6_path
        self.overlay6_size_percent = overlay6_size_percent
        self.overlay6_x_percent = overlay6_x_percent
        self.overlay6_y_percent = overlay6_y_percent
        self.use_overlay7 = use_overlay7
        self.overlay7_path = overlay7_path
        self.overlay7_size_percent = overlay7_size_percent
        self.overlay7_x_percent = overlay7_x_percent
        self.overlay7_y_percent = overlay7_y_percent
        self.overlay6_effect = overlay6_effect
        self.overlay6_start_time = overlay6_start_time
        self.overlay6_duration = overlay6_duration
        self.overlay6_duration_full_checkbox_checked = overlay6_duration_full_checkbox_checked
        self.overlay6_7_start_from = overlay6_7_start_from
        self.overlay6_7_start_at_checkbox_checked = overlay6_7_start_at_checkbox_checked
        self.overlay7_effect = overlay7_effect
        self.overlay7_start_time = overlay7_start_time
        self.overlay7_duration = overlay7_duration
        self.overlay7_duration_full_checkbox_checked = overlay7_duration_full_checkbox_checked
        # --- Add overlay8 attributes ---
        self.use_overlay8 = use_overlay8
        self.overlay8_path = overlay8_path
        self.overlay8_size_percent = overlay8_size_percent
        self.overlay8_x_percent = overlay8_x_percent
        self.overlay8_y_percent = overlay8_y_percent
        self.overlay8_effect = overlay8_effect
        self.overlay8_start_time = overlay8_start_time
        self.overlay8_start_from = overlay8_start_from
        self.overlay8_duration = overlay8_duration
        self.overlay8_duration_full_checkbox_checked = overlay8_duration_full_checkbox_checked
        self.overlay8_start_at_checkbox_checked = overlay8_start_at_checkbox_checked
        self.overlay8_popup_start_at = overlay8_popup_start_at
        self.overlay8_popup_interval = overlay8_popup_interval
        self.overlay8_popup_checkbox_checked = overlay8_popup_checkbox_checked

    def stop(self):
        """Stop the video processing"""
        self._stop = True

    def run(self):
        """Main processing method"""
        # set_low_priority()  # Removed to keep normal priority
        try:
            # Get media files
            from src.utils import get_files_by_type
            mp3_files = get_files_by_type(self.media_sources, "audio")
            image_files = get_files_by_type(self.media_sources, "image")
            
            if not image_files:
                self.error.emit("No image files found in the media folder.")
                return
            if not mp3_files or len(mp3_files) < self.min_mp3_count:
                self.error.emit(f"Not enough mp3 files in folder (need at least {self.min_mp3_count} to start batch processing)")
                return
            
            # Parse start number
            try:
                start_number = int(self.number)
            except ValueError as e:
                logger.warning(f"Invalid start number '{self.number}': {e}")
                start_number = 1
                
            current_number = start_number
            used_images = set()
            total_batches = min(len(image_files), len(mp3_files) // self.min_mp3_count)
            batch_count = 0

            # Print export summary
            self._print_export_summary(total_batches)

            all_failed_moves = []
            while len(mp3_files) >= self.min_mp3_count and batch_count < total_batches:
                if self._stop:
                    self.finished.emit(mp3_files, list(self._used_images), all_failed_moves)
                    return
                success, failed_moves = self._process_batch(
                    mp3_files, image_files, used_images, 
                    current_number, batch_count, total_batches
                )
                all_failed_moves.extend(failed_moves)
                if not success:
                    self.finished.emit(mp3_files, list(self._used_images), all_failed_moves)
                    return
                current_number += 1
                batch_count += 1
                self.progress.emit(batch_count, total_batches)
            print(f"\n💫 All {total_batches} batches completed successfully!")
            print(f"📂 Output folder: {self.folder}")
            self.finished.emit(mp3_files, list(self._used_images), all_failed_moves)
            
        except Exception as e:
            error_msg = f"Error during video creation: {str(e)}"
            print(f"❌ {error_msg}")
            self.error.emit(error_msg)

    def _print_export_summary(self, total_batches: int):
        """Print export configuration summary"""
        print("\n----- 📋 EXPORT SUMMARY -----")
        print(f"Export Name   : {self.export_name}")
        print(f"Output Folder : {self.folder}")
        print(f"Codec        : {self.codec}")
        print(f"Resolution   : {self.resolution}")
        print(f"FPS          : {self.fps}")
        print(f"Total Batches: {total_batches}")
        print("--------------------------\n")

    def _process_batch(self, mp3_files: List[str], image_files: List[str], 
                      used_images: set, current_number: int, batch_count: int, total_batches: int) -> tuple[bool, list]:
        """Process a single batch of video creation"""
        batch_start_time = time.time()
        # Select random MP3s
        selected_mp3s = random.sample(mp3_files, self.min_mp3_count)

        # --- Song Title Overlays: Extract title and create PNG for each selected MP3 ---
        song_title_pngs = []
        if self.use_song_title_overlay:
            from src.utils import extract_mp3_title, create_song_title_png
            for idx, mp3_path in enumerate(selected_mp3s, start=16):  # overlay16, overlay17, ...
                title = extract_mp3_title(mp3_path)
                # Create a temp PNG file for the overlay
                temp_png_path = create_temp_file(suffix=f'_overlay{idx}.png', prefix='supercut_')
                create_song_title_png(title, temp_png_path, width=1920, height=240, font_size=self.song_title_font_size, font_name=self.song_title_font, color=self.song_title_color, bg=self.song_title_bg, bg_color=self.song_title_bg_color, opacity=self.song_title_opacity)
                # Add x/y percent and start_at to overlay dict for ffmpeg_utils
                song_title_pngs.append({'path': temp_png_path, 'title': title, 'x_percent': self.song_title_x_percent, 'y_percent': self.song_title_y_percent, 'start_at': self.song_title_start_at})
        # --- End Song Title Overlays ---
        
        # Select available image
        available_images = [img for img in image_files if img not in used_images]
        if not available_images:
            used_images.clear()
            available_images = image_files[:]
        if not available_images:
            return False, []
            
        selected_image = random.choice(available_images)  # This is now a full path
        used_images.add(selected_image)  # Store full path
        self._used_images.add(selected_image)
        
        # Create output filename
        if self.name_list and batch_count < len(self.name_list):
            from src.utils import sanitize_filename
            name = sanitize_filename(self.name_list[batch_count])
            output_filename = f"{name}.mp4"
        else:
            output_filename = f"{self.export_name}_{current_number}.mp4"
        output_path = os.path.join(self.folder, output_filename)

        # Print batch info
        print(f"--- 📄 Batch {batch_count + 1}/{total_batches} ---")
        print(f"Output: {output_filename}")
        print(f"Image: {os.path.basename(selected_image)}")
        print("MP3s:", ", ".join(os.path.basename(mp3) for mp3 in selected_mp3s))

        # Merge MP3s
        try:
            merged_audio_path, audio_duration = merge_random_mp3s(selected_mp3s)
        except (OSError, ValueError) as e:
            self.error.emit(f"Exception merging MP3 files: {e}")
            return False, []

        if not merged_audio_path or audio_duration <= 0:
            self.error.emit(f"Failed to merge MP3 files or get duration")
            return False, []

        try:
            # Calculate timing for each overlay with proper song durations
            overlay_count = len(song_title_pngs)
            extra_overlays = []
            
            if overlay_count > 0:
                # Get individual song durations
                from src.ffmpeg_utils import get_audio_duration
                song_durations = []
                cumulative_time = 0.0
                for mp3_path in selected_mp3s:
                    duration = get_audio_duration(mp3_path)
                    song_durations.append((cumulative_time, duration))
                    cumulative_time += duration
                
                if overlay_count == 1:
                    # REMOVE this block: Single song - use overlay start time or default to 5s
                    pass
                else:
                    # REMOVE this block: Multiple songs - each song title starts when its MP3 starts
                    pass
            if self.use_song_title_overlay and len(song_title_pngs) > 0:
                # Multiple overlays: first starts at user input, others at song boundaries
                from src.ffmpeg_utils import get_audio_duration
                song_durations = []
                cumulative_time = 0.0
                for mp3_path in selected_mp3s:
                    duration = get_audio_duration(mp3_path)
                    song_durations.append((cumulative_time, duration))
                    cumulative_time += duration
                for i, (song_start, song_duration) in enumerate(song_durations):
                    if i == 0:
                        # First overlay: start at user input, duration shortened if start_at > 0
                        overlay_start = self.song_title_start_at
                        overlay_duration = song_duration - (overlay_start - song_start)
                        overlay_duration = max(overlay_duration, 1.0)
                    else:
                        # Subsequent overlays: start at song start, full song duration
                        overlay_start = song_start
                        overlay_duration = song_duration
                    extra_overlays.append({
                        'path': song_title_pngs[i]['path'],
                        'start': overlay_start,
                        'duration': overlay_duration,
                        'x_percent': song_title_pngs[i]['x_percent'],
                        'y_percent': song_title_pngs[i]['y_percent']
                    })
            
            # Calculate actual intro start time and duration based on checkbox states
            from src.ffmpeg_utils import get_audio_duration
            total_duration = get_audio_duration(merged_audio_path)
            
            actual_intro_start_at = 0
            if self.intro_start_checkbox_checked:
                # Use start from logic: total_duration - start_from_value
                actual_intro_start_at = int(max(0, total_duration - self.intro_start_from))
            else:
                # Use start at value directly
                actual_intro_start_at = self.intro_start_at
            
            actual_intro_duration = self.intro_duration
            if self.intro_duration_full_checkbox_checked:
                # Use full remaining duration: total_duration - start_at
                actual_intro_duration = int(max(1, total_duration - actual_intro_start_at))
            
            # Calculate actual overlay1_2 start times based on checkbox state
            actual_overlay1_start_at = self.overlay1_start_at
            actual_overlay2_start_at = self.overlay2_start_at
            if not self.overlay1_2_start_at_checkbox_checked:
                # Use start from logic: countdown from end
                actual_overlay1_start_at = int(max(0, total_duration - self.overlay1_2_start_from))
                actual_overlay2_start_at = int(max(0, total_duration - self.overlay1_2_start_from))
            
            # Calculate actual overlay4_5 start times based on checkbox state
            actual_overlay4_start_at = self.overlay4_start_time
            actual_overlay5_start_at = self.overlay5_start_time
            if not self.overlay4_5_start_at_checkbox_checked:
                # Use start from logic: countdown from end
                actual_overlay4_start_at = int(max(0, total_duration - self.overlay4_5_start_from))
                actual_overlay5_start_at = int(max(0, total_duration - self.overlay4_5_start_from))
            
            # Calculate actual overlay6_7 start times based on checkbox state
            actual_overlay6_start_at = self.overlay6_start_time
            actual_overlay7_start_at = self.overlay7_start_time
            if not self.overlay6_7_start_at_checkbox_checked:
                # Use start from logic: countdown from end
                actual_overlay6_start_at = int(max(0, total_duration - self.overlay6_7_start_from))
                actual_overlay7_start_at = int(max(0, total_duration - self.overlay6_7_start_from))
            
            # Calculate actual overlay8 start time based on checkbox state
            if self.overlay8_popup_checkbox_checked:
                # Popup mode: calculate multiple overlay instances based on interval count
                # First popup at the specified start time
                first_popup_start = int((self.overlay8_popup_start_at / 100.0) * total_duration)
                
                # Calculate how many additional popups based on interval count (not percentage)
                additional_popups = self.overlay8_popup_interval  # This is the count
                
                if additional_popups > 0:
                    # Calculate the time span for additional popups
                    remaining_time = total_duration - first_popup_start  # NOT subtracting duration
                    if remaining_time > 0:
                        interval_seconds = remaining_time / additional_popups
                    else:
                        interval_seconds = 0
                    
                    # Create multiple overlay instances for popup mode
                    for i in range(additional_popups + 1):  # +1 to include the first popup
                        if i == 0:
                            # First popup at specified start time
                            popup_start = first_popup_start
                        else:
                            # Subsequent popups: first_popup + (interval_seconds * i) - duration
                            popup_start = first_popup_start + (interval_seconds * i) - self.overlay8_duration
                        
                        # Ensure popup doesn't start before 0 or after video ends
                        popup_start = max(0, min(popup_start, int(total_duration - self.overlay8_duration)))
                        
                        # Add to extra_overlays for FFmpeg processing
                        extra_overlays.append({
                            'path': self.overlay8_path,
                            'start': popup_start,
                            'duration': self.overlay8_duration,
                            'x_percent': self.overlay8_x_percent,
                            'y_percent': self.overlay8_y_percent,
                            'size_percent': self.overlay8_size_percent,
                            'effect': self.overlay8_effect
                        })
                        
                        print(f"Overlay8 Popup {i+1}: Start at {popup_start}s, Duration {self.overlay8_duration}s")
                    
                    # Set overlay8 to not be used since we're using extra_overlays
                    actual_overlay8_start_at = -1  # Signal to not use single overlay8
                else:
                    # No additional popups, just use first popup
                    actual_overlay8_start_at = first_popup_start
                    actual_overlay8_start_at = min(actual_overlay8_start_at, int(total_duration - 1))
            elif not self.overlay8_start_at_checkbox_checked:
                # Use start from logic
                if self.overlay8_duration_full_checkbox_checked:
                    # Full duration: simple percentage of total duration
                    actual_overlay8_start_at = int((self.overlay8_start_from / 100.0) * total_duration)
                else:
                    # Limited duration: (total_duration * percentage) - effect_duration
                    effect_duration = self.overlay8_duration
                    percentage_time = (self.overlay8_start_from / 100.0) * total_duration
                    actual_overlay8_start_at = int(max(0, percentage_time - effect_duration))
                # Ensure the start time doesn't exceed the video duration
                actual_overlay8_start_at = min(actual_overlay8_start_at, int(total_duration - 1))
            else:
                # Use start at logic: simple percentage of total duration (NO duration subtraction)
                actual_overlay8_start_at = int((self.overlay8_start_time / 100.0) * total_duration)
                # Ensure the start time doesn't exceed the video duration
                actual_overlay8_start_at = min(actual_overlay8_start_at, int(total_duration - 1))
            
            # Final validation to ensure start time is valid (only for non-popup mode)
            if not self.overlay8_popup_checkbox_checked:
                actual_overlay8_start_at = max(0, actual_overlay8_start_at)
            
            # Debug output for overlay8 timing
            if self.overlay8_popup_checkbox_checked:
                first_popup_time = int((self.overlay8_popup_start_at / 100.0) * total_duration)
                print(f"Overlay8 Popup Debug - Total duration: {total_duration}s, First popup at: {first_popup_time}s, Duration: {self.overlay8_duration}s, Interval: {self.overlay8_popup_interval}s")
            else:
                print(f"Overlay8 Debug - Total duration: {total_duration}s, Start time: {actual_overlay8_start_at}s, Duration: {self.overlay8_duration}s")
            print(f"Overlay8 Debug - Start from percent: {self.overlay8_start_from}, Start time percent: {self.overlay8_start_time}, Popup start at percent: {self.overlay8_popup_start_at}, Popup interval: {self.overlay8_popup_interval}, Popup checked: {self.overlay8_popup_checkbox_checked}")
            
            # Additional validation for overlay8 parameters
            if not self.overlay8_popup_checkbox_checked and actual_overlay8_start_at < 0:
                print(f"Warning: Overlay8 start time is negative: {actual_overlay8_start_at}, setting to 0")
                actual_overlay8_start_at = 0
            if self.overlay8_duration < 0:
                print(f"Warning: Overlay8 duration is negative: {self.overlay8_duration}, setting to 1")
                self.overlay8_duration = 1
            
            # Create video (Overlay 1: GIF/PNG, with size)
            success, error_msg = create_video_with_ffmpeg(
                selected_image, 
                merged_audio_path, 
                output_path, 
                self.resolution, 
                self.fps, 
                self.codec,
                self.use_overlay,
                self.overlay1_path,
                self.overlay1_size_percent,
                self.overlay1_x_percent,
                self.overlay1_y_percent,
                self.use_overlay2,
                self.overlay2_path,
                self.overlay2_size_percent,
                self.overlay2_x_percent,
                self.overlay2_y_percent,
                            self.use_overlay3,
            self.overlay3_path,
            self.overlay3_size_percent,
            self.overlay3_x_percent,
            self.overlay3_y_percent,
                self.use_overlay4,
                self.overlay4_path,
                self.overlay4_size_percent,
                self.overlay4_x_percent,
                self.overlay4_y_percent,
                self.use_overlay5,
                self.overlay5_path,
                self.overlay5_size_percent,
                self.overlay5_x_percent,
                self.overlay5_y_percent,
                self.use_overlay6,
                self.overlay6_path,
                self.overlay6_size_percent,
                self.overlay6_x_percent,
                self.overlay6_y_percent,
                self.use_overlay7,
                self.overlay7_path,
                self.overlay7_size_percent,
                self.overlay7_x_percent,
                self.overlay7_y_percent,
                # Disable overlay8 if using popup mode (actual_overlay8_start_at == -1)
                self.use_overlay8 and actual_overlay8_start_at != -1,
                self.overlay8_path,
                self.overlay8_size_percent,
                self.overlay8_x_percent,
                self.overlay8_y_percent,
                self.use_intro,
                self.intro_path,
                self.intro_size_percent,
                self.intro_x_percent,
                self.intro_y_percent,
                self.overlay1_2_effect,
                self.overlay1_2_start_time,
                self.overlay1_2_duration,
                self.overlay1_2_duration_full_checkbox_checked,
                self.intro_effect,
                actual_intro_duration,
                actual_intro_start_at,
                self.intro_duration_full_checkbox_checked,
                self.preset,
                self.audio_bitrate,
                self.video_bitrate,
                self.maxrate,
                self.bufsize,
                extra_overlays=extra_overlays,
                song_title_effect=self.song_title_effect,
                song_title_font=self.song_title_font,
                song_title_font_size=self.song_title_font_size,
                song_title_color=self.song_title_color,
                song_title_bg=self.song_title_bg,
                song_title_bg_color=self.song_title_bg_color,
                song_title_opacity=self.song_title_opacity,
                song_title_scale_percent=self.song_title_scale_percent,
                overlay3_effect="fadein",
                overlay3_start_time=self.song_title_start_at if (self.use_song_title_overlay and self.song_title_start_at is not None) else 5,
                overlay4_effect=self.overlay4_effect,
                overlay4_start_time=actual_overlay4_start_at,
                overlay4_duration=self.overlay4_duration,
                overlay4_duration_full_checkbox_checked=self.overlay4_duration_full_checkbox_checked,
                overlay5_effect=self.overlay5_effect,
                overlay5_start_time=actual_overlay5_start_at,
                overlay5_duration=self.overlay5_duration,
                overlay5_duration_full_checkbox_checked=self.overlay5_duration_full_checkbox_checked,
                overlay6_effect=self.overlay6_effect,
                overlay6_start_time=actual_overlay6_start_at,
                overlay6_duration=self.overlay6_duration,
                overlay6_duration_full_checkbox_checked=self.overlay6_duration_full_checkbox_checked,
                overlay7_effect=self.overlay7_effect,
                overlay7_start_time=actual_overlay7_start_at,
                overlay7_duration=self.overlay7_duration,
                overlay7_duration_full_checkbox_checked=self.overlay7_duration_full_checkbox_checked,
                overlay8_effect=self.overlay8_effect,
                overlay8_start_time=actual_overlay8_start_at if actual_overlay8_start_at != -1 else 0,
                overlay8_duration=self.overlay8_duration,
                overlay8_duration_full_checkbox_checked=self.overlay8_duration_full_checkbox_checked,
                overlay1_start_at=actual_overlay1_start_at,
                overlay2_start_at=actual_overlay2_start_at
            )
            if not success:
                self.error.emit(error_msg or f"Failed to create video: {output_filename}")
                return False, []
        except (OSError, ValueError) as e:
            self.error.emit(f"Exception creating video: {e}")
            return False, []
        finally:
            # Always cleanup temporary audio file
            self._cleanup_temp_audio(merged_audio_path)
            
        # Create log and move files
        failed_moves = self._create_log_and_move_files(
            output_filename, output_path, selected_image, 
            selected_mp3s, mp3_files, image_files, selected_image
        )
        
        # Print completion message with time spent
        batch_time_spent = time.time() - batch_start_time
        if batch_time_spent >= 60:
            mins = int(batch_time_spent // 60)
            secs = int(batch_time_spent % 60)
            time_str = f"{mins}m {secs}s"
        else:
            time_str = f"{int(batch_time_spent)}s"
        print(f"✔️ Batch {batch_count + 1}/{total_batches} completed: {output_filename} (Time spent: {time_str}) \u2713") 
        
        return True, failed_moves

    def _cleanup_temp_audio(self, audio_path: str):
        """Clean up temporary audio file"""
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except FileNotFoundError:
                logger.warning(f"Temp audio file {audio_path} not found for removal.")
            except PermissionError:
                logger.warning(f"No permission to remove temp audio file {audio_path}.")
            except OSError as e:
                logger.warning(f"OS error removing temp audio file {audio_path}: {e}")

    def _create_log_and_move_files(self, output_filename: str, output_path: str, 
                                  selected_image: str, selected_mp3s: List[str], 
                                  mp3_files: List[str], image_files: List[str], 
                                  selected_image_path: str) -> list:
        """Create log file and move processed files to bin folder. Returns list of failed moves."""
        # Create log file
        output_base_name = os.path.splitext(output_filename)[0]
        log_path = os.path.join(self.media_sources, f"{output_base_name}.log")
        
        with open(log_path, "w", encoding="utf-8") as logf:
            logf.write(f"Output video: {output_path}\n")
            logf.write(f"Image used: {selected_image}\n")
            logf.write("MP3s used:\n")
            for mp3 in selected_mp3s:
                logf.write(f"  {mp3}\n")
        
        # Create bin folder and move files
        bin_folder = os.path.join(self.media_sources, "bin")
        os.makedirs(bin_folder, exist_ok=True)
        
        # Move log file
        shutil.move(log_path, os.path.join(bin_folder, f"{output_base_name}.log"))
        
        failed_moves = []
        # Move MP3 files
        output_base = os.path.splitext(os.path.basename(output_path))[0]
        for idx, mp3 in enumerate(selected_mp3s, 1):
            new_name = f"{output_base}+{idx}.mp3"
            try:
                shutil.move(mp3, os.path.join(bin_folder, new_name))
                if mp3 in mp3_files:
                    mp3_files.remove(mp3)
            except FileNotFoundError:
                logger.error(f"File {mp3} not found for moving.")
                failed_moves.append(mp3)
            except PermissionError:
                logger.error(f"No permission to move file {mp3}.")
                failed_moves.append(mp3)
            except OSError as move_err:
                logger.error(f"OS error moving {mp3} to {os.path.join(bin_folder, new_name)}: {move_err}")
                failed_moves.append(mp3)
        # Move image file
        try:
            img_ext = os.path.splitext(selected_image_path)[1]
            img_new_name = f"{output_base}{img_ext}"
            shutil.move(selected_image_path, os.path.join(bin_folder, img_new_name))
        except FileNotFoundError:
            logger.error(f"File {selected_image_path} not found for moving.")
            failed_moves.append(selected_image_path)
        except PermissionError:
            logger.error(f"No permission to move file {selected_image_path}.")
            failed_moves.append(selected_image_path)
        except OSError as move_err:
            logger.error(f"OS error moving {selected_image_path} to {os.path.join(bin_folder, img_new_name)}: {move_err}")
            failed_moves.append(selected_image_path)
        finally:
            if selected_image_path in image_files:
                image_files.remove(selected_image_path)
        if failed_moves:
            logger.warning(f"Some files could not be moved to bin: {failed_moves}")
        return failed_moves 