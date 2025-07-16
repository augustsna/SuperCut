#!/usr/bin/env python3
"""
Layer Manager for SuperCut
Provides a simple drag-and-drop interface for reordering video layers.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QDialog, QDialogButtonBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from typing import Optional, cast
from PyQt6.QtGui import QIcon, QDrag, QPixmap, QDropEvent
import os

class SafeListWidget(QListWidget):
    """Custom QListWidget with simple up/down button reordering"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget: Optional['LayerManagerWidget'] = cast('LayerManagerWidget', parent) if parent else None

class LayerItem(QListWidgetItem):
    """Custom list item for layers with metadata"""
    def __init__(self, layer_id, display_name, enabled=True, icon_path=None):
        super().__init__()
        self.layer_id = layer_id
        self.display_name = display_name
        self.enabled = enabled
        
        # Set display text
        self.setText(display_name)
        
        # Set icon if provided
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        
        # Set visual state and make item draggable
        flags = (Qt.ItemFlag.ItemIsSelectable | 
                Qt.ItemFlag.ItemIsEnabled | 
                Qt.ItemFlag.ItemIsUserCheckable |
                Qt.ItemFlag.ItemIsDragEnabled | 
                Qt.ItemFlag.ItemIsDropEnabled)
        self.setFlags(flags)
        self.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)

class LayerManagerWidget(QWidget):
    """Widget for managing layer order with drag-and-drop"""
    
    layer_order_changed = pyqtSignal(list)  # Emits list of layer IDs in new order
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layer_items = {}  # layer_id -> LayerItem
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Layer Order")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Select a layer and use ↑/↓ buttons to reorder. Top layers appear in front.")
        instructions.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Layer list
        self.layer_list = SafeListWidget(self)
        self.layer_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.layer_list.setMinimumHeight(200)
        self.layer_list.setMaximumHeight(300)
        self.layer_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                margin: 2px;
                background-color: #f9f9f9;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(self.layer_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_default)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Add up/down buttons for reordering
        reorder_layout = QHBoxLayout()
        
        self.move_up_btn = QPushButton("↑ Move Up")
        self.move_up_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #2196f3;
                border-radius: 4px;
                background-color: #2196f3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #ccc;
                border-color: #ccc;
            }
        """)
        self.move_up_btn.clicked.connect(self.move_selected_up)
        
        self.move_down_btn = QPushButton("↓ Move Down")
        self.move_down_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #2196f3;
                border-radius: 4px;
                background-color: #2196f3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #ccc;
                border-color: #ccc;
            }
        """)
        self.move_down_btn.clicked.connect(self.move_selected_down)
        
        reorder_layout.addWidget(self.move_up_btn)
        reorder_layout.addWidget(self.move_down_btn)
        reorder_layout.addStretch()
        layout.addLayout(reorder_layout)
        
        # Connect signals
        self.layer_list.itemChanged.connect(self.on_layers_reordered)
        self.layer_list.currentRowChanged.connect(self.update_move_buttons)
        
        # Initial button state
        self.update_move_buttons()
        
    def setup_layers(self, layer_configs):
        """Setup layers from configuration
        Args:
            layer_configs: List of dicts with keys: id, name, enabled, icon_path
        """
        self.layer_list.clear()
        self.layer_items.clear()
        for config in layer_configs:
            self.layer_items[config['id']] = config  # Store config, not LayerItem
            item = LayerItem(
                layer_id=config['id'],
                display_name=config['name'],
                enabled=config.get('enabled', True),
                icon_path=config.get('icon_path')
            )
            self.layer_list.addItem(item)

    def get_layer_order(self):
        """Get current layer order as list of layer IDs"""
        order = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if isinstance(item, LayerItem):
                order.append(item.layer_id)
        return order
    
    def get_enabled_layers(self):
        """Get list of enabled layer IDs in current order"""
        enabled = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if isinstance(item, LayerItem) and item.checkState() == Qt.CheckState.Checked:
                enabled.append(item.layer_id)
        return enabled
    
    def on_layers_reordered(self):
        """Handle when layers are reordered"""
        # This will be called automatically when items are moved
        pass
    
    def update_move_buttons(self):
        """Update the enabled state of move up/down buttons"""
        current_row = self.layer_list.currentRow()
        total_items = self.layer_list.count()
        
        # Enable/disable move up button
        self.move_up_btn.setEnabled(current_row > 0)
        
        # Enable/disable move down button
        self.move_down_btn.setEnabled(current_row >= 0 and current_row < total_items - 1)
    
    def move_selected_up(self):
        """Move the selected item up in the list"""
        current_row = self.layer_list.currentRow()
        if current_row > 0:
            # Get the current item
            current_item = self.layer_list.takeItem(current_row)
            # Insert it one position up
            self.layer_list.insertItem(current_row - 1, current_item)
            # Select the moved item
            self.layer_list.setCurrentRow(current_row - 1)
            # Update button states
            self.update_move_buttons()
            # Notify of reorder
            self.on_layers_reordered()
    
    def move_selected_down(self):
        """Move the selected item down in the list"""
        current_row = self.layer_list.currentRow()
        total_items = self.layer_list.count()
        if current_row >= 0 and current_row < total_items - 1:
            # Get the current item
            current_item = self.layer_list.takeItem(current_row)
            # Insert it one position down
            self.layer_list.insertItem(current_row + 1, current_item)
            # Select the moved item
            self.layer_list.setCurrentRow(current_row + 1)
            # Update button states
            self.update_move_buttons()
            # Notify of reorder
            self.on_layers_reordered()
    
    def store_current_state(self):
        """Store the current state before drag operations"""
        self._backup_state = self.get_layer_order()
        print(f"Stored backup state: {self._backup_state}")
    
    def rebuild_layer_list(self):
        """Rebuild the layer list to ensure all items are present"""
        print("Rebuilding layer list to restore missing items...")
        # Use backup state if available, otherwise use current order
        if hasattr(self, '_backup_state') and self._backup_state:
            print("Using backup state for rebuild...")
            target_order = self._backup_state
            self._backup_state = None
        else:
            current_order = self.get_layer_order()
            target_order = current_order
        self.layer_list.clear()
        for layer_id in target_order:
            if layer_id in self.layer_items:
                config = self.layer_items[layer_id]
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=config.get('enabled', True),
                    icon_path=config.get('icon_path')
                )
                self.layer_list.addItem(item)
        # Add any missing items that weren't in the target order
        for layer_id, config in self.layer_items.items():
            if layer_id not in target_order:
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=config.get('enabled', True),
                    icon_path=config.get('icon_path')
                )
                self.layer_list.addItem(item)
    
    def verify_layer_integrity(self):
        """Verify that all layer items are present in the list"""
        current_items = set()
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if isinstance(item, LayerItem):
                current_items.add(item.layer_id)
        
        expected_items = set(self.layer_items.keys())
        
        if current_items != expected_items:
            print(f"Layer integrity check failed. Missing: {expected_items - current_items}")
            print(f"Extra items: {current_items - expected_items}")
            return False
        return True
    
    def reset_to_default(self):
        """Reset layer order to default"""
        # Default order: background, overlays (1-10), intro, frames, song titles, soundwave
        default_order = [
            'background',
            'overlay1', 'overlay2', 'overlay3', 'overlay4', 'overlay5',
            'overlay6', 'overlay7', 'overlay8', 'overlay9', 'overlay10',
            'intro', 'frame_box', 'frame_mp3cover', 'song_titles', 'soundwave'
        ]
        
        # Clear and rebuild with default order
        self.layer_list.clear()
        for layer_id in default_order:
            if layer_id in self.layer_items:
                config = self.layer_items[layer_id]
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=config.get('enabled', True),
                    icon_path=config.get('icon_path')
                )
                self.layer_list.addItem(item)
    
    def apply_order(self):
        """Save and apply the current layer order"""
        order = self.get_layer_order()
        self.layer_order_changed.emit(order)
    
    def update_layer_states(self, layer_states):
        """Update the enabled/disabled state of layers based on a dict of {layer_id: enabled}"""
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if isinstance(item, LayerItem):
                enabled = layer_states.get(item.layer_id, True)
                item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)

