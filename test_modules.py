#!/usr/bin/env python3
"""
Test script to verify all modules can be imported correctly.
Run this to check if the modular structure is working.
"""

def test_imports():
    """Test importing all modules"""
    print("Testing module imports...")
    
    try:
        print("✓ Importing config...")
        import config
        print(f"  - FFMPEG_BINARY: {config.FFMPEG_BINARY}")
        print(f"  - WINDOW_SIZE: {config.WINDOW_SIZE}")
        
        print("✓ Importing utils...")
        import utils
        print(f"  - sanitize_filename function: {utils.sanitize_filename}")
        print(f"  - get_desktop_folder function: {utils.get_desktop_folder}")
        
        print("✓ Importing ffmpeg_utils...")
        import ffmpeg_utils
        print(f"  - get_audio_duration function: {ffmpeg_utils.get_audio_duration}")
        print(f"  - create_video_with_ffmpeg function: {ffmpeg_utils.create_video_with_ffmpeg}")
        
        print("✓ Importing video_worker...")
        import video_worker
        print(f"  - VideoWorker class: {video_worker.VideoWorker}")
        
        print("✓ Importing ui_components...")
        import ui_components
        print(f"  - FolderDropLineEdit class: {ui_components.FolderDropLineEdit}")
        print(f"  - WaitingDialog class: {ui_components.WaitingDialog}")
        
        print("✓ Importing main_ui...")
        import main_ui
        print(f"  - SuperCutUI class: {main_ui.SuperCutUI}")
        
        print("✓ Importing main...")
        import main
        print(f"  - main function: {main.main}")
        
        print("\n🎉 All modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def test_config_values():
    """Test configuration values"""
    print("\nTesting configuration values...")
    
    import config
    
    # Test FFmpeg paths
    print(f"✓ FFMPEG_BINARY exists: {config.FFMPEG_BINARY}")
    print(f"✓ FFPROBE_BINARY exists: {config.FFPROBE_BINARY}")
    
    # Test UI config
    print(f"✓ WINDOW_SIZE: {config.WINDOW_SIZE}")
    print(f"✓ WINDOW_TITLE: {config.WINDOW_TITLE}")
    
    # Test video config
    print(f"✓ DEFAULT_CODECS: {len(config.DEFAULT_CODECS)} codecs")
    print(f"✓ DEFAULT_RESOLUTIONS: {len(config.DEFAULT_RESOLUTIONS)} resolutions")
    print(f"✓ DEFAULT_FPS_OPTIONS: {len(config.DEFAULT_FPS_OPTIONS)} FPS options")
    
    # Test file extensions
    print(f"✓ AUDIO_EXTENSIONS: {config.AUDIO_EXTENSIONS}")
    print(f"✓ IMAGE_EXTENSIONS: {config.IMAGE_EXTENSIONS}")
    print(f"✓ VIDEO_EXTENSIONS: {config.VIDEO_EXTENSIONS}")

def test_utility_functions():
    """Test utility functions"""
    print("\nTesting utility functions...")
    
    import utils
    
    # Test filename sanitization
    test_name = "test<>:\"/\\|?*file"
    sanitized = utils.sanitize_filename(test_name)
    print(f"✓ sanitize_filename: '{test_name}' -> '{sanitized}'")
    
    # Test file type detection
    print(f"✓ is_audio_file('test.mp3'): {utils.is_audio_file('test.mp3')}")
    print(f"✓ is_image_file('test.jpg'): {utils.is_image_file('test.jpg')}")
    print(f"✓ is_video_file('test.mp4'): {utils.is_video_file('test.mp4')}")
    
    # Test validation functions
    is_valid, error = utils.validate_inputs("folder", "name", "123")
    print(f"✓ validate_inputs: valid={is_valid}, error='{error}'")

def main():
    """Run all tests"""
    print("SuperCut Modular Structure Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False
    
    # Test configuration
    test_config_values()
    
    # Test utilities
    test_utility_functions()
    
    print("\n✅ All tests passed! The modular structure is working correctly.")
    print("\nYou can now run the application with: python main.py")
    return True

if __name__ == "__main__":
    main() 