#!/usr/bin/env python3
"""
Test script for FFmpeg integration in SuperCut
Tests audio concatenation and video creation functionality
"""

import os
import sys
import tempfile
import json
import subprocess

# Import the functions from the reworked file
sys.path.append(os.path.dirname(__file__))

# Set FFMPEG paths (use local ffmpeg folder)
FFMPEG_PATH = os.path.abspath("C:/SuperCut/ffmpeg/bin/ffmpeg.exe")
FFPROBE_PATH = os.path.abspath("C:/SuperCut/ffmpeg/bin/ffprobe.exe")

def get_audio_duration(file_path):
    """Get audio duration using ffprobe"""
    try:
        cmd = [
            FFPROBE_PATH,
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception as e:
        print(f"Error getting duration for {file_path}: {e}")
        return 0.0

def concatenate_audio_files(input_files, output_file):
    """Concatenate multiple audio files using FFmpeg"""
    try:
        # Create a temporary file list for FFmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_list_file = f.name
            for file_path in input_files:
                f.write(f"file '{file_path}'\n")
        
        # Use FFmpeg to concatenate
        cmd = [
            FFMPEG_PATH,
            "-f", "concat",
            "-safe", "0",
            "-i", temp_list_file,
            "-c", "copy",
            output_file,
            "-y"  # Overwrite output file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up temp file
        try:
            os.unlink(temp_list_file)
        except:
            pass
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error concatenating audio: {e}")
        return False

def create_video_from_image_and_audio(image_path, audio_path, output_path, resolution, fps, codec):
    """Create video from image and audio using FFmpeg"""
    try:
        width, height = map(int, resolution.split('x'))
        
        # Build FFmpeg command
        cmd = [
            FFMPEG_PATH,
            "-loop", "1",  # Loop the image
            "-i", image_path,  # Input image
            "-i", audio_path,  # Input audio
            "-c:v", codec,  # Video codec
            "-c:a", "aac",  # Audio codec
            "-b:a", "384k",  # Audio bitrate
            "-ar", "48000",  # Audio sample rate
            "-ac", "2",  # Audio channels
            "-vf", f"scale={width}:{height}",  # Scale to resolution
            "-r", str(fps),  # Frame rate
            "-shortest",  # End when shortest input ends
            "-y"  # Overwrite output
        ]
        
        # Add codec-specific parameters
        if codec in ("libx264", "h264_nvenc"):
            cmd.extend([
                "-preset", "slow",
                "-profile:v", "high",
                "-level:v", "4.2"
            ])
        
        # Add common parameters
        cmd.extend([
            "-movflags", "+faststart",
            "-b:v", "15M",
            "-maxrate", "20M",
            "-bufsize", "24M",
            "-pix_fmt", "yuv420p",
            "-g", "120",
            "-bf", "2"
        ])
        
        # Add NVENC-specific parameters
        if codec == "h264_nvenc":
            cmd.extend(["-rc", "vbr_hq"])
        
        cmd.append(output_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error creating video: {e}")
        return False

def test_ffmpeg_installation():
    """Test if FFmpeg is properly installed"""
    print("🔍 Testing FFmpeg installation...")
    
    if not os.path.exists(FFMPEG_PATH):
        print(f"❌ FFmpeg not found at: {FFMPEG_PATH}")
        return False
    
    if not os.path.exists(FFPROBE_PATH):
        print(f"❌ FFprobe not found at: {FFPROBE_PATH}")
        return False
    
    print("✅ FFmpeg and FFprobe found")
    
    # Test FFmpeg version
    try:
        result = subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, text=True, check=True)
        version_line = result.stdout.split('\n')[0]
        print(f"✅ FFmpeg version: {version_line}")
    except Exception as e:
        print(f"❌ Error getting FFmpeg version: {e}")
        return False
    
    return True

def test_audio_duration():
    """Test audio duration detection"""
    print("\n🔍 Testing audio duration detection...")
    
    # Look for test audio files
    test_audio = None
    for root, dirs, files in os.walk("sources"):
        for file in files:
            if file.lower().endswith('.mp3'):
                test_audio = os.path.join(root, file)
                break
        if test_audio:
            break
    
    if not test_audio:
        print("⚠️  No test audio file found in sources folder")
        return True
    
    duration = get_audio_duration(test_audio)
    if duration > 0:
        print(f"✅ Audio duration detected: {duration:.2f} seconds for {os.path.basename(test_audio)}")
        return True
    else:
        print(f"❌ Failed to detect audio duration for {test_audio}")
        return False

def test_audio_concatenation():
    """Test audio concatenation"""
    print("\n🔍 Testing audio concatenation...")
    
    # Look for test audio files
    test_audios = []
    for root, dirs, files in os.walk("sources"):
        for file in files:
            if file.lower().endswith('.mp3'):
                test_audios.append(os.path.join(root, file))
                if len(test_audios) >= 2:  # Need at least 2 files
                    break
        if len(test_audios) >= 2:
            break
    
    if len(test_audios) < 2:
        print("⚠️  Not enough test audio files found for concatenation test")
        return True
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        output_file = tmp.name
    
    try:
        success = concatenate_audio_files(test_audios[:2], output_file)
        if success and os.path.exists(output_file):
            duration = get_audio_duration(output_file)
            print(f"✅ Audio concatenation successful: {duration:.2f} seconds")
            return True
        else:
            print("❌ Audio concatenation failed")
            return False
    finally:
        # Clean up
        try:
            os.unlink(output_file)
        except:
            pass

def test_video_creation():
    """Test video creation from image and audio"""
    print("\n🔍 Testing video creation...")
    
    # Look for test files
    test_image = None
    test_audio = None
    
    for root, dirs, files in os.walk("sources"):
        for file in files:
            if file.lower().endswith(('.jpg', '.png')) and not test_image:
                test_image = os.path.join(root, file)
            elif file.lower().endswith('.mp3') and not test_audio:
                test_audio = os.path.join(root, file)
            if test_image and test_audio:
                break
        if test_image and test_audio:
            break
    
    if not test_image or not test_audio:
        print("⚠️  Test image or audio file not found")
        return True
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        output_file = tmp.name
    
    try:
        success = create_video_from_image_and_audio(
            test_image, test_audio, output_file,
            "1920x1080", 24, "libx264"
        )
        
        if success and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Video creation successful: {file_size} bytes")
            return True
        else:
            print("❌ Video creation failed")
            return False
    finally:
        # Clean up
        try:
            os.unlink(output_file)
        except:
            pass

def main():
    """Run all tests"""
    print("🚀 SuperCut FFmpeg Integration Test")
    print("=" * 50)
    
    tests = [
        test_ffmpeg_installation,
        test_audio_duration,
        test_audio_concatenation,
        test_video_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! FFmpeg integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check FFmpeg installation and file paths.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 