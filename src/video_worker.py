# This file uses PyQt6
import os
import random
import shutil
from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Optional
from src.ffmpeg_utils import merge_random_mp3s, create_video_with_ffmpeg
from src.utils import set_low_priority
import time
from src.logger import logger

class VideoWorker(QObject):
    """Worker class for processing video creation in background thread. Supports GIF overlay for Overlay 1. Optionally supports a name list for output naming."""
    progress = pyqtSignal(int, int)  # batch_count, total_batches
    error = pyqtSignal(str)
    finished = pyqtSignal(list, list, list)  # leftover_mp3s, used_images, failed_moves

    def __init__(self, media_sources: str, export_name: str, number: str, 
                 folder: str, codec: str = "libx264", resolution: str = "1920x1080", fps: int = 24, use_overlay: bool = False, min_mp3_count: int = 3, overlay1_path: str = "", overlay1_size_percent: int = 100, overlay1_position: str = "top_left",
                 use_overlay2: bool = False, overlay2_path: str = "", overlay2_size_percent: int = 10, overlay2_position: str = "top_left",
                 use_overlay3: bool = False, overlay3_path: str = "", overlay3_size_percent: int = 10, overlay3_position: str = "top_left",
                 use_intro: bool = False, intro_path: str = "", intro_size_percent: int = 10, intro_position: str = "center",
                 effect: str = "fadein", effect_time: int = 5,
                 intro_effect: str = "fadeout", intro_duration: int = 5,
                 name_list: Optional[List[str]] = None,
                 preset: str = "slow",
                 audio_bitrate: str = "384k",
                 video_bitrate: str = "12M",
                 maxrate: str = "16M",
                 bufsize: str = "24M",
                 use_song_title_overlay: bool = True):
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
        self.overlay1_position = overlay1_position
        self.use_overlay2 = use_overlay2
        self.overlay2_path = overlay2_path
        self.overlay2_size_percent = overlay2_size_percent
        self.overlay2_position = overlay2_position
        self.use_overlay3 = use_overlay3
        self.overlay3_path = overlay3_path
        self.overlay3_size_percent = overlay3_size_percent
        self.overlay3_position = overlay3_position
        self.use_intro = use_intro
        self.intro_path = intro_path
        self.intro_size_percent = intro_size_percent
        self.intro_position = intro_position
        self.effect = effect
        self.effect_time = effect_time
        self.intro_effect = intro_effect
        self.intro_duration = intro_duration
        self.name_list = name_list if name_list is not None else []
        self.preset = preset
        self.audio_bitrate = audio_bitrate
        self.video_bitrate = video_bitrate
        self.maxrate = maxrate
        self.bufsize = bufsize
        self._stop = False
        self._used_images = set()
        self.use_song_title_overlay = use_song_title_overlay

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
            print(f"Output folder: {self.folder}")
            self.finished.emit(mp3_files, list(self._used_images), all_failed_moves)
            
        except Exception as e:
            error_msg = f"Error during video creation: {str(e)}"
            print(f"❌ {error_msg}")
            self.error.emit(error_msg)

    def _print_export_summary(self, total_batches: int):
        """Print export configuration summary"""
        print("\n----- EXPORT SUMMARY -----")
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
            import tempfile
            for idx, mp3_path in enumerate(selected_mp3s, start=5):  # overlay5, overlay6, ...
                title = extract_mp3_title(mp3_path)
                # Create a temp PNG file for the overlay
                temp_png = tempfile.NamedTemporaryFile(delete=False, suffix=f'_overlay{idx}.png')
                temp_png.close()
                create_song_title_png(title, temp_png.name, width=800, height=80, font_size=32)
                song_title_pngs.append((temp_png.name, title))
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
        print(f"\n--- Batch {batch_count + 1}/{total_batches} ---")
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
            # Calculate timing for each overlay (equal split for now)
            overlay_count = len(song_title_pngs)
            overlay_duration = audio_duration / overlay_count if overlay_count else 0
            extra_overlays = []
            for i, (png_path, title) in enumerate(song_title_pngs):
                start = i * overlay_duration
                extra_overlays.append({
                    'path': png_path,
                    'start': start,
                    'duration': overlay_duration,
                    'fade': True
                })
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
                self.overlay1_position,
                self.use_overlay2,
                self.overlay2_path,
                self.overlay2_size_percent,
                self.overlay2_position,
                self.use_overlay3,
                self.overlay3_path,
                self.overlay3_size_percent,
                self.overlay3_position,
                self.use_intro,
                self.intro_path,
                self.intro_size_percent,
                self.intro_position,
                self.effect,
                self.effect_time,
                self.intro_effect,
                self.intro_duration,
                self.preset,
                self.audio_bitrate,
                self.video_bitrate,
                self.maxrate,
                self.bufsize,
                extra_overlays=extra_overlays
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
        print(f"\u2713 Batch {batch_count + 1}/{total_batches} completed: {output_filename} (Time spent: {time_str})")
        
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