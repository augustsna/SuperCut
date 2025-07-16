# This file uses PyQt6
"""
Layer Processing Wrapper for SuperCut
Wraps existing video processing to apply custom layer ordering.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def create_ordered_overlay_params(params: Dict[str, Any], layer_order: List[int], active_layers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a new params dictionary with overlays reordered based on layer_order.
    
    This function doesn't modify the original processing logic, it just reorders
    the parameters to achieve the desired layer stacking order.
    
    Args:
        params: Original parameters dictionary
        layer_order: List of indices representing desired order
        active_layers: List of active layer information
        
    Returns:
        New params dictionary with reordered overlays
    """
    try:
        # If no custom order or no active layers, return original params
        if not layer_order or not active_layers:
            return params
            
        # Check if any layers are actually enabled
        enabled_layers = [layer for layer in active_layers if layer.get('enabled', False)]
        if not enabled_layers:
            # No layers are enabled, return original params without processing
            return params
            
        # Create a copy of params to avoid modifying original
        new_params = params.copy()
        
        # Create mapping of layer IDs to their parameters
        layer_params = {}
        
        # Extract parameters for each layer type
        for layer in active_layers:
            layer_id = layer['id']
            
            if layer_id == 'overlay1':
                layer_params[layer_id] = {
                    'use': params.get('use_overlay', False),
                    'path': params.get('overlay1_path', ''),
                    'size_percent': params.get('overlay1_size_percent', 100),
                    'x_percent': params.get('overlay1_x_percent', 0),
                    'y_percent': params.get('overlay1_y_percent', 0),
                    'start_at': params.get('overlay1_start_at', 0),
                    'effect': params.get('overlay1_2_effect', 'fadein'),
                    'duration': params.get('overlay1_2_duration', 6),
                    'duration_full': params.get('overlay1_2_duration_full_checkbox_checked', False)
                }
            elif layer_id == 'overlay2':
                layer_params[layer_id] = {
                    'use': params.get('use_overlay2', False),
                    'path': params.get('overlay2_path', ''),
                    'size_percent': params.get('overlay2_size_percent', 10),
                    'x_percent': params.get('overlay2_x_percent', 75),
                    'y_percent': params.get('overlay2_y_percent', 0),
                    'start_at': params.get('overlay2_start_at', 0),
                    'effect': params.get('overlay1_2_effect', 'fadein'),
                    'duration': params.get('overlay1_2_duration', 6),
                    'duration_full': params.get('overlay1_2_duration_full_checkbox_checked', False)
                }
            elif layer_id == 'overlay3':
                layer_params[layer_id] = {
                    'use': params.get('use_overlay3', False),
                    'path': params.get('overlay3_path', ''),
                    'size_percent': params.get('overlay3_size_percent', 10),
                    'x_percent': params.get('overlay3_x_percent', 75),
                    'y_percent': params.get('overlay3_y_percent', 0)
                }
            elif layer_id == 'intro':
                layer_params[layer_id] = {
                    'use': params.get('use_intro', False),
                    'path': params.get('intro_path', ''),
                    'size_percent': params.get('intro_size_percent', 10),
                    'x_percent': params.get('intro_x_percent', 50),
                    'y_percent': params.get('intro_y_percent', 50)
                }
            # Continue for other overlays...
            
        # Store the layer order in params for processing (inverted so first layer is at bottom)
        new_params['layer_render_order'] = layer_order[::-1]  # Reverse the order
        new_params['layer_params'] = layer_params
        new_params['active_layers'] = active_layers
        
        return new_params
        
    except Exception as e:
        logger.error(f"Error creating ordered overlay params: {e}")
        return params  # Return original on error

def should_use_layer_ordering(params: Dict[str, Any]) -> bool:
    """
    Check if layer ordering should be applied.
    
    Args:
        params: Parameters dictionary
        
    Returns:
        True if layer ordering info is present and should be used
    """
    return 'layer_render_order' in params and bool(params.get('layer_render_order'))

def get_layer_position(layer_id: str, params: Dict[str, Any]) -> int:
    """
    Get the render position for a specific layer.
    
    Args:
        layer_id: The layer identifier
        params: Parameters dictionary with layer ordering info
        
    Returns:
        The position index, or -1 if not found
    """
    try:
        if not should_use_layer_ordering(params):
            return -1
            
        active_layers = params.get('active_layers', [])
        layer_order = params.get('layer_render_order', [])
        
        # Find the layer's original index
        original_idx = -1
        for i, layer in enumerate(active_layers):
            if layer['id'] == layer_id:
                original_idx = i
                break
                
        if original_idx == -1:
            return -1
            
        # Find where this index appears in the order
        try:
            return layer_order.index(original_idx)
        except ValueError:
            return -1
            
    except Exception as e:
        logger.error(f"Error getting layer position: {e}")
        return -1 