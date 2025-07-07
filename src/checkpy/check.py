# This file uses PyQt6
import os
# Set FFMPEG paths (use local ffmpeg folder)
os.environ["FFMPEG_BINARY"] = os.path.abspath("ffmpeg/bin/ffmpeg.exe")
os.environ["FFPLAY_BINARY"] = os.path.abspath("ffmpeg/bin/ffplay.exe")

from moviepy.config import check
check() 