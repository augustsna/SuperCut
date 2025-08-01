#!/usr/bin/env python3
"""
Unit tests for video worker functionality in src/video_worker.py
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
import subprocess

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from video_worker import VideoWorker

class TestVideoWorker(unittest.TestCase):
    """Test VideoWorker class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.media_sources = self.temp_dir
        self.export_name = "test_export"
        self.number = "1"
        
        # Create test MP3 and image files
        self.mp3_files = []
        self.image_files = []
        
        for i in range(3):
            # Create dummy MP3 file
            mp3_path = os.path.join(self.temp_dir, f"test_{i}.mp3")
            with open(mp3_path, 'w') as f:
                f.write("dummy mp3 content")
            self.mp3_files.append(mp3_path)
            
            # Create dummy image file
            img_path = os.path.join(self.temp_dir, f"test_{i}.jpg")
            with open(img_path, 'w') as f:
                f.write("dummy image content")
            self.image_files.append(img_path)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_worker_initialization(self):
        """Test VideoWorker initialization"""
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        self.assertEqual(worker.media_sources, self.media_sources)
        self.assertEqual(worker.export_name, self.export_name)
        self.assertEqual(worker.number, self.number)
        self.assertFalse(worker.is_running)
    
    @patch('video_worker.check_ffmpeg_installation')
    def test_validate_environment_success(self, mock_check_ffmpeg):
        """Test environment validation with success"""
        mock_check_ffmpeg.return_value = True
        
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        valid, error = worker.validate_environment()
        
        self.assertTrue(valid)
        self.assertEqual(error, "")
    
    @patch('video_worker.check_ffmpeg_installation')
    def test_validate_environment_ffmpeg_missing(self, mock_check_ffmpeg):
        """Test environment validation with missing FFmpeg"""
        mock_check_ffmpeg.return_value = False
        
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        valid, error = worker.validate_environment()
        
        self.assertFalse(valid)
        self.assertIn("FFmpeg", error)
    
    @patch('video_worker.os.path.exists')
    @patch('video_worker.check_ffmpeg_installation')
    def test_validate_environment_invalid_directory(self, mock_check_ffmpeg, mock_exists):
        """Test environment validation with invalid directory"""
        mock_check_ffmpeg.return_value = True
        mock_exists.return_value = False
        
        worker = VideoWorker("/invalid/path", self.export_name, self.number)
        valid, error = worker.validate_environment()
        
        self.assertFalse(valid)
        self.assertIn("not found", error)
    
    @patch('video_worker.os.access')
    @patch('video_worker.os.path.exists')
    @patch('video_worker.check_ffmpeg_installation')
    def test_validate_environment_no_write_permission(self, mock_check_ffmpeg, mock_exists, mock_access):
        """Test environment validation with no write permission"""
        mock_check_ffmpeg.return_value = True
        mock_exists.return_value = True
        mock_access.return_value = False
        
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        valid, error = worker.validate_environment()
        
        self.assertFalse(valid)
        self.assertIn("write permission", error)
    
    def test_stop_worker(self):
        """Test worker stop functionality"""
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        worker.is_running = True
        
        worker.stop()
        
        self.assertFalse(worker.is_running)
    
    @patch('video_worker.subprocess.run')
    @patch('video_worker.check_ffmpeg_installation')
    def test_process_batch_success(self, mock_check_ffmpeg, mock_subprocess):
        """Test successful batch processing"""
        mock_check_ffmpeg.return_value = True
        
        # Mock successful subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"success"
        mock_result.stderr = b""
        mock_subprocess.return_value = mock_result
        
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        # Test batch processing
        success = worker._process_batch(self.mp3_files, self.image_files, 1, 3)
        
        self.assertTrue(success)
    
    @patch('video_worker.subprocess.run')
    @patch('video_worker.check_ffmpeg_installation')
    def test_process_batch_ffmpeg_failure(self, mock_check_ffmpeg, mock_subprocess):
        """Test batch processing with FFmpeg failure"""
        mock_check_ffmpeg.return_value = True
        
        # Mock failed subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = b"FFmpeg error"
        mock_subprocess.return_value = mock_result
        
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        # Test batch processing
        success = worker._process_batch(self.mp3_files, self.image_files, 1, 3)
        
        self.assertFalse(success)
    
    @patch('video_worker.subprocess.run')
    @patch('video_worker.check_ffmpeg_installation')
    def test_process_batch_subprocess_exception(self, mock_check_ffmpeg, mock_subprocess):
        """Test batch processing with subprocess exception"""
        mock_check_ffmpeg.return_value = True
        mock_subprocess.side_effect = subprocess.TimeoutExpired("ffmpeg", 30)
        
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        # Test batch processing
        success = worker._process_batch(self.mp3_files, self.image_files, 1, 3)
        
        self.assertFalse(success)
    
    def test_cleanup_temp_audio(self):
        """Test temporary audio file cleanup"""
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        # Create a temporary audio file
        temp_audio = os.path.join(self.temp_dir, "temp_audio.mp3")
        with open(temp_audio, 'w') as f:
            f.write("temp audio content")
        
        # Test cleanup
        worker._cleanup_temp_audio(temp_audio)
        
        # Verify file is removed
        self.assertFalse(os.path.exists(temp_audio))
    
    def test_cleanup_temp_audio_nonexistent(self):
        """Test cleanup of non-existent audio file"""
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        # Test cleanup of non-existent file
        worker._cleanup_temp_audio("/nonexistent/audio.mp3")
        
        # Should not raise exception
        self.assertTrue(True)
    
    @patch('video_worker.shutil.move')
    def test_create_log_and_move_files_success(self, mock_move):
        """Test successful file moving and log creation"""
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        # Create test output file
        output_file = os.path.join(self.temp_dir, "output.mp4")
        with open(output_file, 'w') as f:
            f.write("test video content")
        
        # Test file moving
        success = worker._create_log_and_move_files(output_file, self.temp_dir)
        
        self.assertTrue(success)
        mock_move.assert_called()
    
    @patch('video_worker.shutil.move')
    def test_create_log_and_move_files_move_failure(self, mock_move):
        """Test file moving with failure"""
        mock_move.side_effect = OSError("Permission denied")
        
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        # Create test output file
        output_file = os.path.join(self.temp_dir, "output.mp4")
        with open(output_file, 'w') as f:
            f.write("test video content")
        
        # Test file moving
        success = worker._create_log_and_move_files(output_file, self.temp_dir)
        
        self.assertFalse(success)

class TestVideoWorkerIntegration(unittest.TestCase):
    """Integration tests for VideoWorker"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.media_sources = self.temp_dir
        self.export_name = "integration_test"
        self.number = "1"
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('video_worker.check_ffmpeg_installation')
    def test_worker_lifecycle(self, mock_check_ffmpeg):
        """Test complete worker lifecycle"""
        mock_check_ffmpeg.return_value = True
        
        # Create worker
        worker = VideoWorker(self.media_sources, self.export_name, self.number)
        
        # Test initialization
        self.assertFalse(worker.is_running)
        self.assertEqual(worker.media_sources, self.media_sources)
        
        # Test environment validation
        valid, error = worker.validate_environment()
        self.assertTrue(valid)
        
        # Test stop functionality
        worker.is_running = True
        worker.stop()
        self.assertFalse(worker.is_running)

if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestVideoWorker,
        TestVideoWorkerIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Video Worker Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Exit with appropriate code
    if result.failures or result.errors:
        sys.exit(1)
    else:
        sys.exit(0) 