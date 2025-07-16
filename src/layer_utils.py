# This file uses PyQt6
"""
Layer Utilities for SuperCut
Handles layer order translation and processing without modifying existing code.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def get_ordered_layers(layers: List[Dict[str, Any]], layer_order: List[int]) -> List[Dict[str, Any]]:
    """
    Convert layer_order indices to actual layer sequence.
    
    Args:
        layers: List of layer dictionaries
        layer_order: List of indices representing the desired order
        
    Returns:
        List of layers in the specified order
    """
    try:
        if not layer_order or not layers:
            return layers  # Return original if no order specified
            
        ordered_layers = []
        for idx in layer_order:
            if 0 <= idx < len(layers):
                ordered_layers.append(layers[idx])
            else:
                logger.warning(f"Layer index {idx} out of range, skipping")
                
        return ordered_layers
    except Exception as e:
        logger.error(f"Error in get_ordered_layers: {e}")
        return layers  # Fallback to original order

def collect_active_layers_from_ui(ui_instance) -> List[Dict[str, Any]]:
    """
    Collect all layers from the UI instance (both enabled and disabled).
    
    Args:
        ui_instance: The main UI instance (SuperCutUI)
        
    Returns:
        List of layer dictionaries with layer information
    """
    layers = []
    
    try:
        print("=== Collecting layers from UI ===")
        
        # Background Layer (always enabled, checkbox is for settings only)
        if hasattr(ui_instance, 'bg_layer_checkbox'):
            bg_enabled = ui_instance.bg_layer_checkbox.isChecked()
            print(f"Background Layer checkbox found: {bg_enabled}")
            layers.append({
                'id': 'bg_layer',
                'name': 'Background Layer',
                'enabled': True,  # Always enabled, checkbox is for settings only
                'type': 'background',
                'index': 0
            })
        else:
            print("Background Layer checkbox not found")
        
        # Intro Layer
        if hasattr(ui_instance, 'intro_checkbox'):
            intro_enabled = ui_instance.intro_checkbox.isChecked()
            print(f"Intro Layer checkbox found: {intro_enabled}")
            layers.append({
                'id': 'intro',
                'name': 'Intro Layer',
                'enabled': intro_enabled,
                'type': 'overlay',
                'index': 1
            })
        else:
            print("Intro Layer checkbox not found")
        
        # Overlay 1
        if hasattr(ui_instance, 'overlay_checkbox'):
            overlay1_enabled = ui_instance.overlay_checkbox.isChecked()
            print(f"Overlay 1 checkbox found: {overlay1_enabled}")
            layers.append({
                'id': 'overlay1',
                'name': 'Overlay 1',
                'enabled': overlay1_enabled,
                'type': 'overlay',
                'index': 2
            })
        else:
            print("Overlay 1 checkbox not found")
        
        # Overlay 2
        if hasattr(ui_instance, 'overlay2_checkbox'):
            overlay2_enabled = ui_instance.overlay2_checkbox.isChecked()
            print(f"Overlay 2 checkbox found: {overlay2_enabled}")
            layers.append({
                'id': 'overlay2',
                'name': 'Overlay 2',
                'enabled': overlay2_enabled,
                'type': 'overlay',
                'index': 3
            })
        else:
            print("Overlay 2 checkbox not found")
        
        # Overlay 3
        if hasattr(ui_instance, 'overlay3_checkbox'):
            overlay3_enabled = ui_instance.overlay3_checkbox.isChecked()
            print(f"Overlay 3 checkbox found: {overlay3_enabled}")
            layers.append({
                'id': 'overlay3',
                'name': 'Overlay 3',
                'enabled': overlay3_enabled,
                'type': 'overlay',
                'index': 4
            })
        else:
            print("Overlay 3 checkbox not found")
        
        # Overlay 4
        if hasattr(ui_instance, 'overlay4_checkbox'):
            overlay4_enabled = ui_instance.overlay4_checkbox.isChecked()
            print(f"Overlay 4 checkbox found: {overlay4_enabled}")
            layers.append({
                'id': 'overlay4',
                'name': 'Overlay 4',
                'enabled': overlay4_enabled,
                'type': 'overlay',
                'index': 5
            })
        else:
            print("Overlay 4 checkbox not found")
        
        # Overlay 5
        if hasattr(ui_instance, 'overlay5_checkbox'):
            overlay5_enabled = ui_instance.overlay5_checkbox.isChecked()
            print(f"Overlay 5 checkbox found: {overlay5_enabled}")
            layers.append({
                'id': 'overlay5',
                'name': 'Overlay 5',
                'enabled': overlay5_enabled,
                'type': 'overlay',
                'index': 6
            })
        else:
            print("Overlay 5 checkbox not found")
        
        # Overlay 6
        if hasattr(ui_instance, 'overlay6_checkbox'):
            overlay6_enabled = ui_instance.overlay6_checkbox.isChecked()
            print(f"Overlay 6 checkbox found: {overlay6_enabled}")
            layers.append({
                'id': 'overlay6',
                'name': 'Overlay 6',
                'enabled': overlay6_enabled,
                'type': 'overlay',
                'index': 7
            })
        else:
            print("Overlay 6 checkbox not found")
        
        # Overlay 7
        if hasattr(ui_instance, 'overlay7_checkbox'):
            overlay7_enabled = ui_instance.overlay7_checkbox.isChecked()
            print(f"Overlay 7 checkbox found: {overlay7_enabled}")
            layers.append({
                'id': 'overlay7',
                'name': 'Overlay 7',
                'enabled': overlay7_enabled,
                'type': 'overlay',
                'index': 8
            })
        else:
            print("Overlay 7 checkbox not found")
        
        # Overlay 8
        if hasattr(ui_instance, 'overlay8_checkbox'):
            overlay8_enabled = ui_instance.overlay8_checkbox.isChecked()
            print(f"Overlay 8 checkbox found: {overlay8_enabled}")
            layers.append({
                'id': 'overlay8',
                'name': 'Overlay 8',
                'enabled': overlay8_enabled,
                'type': 'overlay',
                'index': 9
            })
        else:
            print("Overlay 8 checkbox not found")
        
        # Overlay 9
        if hasattr(ui_instance, 'overlay9_checkbox'):
            overlay9_enabled = ui_instance.overlay9_checkbox.isChecked()
            print(f"Overlay 9 checkbox found: {overlay9_enabled}")
            layers.append({
                'id': 'overlay9',
                'name': 'Overlay 9',
                'enabled': overlay9_enabled,
                'type': 'overlay',
                'index': 10
            })
        else:
            print("Overlay 9 checkbox not found")
        
        # Overlay 10
        if hasattr(ui_instance, 'overlay10_checkbox'):
            overlay10_enabled = ui_instance.overlay10_checkbox.isChecked()
            print(f"Overlay 10 checkbox found: {overlay10_enabled}")
            layers.append({
                'id': 'overlay10',
                'name': 'Overlay 10',
                'enabled': overlay10_enabled,
                'type': 'overlay',
                'index': 11
            })
        else:
            print("Overlay 10 checkbox not found")
        
        # Frame Box
        if hasattr(ui_instance, 'frame_box_checkbox'):
            frame_box_enabled = ui_instance.frame_box_checkbox.isChecked()
            print(f"Frame Box checkbox found: {frame_box_enabled}")
            layers.append({
                'id': 'frame_box',
                'name': 'Frame Box',
                'enabled': frame_box_enabled,
                'type': 'frame',
                'index': 12
            })
        else:
            print("Frame Box checkbox not found")
        
        # Frame MP3 Cover
        if hasattr(ui_instance, 'frame_mp3cover_checkbox'):
            frame_mp3cover_enabled = ui_instance.frame_mp3cover_checkbox.isChecked()
            print(f"Frame MP3 Cover checkbox found: {frame_mp3cover_enabled}")
            layers.append({
                'id': 'frame_mp3cover',
                'name': 'MP3 Cover Frame',
                'enabled': frame_mp3cover_enabled,
                'type': 'frame',
                'index': 13
            })
        else:
            print("Frame MP3 Cover checkbox not found")
        
        # MP3 Cover Overlay
        if hasattr(ui_instance, 'mp3_cover_overlay_checkbox'):
            mp3_cover_enabled = ui_instance.mp3_cover_overlay_checkbox.isChecked()
            print(f"MP3 Cover Overlay checkbox found: {mp3_cover_enabled}")
            layers.append({
                'id': 'mp3_cover_overlay',
                'name': 'MP3 Cover Overlay',
                'enabled': mp3_cover_enabled,
                'type': 'overlay',
                'index': 14
            })
        else:
            print("MP3 Cover Overlay checkbox not found")
        
        # Soundwave Overlay
        if hasattr(ui_instance, 'soundwave_checkbox'):
            soundwave_enabled = ui_instance.soundwave_checkbox.isChecked()
            print(f"Soundwave checkbox found: {soundwave_enabled}")
            layers.append({
                'id': 'soundwave',
                'name': 'Soundwave Generator',
                'enabled': soundwave_enabled,
                'type': 'overlay',
                'index': 15
            })
        else:
            print("Soundwave checkbox not found")
        
        # Song Title Overlay
        if hasattr(ui_instance, 'song_title_checkbox'):
            song_title_enabled = ui_instance.song_title_checkbox.isChecked()
            print(f"Song Title checkbox found: {song_title_enabled}")
            layers.append({
                'id': 'song_title',
                'name': 'Song Title Overlay',
                'enabled': song_title_enabled,
                'type': 'overlay',
                'index': 16
            })
        else:
            print("Song Title checkbox not found")
            
        print(f"=== Total layers collected: {len(layers)} ===")
            
    except Exception as e:
        logger.error(f"Error collecting layers from UI: {e}")
        print(f"Error collecting layers: {e}")
        return []
    
    return layers

def apply_layer_order_to_processing(ui_instance, layer_order: List[int]) -> Dict[str, Any]:
    """
    Apply layer order to video processing parameters.
    This function acts as a bridge between the UI and existing processing code.
    
    Args:
        ui_instance: The main UI instance
        layer_order: List of layer indices in desired order
        
    Returns:
        Dictionary with processing parameters in the correct order
    """
    try:
        # Get all active layers
        active_layers = collect_active_layers_from_ui(ui_instance)
        
        # If no custom order or no layers, return original processing
        if not layer_order or not active_layers:
            return {}
        
        # Create a mapping of layer IDs to their new positions
        layer_id_to_position = {}
        for new_pos, layer_idx in enumerate(layer_order):
            if layer_idx < len(active_layers):
                layer_id = active_layers[layer_idx]['id']
                layer_id_to_position[layer_id] = new_pos
        
        # Return the order mapping for processing
        return {
            'layer_order': layer_order,
            'layer_mapping': layer_id_to_position,
            'active_layers': active_layers
        }
        
    except Exception as e:
        logger.error(f"Error applying layer order: {e}")
        return {}

def validate_layer_order(layer_order: List[int], max_layers: int) -> bool:
    """
    Validate that the layer order is valid.
    
    Args:
        layer_order: List of layer indices
        max_layers: Maximum number of layers
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not layer_order:
            return True
            
        # Check for duplicate indices
        if len(set(layer_order)) != len(layer_order):
            return False
            
        # Check for out-of-range indices
        for idx in layer_order:
            if idx < 0 or idx >= max_layers:
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error validating layer order: {e}")
        return False 