class LayerManagerDialog(QDialog):
    """Dialog for managing layer order"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Layer Order Manager")
        self.setModal(True)
        self.setMinimumSize(400, 500)
        
        # Default layer configuration
        self.default_layers = [
            {'id': 'background', 'name': 'Background Image', 'enabled': True},
            {'id': 'overlay1', 'name': 'Overlay 1', 'enabled': False},
            {'id': 'overlay2', 'name': 'Overlay 2', 'enabled': False},
            {'id': 'overlay3', 'name': 'Overlay 3 (Soundwave)', 'enabled': False},
            {'id': 'overlay4', 'name': 'Overlay 4', 'enabled': False},
            {'id': 'overlay5', 'name': 'Overlay 5', 'enabled': False},
            {'id': 'overlay6', 'name': 'Overlay 6', 'enabled': False},
            {'id': 'overlay7', 'name': 'Overlay 7', 'enabled': False},
            {'id': 'overlay8', 'name': 'Overlay 8', 'enabled': False},
            {'id': 'overlay9', 'name': 'Overlay 9', 'enabled': False},
            {'id': 'overlay10', 'name': 'Overlay 10', 'enabled': False},
            {'id': 'intro', 'name': 'Intro', 'enabled': False},
            {'id': 'frame_box', 'name': 'Frame Box', 'enabled': False},
            {'id': 'frame_mp3cover', 'name': 'Frame MP3 Cover', 'enabled': False},
            {'id': 'song_titles', 'name': 'Song Titles', 'enabled': True},
            {'id': 'soundwave', 'name': 'Soundwave', 'enabled': False},
        ]
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Layer manager widget
        self.layer_manager = LayerManagerWidget()
        self.layer_manager.setup_layers(self.default_layers)
        layout.addWidget(self.layer_manager)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("Save & Apply")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect layer order changes
        self.layer_manager.layer_order_changed.connect(self.on_layer_order_changed)
        
        # Connect OK button to apply order
        button_box.accepted.connect(self.apply_and_close)
        
    def on_layer_order_changed(self, order):
        """Handle layer order changes"""
        # Store the new order for retrieval
        self.current_order = order
    
    def apply_and_close(self):
        """Apply the current layer order and close the dialog"""
        # Get current order and emit signal
        order = self.layer_manager.get_layer_order()
        self.layer_manager.layer_order_changed.emit(order)
        # Close the dialog
        self.accept()
        
    def get_layer_order(self):
        """Get the current layer order"""
        return self.layer_manager.get_layer_order()
    
    def get_enabled_layers(self):
        """Get enabled layers in current order"""
        return self.layer_manager.get_enabled_layers()
    
    def update_layer_states(self, layer_states):
        """Update the enabled/disabled state of layers
        
        Args:
            layer_states: Dict mapping layer_id to enabled state
        """
        # Update the layer manager's layer states
        self.layer_manager.update_layer_states(layer_states) 