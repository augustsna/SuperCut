#!/usr/bin/env python3
"""
Test script for enhanced template manager with search, filtering, and favorites
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from template_manager_dialog import TemplateManagerDialog

def test_enhanced_template_manager():
    """Test the enhanced template manager with new features"""
    print("🧪 Testing Enhanced Template Manager...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Sample current settings for testing
    current_settings = {
        'codec': 'h264_nvenc',
        'resolution': '1920x1080',
        'fps': 24,
        'preset': 'slow',
        'audio_bitrate': '384k',
        'video_bitrate': '12M',
        'maxrate': '16M',
        'bufsize': '24M',
        'layer_order': ['background', 'overlay1', 'song_titles'],
        'layer_settings': {
            'background': {'enabled': True, 'scale_percent': 103},
            'overlay1': {'enabled': False, 'size_percent': 100},
            'song_titles': {'enabled': True, 'font_size': 32}
        },
        'ui_settings': {
            'show_intro_settings': False,
            'show_overlay1_2_settings': True,
            'show_overlay3_titles_soundwave_settings': True
        }
    }
    
    # Create and show the dialog
    dialog = TemplateManagerDialog(current_settings=current_settings)
    
    # Connect template applied signal
    def on_template_applied(template_data):
        print(f"✅ Template applied: {template_data.get('name', 'Unknown')}")
        print(f"   Resolution: {template_data.get('video_settings', {}).get('resolution', 'Unknown')}")
        print(f"   FPS: {template_data.get('video_settings', {}).get('fps', 'Unknown')}")
        print(f"   Rating: {template_data.get('rating', 'No rating')}")
        print(f"   Usage: {template_data.get('usage_count', 0)} times")
        print(f"   Tags: {', '.join(template_data.get('tags', []))}")
    
    dialog.template_applied.connect(on_template_applied)
    
    print("📋 Opening Enhanced Template Manager...")
    print("   - Test search functionality (try 'music', 'gaming', 'modern')")
    print("   - Test resolution filter (1080p, 720p, 4K)")
    print("   - Test FPS filter (24, 30, 60)")
    print("   - Test favorites filter (⭐ Favorites button)")
    print("   - Test category filter (Music, Gaming, etc.)")
    print("   - Select a template to see enhanced details")
    print("   - Test favorite/unfavorite functionality")
    print("   - Test template application")
    print("   - Close dialog when done testing")
    
    # Show the dialog
    result = dialog.exec()
    
    if result == dialog.DialogCode.Accepted:
        print("✅ Dialog closed normally")
    else:
        print("❌ Dialog closed with cancel")
    
    print("\n🎉 Enhanced Template Manager test completed!")

if __name__ == "__main__":
    test_enhanced_template_manager() 