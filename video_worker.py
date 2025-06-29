import os
import random
import shutil
from PyQt5.QtCore import QObject, pyqtSignal
from typing import List
from ffmpeg_utils import merge_random_mp3s, create_video_with_ffmpeg
from utils import set_low_priority

class VideoWorker(QObject):
    """Worker class for processing video creation in background thread"""
    progress = pyqtSignal(int, int)  # batch_count, total_batches
    error = pyqtSignal(str)
    finished = pyqtSignal(list)  # leftover_files

    def __init__(self, media_sources: str, export_name: str, number: str, 
                 folder: str, codec: str = "libx264", resolution: str = "1920x1080", fps: int = 24):
        super().__init__()
        self.media_sources = media_sources
        self.export_name = export_name
        self.number = number
        self.folder = folder
        self.codec = codec
        self.resolution = resolution
        self.fps = fps
        self._stop = False

    def stop(self):
        """Stop the video processing"""
        self._stop = True

    def run(self):
        """Main processing method"""
        set_low_priority()
        try:
            # Get media files
            from utils import get_files_by_type
            mp3_files = get_files_by_type(self.media_sources, "audio")
            image_files = get_files_by_type(self.media_sources, "image")
            
            if not image_files:
                self.error.emit("No image files found in the media folder.")
                return
            if not mp3_files or len(mp3_files) < 3:
                self.error.emit("Not enough mp3 files in folder (need at least 3 to start batch processing)")
                return
            
            # Parse start number
            try:
                start_number = int(self.number)
            except Exception:
                start_number = 1
                
            current_number = start_number
            used_images = set()
            total_batches = len(mp3_files) // 3
            batch_count = 0

            # Print export summary
            self._print_export_summary(total_batches)

            # Process batches
            while len(mp3_files) >= 3:
                if self._stop:
                    self.finished.emit(mp3_files)
                    return
                    
                # Process single batch
                success = self._process_batch(
                    mp3_files, image_files, used_images, 
                    current_number, batch_count, total_batches
                )
                
                if not success:
                    return
                    
                current_number += 1
                batch_count += 1
                self.progress.emit(batch_count, total_batches)
                
            # Print final completion message
            print(f"\n🎉 All {total_batches} batches completed successfully!")
            print(f"Output folder: {self.folder}")
            
            # Emit finished signal with leftover files
            self.finished.emit(mp3_files)
            
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
                      used_images: set, current_number: int, batch_count: int, total_batches: int) -> bool:
        """Process a single batch of video creation"""
        # Select random MP3s
        selected_mp3s = random.sample(mp3_files, 3)
        
        # Select available image
        available_images = [img for img in image_files if img not in used_images]
        if not available_images:
            used_images.clear()
            available_images = image_files[:]
        if not available_images:
            return False
            
        selected_image_name = random.choice(available_images)
        selected_image = os.path.join(self.media_sources, selected_image_name)
        used_images.add(selected_image_name)
        
        # Create output filename
        output_filename = f"{self.export_name}_{current_number}.mp4"
        output_path = os.path.join(self.folder, output_filename)

        # Print batch info
        print(f"\n--- Batch {batch_count + 1}/{total_batches} ---")
        print(f"Output: {output_filename}")
        print(f"Image: {os.path.basename(selected_image)}")
        print("MP3s:", ", ".join(os.path.basename(mp3) for mp3 in selected_mp3s))

        # Merge MP3s
        merged_audio_path, audio_duration = merge_random_mp3s(selected_mp3s)
        if not merged_audio_path or audio_duration <= 0:
            self.error.emit(f"Failed to merge MP3 files or get duration")
            return False
        
        try:
            # Create video
            if not create_video_with_ffmpeg(
                selected_image, 
                merged_audio_path, 
                output_path, 
                self.resolution, 
                self.fps, 
                self.codec
            ):
                self.error.emit(f"Failed to create video: {output_filename}")
                return False
                
        except Exception as e:
            # Cleanup on error
            self._cleanup_temp_audio(merged_audio_path)
            raise e
        finally:
            # Always cleanup temporary audio file
            self._cleanup_temp_audio(merged_audio_path)
            
        # Create log and move files
        self._create_log_and_move_files(
            output_filename, output_path, selected_image, 
            selected_mp3s, mp3_files, image_files, selected_image_name
        )
        
        # Emit progress signal
        self.progress.emit(batch_count + 1, total_batches)
        
        # Print completion message
        print(f"✓ Batch {batch_count + 1}/{total_batches} completed: {output_filename}")
        
        return True

    def _cleanup_temp_audio(self, audio_path: str):
        """Clean up temporary audio file"""
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass  # Ignore cleanup errors

    def _create_log_and_move_files(self, output_filename: str, output_path: str, 
                                  selected_image: str, selected_mp3s: List[str], 
                                  mp3_files: List[str], image_files: List[str], 
                                  selected_image_name: str):
        """Create log file and move processed files to bin folder"""
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
        
        # Move MP3 files
        output_base = os.path.splitext(os.path.basename(output_path))[0]
        for idx, mp3 in enumerate(selected_mp3s, 1):
            new_name = f"{output_base}+{idx}.mp3"
            try:
                shutil.move(mp3, os.path.join(bin_folder, new_name))
                mp3_files.remove(mp3)
            except Exception as move_err:
                print(f"Failed to move {mp3}: {move_err}")
        
        # Move image file
        try:
            img_ext = os.path.splitext(selected_image)[1]
            img_new_name = f"{output_base}{img_ext}"
            shutil.move(selected_image, os.path.join(bin_folder, img_new_name))
        except Exception as move_err:
            print(f"Failed to move {selected_image}: {move_err}")
        finally:
            if selected_image_name in image_files:
                image_files.remove(selected_image_name) 