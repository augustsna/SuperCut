import os
# Set FFMPEG paths (use local ffmpeg folder)
os.environ["FFMPEG_BINARY"] = os.path.abspath("ffmpeg/ffmpeg.exe")
os.environ["FFPLAY_BINARY"] = os.path.abspath("ffmpeg/ffplay.exe")

from moviepy.config import check
check()
