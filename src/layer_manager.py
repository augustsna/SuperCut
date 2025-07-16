#!/usr/bin/env python3
"""
Layer Manager for SuperCut
Provides a simple drag-and-drop interface for reordering video layers.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QDialog, QDialogButtonBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from typing import Optional, cast
from PyQt6.QtGui import QIcon, QDrag, QPixmap, QDropEvent, QKeySequence, QShortcut
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
        
        # Set visual state and make item selectable (but not checkable by user)
        flags = (Qt.ItemFlag.ItemIsSelectable | 
                Qt.ItemFlag.ItemIsEnabled)
        self.setFlags(flags)
        
        # Set check state for display only (read-only)
        self.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)

class LayerManagerWidget(QWidget):
    """Widget for managing layer order with drag-and-drop"""
    
    layer_order_changed = pyqtSignal(list)  # Emits list of layer IDs in new order
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layer_items = {}  # layer_id -> LayerItem
        self.last_applied_order = None  # Store the last applied order
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Layer Order")
        title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(title)
        # Layer list
        self.layer_list = SafeListWidget(self)
        self.layer_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.layer_list.setMinimumHeight(200)
        self.layer_list.setMaximumHeight(265)
        self.layer_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                margin: 2px;
                background-color: #f9f9f9;
                outline: none;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border-color: #2196f3;
                color: black;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QListWidget::item:focus {
                outline: none;
            }
            QListWidget::indicator {
                width: 16px;
                height: 16px;
            }
            QListWidget::indicator:unchecked {
                image: none;
                border: 1px solid #ccc;
                background-color: transparent;
                border-radius: 4px;
            }
            QListWidget::indicator:checked {
                background: transparent;
                border-radius: 4px;
                border: 1px solid #ccc;
                image: url(src/sources/black_tick.svg);
            }
        """)
        layout.addWidget(self.layer_list)
        
        # Buttons - all on same line with reset on right edge
        button_layout = QHBoxLayout()
        
        self.move_up_btn = QPushButton("↑ Up")
        self.move_up_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #4a90e2;
                border-radius: 4px;
                background-color: #4a90e2;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #4a90e2;
                border-color: white;
            }
        """)
        self.move_up_btn.clicked.connect(self.move_selected_up)
        
        self.move_down_btn = QPushButton("↓ Down")
        self.move_down_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #4a90e2;
                border-radius: 4px;
                background-color: #4a90e2;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:disabled {
                background-color: #4a90e2;
                border-color: white;
            }
        """)
        self.move_down_btn.clicked.connect(self.move_selected_down)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ccc;
                color: black;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_default)
        
        button_layout.addWidget(self.move_up_btn)
        button_layout.addWidget(self.move_down_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_btn)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.layer_list.itemChanged.connect(self.on_layers_reordered)
        self.layer_list.currentRowChanged.connect(self.update_move_buttons)
        
        # Initial button state
        self.update_move_buttons()
        
    def setup_layers(self, layer_configs, saved_order=None):
        """Setup layers from configuration
        Args:
            layer_configs: List of dicts with keys: id, name, enabled, icon_path
            saved_order: Optional list of layer IDs in saved order
        """
        self.layer_list.clear()
        self.layer_items.clear()
        
        # Store the saved order if provided
        if saved_order:
            self.last_applied_order = saved_order
        
        # If we have a saved order, use it; otherwise use default order
        if self.last_applied_order:
            # Use saved order, adding any missing layers at the end
            used_ids = set()
            for layer_id in self.last_applied_order:
                if layer_id in [config['id'] for config in layer_configs]:
                    used_ids.add(layer_id)
                    config = next(c for c in layer_configs if c['id'] == layer_id)
                    self.layer_items[config['id']] = config
                    item = LayerItem(
                        layer_id=config['id'],
                        display_name=config['name'],
                        enabled=config.get('enabled', True),
                        icon_path=config.get('icon_path')
                    )
                    self.layer_list.insertItem(0, item)  # Insert at top (reverse order)
            
            # Add any remaining layers that weren't in the saved order
            for config in layer_configs:
                if config['id'] not in used_ids:
                    self.layer_items[config['id']] = config
                    item = LayerItem(
                        layer_id=config['id'],
                        display_name=config['name'],
                        enabled=config.get('enabled', True),
                        icon_path=config.get('icon_path')
                    )
                    self.layer_list.insertItem(0, item)  # Insert at top (reverse order)
        else:
            # Use default order (original behavior) - but display in reverse
            for config in layer_configs:
                self.layer_items[config['id']] = config
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=config.get('enabled', True),
                    icon_path=config.get('icon_path')
                )
                self.layer_list.insertItem(0, item)  # Insert at top (reverse order)

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
        
        # Get the current item to check if it's background
        current_item = self.layer_list.item(current_row) if current_row >= 0 else None
        is_background = isinstance(current_item, LayerItem) and current_item.layer_id == 'background'
        
        # Disable move buttons if background is selected (background should stay at bottom)
        if is_background:
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
        else:
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
            # Check if the item below is background (prevent moving past background)
            next_item = self.layer_list.item(current_row + 1)
            if isinstance(next_item, LayerItem) and next_item.layer_id == 'background':
                return  # Don't allow moving past background
            
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
                self.layer_list.insertItem(0, item)  # Insert at top (reverse order)
        # Add any missing items that weren't in the target order
        for layer_id, config in self.layer_items.items():
            if layer_id not in target_order:
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=config.get('enabled', True),
                    icon_path=config.get('icon_path')
                )
                self.layer_list.insertItem(0, item)  # Insert at top (reverse order)
    
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
        
        # Clear and rebuild with default order (display in reverse)
        self.layer_list.clear()
        for layer_id in default_order:
            if layer_id in self.layer_items:
                config = self.layer_items[layer_id]
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=False,  # Start unchecked, let live sync set the correct state
                    icon_path=config.get('icon_path')
                )
                self.layer_list.insertItem(0, item)  # Insert at top (reverse order)
        
        # Clear the saved order when resetting to default
        self.last_applied_order = None
        
        # Update button states after reset
        self.update_move_buttons()
        
        # Scroll to bottom to show background image after reset
        QTimer.singleShot(100, lambda: self.layer_list.scrollToBottom())
        
        # Pre-select the 2nd item from bottom after reset
        QTimer.singleShot(150, self._select_second_from_bottom)
    
    def apply_order(self):
        """Save and apply the current layer order"""
        order = self.get_layer_order()
        self.last_applied_order = order  # Store the applied order
        self.layer_order_changed.emit(order)
    
    def update_layer_states(self, layer_states):
        """Update the enabled/disabled state of layers based on a dict of {layer_id: enabled}"""
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if isinstance(item, LayerItem):
                enabled = layer_states.get(item.layer_id, True)
                item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
    
    def _select_second_from_bottom(self):
        """Select the 2nd item from the bottom of the list"""
        total_items = self.layer_list.count()
        if total_items >= 2:
            second_from_bottom_index = total_items - 2
            self.layer_list.setCurrentRow(second_from_bottom_index)

