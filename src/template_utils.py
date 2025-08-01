#!/usr/bin/env python3
"""
Template utilities for SuperCut
Provides helper functions for template operations
"""

import os
import json
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
            "buffsize": current_settings.get('buffsize', '24M')
        },
        "layer_order": current_settings.get('layer_order', []),
        "layer_settings": current_settings.get('layer_settings', {}),
        "ui_settings": current_settings.get('ui_settings', {})
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
    
    return settings

def validate_template(template_data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate template data structure"""
    required_fields = ['name', 'description', 'category', 'video_settings']
    
    for field in required_fields:
        if field not in template_data:
            return False, f"Missing required field: {field}"
    
    # Validate video settings
    video_settings = template_data.get('video_settings', {})
    required_video_fields = ['codec', 'resolution', 'fps']
    
    for field in required_video_fields:
        if field not in video_settings:
            return False, f"Missing required video setting: {field}"
    
    return True, "Template is valid"

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
        'version': template_data.get('version', '1.0'),
        'author': template_data.get('author', 'Unknown'),
        'created_date': template_data.get('created_date', ''),
        'resolution': template_data.get('video_settings', {}).get('resolution', 'Unknown'),
        'fps': template_data.get('video_settings', {}).get('fps', 'Unknown'),
        'layer_count': len(template_data.get('layer_order', [])),
        'enabled_layers': len([layer for layer in template_data.get('layer_settings', {}).values() 
                              if layer.get('enabled', False)])
    } 