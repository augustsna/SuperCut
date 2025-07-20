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
    """Worker class for processing video creation in background thread. Supports GIF, PNG, and MP4 overlay for Overlay 1. Optionally supports a name list for output naming."""
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
                 # --- Add song title text effect parameters ---
                 song_title_text_effect: str = "none",
                 song_title_text_effect_color: tuple = (0, 0, 0),
                 song_title_text_effect_intensity: int = 20,
                 overlay4_effect: str = "fadein", overlay4_start_time: int = 5, overlay4_duration: int = 6, overlay4_duration_full_checkbox_checked: bool = False,
                 overlay5_effect: str = "fadein", overlay5_start_time: int = 5, overlay5_duration: int = 6, overlay5_duration_full_checkbox_checked: bool = False, overlay4_5_start_from: int = 0, overlay4_5_start_at_checkbox_checked: bool = True,
                 # --- Add overlay6, overlay7, overlay6_7 effect ---
                 use_overlay6: bool = False, overlay6_path: str = "", overlay6_size_percent: int = 10, overlay6_x_percent: int = 75, overlay6_y_percent: int = 0,
                 use_overlay7: bool = False, overlay7_path: str = "", overlay7_size_percent: int = 10, overlay7_x_percent: int = 75, overlay7_y_percent: int = 0,
                 overlay6_effect: str = "fadein", overlay6_start_time: int = 5, overlay6_duration: int = 6, overlay6_duration_full_checkbox_checked: bool = False, overlay6_7_start_from: int = 0, overlay6_7_start_at_checkbox_checked: bool = True,
                 overlay7_effect: str = "fadein", overlay7_start_time: int = 5, overlay7_duration: int = 6, overlay7_duration_full_checkbox_checked: bool = False,
                 # --- Add overlay8, overlay8 effect ---
                 use_overlay8: bool = False, overlay8_path: str = "", overlay8_size_percent: int = 10, overlay8_x_percent: int = 75, overlay8_y_percent: int = 0,
                 overlay8_effect: str = "fadein", overlay8_start_time: int = 5, overlay8_start_from: int = 0, overlay8_duration: int = 6, overlay8_duration_full_checkbox_checked: bool = False, overlay8_start_at_checkbox_checked: bool = True,
                 # --- Add overlay9, overlay9 effect ---
                 use_overlay9: bool = False, overlay9_path: str = "", overlay9_size_percent: int = 10, overlay9_x_percent: int = 75, overlay9_y_percent: int = 0,
                 overlay9_effect: str = "fadein", overlay9_start_time: int = 5, overlay9_start_from: int = 0, overlay9_duration: int = 6, overlay9_duration_full_checkbox_checked: bool = False, overlay9_start_at_checkbox_checked: bool = True,
                 # --- Add overlay10, overlay10 effect ---
                 use_overlay10: bool = False, overlay10_path: str = "", overlay10_size_percent: int = 10, overlay10_x_percent: int = 75, overlay10_y_percent: int = 0,
                 overlay10_effect: str = "fadein", overlay10_start_time: int = 5, overlay10_start_from: int = 0, overlay10_duration: int = 6, overlay10_start_at_checkbox_checked: bool = True,
                 overlay10_start_time_percent: int = 0,
                 overlay10_song_start_end_checked: bool = False, overlay10_start_end_value: str = "start",
                 # --- Add frame box parameters ---
                 use_frame_box: bool = False, frame_box_path: str = "", frame_box_size_percent: int = 50, frame_box_x_percent: int = 0, frame_box_y_percent: int = 0,
                 frame_box_effect: str = "fadein", frame_box_start_time: int = 5, frame_box_duration: int = 6, frame_box_duration_full_checkbox_checked: bool = True,
                 frame_box_pad_left: int = 12, frame_box_pad_right: int = 12, frame_box_pad_top: int = 12, frame_box_pad_bottom: int = 12,
                 # --- Add frame box custom image parameters ---
                 use_frame_box_custom_image: bool = False, frame_box_custom_image_path: str = "",
                 # --- Add frame mp3cover parameters ---
                 use_frame_mp3cover: bool = False, frame_mp3cover_path: str = "", frame_mp3cover_size_percent: int = 50, frame_mp3cover_x_percent: int = 0, frame_mp3cover_y_percent: int = 0,
                 frame_mp3cover_effect: str = "fadein", frame_mp3cover_start_time: int = 5, frame_mp3cover_duration: int = 6, frame_mp3cover_duration_full_checkbox_checked: bool = True,
                 # --- Add dynamic MP3 cover parameters ---
                 use_mp3_cover_overlay: bool = False,
                 mp3_cover_effect: str = "fadeinout",
                 mp3_cover_size_percent: int = 20,
                 mp3_cover_x_percent: int = 75,
                 mp3_cover_y_percent: int = 75,
                 mp3_cover_start_at: int = 0,
                 mp3_cover_duration: int = 6,
                 mp3_cover_duration_full_checkbox_checked: bool = True,
                 mp3_cover_frame_color: tuple = (255, 255, 255),
                 mp3_cover_frame_size: int = 10,
                 mp3_cover_custom_image_path: str = "",
                 # --- Add background layer parameters ---
                 use_bg_layer: bool = False,
                 bg_scale_percent: int = 103,
                 bg_crop_position: str = "center",
                 bg_effect: str = "none",
                 bg_intensity: int = 50,
                 # --- Add soundwave overlay parameters ---
                 use_soundwave_overlay: bool = False,
                 soundwave_method: str = "bars",
                 soundwave_color: str = "hue_rotate",
                 soundwave_size_percent: int = 50,
                 soundwave_x_percent: int = 50,
                 soundwave_y_percent: int = 50,
                 layer_order: Optional[List[str]] = None):
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
        self.overlay1_path = overlay1_path  # Should be a GIF, PNG, or MP4 file if used (MP4 will loop infinitely)
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
        # --- Add song title text effect attributes ---
        self.song_title_text_effect = song_title_text_effect
        self.song_title_text_effect_color = song_title_text_effect_color
        self.song_title_text_effect_intensity = song_title_text_effect_intensity
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
        # --- Add overlay9 attributes ---
        self.use_overlay9 = use_overlay9
        self.overlay9_path = overlay9_path
        self.overlay9_size_percent = overlay9_size_percent
        self.overlay9_x_percent = overlay9_x_percent
        self.overlay9_y_percent = overlay9_y_percent
        self.overlay9_effect = overlay9_effect
        self.overlay9_start_time = overlay9_start_time
        self.overlay9_start_from = overlay9_start_from
        self.overlay9_duration = overlay9_duration
        self.overlay9_duration_full_checkbox_checked = overlay9_duration_full_checkbox_checked
        self.overlay9_start_at_checkbox_checked = overlay9_start_at_checkbox_checked
        # --- Add overlay10 attributes ---
        self.use_overlay10 = use_overlay10
        self.overlay10_path = overlay10_path
        self.overlay10_size_percent = overlay10_size_percent
        self.overlay10_x_percent = overlay10_x_percent
        self.overlay10_y_percent = overlay10_y_percent
        self.overlay10_effect = overlay10_effect
        self.overlay10_start_time = overlay10_start_time
        self.overlay10_start_from = overlay10_start_from
        self.overlay10_duration = overlay10_duration
        self.overlay10_start_at_checkbox_checked = overlay10_start_at_checkbox_checked
        self.overlay10_start_time_percent = overlay10_start_time_percent
        self.overlay10_song_start_end_checked = overlay10_song_start_end_checked
        self.overlay10_start_end_value = overlay10_start_end_value
        # --- Add frame box attributes ---
        self.use_frame_box = use_frame_box
        self.frame_box_path = frame_box_path
        self.frame_box_size_percent = frame_box_size_percent
        self.frame_box_x_percent = frame_box_x_percent
        self.frame_box_y_percent = frame_box_y_percent
        self.frame_box_effect = frame_box_effect
        self.frame_box_start_time = frame_box_start_time
        self.frame_box_duration = frame_box_duration
        self.frame_box_duration_full_checkbox_checked = frame_box_duration_full_checkbox_checked
        self.frame_box_pad_left = frame_box_pad_left
        self.frame_box_pad_right = frame_box_pad_right
        self.frame_box_pad_top = frame_box_pad_top
        self.frame_box_pad_bottom = frame_box_pad_bottom
        # --- Add frame box custom image attributes ---
        self.use_frame_box_custom_image = use_frame_box_custom_image
        self.frame_box_custom_image_path = frame_box_custom_image_path
        # --- Add frame mp3cover attributes ---
        self.use_frame_mp3cover = use_frame_mp3cover
        self.frame_mp3cover_path = frame_mp3cover_path
        self.frame_mp3cover_size_percent = frame_mp3cover_size_percent
        self.frame_mp3cover_x_percent = frame_mp3cover_x_percent
        self.frame_mp3cover_y_percent = frame_mp3cover_y_percent
        self.frame_mp3cover_effect = frame_mp3cover_effect
        self.frame_mp3cover_start_time = frame_mp3cover_start_time
        self.frame_mp3cover_duration = frame_mp3cover_duration
        self.frame_mp3cover_duration_full_checkbox_checked = frame_mp3cover_duration_full_checkbox_checked
        
        # --- Add dynamic MP3 cover attributes ---
        self.use_mp3_cover_overlay = use_mp3_cover_overlay
        self.mp3_cover_effect = mp3_cover_effect
        self.mp3_cover_size_percent = mp3_cover_size_percent
        self.mp3_cover_x_percent = mp3_cover_x_percent
        self.mp3_cover_y_percent = mp3_cover_y_percent
        self.mp3_cover_start_at = mp3_cover_start_at
        self.mp3_cover_duration = mp3_cover_duration
        self.mp3_cover_duration_full_checkbox_checked = mp3_cover_duration_full_checkbox_checked
        self.mp3_cover_frame_color = mp3_cover_frame_color
        self.mp3_cover_frame_size = mp3_cover_frame_size
        self.mp3_cover_custom_image_path = mp3_cover_custom_image_path
        # --- Add background layer attributes ---
        self.use_bg_layer = use_bg_layer
        self.bg_scale_percent = bg_scale_percent
        self.bg_crop_position = bg_crop_position
        self.bg_effect = bg_effect
        self.bg_intensity = bg_intensity
        # --- Soundwave overlay parameters ---
        self.use_soundwave_overlay = use_soundwave_overlay
        self.soundwave_method = soundwave_method
        self.soundwave_color = soundwave_color
        self.soundwave_size_percent = soundwave_size_percent
        self.soundwave_x_percent = soundwave_x_percent
        self.soundwave_y_percent = soundwave_y_percent
        self.layer_order = layer_order
                
        # Debug layer order


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
            from src.utils import extract_mp3_title, create_song_title_png, preprocess_song_title_png
            for idx, mp3_path in enumerate(selected_mp3s, start=16):  # overlay16, overlay17, ...
                title = extract_mp3_title(mp3_path)
                # Create a temp PNG file for the overlay
                temp_png_path = create_temp_file(suffix=f'_overlay{idx}.png', prefix='supercut_')
                create_song_title_png(title, temp_png_path, width=1920, height=240, font_size=self.song_title_font_size, font_name=self.song_title_font, color=self.song_title_color, bg=self.song_title_bg, bg_color=self.song_title_bg_color, opacity=self.song_title_opacity, text_effect=self.song_title_text_effect, text_effect_color=self.song_title_text_effect_color, text_effect_intensity=self.song_title_text_effect_intensity, bottom_padding=0)
                
                # Always preprocess the song title PNG
                processed_png_path = preprocess_song_title_png(
                    png_path=temp_png_path,
                    scale_percent=self.song_title_scale_percent
                )
                
                # Add x/y percent and start_at to overlay dict for ffmpeg_utils
                song_title_pngs.append({'path': processed_png_path, 'title': title, 'x_percent': self.song_title_x_percent, 'y_percent': self.song_title_y_percent, 'start_at': self.song_title_start_at})
        # --- End Song Title Overlays ---

        # --- MP3 Cover Overlays: Extract cover and create framed PNG for each selected MP3 ---
        mp3_cover_pngs = []
        if self.use_mp3_cover_overlay:
            from src.utils import extract_and_frame_mp3_cover, preprocess_mp3_cover_png
            for idx, mp3_path in enumerate(selected_mp3s, start=100):  # mp3cover100, mp3cover101, ...
                # Create a temp PNG file for the MP3 cover overlay
                temp_cover_path = create_temp_file(suffix=f'_mp3cover{idx}.png', prefix='supercut_')
                
                # Extract and frame the MP3 cover image with custom frame color and size
                # Use custom image if provided, otherwise use default
                default_cover_path = self.mp3_cover_custom_image_path if self.mp3_cover_custom_image_path else "src/sources/mp3cover/mp3cover.png"
                success = extract_and_frame_mp3_cover(mp3_path, temp_cover_path, default_cover_path=default_cover_path, frame_width=self.mp3_cover_frame_size, frame_color=self.mp3_cover_frame_color)
                
                if success:
                    # Always preprocess the MP3 cover PNG
                    processed_cover_path = preprocess_mp3_cover_png(
                        png_path=temp_cover_path,
                        scale_percent=self.mp3_cover_size_percent
                    )
                    
                    # Add x/y percent and start_at to overlay dict for ffmpeg_utils
                    mp3_cover_pngs.append({
                        'path': processed_cover_path, 
                        'mp3_path': mp3_path, 
                        'x_percent': self.mp3_cover_x_percent, 
                        'y_percent': self.mp3_cover_y_percent, 
                        'start_at': 0,  # Will be overridden by timing logic
                        'size_percent': self.mp3_cover_size_percent,
                        'effect': self.mp3_cover_effect
                    })
                else:
                    logger.warning(f"Failed to create MP3 cover overlay for {mp3_path}")
        # --- End MP3 Cover Overlays ---
        
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
        
        # Preprocess background image (always done in advance)
        from src.utils import preprocess_background_image
        if self.use_bg_layer:
            # Use custom background layer settings
            processed_image_path = preprocess_background_image(
                image_path=selected_image,
                resolution=self.resolution,
                scale_percent=self.bg_scale_percent,
                crop_position=self.bg_crop_position,
                effect=self.bg_effect,
                intensity=self.bg_intensity
            )
        else:
            # Use default 103% scale + center crop
            processed_image_path = preprocess_background_image(
                image_path=selected_image,
                resolution=self.resolution,
                scale_percent=103,  # Default 103%
                crop_position="center",  # Default center crop
                effect="none",  # No effects
                intensity=50  # Default intensity
            )
        
        # Preprocess overlay1 image (only for images, not videos)
        processed_overlay1_path = self.overlay1_path
        if self.use_overlay and self.overlay1_path:
            file_ext = os.path.splitext(self.overlay1_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay1_image
                processed_overlay1_path = preprocess_overlay1_image(
                    image_path=self.overlay1_path,
                    size_percent=self.overlay1_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay1_path = self.overlay1_path
        
        # Preprocess overlay2 image (only for images, not videos)
        processed_overlay2_path = self.overlay2_path
        if self.use_overlay2 and self.overlay2_path:
            file_ext = os.path.splitext(self.overlay2_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay2_image
                processed_overlay2_path = preprocess_overlay2_image(
                    image_path=self.overlay2_path,
                    size_percent=self.overlay2_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay2_path = self.overlay2_path
        
        # Preprocess overlay3 image (only for images, not videos)
        processed_overlay3_path = self.overlay3_path
        if self.use_overlay3 and self.overlay3_path:
            file_ext = os.path.splitext(self.overlay3_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay3_image
                processed_overlay3_path = preprocess_overlay3_image(
                    image_path=self.overlay3_path,
                    size_percent=self.overlay3_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay3_path = self.overlay3_path
        
        # Preprocess intro image (only for images, not videos)
        processed_intro_path = self.intro_path
        if self.use_intro and self.intro_path:
            file_ext = os.path.splitext(self.intro_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_intro_image
                processed_intro_path = preprocess_intro_image(
                    image_path=self.intro_path,
                    size_percent=self.intro_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_intro_path = self.intro_path
        
        # Preprocess overlay4 image (only for images, not videos)
        processed_overlay4_path = self.overlay4_path
        if self.use_overlay4 and self.overlay4_path:
            file_ext = os.path.splitext(self.overlay4_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay4_image
                processed_overlay4_path = preprocess_overlay4_image(
                    image_path=self.overlay4_path,
                    size_percent=self.overlay4_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay4_path = self.overlay4_path
        
        # Preprocess overlay5 image (only for images, not videos)
        processed_overlay5_path = self.overlay5_path
        if self.use_overlay5 and self.overlay5_path:
            file_ext = os.path.splitext(self.overlay5_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay5_image
                processed_overlay5_path = preprocess_overlay5_image(
                    image_path=self.overlay5_path,
                    size_percent=self.overlay5_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay5_path = self.overlay5_path
        
        # Preprocess overlay6 image (only for images, not videos)
        processed_overlay6_path = self.overlay6_path
        if self.use_overlay6 and self.overlay6_path:
            file_ext = os.path.splitext(self.overlay6_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay6_image
                processed_overlay6_path = preprocess_overlay6_image(
                    image_path=self.overlay6_path,
                    size_percent=self.overlay6_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay6_path = self.overlay6_path
        
        # Preprocess overlay7 image (only for images, not videos)
        processed_overlay7_path = self.overlay7_path
        if self.use_overlay7 and self.overlay7_path:
            file_ext = os.path.splitext(self.overlay7_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay7_image
                processed_overlay7_path = preprocess_overlay7_image(
                    image_path=self.overlay7_path,
                    size_percent=self.overlay7_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay7_path = self.overlay7_path
        
        # Preprocess overlay8 image (only for images, not videos)
        processed_overlay8_path = self.overlay8_path
        if self.use_overlay8 and self.overlay8_path:
            file_ext = os.path.splitext(self.overlay8_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay8_image
                processed_overlay8_path = preprocess_overlay8_image(
                    image_path=self.overlay8_path,
                    size_percent=self.overlay8_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay8_path = self.overlay8_path
        
        # Preprocess overlay9 image (only for images, not videos)
        processed_overlay9_path = self.overlay9_path
        if self.use_overlay9 and self.overlay9_path:
            file_ext = os.path.splitext(self.overlay9_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay9_image
                processed_overlay9_path = preprocess_overlay9_image(
                    image_path=self.overlay9_path,
                    size_percent=self.overlay9_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay9_path = self.overlay9_path
        
        # Preprocess overlay10 image (only for images, not videos)
        processed_overlay10_path = self.overlay10_path
        if self.use_overlay10 and self.overlay10_path:
            file_ext = os.path.splitext(self.overlay10_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_overlay10_image
                processed_overlay10_path = preprocess_overlay10_image(
                    image_path=self.overlay10_path,
                    size_percent=self.overlay10_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_overlay10_path = self.overlay10_path
        
        # Preprocess framebox image (only for images, not videos)
        processed_frame_box_path = self.frame_box_path
        if self.use_frame_box and self.frame_box_path:
            file_ext = os.path.splitext(self.frame_box_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_framebox_image
                processed_frame_box_path = preprocess_framebox_image(
                    image_path=self.frame_box_path,
                    size_percent=self.frame_box_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_frame_box_path = self.frame_box_path
        
        # Preprocess frame_mp3cover image (only for images, not videos)
        processed_frame_mp3cover_path = self.frame_mp3cover_path
        if self.use_frame_mp3cover and self.frame_mp3cover_path:
            file_ext = os.path.splitext(self.frame_mp3cover_path)[1].lower()
            is_gif = file_ext == '.gif'
            is_video = file_ext in ['.mp4', '.mov', '.mkv']
            
            if not is_gif and not is_video:
                # Only preprocess non-GIF images (PNG, etc.), not GIFs or videos
                from src.utils import preprocess_frame_mp3cover_image
                processed_frame_mp3cover_path = preprocess_frame_mp3cover_image(
                    image_path=self.frame_mp3cover_path,
                    size_percent=self.frame_mp3cover_size_percent
                )
            else:
                # For GIFs and videos, use original path - FFmpeg will handle scaling
                processed_frame_mp3cover_path = self.frame_mp3cover_path
        
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

        # Get total duration from merged audio
        from src.ffmpeg_utils import get_audio_duration
        total_duration = get_audio_duration(merged_audio_path)
        
        # --- Calculate song durations only if needed by overlays ---
        song_durations = []
        needs_song_durations = (
            self.use_song_title_overlay or 
            self.use_mp3_cover_overlay or 
            (self.use_overlay10 and self.overlay10_song_start_end_checked)
        )
        
        if needs_song_durations:
            cumulative_time = 0.0
            for mp3_path in selected_mp3s:
                duration = get_audio_duration(mp3_path)
                song_durations.append((cumulative_time, duration))
                cumulative_time += duration

        # --- Generate soundwave overlay if enabled ---
        soundwave_overlay_path = None
        try:
            # Initialize extra overlays list
            extra_overlays = []
            
            # Process Song Title overlays independently (only if song titles are enabled)
            if self.use_song_title_overlay and len(song_title_pngs) > 0 and song_durations:
                # Multiple overlays: first starts at user input, others at song boundaries
                # Use pre-calculated song_durations
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
                        'y_percent': song_title_pngs[i]['y_percent'],
                        'size_percent': 100,  # Already prescaled, so use 100% to avoid double scaling
                        'effect': self.song_title_effect,
                        'type': 'song_title'
                    })

            # Process MP3 Cover overlays independently (only if MP3 covers are enabled)
            if self.use_mp3_cover_overlay and len(mp3_cover_pngs) > 0 and song_durations:
                # MP3 covers work like song titles: each cover appears during its corresponding song
                # Use pre-calculated song_durations
                for i, (song_start, song_duration) in enumerate(song_durations):
                    if i < len(mp3_cover_pngs):  # Make sure we have a cover for this song
                        if i == 0:
                            # First cover: start at user input, duration depends on full duration checkbox
                            overlay_start = self.mp3_cover_start_at
                            if self.mp3_cover_duration_full_checkbox_checked:
                                overlay_duration = song_duration - (overlay_start - song_start)
                                overlay_duration = max(overlay_duration, 1.0)
                            else:
                                overlay_duration = self.mp3_cover_duration
                        else:
                            # Subsequent covers: start at song start, duration depends on full duration checkbox
                            overlay_start = song_start
                            if self.mp3_cover_duration_full_checkbox_checked:
                                overlay_duration = song_duration
                            else:
                                overlay_duration = self.mp3_cover_duration
                        
                        extra_overlays.append({
                            'path': mp3_cover_pngs[i]['path'],
                            'start': overlay_start,
                            'duration': overlay_duration,
                            'x_percent': mp3_cover_pngs[i]['x_percent'],
                            'y_percent': mp3_cover_pngs[i]['y_percent'],
                            'size_percent': 100,  # Already prescaled, so use 100% to avoid double scaling
                            'effect': mp3_cover_pngs[i]['effect'],
                            'type': 'mp3_cover'
                        })
            
            # --- Generate soundwave overlay if enabled ---
            if self.use_soundwave_overlay and merged_audio_path:
                print("🎵 Attempting to generate soundwave overlay...")
                print(f"🎵 Soundwave settings: method={self.soundwave_method}, color={self.soundwave_color}, size={self.soundwave_size_percent}%, x={self.soundwave_x_percent}%, y={self.soundwave_y_percent}%")
                logger.info(f"Attempting to generate soundwave overlay...")
                logger.info(f"Soundwave settings: method={self.soundwave_method}, color={self.soundwave_color}, size={self.soundwave_size_percent}%, x={self.soundwave_x_percent}%, y={self.soundwave_y_percent}%")
                try:
                    from src.soundwave_generator import create_soundwave_from_merged_audio
                    print("🎵 Calling soundwave generation function...")
                    soundwave_overlay_path = create_soundwave_from_merged_audio(
                        merged_audio_path=merged_audio_path,
                        method=self.soundwave_method,
                        color=self.soundwave_color,
                        size_percent=self.soundwave_size_percent,
                        x_percent=self.soundwave_x_percent,
                        y_percent=self.soundwave_y_percent
                    )
                    if soundwave_overlay_path:
                        print(f"✅ Soundwave overlay generated successfully: {soundwave_overlay_path}")
                        logger.info(f"Soundwave overlay generated successfully: {soundwave_overlay_path}")
                    else:
                        print("❌ Failed to generate soundwave overlay - function returned None")
                        logger.warning("Failed to generate soundwave overlay - function returned None")
                        soundwave_overlay_path = None
                except Exception as e:
                    print(f"❌ Error generating soundwave overlay: {e}")
                    logger.error(f"Error generating soundwave overlay: {e}")
                    import traceback
                    traceback_str = traceback.format_exc()
                    print(f"❌ Traceback: {traceback_str}")
                    logger.error(f"Traceback: {traceback_str}")
                    soundwave_overlay_path = None
            else:
                print(f"ℹ️ Soundwave overlay not enabled: use_soundwave_overlay={self.use_soundwave_overlay}, merged_audio_path exists={merged_audio_path is not None}")
                logger.info(f"Soundwave overlay not enabled: use_soundwave_overlay={self.use_soundwave_overlay}, merged_audio_path exists={merged_audio_path is not None}")
            # --- End soundwave overlay ---
            
            # Calculate actual intro start time and duration based on checkbox states (only if intro is enabled)
            actual_intro_start_at = 0
            actual_intro_duration = self.intro_duration
            
            if self.use_intro:
                if not self.intro_start_checkbox_checked:
                    # Use start from logic: countdown from end
                    actual_intro_start_at = int(max(0, total_duration - self.intro_start_from))
                else:
                    # Use start at value directly
                    actual_intro_start_at = self.intro_start_at
                
                if self.intro_duration_full_checkbox_checked:
                    # Use full remaining duration: total_duration - start_at
                    actual_intro_duration = int(max(1, total_duration - actual_intro_start_at))
            
            # Calculate actual overlay1_2 start times based on checkbox state (only if overlays are enabled)
            actual_overlay1_start_at = self.overlay1_start_at
            actual_overlay2_start_at = self.overlay2_start_at
            
            if self.use_overlay or self.use_overlay2:
                if not self.overlay1_2_start_at_checkbox_checked:
                    # Use start from logic: countdown from end
                    actual_overlay1_start_at = int(max(0, total_duration - self.overlay1_2_start_from))
                    actual_overlay2_start_at = int(max(0, total_duration - self.overlay1_2_start_from))
            
            # Calculate actual overlay4_5 start times based on checkbox state (only if overlays are enabled)
            actual_overlay4_start_at = self.overlay4_start_time
            actual_overlay5_start_at = self.overlay5_start_time
            
            if self.use_overlay4 or self.use_overlay5:
                if not self.overlay4_5_start_at_checkbox_checked:
                    # Use start from logic: countdown from end
                    actual_overlay4_start_at = int(max(0, total_duration - self.overlay4_5_start_from))
                    actual_overlay5_start_at = int(max(0, total_duration - self.overlay4_5_start_from))
            
            # Calculate actual overlay6_7 start times based on checkbox state (only if overlays are enabled)
            actual_overlay6_start_at = self.overlay6_start_time
            actual_overlay7_start_at = self.overlay7_start_time
            
            if self.use_overlay6 or self.use_overlay7:
                if not self.overlay6_7_start_at_checkbox_checked:
                    # Use start from logic: countdown from end
                    actual_overlay6_start_at = int(max(0, total_duration - self.overlay6_7_start_from))
                    actual_overlay7_start_at = int(max(0, total_duration - self.overlay6_7_start_from))
            
            # Calculate actual overlay8 start time based on checkbox state (only if overlay8 is enabled)
            actual_overlay8_start_at = 0  # Default value
            
            if self.use_overlay8:
                if not self.overlay8_start_at_checkbox_checked:
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
                
                # Final validation to ensure start time is valid
                actual_overlay8_start_at = max(0, actual_overlay8_start_at)           
                
                # Additional validation for overlay8 parameters
                if actual_overlay8_start_at < 0:                
                    actual_overlay8_start_at = 0
                if self.overlay8_duration < 0:                
                    self.overlay8_duration = 1
            
            # Calculate actual overlay9 start time based on checkbox state (only if overlay9 is enabled)
            actual_overlay9_start_at = 0  # Default value
            
            if self.use_overlay9:
                if not self.overlay9_start_at_checkbox_checked:
                    # Use start from logic
                    if self.overlay9_duration_full_checkbox_checked:
                        # Full duration: simple percentage of total duration
                        actual_overlay9_start_at = int((self.overlay9_start_from / 100.0) * total_duration)
                    else:
                        # Limited duration: (total_duration * percentage) - effect_duration
                        effect_duration = self.overlay9_duration
                        percentage_time = (self.overlay9_start_from / 100.0) * total_duration
                        actual_overlay9_start_at = int(max(0, percentage_time - effect_duration))
                    # Ensure the start time doesn't exceed the video duration
                    actual_overlay9_start_at = min(actual_overlay9_start_at, int(total_duration - 1))
                else:
                    # Use start at logic: simple percentage of total duration (NO duration subtraction)
                    actual_overlay9_start_at = int((self.overlay9_start_time / 100.0) * total_duration)
                    # Ensure the start time doesn't exceed the video duration
                    actual_overlay9_start_at = min(actual_overlay9_start_at, int(total_duration - 1))
                
                # Final validation to ensure start time is valid
                actual_overlay9_start_at = max(0, actual_overlay9_start_at)
                           
                # Additional validation for overlay9 parameters
                if actual_overlay9_start_at < 0:                
                    actual_overlay9_start_at = 0
                if self.overlay9_duration < 0:                
                    self.overlay9_duration = 1
            
            # Calculate actual overlay10 start time based on checkbox state (only if overlay10 is enabled)
            actual_overlay10_start_at = 0  # Default value
            
            if self.use_overlay10:
                if not self.overlay10_start_at_checkbox_checked:
                    # Use start from logic: (total_duration * percentage) - effect_duration
                    effect_duration = self.overlay10_duration
                    if self.overlay10_start_time_percent > 0:
                        # Use percentage of total duration if specified
                        actual_overlay10_start_at = int((self.overlay10_start_time_percent / 100.0) * total_duration)
                    else:
                        # Fall back to regular start from logic
                        percentage_time = (self.overlay10_start_from / 100.0) * total_duration
                        actual_overlay10_start_at = int(max(0, percentage_time - effect_duration))
                    # Ensure the start time doesn't exceed the video duration
                    actual_overlay10_start_at = min(actual_overlay10_start_at, int(total_duration - 1))
                else:
                    # Use start at logic: simple percentage of total duration (NO duration subtraction)
                    actual_overlay10_start_at = int((self.overlay10_start_time / 100.0) * total_duration)
                    # Ensure the start time doesn't exceed the video duration
                    actual_overlay10_start_at = min(actual_overlay10_start_at, int(total_duration - 1))
                
                # Final validation to ensure start time is valid
                actual_overlay10_start_at = max(0, actual_overlay10_start_at)            
                
                # Additional validation for overlay10 parameters
                if actual_overlay10_start_at < 0:                
                    actual_overlay10_start_at = 0
                if self.overlay10_duration < 0:                
                    self.overlay10_duration = 1
            
            

            # Create video (Overlay 1: GIF/PNG, with size)
            success, err = create_video_with_ffmpeg(
                processed_image_path, merged_audio_path, output_path, self.resolution, self.fps, self.codec,
                use_overlay=self.use_overlay,
                overlay1_path=processed_overlay1_path,  # Use preprocessed overlay1
                overlay1_size_percent=self.overlay1_size_percent,  # Pass original size percent for detection
                overlay1_x_percent=self.overlay1_x_percent,
                overlay1_y_percent=self.overlay1_y_percent,
                use_overlay2=self.use_overlay2,
                overlay2_path=processed_overlay2_path,  # Use preprocessed overlay2
                overlay2_size_percent=self.overlay2_size_percent,  # Pass original size percent for detection
                overlay2_x_percent=self.overlay2_x_percent,
                overlay2_y_percent=self.overlay2_y_percent,
                use_overlay3=self.use_overlay3,
                overlay3_path=processed_overlay3_path,  # Use preprocessed overlay3
                overlay3_size_percent=self.overlay3_size_percent,  # Pass original size percent for detection
                overlay3_x_percent=self.overlay3_x_percent,
                overlay3_y_percent=self.overlay3_y_percent,
                use_overlay4=self.use_overlay4,
                overlay4_path=processed_overlay4_path,  # Use preprocessed overlay4
                overlay4_size_percent=self.overlay4_size_percent,  # Pass original size percent for detection
                overlay4_x_percent=self.overlay4_x_percent,
                overlay4_y_percent=self.overlay4_y_percent,
                use_overlay5=self.use_overlay5,
                overlay5_path=processed_overlay5_path,  # Use preprocessed overlay5
                overlay5_size_percent=self.overlay5_size_percent,  # Pass original size percent for detection
                overlay5_x_percent=self.overlay5_x_percent,
                overlay5_y_percent=self.overlay5_y_percent,
                use_overlay6=self.use_overlay6,
                overlay6_path=processed_overlay6_path,  # Use preprocessed overlay6
                overlay6_size_percent=self.overlay6_size_percent,  # Pass original size percent for detection
                overlay6_x_percent=self.overlay6_x_percent,
                overlay6_y_percent=self.overlay6_y_percent,
                use_overlay7=self.use_overlay7,
                overlay7_path=processed_overlay7_path,  # Use preprocessed overlay7
                overlay7_size_percent=self.overlay7_size_percent,  # Pass original size percent for detection
                overlay7_x_percent=self.overlay7_x_percent,
                overlay7_y_percent=self.overlay7_y_percent,
                use_overlay8=self.use_overlay8,
                overlay8_path=processed_overlay8_path,  # Use preprocessed overlay8
                overlay8_size_percent=self.overlay8_size_percent,  # Pass original size percent for detection
                overlay8_x_percent=self.overlay8_x_percent,
                overlay8_y_percent=self.overlay8_y_percent,
                use_overlay9=self.use_overlay9,
                overlay9_path=processed_overlay9_path,  # Use preprocessed overlay9
                overlay9_size_percent=self.overlay9_size_percent,  # Pass original size percent for detection
                overlay9_x_percent=self.overlay9_x_percent,
                overlay9_y_percent=self.overlay9_y_percent,
                use_overlay10=self.use_overlay10,
                overlay10_path=processed_overlay10_path,  # Use preprocessed overlay10
                overlay10_size_percent=self.overlay10_size_percent,  # Pass original size percent for detection
                overlay10_x_percent=self.overlay10_x_percent,
                overlay10_y_percent=self.overlay10_y_percent,
                use_intro=self.use_intro,
                intro_path=processed_intro_path,  # Use preprocessed intro
                intro_size_percent=self.intro_size_percent,  # Pass original size percent for detection
                intro_x_percent=self.intro_x_percent,
                intro_y_percent=self.intro_y_percent,
                overlay1_2_effect=self.overlay1_2_effect,
                overlay1_2_start_time=actual_overlay1_start_at,
                overlay1_2_duration=self.overlay1_2_duration,
                overlay1_2_duration_full_checkbox_checked=self.overlay1_2_duration_full_checkbox_checked,
                intro_effect=self.intro_effect,
                intro_duration=actual_intro_duration,
                intro_start_at=actual_intro_start_at,
                intro_duration_full_checkbox_checked=self.intro_duration_full_checkbox_checked,
                preset=self.preset,
                audio_bitrate=self.audio_bitrate,
                video_bitrate=self.video_bitrate,
                maxrate=self.maxrate,
                bufsize=self.bufsize,
                extra_overlays=extra_overlays,
                song_title_effect=self.song_title_effect,
                song_title_font=self.song_title_font,
                song_title_font_size=self.song_title_font_size,
                song_title_color=self.song_title_color,
                song_title_bg=self.song_title_bg,
                song_title_bg_color=self.song_title_bg_color,
                song_title_opacity=self.song_title_opacity,
                song_title_scale_percent=self.song_title_scale_percent,
                # --- Add song title text effect parameters ---
                song_title_text_effect=self.song_title_text_effect,
                song_title_text_effect_color=self.song_title_text_effect_color,
                song_title_text_effect_intensity=self.song_title_text_effect_intensity,
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
                overlay8_start_time=actual_overlay8_start_at,
                overlay8_duration=self.overlay8_duration,
                overlay8_duration_full_checkbox_checked=self.overlay8_duration_full_checkbox_checked,
                overlay9_effect=self.overlay9_effect,
                overlay9_start_time=actual_overlay9_start_at,
                overlay9_duration=self.overlay9_duration,
                overlay10_effect=self.overlay10_effect,
                overlay10_start_time=actual_overlay10_start_at,
                overlay10_duration=self.overlay10_duration,
                overlay9_duration_full_checkbox_checked=self.overlay9_duration_full_checkbox_checked,
                # --- Add frame box parameters ---
                use_frame_box=self.use_frame_box,
                frame_box_path=processed_frame_box_path,
                frame_box_size_percent=self.frame_box_size_percent,
                frame_box_x_percent=self.frame_box_x_percent,
                frame_box_y_percent=self.frame_box_y_percent,
                frame_box_effect=self.frame_box_effect,
                frame_box_start_time=self.frame_box_start_time,
                frame_box_duration=self.frame_box_duration,
                frame_box_duration_full_checkbox_checked=self.frame_box_duration_full_checkbox_checked,
                frame_box_pad_left=self.frame_box_pad_left,
                frame_box_pad_right=self.frame_box_pad_right,
                frame_box_pad_top=self.frame_box_pad_top,
                frame_box_pad_bottom=self.frame_box_pad_bottom,
                # --- Add frame box custom image parameters ---
                use_frame_box_custom_image=self.use_frame_box_custom_image,
                frame_box_custom_image_path=self.frame_box_custom_image_path,
                # --- Add frame mp3cover parameters ---
                use_frame_mp3cover=self.use_frame_mp3cover,
                frame_mp3cover_path=processed_frame_mp3cover_path,
                frame_mp3cover_size_percent=self.frame_mp3cover_size_percent,
                frame_mp3cover_x_percent=self.frame_mp3cover_x_percent,
                frame_mp3cover_y_percent=self.frame_mp3cover_y_percent,
                frame_mp3cover_effect=self.frame_mp3cover_effect,
                frame_mp3cover_start_time=self.frame_mp3cover_start_time,
                frame_mp3cover_duration=self.frame_mp3cover_duration,
                frame_mp3cover_duration_full_checkbox_checked=self.frame_mp3cover_duration_full_checkbox_checked,
                # --- Background layer parameters are now handled in advance during image preprocessing ---
                # --- Add soundwave overlay parameters ---
                use_soundwave_overlay=self.use_soundwave_overlay,
                soundwave_overlay_path=soundwave_overlay_path or "",
                soundwave_size_percent=self.soundwave_size_percent,
                soundwave_x_percent=self.soundwave_x_percent,
                soundwave_y_percent=self.soundwave_y_percent,
                overlay1_start_at=actual_overlay1_start_at,
                overlay2_start_at=actual_overlay2_start_at,
                # --- Add layer order parameter ---
                layer_order=self.layer_order
            )
            if not success:
                self.error.emit(err or f"Failed to create video: {output_filename}")
                return False, []
        except (OSError, ValueError) as e:
            self.error.emit(f"Exception creating video: {e}")
            return False, []
        finally:
            # Always cleanup temporary audio file
            self._cleanup_temp_audio(merged_audio_path)
            # Clean up soundwave overlay file
            if 'soundwave_overlay_path' in locals() and soundwave_overlay_path and os.path.exists(soundwave_overlay_path):
                try:
                    os.remove(soundwave_overlay_path)
                except:
                    pass
            # Clean up processed background image if it was created
            if 'processed_image_path' in locals() and processed_image_path != selected_image and os.path.exists(processed_image_path):
                try:
                    os.remove(processed_image_path)
                except:
                    pass
            # Clean up processed overlay1 image if it was created
            if 'processed_overlay1_path' in locals() and processed_overlay1_path != self.overlay1_path and os.path.exists(processed_overlay1_path):
                try:
                    os.remove(processed_overlay1_path)
                except:
                    pass
            # Clean up processed overlay2 image if it was created
            if 'processed_overlay2_path' in locals() and processed_overlay2_path != self.overlay2_path and os.path.exists(processed_overlay2_path):
                try:
                    os.remove(processed_overlay2_path)
                except:
                    pass
            # Clean up processed overlay3 image if it was created
            if 'processed_overlay3_path' in locals() and processed_overlay3_path != self.overlay3_path and os.path.exists(processed_overlay3_path):
                try:
                    os.remove(processed_overlay3_path)
                except:
                    pass
            # Clean up processed intro image if it was created
            if 'processed_intro_path' in locals() and processed_intro_path != self.intro_path and os.path.exists(processed_intro_path):
                try:
                    os.remove(processed_intro_path)
                except:
                    pass
            # Clean up processed overlay4 image if it was created
            if 'processed_overlay4_path' in locals() and processed_overlay4_path != self.overlay4_path and os.path.exists(processed_overlay4_path):
                try:
                    os.remove(processed_overlay4_path)
                except:
                    pass
            # Clean up processed overlay5 image if it was created
            if 'processed_overlay5_path' in locals() and processed_overlay5_path != self.overlay5_path and os.path.exists(processed_overlay5_path):
                try:
                    os.remove(processed_overlay5_path)
                except:
                    pass
            # Clean up processed overlay6 image if it was created
            if 'processed_overlay6_path' in locals() and processed_overlay6_path != self.overlay6_path and os.path.exists(processed_overlay6_path):
                try:
                    os.remove(processed_overlay6_path)
                except:
                    pass
            # Clean up processed overlay7 image if it was created
            if 'processed_overlay7_path' in locals() and processed_overlay7_path != self.overlay7_path and os.path.exists(processed_overlay7_path):
                try:
                    os.remove(processed_overlay7_path)
                except:
                    pass
            # Clean up processed overlay8 image if it was created
            if 'processed_overlay8_path' in locals() and processed_overlay8_path != self.overlay8_path and os.path.exists(processed_overlay8_path):
                try:
                    os.remove(processed_overlay8_path)
                except:
                    pass
            # Clean up processed overlay9 image if it was created
            if 'processed_overlay9_path' in locals() and processed_overlay9_path != self.overlay9_path and os.path.exists(processed_overlay9_path):
                try:
                    os.remove(processed_overlay9_path)
                except:
                    pass
            # Clean up processed overlay10 image if it was created
            if 'processed_overlay10_path' in locals() and processed_overlay10_path != self.overlay10_path and os.path.exists(processed_overlay10_path):
                try:
                    os.remove(processed_overlay10_path)
                except:
                    pass
            # Clean up processed framebox image if it was created
            if 'processed_frame_box_path' in locals() and processed_frame_box_path != self.frame_box_path and os.path.exists(processed_frame_box_path):
                try:
                    os.remove(processed_frame_box_path)
                except:
                    pass
            # Clean up processed frame_mp3cover image if it was created
            if 'processed_frame_mp3cover_path' in locals() and processed_frame_mp3cover_path != self.frame_mp3cover_path and os.path.exists(processed_frame_mp3cover_path):
                try:
                    os.remove(processed_frame_mp3cover_path)
                except:
                    pass
            
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