# SuperCut Video Maker - Modular Version

A modular video creation application that combines images and audio files into videos using FFmpeg.

## Project Structure

The application has been deconstructed into smaller, focused modules:

### Core Modules

- **`main.py`** - Main entry point and application startup
- **`config.py`** - Configuration settings, constants, and FFmpeg paths
- **`utils.py`** - Utility functions for file operations, validation, and system utilities
- **`ffmpeg_utils.py`** - FFmpeg-specific operations (audio merging, video creation, progress tracking)
- **`video_worker.py`** - Background worker for video processing
- **`ui_components.py`** - Reusable UI components and dialogs
- **`main_ui.py`** - Main application window and UI logic

### Module Responsibilities

#### `config.py`
- FFmpeg binary paths and environment setup
- UI configuration (window size, styles, etc.)
- Video encoding settings and defaults
- File extension definitions
- Style sheet definitions

#### `utils.py`
- File type detection and validation
- Temporary file management
- System utilities (desktop folder, file explorer)
- Input validation functions
- Filename sanitization

#### `ffmpeg_utils.py`
- Audio duration extraction using ffprobe
- MP3 file merging with progress tracking
- Video creation from image + audio
- Real-time progress reporting
- FFmpeg command building

#### `video_worker.py`
- Background video processing
- Batch processing logic
- File organization and cleanup
- Progress signaling to UI
- Error handling and recovery

#### `ui_components.py`
- Custom drag-and-drop line edit
- Progress dialogs (waiting, stopped, success)
- Reusable dialog components
- Consistent styling

#### `main_ui.py`
- Main application window
- UI layout and component management
- User interaction handling
- Thread management
- Settings persistence

## Benefits of Modular Structure

1. **Maintainability** - Each module has a single responsibility
2. **Testability** - Individual modules can be tested in isolation
3. **Reusability** - Components can be reused in other projects
4. **Readability** - Code is organized logically and easy to navigate
5. **Scalability** - New features can be added without affecting existing code

## Usage

### Running the Application

```bash
python main.py
```

### Requirements

- Python 3.6+
- PyQt5
- FFmpeg (must be installed in `C:/SuperCut/ffmpeg/bin/`)

### Features

- **Drag & Drop** - Drop folders directly into the UI
- **Batch Processing** - Process multiple videos automatically
- **Progress Tracking** - Real-time progress with ETA
- **Multiple Codecs** - Support for H.264 NVENC and libx264
- **Various Resolutions** - Full HD, 4K, Vertical, Square formats
- **File Organization** - Automatic organization of processed files
- **Error Handling** - Comprehensive error handling and recovery

## File Organization

The application automatically organizes files:

- **Input**: MP3 and image files in the media folder
- **Output**: MP4 videos in the output folder
- **Bin Folder**: Processed files moved to `bin/` subfolder with logs

## Configuration

Edit `config.py` to modify:
- FFmpeg paths
- Default video settings
- UI styling
- File extensions
- Window properties

## Development

### Adding New Features

1. **UI Components** - Add to `ui_components.py`
2. **FFmpeg Operations** - Add to `ffmpeg_utils.py`
3. **Utility Functions** - Add to `utils.py`
4. **Configuration** - Add to `config.py`
5. **Main Logic** - Add to `main_ui.py` or `video_worker.py`

### Testing Individual Modules

Each module can be tested independently:

```python
# Test utils
from utils import validate_inputs
result, error = validate_inputs("folder", "name", "123")
print(result, error)

# Test ffmpeg utils
from ffmpeg_utils import get_audio_duration
duration = get_audio_duration("audio.mp3")
print(duration)
```

## Error Handling

The application includes comprehensive error handling:
- FFmpeg installation validation
- Input validation
- File existence checks
- Process interruption handling
- Temporary file cleanup

## Performance

- Background processing prevents UI freezing
- Low priority process setting for better system performance
- Efficient file handling and cleanup
- Progress tracking with minimal overhead 