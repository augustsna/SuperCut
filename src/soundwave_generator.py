#!/usr/bin/env python3
"""
Soundwave Generator Module
Integrates py-sound-viewer functionality to generate soundwave MP4 files with transparent backgrounds.
"""

import os
import sys
import wave
import subprocess
import tempfile
from typing import Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend to avoid GUI issues
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import collections as mc
import numpy as np
import colorsys
from src.logger import logger
from src.utils import create_temp_file
from src.config import FFMPEG_BINARY

# Import py-sound-viewer compute functions
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'py-sound-viewer-main'))
    from compute import compute, WIDTH, HEIGHT, SAMPLE_SIZE, CHANNELS, RATE, FPS  # type: ignore
except ImportError as e:
    logger.error(f"Failed to import py-sound-viewer compute functions: {e}")
    logger.error("Make sure the py-sound-viewer-main folder is in the src directory")
    # Set default values if import fails
    WIDTH = 1280
    HEIGHT = 720
    SAMPLE_SIZE = 2
    CHANNELS = 2
    RATE = 44100
    FPS = 25.0
    compute = None

class SoundwaveGenerator:
    """Generate soundwave MP4 files with transparent backgrounds"""
    
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.sample_size = SAMPLE_SIZE
        self.channels = CHANNELS
        self.rate = RATE
        self.fps = FPS
    
    def convert_audio_to_wav(self, audio_path: str) -> Optional[str]:
        """Convert audio file to WAV format required by py-sound-viewer"""
        try:
            # Create temporary WAV file
            wav_path = create_temp_file(suffix='.wav', prefix='soundwave_')
            
            # Use FFmpeg to convert to WAV with specific parameters
            cmd = [
                FFMPEG_BINARY,
                '-i', audio_path,
                '-acodec', 'pcm_s16le',  # 16-bit signed little-endian
                '-ac', str(self.channels),  # Number of channels
                '-ar', str(self.rate),      # Sample rate
                '-y',  # Overwrite output
                wav_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return wav_path
            else:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {e}")
            return None
    
    def create_soundwave_mp4(self, 
                            audio_path: str, 
                            output_path: str, 
                            method: str = "bars",
                            color: str = "hue_rotate",
                            transparent_bg: bool = True) -> bool:
        """
        Create a soundwave MP4 file from audio
        
        Args:
            audio_path: Path to input audio file (MP3, M4A, etc.)
            output_path: Path for output MP4 file
            method: Visualization method ('bars', 'spectrum', 'wave', 'rain')
            color: Color scheme ('hue_rotate' or hex color)
            transparent_bg: Whether to use transparent background
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert audio to WAV format
            wav_path = self.convert_audio_to_wav(audio_path)
            if not wav_path:
                return False
            
            # Verify WAV file properties
            with wave.open(wav_path, 'rb') as wf:
                if (wf.getnchannels() != self.channels or 
                    wf.getsampwidth() != self.sample_size or 
                    wf.getframerate() != self.rate):
                    logger.error("WAV file properties don't match expected format")
                    return False
            
            # Create matplotlib figure with transparent background
            dpi = plt.rcParams['figure.dpi']
            plt.rcParams['savefig.dpi'] = 300
            plt.rcParams['figure.figsize'] = (1.0 * self.width / dpi, 1.0 * self.height / dpi)
            
            # Set figure background to transparent if requested
            if transparent_bg:
                fig = plt.figure(facecolor='none', edgecolor='none')
            else:
                fig = plt.figure(facecolor='black', edgecolor='black')
            
            # Generate animation using py-sound-viewer
            if compute is None:
                logger.error("py-sound-viewer compute function not available")
                return False
                
            with wave.open(wav_path, 'rb') as wf:
                ani = compute(method, color, fig, wf)
                if ani is None:
                    logger.error(f"Failed to create animation for method: {method}")
                    return False
                
                # Save animation with improved settings for FFmpeg compatibility
                save_kwargs = {
                    'fps': self.fps,
                    'codec': 'qtrle',  # Use QuickTime Animation codec for better transparency
                    'extra_args': [
                        '-pix_fmt', 'argb',  # Use ARGB for full transparency support
                        '-preset', 'ultrafast'
                    ]
                }
                if transparent_bg:
                    save_kwargs['savefig_kwargs'] = {'facecolor': 'none', 'transparent': True}
                else:
                    save_kwargs['savefig_kwargs'] = {'facecolor': 'black'}
                
                ani.save(output_path, **save_kwargs)
            
            logger.info(f"Soundwave MP4 created successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating soundwave MP4: {e}")
            return False
        finally:
            # Clean up temporary WAV file
            if 'wav_path' in locals() and wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except (OSError, PermissionError) as e:
                    logger.warning(f"Failed to remove temporary WAV file: {e}")
    
    def create_soundwave_overlay(self, 
                                audio_path: str, 
                                method: str = "bars",
                                color: str = "hue_rotate",
                                size_percent: int = 100,
                                x_percent: int = 50,
                                y_percent: int = 50) -> Optional[str]:
        """
        Create a soundwave overlay MOV file for use in video creation
        
        Args:
            audio_path: Path to input audio file
            method: Visualization method
            color: Color scheme
            size_percent: Size as percentage of video (1-100)
            x_percent: X position as percentage (0-100)
            y_percent: Y position as percentage (0-100)
            
        Returns:
            str: Path to created MOV file, or None if failed
        """
        try:
            # Create temporary MOV file
            output_path = create_temp_file(suffix='.mov', prefix='soundwave_overlay_')
            
            # Create the soundwave MOV
            if self.create_soundwave_mp4(audio_path, output_path, method, color, transparent_bg=True):
                return output_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error creating soundwave overlay: {e}")
            return None

def create_soundwave_from_merged_audio(merged_audio_path: str, 
                                     method: str = "bars",
                                     color: str = "hue_rotate",
                                     size_percent: int = 100,
                                     x_percent: int = 50,
                                     y_percent: int = 50) -> Optional[str]:
    """
    Create a soundwave MP4 from merged audio file
    
    Args:
        merged_audio_path: Path to merged audio file
        method: Visualization method
        color: Color scheme
        size_percent: Size as percentage of video (1-100)
        x_percent: X position as percentage (0-100)
        y_percent: Y position as percentage (0-100)
        
    Returns:
        str: Path to created MP4 file, or None if failed
    """
    try:
        generator = SoundwaveGenerator()
        return generator.create_soundwave_overlay(
            merged_audio_path, 
            method=method, 
            color=color,
            size_percent=size_percent,
            x_percent=x_percent,
            y_percent=y_percent
        )
    except Exception as e:
        logger.error(f"Error creating soundwave from merged audio: {e}")
        return None

# Available visualization methods
SOUNDWAVE_METHODS = ['bars', 'spectrum', 'wave', 'rain']

# Available color schemes
SOUNDWAVE_COLORS = ['hue_rotate', '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff']  