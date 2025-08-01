#!/usr/bin/env python3
"""
Unit tests for template utilities in src/template_utils.py
"""

import unittest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from template_utils import sanitize_template_name, validate_template

class TestTemplateSanitization(unittest.TestCase):
    """Test template name sanitization"""
    
    def test_sanitize_template_name_basic(self):
        """Test basic template name sanitization"""
        # Test normal names
        self.assertEqual(sanitize_template_name("My Template"), "My_Template")
        self.assertEqual(sanitize_template_name("template-1"), "template-1")
        self.assertEqual(sanitize_template_name("template_1"), "template_1")
        
        # Test special characters
        self.assertEqual(sanitize_template_name("template<>:\"/\\|?*"), "template")
        self.assertEqual(sanitize_template_name("template with dots..."), "template_with_dots")
        
        # Test empty and whitespace
        self.assertEqual(sanitize_template_name(""), "")
        self.assertEqual(sanitize_template_name("   "), "")
        self.assertEqual(sanitize_template_name("  template  "), "template")
        
        # Test length limits
        long_name = "a" * 150
        sanitized = sanitize_template_name(long_name)
        self.assertLessEqual(len(sanitized), 100)
    
    def test_sanitize_template_name_edge_cases(self):
        """Test edge cases for template name sanitization"""
        # Test numbers and mixed characters
        self.assertEqual(sanitize_template_name("Template 123"), "Template_123")
        self.assertEqual(sanitize_template_name("123 Template"), "123_Template")
        
        # Test consecutive special characters
        self.assertEqual(sanitize_template_name("template..."), "template")
        self.assertEqual(sanitize_template_name("template___"), "template___")
        
        # Test leading/trailing special characters
        self.assertEqual(sanitize_template_name("...template..."), "template")

class TestTemplateValidation(unittest.TestCase):
    """Test template validation"""
    
    def test_validate_template_valid(self):
        """Test validation of valid template"""
        valid_template = {
            "name": "Test Template",
            "description": "A test template",
            "video_settings": {
                "resolution": "1920x1080",
                "fps": 24,
                "codec": "h264"
            },
            "layer_settings": {
                "background": {"enabled": True},
                "overlay1": {"enabled": False}
            },
            "tags": ["test", "sample"],
            "rating": 5,
            "usage_count": 0
        }
        
        valid, error = validate_template(valid_template)
        self.assertTrue(valid)
        self.assertEqual(error, "")
    
    def test_validate_template_missing_required_fields(self):
        """Test validation with missing required fields"""
        invalid_template = {
            "description": "A test template",
            "video_settings": {
                "resolution": "1920x1080"
            }
        }
        
        valid, error = validate_template(invalid_template)
        self.assertFalse(valid)
        self.assertIn("name", error)
    
    def test_validate_template_invalid_data_types(self):
        """Test validation with invalid data types"""
        invalid_template = {
            "name": 123,  # Should be string
            "description": "A test template",
            "video_settings": {
                "resolution": "1920x1080",
                "fps": "24",  # Should be int
                "codec": "h264"
            }
        }
        
        valid, error = validate_template(invalid_template)
        self.assertFalse(valid)
        self.assertIn("name", error)
    
    def test_validate_template_invalid_string_lengths(self):
        """Test validation with invalid string lengths"""
        # Test name too long
        invalid_template = {
            "name": "a" * 200,  # Too long
            "description": "A test template",
            "video_settings": {
                "resolution": "1920x1080",
                "fps": 24,
                "codec": "h264"
            }
        }
        
        valid, error = validate_template(invalid_template)
        self.assertFalse(valid)
        self.assertIn("name", error)
    
    def test_validate_template_invalid_nested_structure(self):
        """Test validation with invalid nested structure"""
        invalid_template = {
            "name": "Test Template",
            "description": "A test template",
            "video_settings": "invalid",  # Should be dict
            "layer_settings": {
                "background": {"enabled": True}
            }
        }
        
        valid, error = validate_template(invalid_template)
        self.assertFalse(valid)
        self.assertIn("video_settings", error)
    
    def test_validate_template_invalid_boolean_values(self):
        """Test validation with invalid boolean values"""
        invalid_template = {
            "name": "Test Template",
            "description": "A test template",
            "video_settings": {
                "resolution": "1920x1080",
                "fps": 24,
                "codec": "h264"
            },
            "layer_settings": {
                "background": {"enabled": "true"}  # Should be boolean
            }
        }
        
        valid, error = validate_template(invalid_template)
        self.assertFalse(valid)
        self.assertIn("enabled", error)
    
    def test_validate_template_invalid_numeric_values(self):
        """Test validation with invalid numeric values"""
        invalid_template = {
            "name": "Test Template",
            "description": "A test template",
            "video_settings": {
                "resolution": "1920x1080",
                "fps": -1,  # Invalid fps
                "codec": "h264"
            }
        }
        
        valid, error = validate_template(invalid_template)
        self.assertFalse(valid)
        self.assertIn("fps", error)
    
    def test_validate_template_invalid_list_values(self):
        """Test validation with invalid list values"""
        invalid_template = {
            "name": "Test Template",
            "description": "A test template",
            "video_settings": {
                "resolution": "1920x1080",
                "fps": 24,
                "codec": "h264"
            },
            "tags": "not_a_list"  # Should be list
        }
        
        valid, error = validate_template(invalid_template)
        self.assertFalse(valid)
        self.assertIn("tags", error)

class TestTemplateValidationEdgeCases(unittest.TestCase):
    """Test edge cases for template validation"""
    
    def test_validate_template_empty_dict(self):
        """Test validation of empty template"""
        valid, error = validate_template({})
        self.assertFalse(valid)
        self.assertIn("name", error)
    
    def test_validate_template_none(self):
        """Test validation of None template"""
        valid, error = validate_template(None)
        self.assertFalse(valid)
        self.assertIn("not a dictionary", error)
    
    def test_validate_template_deep_nesting(self):
        """Test validation of deeply nested template"""
        deep_template = {
            "name": "Deep Template",
            "description": "A deeply nested template",
            "video_settings": {
                "resolution": "1920x1080",
                "fps": 24,
                "codec": "h264",
                "advanced": {
                    "preset": "slow",
                    "tune": "film",
                    "profile": {
                        "level": "4.1",
                        "high_tier": True
                    }
                }
            },
            "layer_settings": {
                "background": {
                    "enabled": True,
                    "settings": {
                        "scale": 100,
                        "position": "center"
                    }
                }
            }
        }
        
        valid, error = validate_template(deep_template)
        self.assertTrue(valid)
        self.assertEqual(error, "")
    
    def test_validate_template_mixed_data_types(self):
        """Test validation with mixed valid and invalid data types"""
        mixed_template = {
            "name": "Mixed Template",
            "description": "A template with mixed data types",
            "video_settings": {
                "resolution": "1920x1080",
                "fps": 24,
                "codec": "h264"
            },
            "layer_settings": {
                "background": {"enabled": True},
                "overlay1": {"enabled": "invalid"}  # Invalid boolean
            },
            "tags": ["valid", "tags"],
            "rating": 5,
            "usage_count": 0
        }
        
        valid, error = validate_template(mixed_template)
        self.assertFalse(valid)
        self.assertIn("enabled", error)

if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTemplateSanitization,
        TestTemplateValidation,
        TestTemplateValidationEdgeCases
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Template Utils Test Summary:")
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