#!/usr/bin/env python3
"""
Unit tests for main UI functionality in src/main_ui.py
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import after setting up the path
from main_ui import SuperCutUI

class TestMainUI(unittest.TestCase):
    """Test main UI functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests"""
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('main_ui.QIcon')
    @patch('main_ui.QPixmap')
    def test_ui_initialization(self, mock_pixmap, mock_icon):
        """Test UI initialization"""
        # Mock icon loading
        mock_pixmap.return_value = MagicMock()
        mock_icon.return_value = MagicMock()
        
        # Create UI instance
        ui = SuperCutUI()
        
        # Test basic initialization
        self.assertIsNotNone(ui)
        self.assertFalse(ui.worker_thread)
        self.assertFalse(ui.worker)
        self.assertFalse(ui.dry_run_thread)
        self.assertFalse(ui.dry_run_worker)
    
    def test_ui_cleanup_methods(self):
        """Test UI cleanup methods"""
        ui = SuperCutUI()
        
        # Test cleanup methods exist and don't raise exceptions
        try:
            ui.cleanup_worker_and_thread()
            ui.cleanup_dry_run_thread()
            ui.disconnect_all_signals()
            ui.cleanup_all_resources()
        except Exception as e:
            self.fail(f"Cleanup methods should not raise exceptions: {e}")
    
    @patch('main_ui.QThread')
    def test_thread_cleanup(self, mock_qthread):
        """Test thread cleanup functionality"""
        ui = SuperCutUI()
        
        # Mock thread and worker
        mock_thread = MagicMock()
        mock_worker = MagicMock()
        ui.worker_thread = mock_thread
        ui.worker = mock_worker
        
        # Test cleanup
        ui.cleanup_worker_and_thread()
        
        # Verify cleanup calls
        mock_worker.stop.assert_called_once()
        mock_thread.quit.assert_called_once()
        mock_thread.wait.assert_called_once()
        mock_thread.deleteLater.assert_called_once()
    
    def test_safe_ui_update(self):
        """Test safe UI update functionality"""
        ui = SuperCutUI()
        
        # Test that safe UI update doesn't raise exceptions
        try:
            ui._safe_ui_update(lambda: None)
        except Exception as e:
            self.fail(f"Safe UI update should not raise exceptions: {e}")
    
    def test_memory_management_integration(self):
        """Test memory management integration"""
        ui = SuperCutUI()
        
        # Test memory monitoring methods exist
        self.assertTrue(hasattr(ui, '_monitor_memory_usage'))
        self.assertTrue(hasattr(ui, '_cleanup_memory'))
        
        # Test memory monitoring doesn't raise exceptions
        try:
            ui._monitor_memory_usage()
            ui._cleanup_memory()
        except Exception as e:
            self.fail(f"Memory management methods should not raise exceptions: {e}")
    
    def test_input_validation_integration(self):
        """Test input validation integration"""
        ui = SuperCutUI()
        
        # Test validation methods exist
        self.assertTrue(hasattr(ui, '_validate_numeric_inputs'))
        
        # Test validation doesn't raise exceptions
        try:
            ui._validate_numeric_inputs()
        except Exception as e:
            self.fail(f"Input validation should not raise exceptions: {e}")

class TestMainUISignals(unittest.TestCase):
    """Test UI signal handling"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests"""
        cls.app = QApplication(sys.argv)
    
    def test_signal_connections(self):
        """Test signal connection functionality"""
        ui = SuperCutUI()
        
        # Test that signal disconnection doesn't raise exceptions
        try:
            ui.disconnect_all_signals()
        except Exception as e:
            self.fail(f"Signal disconnection should not raise exceptions: {e}")
    
    def test_worker_signal_handling(self):
        """Test worker signal handling"""
        ui = SuperCutUI()
        
        # Test worker signal methods exist
        self.assertTrue(hasattr(ui, 'on_worker_finished'))
        self.assertTrue(hasattr(ui, 'on_worker_error'))
        self.assertTrue(hasattr(ui, 'on_worker_progress'))
        
        # Test signal handlers don't raise exceptions
        try:
            ui.on_worker_finished()
            ui.on_worker_error("test error")
            ui.on_worker_progress(50)
        except Exception as e:
            self.fail(f"Worker signal handlers should not raise exceptions: {e}")

class TestMainUIValidation(unittest.TestCase):
    """Test UI validation methods"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests"""
        cls.app = QApplication(sys.argv)
    
    def test_file_validation_integration(self):
        """Test file validation integration"""
        ui = SuperCutUI()
        
        # Test validation methods exist
        self.assertTrue(hasattr(ui, 'validate_file_path'))
        
        # Test validation with valid path
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            try:
                valid, error = ui.validate_file_path(temp_path)
                self.assertTrue(valid)
            finally:
                os.unlink(temp_path)
    
    def test_numeric_validation_integration(self):
        """Test numeric validation integration"""
        ui = SuperCutUI()
        
        # Test validation methods exist
        self.assertTrue(hasattr(ui, 'validate_numeric_input'))
        
        # Test validation with valid input
        try:
            valid, error, value = ui.validate_numeric_input("123")
            self.assertTrue(valid)
            self.assertEqual(value, 123)
        except Exception as e:
            self.fail(f"Numeric validation should not raise exceptions: {e}")

if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestMainUI,
        TestMainUISignals,
        TestMainUIValidation
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Main UI Test Summary:")
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