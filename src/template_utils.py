#!/usr/bin/env python3
"""
Template utilities for SuperCut
Provides helper functions for template operations
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.config import (
    get_templates_dir, 
    save_template, 
    load_template, 
    get_available_templates,
    delete_template,
    get_template_categories
)

def sanitize_template_name(name: str) -> str:
    """Sanitize template name for filesystem use"""
    if not name:
        return "untitled_template"
    
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it's not empty after sanitization
    if not sanitized:
        return "untitled_template"
    
    # Limit length to prevent filesystem issues
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized

def get_template_by_name(template_name: str) -> Optional[Dict[str, Any]]:
    """Get template by name, handling different naming conventions"""
    # Try exact name first
    template = load_template(template_name)
    if template:
        return template
    
    # Try converting name to filename format
    filename = template_name.lower().replace(' ', '_').replace('-', '_')
    template = load_template(filename)
    if template:
        return template
    
    # Try searching through all templates
    templates = get_available_templates()
    for template_data in templates:
        if template_data.get('name', '').lower() == template_name.lower():
            return template_data
    
    return None

def get_templates_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all templates in a specific category"""
    templates = get_available_templates()
    return [t for t in templates if t.get('category', '') == category]

def create_template_from_current_settings(
    name: str,
    description: str,
    category: str,
    current_settings: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a template from current application settings"""
    template = {
        "name": name,
        "description": description,
        "category": category,
        "video_settings": {
            "codec": current_settings.get('codec', 'h264_nvenc'),
            "resolution": current_settings.get('resolution', '1920x1080'),
            "fps": current_settings.get('fps', 24),
            "preset": current_settings.get('preset', 'slow'),
            "audio_bitrate": current_settings.get('audio_bitrate', '384k'),
            "video_bitrate": current_settings.get('video_bitrate', '12M'),
            "maxrate": current_settings.get('maxrate', '16M'),
            "bufsize": current_settings.get('bufsize', '24M')
        },
        "layer_order": current_settings.get('layer_order', []),
        "layer_settings": current_settings.get('layer_settings', {}),
        "ui_settings": current_settings.get('ui_settings', {}),
        "checkbox_labels": current_settings.get('checkbox_labels', {}),
        "overlay1_2_effect_settings": current_settings.get('overlay1_2_effect_settings', {}),
        "overlay4_5_effect_settings": current_settings.get('overlay4_5_effect_settings', {}),
        "overlay6_7_effect_settings": current_settings.get('overlay6_7_effect_settings', {}),
        "overlay3_soundwave_effect_settings": current_settings.get('overlay3_soundwave_effect_settings', {})
    }
    return template

def apply_template_to_settings(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert template data to application settings format"""
    settings = {}
    
    # Apply video settings
    if 'video_settings' in template_data:
        settings.update(template_data['video_settings'])
    
    # Apply layer order
    if 'layer_order' in template_data:
        settings['layer_order'] = template_data['layer_order']
    
    # Apply layer settings
    if 'layer_settings' in template_data:
        settings['layer_settings'] = template_data['layer_settings']
    
    # Apply UI settings
    if 'ui_settings' in template_data:
        settings['ui_settings'] = template_data['ui_settings']
    
    # Apply checkbox labels
    if 'checkbox_labels' in template_data:
        settings['checkbox_labels'] = template_data['checkbox_labels']
    
    # Apply overlay1_2_effect_settings
    if 'overlay1_2_effect_settings' in template_data:
        settings['overlay1_2_effect_settings'] = template_data['overlay1_2_effect_settings']
    
    # Apply overlay4_5_effect_settings
    if 'overlay4_5_effect_settings' in template_data:
        settings['overlay4_5_effect_settings'] = template_data['overlay4_5_effect_settings']
    
    # Apply overlay6_7_effect_settings
    if 'overlay6_7_effect_settings' in template_data:
        settings['overlay6_7_effect_settings'] = template_data['overlay6_7_effect_settings']
    
    # Apply overlay3_soundwave_effect_settings
    if 'overlay3_soundwave_effect_settings' in template_data:
        settings['overlay3_soundwave_effect_settings'] = template_data['overlay3_soundwave_effect_settings']
    
    return settings

def validate_template(template_data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate template data structure"""
    if not isinstance(template_data, dict):
        return False, "Template data must be a dictionary"
    
    # Validate name (required)
    name = template_data.get('name', '')
    if not name or not isinstance(name, str):
        return False, "Template name must be a non-empty string"
    if len(name) > 100:
        return False, "Template name must be 100 characters or less"
    
    # Validate description (optional)
    description = template_data.get('description', '')
    if description and not isinstance(description, str):
        return False, "Template description must be a string"
    if len(description) > 500:
        return False, "Template description must be 500 characters or less"
    
    # Validate video settings (required)
    video_settings = template_data.get('video_settings', {})
    if not isinstance(video_settings, dict):
        return False, "Video settings must be a dictionary"
    
    # Validate required video fields
    required_video_fields = ['codec', 'resolution', 'fps']
    for field in required_video_fields:
        if field not in video_settings:
            return False, f"Missing required video setting: {field}"
    
    # Validate codec
    codec = video_settings.get('codec', '')
    if not codec or not isinstance(codec, str):
        return False, "Video codec must be a non-empty string"
    
    # Validate resolution
    resolution = video_settings.get('resolution', '')
    if not resolution or not isinstance(resolution, str):
        return False, "Video resolution must be a non-empty string"
    
    # Validate fps
    fps = video_settings.get('fps', '')
    if not fps or not isinstance(fps, (int, str)):
        return False, "Video fps must be a non-empty string or integer"
    
    # Validate optional fields if present
    optional_fields = ['layer_order', 'layer_settings', 'ui_settings', 'checkbox_labels', 'tags', 'rating', 'usage_count']
    for field in optional_fields:
        if field in template_data:
            if field == 'layer_order' and not isinstance(template_data[field], list):
                return False, f"Field '{field}' must be a list"
            elif field == 'tags' and not isinstance(template_data[field], list):
                return False, f"Field '{field}' must be a list"
            elif field in ['rating', 'usage_count'] and not isinstance(template_data[field], (int, float)):
                return False, f"Field '{field}' must be a number"
            elif field not in ['layer_order', 'tags', 'rating', 'usage_count'] and not isinstance(template_data[field], dict):
                return False, f"Field '{field}' must be a dictionary"
    
    # Validate layer_order if present
    if 'layer_order' in template_data:
        layer_order = template_data['layer_order']
        for layer in layer_order:
            if not isinstance(layer, str):
                return False, "Layer order items must be strings"
    
    # Validate layer_settings if present
    if 'layer_settings' in template_data:
        layer_settings = template_data['layer_settings']
        for layer_name, settings in layer_settings.items():
            if not isinstance(settings, dict):
                return False, f"Layer settings for '{layer_name}' must be a dictionary"
            # Validate boolean fields in layer settings
            for key, value in settings.items():
                if key == 'enabled' and not isinstance(value, bool):
                    return False, f"Layer setting 'enabled' must be a boolean"
    
    return True, ""

def export_template(template_name: str, export_path: str) -> bool:
    """Export a template to a file"""
    template_data = get_template_by_name(template_name)
    if not template_data:
        return False
    
    try:
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error exporting template: {e}")
        return False

def import_template(import_path: str) -> tuple[bool, str]:
    """Import a template from a file"""
    try:
        with open(import_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        # Validate template
        is_valid, message = validate_template(template_data)
        if not is_valid:
            return False, message
        
        # Save template
        template_name = template_data['name'].lower().replace(' ', '_')
        if save_template(template_data, template_name):
            return True, f"Template '{template_data['name']}' imported successfully"
        else:
            return False, "Failed to save imported template"
    
    except Exception as e:
        return False, f"Error importing template: {e}"

def get_template_preview_info(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get preview information for a template"""
    return {
        'name': template_data.get('name', 'Unknown'),
        'description': template_data.get('description', 'No description'),
        'category': template_data.get('category', 'Unknown'),
        'resolution': template_data.get('video_settings', {}).get('resolution', 'Unknown'),
        'fps': template_data.get('video_settings', {}).get('fps', 'Unknown'),
        'layer_count': len(template_data.get('layer_order', [])),
        'enabled_layers': len([layer for layer in template_data.get('layer_settings', {}).values() 
                              if layer.get('enabled', False)])
    } 