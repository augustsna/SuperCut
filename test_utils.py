#!/usr/bin/env python3
"""
Unit tests for utility functions in src/utils.py
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import io

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils import (
    sanitize_filename, clean_file_path, validate_file_path, validate_numeric_input,
    validate_inputs, validate_media_files, get_memory_usage, register_for_cleanup,
    unregister_from_cleanup, force_garbage_collection, cleanup_large_objects,
    get_memory_registry_stats, create_temp_file, cleanup_temp_files,
    is_audio_file, is_image_file, is_video_file, format_time
)

class TestValidationFunctions(unittest.TestCase):
    """Test input validation and sanitization functions"""
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test basic sanitization
        self.assertEqual(sanitize_filename("test file.txt"), "test_file.txt")
        self.assertEqual(sanitize_filename("file with spaces"), "file_with_spaces")
        
        # Test special characters
        self.assertEqual(sanitize_filename("file<>:\"/\\|?*"), "file")
        self.assertEqual(sanitize_filename("file with dots..."), "file_with_dots")
        
        # Test empty and whitespace
        self.assertEqual(sanitize_filename(""), "")
        self.assertEqual(sanitize_filename("   "), "")
        self.assertEqual(sanitize_filename("  test  "), "test")
        
        # Test length limits
        long_name = "a" * 300
        sanitized = sanitize_filename(long_name)
        self.assertLessEqual(len(sanitized), 200)
    
    def test_clean_file_path(self):
        """Test file path cleaning"""
        # Test file:/// prefix removal
        self.assertEqual(clean_file_path("file:///C:/test/file.txt"), "C:/test/file.txt")
        self.assertEqual(clean_file_path("file:///test/file.txt"), "/test/file.txt")
        
        # Test normal paths
        self.assertEqual(clean_file_path("C:/test/file.txt"), "C:/test/file.txt")
        self.assertEqual(clean_file_path("/test/file.txt"), "/test/file.txt")
        
        # Test Windows paths
        self.assertEqual(clean_file_path("C:\\test\\file.txt"), "C:/test/file.txt")
    
    def test_validate_file_path(self):
        """Test file path validation"""
        # Test with non-existent file
        valid, error = validate_file_path("nonexistent.txt")
        self.assertFalse(valid)
        self.assertIn("not found", error)
        
        # Test with directory
        with tempfile.TemporaryDirectory() as temp_dir:
            valid, error = validate_file_path(temp_dir)
            self.assertFalse(valid)
            self.assertIn("is a directory", error)
        
        # Test with valid file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            valid, error = validate_file_path(temp_path)
            self.assertTrue(valid)
            self.assertEqual(error, "")
            
            # Clean up
            os.unlink(temp_path)
    
    def test_validate_numeric_input(self):
        """Test numeric input validation"""
        # Test valid integers
        valid, error, value = validate_numeric_input("123", min_val=0, max_val=1000)
        self.assertTrue(valid)
        self.assertEqual(value, 123)
        self.assertEqual(error, "")
        
        # Test valid floats
        valid, error, value = validate_numeric_input("123.45", allow_float=True)
        self.assertTrue(valid)
        self.assertEqual(value, 123.45)
        
        # Test invalid input
        valid, error, value = validate_numeric_input("abc")
        self.assertFalse(valid)
        self.assertIn("not a valid number", error)
        
        # Test bounds checking
        valid, error, value = validate_numeric_input("150", min_val=0, max_val=100)
        self.assertFalse(valid)
        self.assertIn("must be between", error)
    
    def test_validate_inputs(self):
        """Test input validation for main UI"""
        # Test valid inputs
        valid, error = validate_inputs("/valid/path", "export_name", "5")
        self.assertTrue(valid)
        self.assertEqual(error, "")
        
        # Test invalid export name
        valid, error = validate_inputs("/valid/path", "", "5")
        self.assertFalse(valid)
        self.assertIn("Export name", error)
        
        # Test invalid number
        valid, error = validate_inputs("/valid/path", "export", "abc")
        self.assertFalse(valid)
        self.assertIn("Number", error)
    
    def test_validate_media_files(self):
        """Test media files validation"""
        # Test with non-existent directory
        valid, error, mp3_files, image_files = validate_media_files("/nonexistent/path")
        self.assertFalse(valid)
        self.assertIn("not found", error)
        
        # Test with empty directory
        with tempfile.TemporaryDirectory() as temp_dir:
            valid, error, mp3_files, image_files = validate_media_files(temp_dir)
            self.assertFalse(valid)
            self.assertIn("No MP3 files found", error)

class TestFileTypeFunctions(unittest.TestCase):
    """Test file type detection functions"""
    
    def test_is_audio_file(self):
        """Test audio file detection"""
        self.assertTrue(is_audio_file("test.mp3"))
        self.assertTrue(is_audio_file("test.MP3"))
        self.assertTrue(is_audio_file("test.wav"))
        self.assertFalse(is_audio_file("test.txt"))
        self.assertFalse(is_audio_file("test.jpg"))
    
    def test_is_image_file(self):
        """Test image file detection"""
        self.assertTrue(is_image_file("test.jpg"))
        self.assertTrue(is_image_file("test.png"))
        self.assertTrue(is_image_file("test.gif"))
        self.assertFalse(is_image_file("test.txt"))
        self.assertFalse(is_image_file("test.mp3"))
    
    def test_is_video_file(self):
        """Test video file detection"""
        self.assertTrue(is_video_file("test.mp4"))
        self.assertTrue(is_video_file("test.avi"))
        self.assertTrue(is_video_file("test.mov"))
        self.assertFalse(is_video_file("test.txt"))
        self.assertFalse(is_video_file("test.jpg"))

class TestMemoryManagement(unittest.TestCase):
    """Test memory management functions"""
    
    def test_register_for_cleanup(self):
        """Test object registration for cleanup"""
        test_obj = {"test": "data"}
        name = register_for_cleanup(test_obj, "test_obj")
        self.assertEqual(name, "test_obj")
        
        # Test unregistration
        success = unregister_from_cleanup("test_obj")
        self.assertTrue(success)
        
        # Test unregistering non-existent object
        success = unregister_from_cleanup("nonexistent")
        self.assertFalse(success)
    
    def test_force_garbage_collection(self):
        """Test forced garbage collection"""
        result = force_garbage_collection()
        self.assertIsInstance(result, dict)
        self.assertIn("collected_objects", result)
    
    def test_cleanup_large_objects(self):
        """Test large object cleanup"""
        result = cleanup_large_objects()
        self.assertIsInstance(result, dict)
        self.assertIn("large_objects_cleaned", result)
    
    def test_get_memory_registry_stats(self):
        """Test memory registry statistics"""
        stats = get_memory_registry_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_objects", stats)
    
    @patch('utils.psutil')
    def test_get_memory_usage(self, mock_psutil):
        """Test memory usage monitoring"""
        # Mock psutil
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1024*1024*100, vms=1024*1024*200)
        mock_process.memory_percent.return_value = 5.0
        mock_psutil.Process.return_value = mock_process
        mock_psutil.virtual_memory.return_value = MagicMock(available=1024*1024*1000)
        
        result = get_memory_usage()
        self.assertIsInstance(result, dict)
        self.assertIn("rss_mb", result)
        self.assertIn("vms_mb", result)
        self.assertIn("percent", result)

class TestFileOperations(unittest.TestCase):
    """Test file operation functions"""
    
    def test_create_temp_file(self):
        """Test temporary file creation"""
        temp_path = create_temp_file(suffix=".txt", prefix="test_")
        self.assertTrue(os.path.exists(temp_path))
        self.assertTrue(temp_path.endswith(".txt"))
        self.assertTrue(os.path.basename(temp_path).startswith("test_"))
        
        # Clean up
        os.unlink(temp_path)
    
    def test_cleanup_temp_files(self):
        """Test temporary file cleanup"""
        # Create some temp files
        temp_files = []
        for i in range(3):
            temp_path = create_temp_file(suffix=f"_{i}.txt")
            temp_files.append(temp_path)
        
        # Verify files exist
        for temp_path in temp_files:
            self.assertTrue(os.path.exists(temp_path))
        
        # Clean up
        cleanup_temp_files()
        
        # Verify files are removed
        for temp_path in temp_files:
            self.assertFalse(os.path.exists(temp_path))

class TestUtilityFunctions(unittest.TestCase):
    """Test other utility functions"""
    
    def test_format_time(self):
        """Test time formatting"""
        self.assertEqual(format_time(0), "00:00")
        self.assertEqual(format_time(60), "01:00")
        self.assertEqual(format_time(125), "02:05")
        self.assertEqual(format_time(3661), "01:01:01")
    
    def test_get_file_extension(self):
        """Test file extension extraction"""
        from utils import get_file_extension
        self.assertEqual(get_file_extension("test.txt"), ".txt")
        self.assertEqual(get_file_extension("test.file.txt"), ".txt")
        self.assertEqual(get_file_extension("test"), "")
        self.assertEqual(get_file_extension(""), "")

if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestValidationFunctions,
        TestFileTypeFunctions,
        TestMemoryManagement,
        TestFileOperations,
        TestUtilityFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
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