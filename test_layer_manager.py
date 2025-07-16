#!/usr/bin/env python3
"""
Test script for Layer Manager functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.layer_manager import LayerManagerWidget
from src.layer_utils import collect_active_layers_from_ui

def test_layer_manager():
    """Test the layer manager widget"""
    app = QApplication(sys.argv)
    
    # Create the layer manager widget
    layer_manager = LayerManagerWidget()
    layer_manager.setWindowTitle("Layer Manager Test")
    layer_manager.resize(300, 400)
    
    # Create some test layer data
    test_layers = [
        {'id': 'bg_layer', 'name': 'Background Layer', 'enabled': True, 'type': 'background'},
        {'id': 'overlay1', 'name': 'Overlay 1', 'enabled': True, 'type': 'overlay'},
        {'id': 'overlay2', 'name': 'Overlay 2', 'enabled': True, 'type': 'overlay'},
        {'id': 'frame_box', 'name': 'Frame Box', 'enabled': True, 'type': 'frame'},
        {'id': 'song_title', 'name': 'Song Title', 'enabled': False, 'type': 'overlay'},
    ]
    
    # Set the layers
    layer_manager.set_layers(test_layers)
    
    # Connect to layer order changed signal
    def on_order_changed(new_order):
        print(f"Layer order changed to: {new_order}")
        ordered_layers = layer_manager.get_ordered_layers()
        print("Ordered layers:")
        for i, layer in enumerate(ordered_layers):
            print(f"  {i+1}. {layer['name']} ({'enabled' if layer['enabled'] else 'disabled'})")
    
    layer_manager.layer_order_changed.connect(on_order_changed)
    
    # Show the widget
    layer_manager.show()
    
    print("Layer Manager Test")
    print("==================")
    print("1. The layer manager window should appear")
    print("2. You should see 5 layers listed")
    print("3. Try dragging layers to reorder them")
    print("4. Use the up/down buttons to move layers")
    print("5. Check the console for order change messages")
    print("6. Close the window to exit")
    
    return app.exec()

if __name__ == "__main__":
    test_layer_manager() 