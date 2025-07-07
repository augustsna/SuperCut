# NOTE: This project now uses PyQt6 instead of PyQt5.

# FFmpeg Unzipper CLI Tool

A simple Python CLI program that extracts FFmpeg components to the specified directories.

## Features

- Extracts `ffmpeg-folder.zip` to `C:\SuperCut\ffmpeg\`
- Extracts `ffmpeg.zip` to `C:\SuperCut\ffmpeg\bin\`
- Extracts `ffplay.zip` to `C:\SuperCut\ffmpeg\bin\`
- Extracts `ffprobe.zip` to `C:\SuperCut\ffmpeg\bin\`
- Creates necessary directories automatically
- Shows progress and success messages
- Error handling for missing files or extraction issues

## Requirements

- Python 3.6 or higher
- No additional dependencies required (uses built-in `zipfile` module)

## Usage

1. Make sure the zip files are in the `sources/` directory:
   - `sources/ffmpeg-folder.zip`
   - `sources/ffmpeg.zip`
   - `sources/ffplay.zip`
   - `sources/ffprobe.zip`

2. Run the program:
   ```bash
   python unzip_ffmpeg.py
   ```

## Output

The program will:
- Create the necessary directories (`C:\SuperCut\ffmpeg\` and `C:\SuperCut\ffmpeg\bin\`)
- Extract each zip file to its designated location
- Show progress messages for each operation
- Display a final success message when complete

## Example Output

```
🚀 FFmpeg Unzipper CLI Tool
========================================

📁 Creating directories...
✓ Directory created/verified: C:\SuperCut\ffmpeg
✓ Directory created/verified: C:\SuperCut\ffmpeg\bin

📦 Starting extraction process...
📦 Extracting FFmpeg folder...
✓ Successfully extracted FFmpeg folder to C:\SuperCut\ffmpeg

📦 Extracting FFmpeg executable...
✓ Successfully extracted FFmpeg executable to C:\SuperCut\ffmpeg\bin

📦 Extracting FFplay executable...
✓ Successfully extracted FFplay executable to C:\SuperCut\ffmpeg\bin

📦 Extracting FFprobe executable...
✓ Successfully extracted FFprobe executable to C:\SuperCut\ffmpeg\bin

========================================
💫 All files extracted successfully!
📂 FFmpeg components are now available in: C:\SuperCut\ffmpeg
🔧 Executables are located in: C:\SuperCut\ffmpeg\bin

✨ FFmpeg setup complete! 