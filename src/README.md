# NOTE: This project now uses PyQt6 instead of PyQt5.

# SuperCut Video Maker

A powerful video creation tool that combines images with audio files to generate videos in batch processing mode.

## Features

- **Batch Video Creation**: Process multiple videos simultaneously using 3 MP3 files per video
- **Drag & Drop Interface**: Easy folder selection with drag and drop support
- **Customizable Export Settings**: Control video codec, resolution, and FPS
- **File Management**: Automatic organization of processed files into bin folders
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites
- Python 3.7 or higher
- PyQt5
- FFmpeg (automatically extracted on first run)

### Setup
1. Clone or download the repository
2. Install required Python packages:
   ```bash
   pip install PyQt5
   ```
3. Run the application:
   ```bash
   python main_ui.py
   ```

## Usage

### Basic Workflow
1. **Select Media Folder**: Choose a folder containing your MP3 and image files
2. **Set Export Name**: Enter a base name for your videos (e.g., "MyVideo")
3. **Set Start Number**: Enter the starting number for video naming (e.g., 1)
4. **Choose Output Folder**: Select where to save the generated videos
5. **Configure Settings**: Adjust codec, resolution, and FPS as needed
6. **Create Videos**: Click "Create Video" to start batch processing

### File Requirements
- **MP3 Files**: At least 3 MP3 files per video (processed in groups of 3)
- **Image Files**: JPG or PNG files (one per video)
- **Output**: MP4 videos with merged audio

### Batch Processing
- Each video uses 3 MP3 files and 1 image
- Files are automatically moved to a "bin" folder after processing
- Log files are created for each video showing which files were used

## Configuration

### Video Settings
- **Codec**: libx264 (default), libx265, or other FFmpeg codecs
- **Resolution**: 1920x1080, 1280x720, 854x480, or custom
- **FPS**: 24, 30, 60, or custom frame rates

## Troubleshooting

### Common Issues
1. **No image files found**: Ensure your media folder contains JPG or PNG files
2. **Not enough MP3 files**: You need at least 3 MP3 files to start processing
3. **FFmpeg not found**: The application will automatically extract FFmpeg on first run

### Error Handling
- Error messages provide specific information about what went wrong
- Temporary files are automatically cleaned up on errors

## Development

### Architecture
- **main_ui.py**: Main application interface
- **ui_components.py**: UI components and dialogs
- **video_worker.py**: Background video processing
- **ffmpeg_utils.py**: FFmpeg integration utilities
- **utils.py**: General utility functions

## License

This project is open source and available under the MIT License. 