class LayerManagerDialog(QWidget):
    """Window for managing layer order"""
    
    def __init__(self, parent=None, saved_order=None):
        super().__init__(parent)
        self.setWindowTitle("Layer Order Manager")
        self.setWindowFlags(Qt.WindowType.Window)  # Make it a regular window
        self.setMinimumSize(400, 500)
        self.saved_order = saved_order
        self.main_window = parent  # Store parent reference for live updates
        
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
        self.layer_manager.setup_layers(self.default_layers, self.saved_order)
        layout.addWidget(self.layer_manager)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save && Apply")
        save_btn.setFixedHeight(32)
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #4a90e2;
                border-radius: 4px;
                background-color: #4a90e2;
                color: white;                
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        save_btn.clicked.connect(self.apply_and_close)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(32)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #4a90e2;
                border-radius: 4px;
                background-color: #4a90e2;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        cancel_btn.clicked.connect(self.close)
        
        layout.addSpacing(30)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addSpacing(5)
        
        # Connect layer order changes
        self.layer_manager.layer_order_changed.connect(self.on_layer_order_changed)
        
        # Set up timer for live checkbox updates
        self.update_timer = None
        self.setup_live_updates()
        
        # Scroll to bottom to show background image (now at bottom due to reversed order)
        self.scroll_to_bottom()
        
        # Pre-select the 2nd item from bottom (2nd item in logical order)
        self.select_second_from_bottom()
        
        # Add Ctrl+W shortcut to close dialog
        self.shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcut.activated.connect(self.close)
        
    def on_layer_order_changed(self, order):
        """Handle layer order changes"""
        # Store the new order for retrieval
        self.current_order = order
    
    def apply_and_close(self):
        """Apply the current layer order and close the window"""
        # Get current order and emit signal
        order = self.layer_manager.get_layer_order()
        self.layer_manager.layer_order_changed.emit(order)
        
        # Update main window's layer order
        if self.main_window:
            self.main_window.layer_order = order
            self.main_window.enabled_layers = self.layer_manager.get_enabled_layers()
            print(f"Layer order applied: {order}")
            print(f"Enabled layers: {self.layer_manager.get_enabled_layers()}")
        
        # Close the window
        self.close()
        
    def get_layer_order(self):
        """Get the current layer order"""
        return self.layer_manager.get_layer_order()
    
    def get_enabled_layers(self):
        """Get enabled layers in current order"""
        return self.layer_manager.get_enabled_layers()
    
    def setup_live_updates(self):
        """Set up timer for live checkbox updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_checkbox_states)
        self.update_timer.start(100)  # Update every 500ms
    
    def update_checkbox_states(self):
        """Update checkbox states based on main UI state"""
        if not self.main_window:
            return
            
        # Get current layer states from main UI
        layer_states = {}
        
        # Background
        if hasattr(self.main_window, 'background_checkbox'):
            layer_states['background'] = self.main_window.background_checkbox.isChecked()
        
        # Overlays
        for i in range(1, 11):
            checkbox_name = f'overlay{i}_checkbox' if i > 1 else 'overlay_checkbox'
            if hasattr(self.main_window, checkbox_name):
                checkbox = getattr(self.main_window, checkbox_name)
                layer_states[f'overlay{i}'] = checkbox.isChecked()
        
        # Intro
        if hasattr(self.main_window, 'intro_checkbox'):
            layer_states['intro'] = self.main_window.intro_checkbox.isChecked()
        
        # Frames
        if hasattr(self.main_window, 'frame_box_checkbox'):
            layer_states['frame_box'] = self.main_window.frame_box_checkbox.isChecked()
        if hasattr(self.main_window, 'frame_mp3cover_checkbox'):
            layer_states['frame_mp3cover'] = self.main_window.frame_mp3cover_checkbox.isChecked()
        
        # Song titles
        if hasattr(self.main_window, 'song_title_checkbox'):
            layer_states['song_titles'] = self.main_window.song_title_checkbox.isChecked()
        
        # Soundwave
        if hasattr(self.main_window, 'soundwave_checkbox'):
            layer_states['soundwave'] = self.main_window.soundwave_checkbox.isChecked()
        
        # Update the layer manager's checkbox states
        self.layer_manager.update_layer_states(layer_states)
    
    def closeEvent(self, event):
        """Clean up timer when dialog is closed"""
        if self.update_timer:
            self.update_timer.stop()
        super().closeEvent(event)
    
    def scroll_to_bottom(self):
        """Scroll the layer list to the bottom to show background image"""
        if hasattr(self.layer_manager, 'layer_list'):
            # Use a timer to ensure the list is fully loaded before scrolling
            QTimer.singleShot(50, lambda: self.layer_manager.layer_list.scrollToBottom())
    
    def select_second_from_bottom(self):
        """Pre-select the 2nd item from the bottom of the list"""
        if hasattr(self.layer_manager, 'layer_list'):
            # Use a timer to ensure the list is fully loaded before selecting
            QTimer.singleShot(100, self._do_select_second_from_bottom)
    
    def _do_select_second_from_bottom(self):
        """Actually perform the selection of 2nd item from bottom"""
        if hasattr(self.layer_manager, 'layer_list'):
            layer_list = self.layer_manager.layer_list
            total_items = layer_list.count()
            if total_items >= 2:
                # 2nd item from bottom = index (total_items - 2)
                second_from_bottom_index = total_items - 2
                layer_list.setCurrentRow(second_from_bottom_index)
    
    def update_layer_states(self, layer_states):
        """Update the enabled/disabled state of layers
        
        Args:
            layer_states: Dict mapping layer_id to enabled state
        """
        # Update the layer manager's layer states
        self.layer_manager.update_layer_states(layer_states) 