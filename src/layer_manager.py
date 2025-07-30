#!/usr/bin/env python3
"""
Layer Manager for SuperCut
Provides a simple drag-and-drop interface for reordering video layers.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QDialog, QDialogButtonBox, QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from typing import Optional, cast
from PyQt6.QtGui import QIcon, QDrag, QPixmap, QDropEvent, QKeySequence, QShortcut, QMouseEvent
import os

class SafeListWidget(QListWidget):
    """Custom QListWidget with simple up/down button reordering"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget: Optional['LayerManagerWidget'] = cast('LayerManagerWidget', parent) if parent else None
    
    def paintEvent(self, event):
        """Custom paint event to ensure rounded corners are properly clipped"""
        from PyQt6.QtGui import QPainter, QPainterPath
        
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create rounded rectangle path for clipping
        path = QPainterPath()
        path.addRoundedRect(self.rect().toRectF(), 12, 12)
        painter.setClipPath(path)
        
        # Call the parent paint event
        super().paintEvent(event)

class LayerItem(QListWidgetItem):
    """Custom list item for layers with metadata"""
    def __init__(self, layer_id, display_name, enabled=True, icon_path=None, order_number=None):
        super().__init__()
        self.layer_id = layer_id
        self.display_name = display_name
        self.enabled = enabled
        self.order_number = order_number
        
        # Set display text with order number
        if order_number is not None:
            self.setText(f"{order_number}. {display_name}")
        else:
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
    
    def update_order_number(self, new_order_number):
        """Update the order number and display text"""
        self.order_number = new_order_number
        if new_order_number is not None:
            self.setText(f"{new_order_number}. {self.display_name}")
        else:
            self.setText(self.display_name)

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        

        # Create scroll area for layer list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(250)
        scroll_area.setMaximumHeight(400)  # Increased to give more space
        scroll_area.setMinimumWidth(350)  # Ensure minimum width for proper layout
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
                margin: 0px;
                padding: 0px;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background: rgba(240, 240, 240, 0.8);
                width: 12px;
                border-radius: 8px;
                margin-left: 4px;
                position: absolute;
                right: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(192, 192, 192, 0.8);
                border-radius: 6px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(160, 160, 160, 0.9);
            }
            QScrollBar:horizontal {
                background: rgba(240, 240, 240, 0.8);
                height: 12px;
                border-radius: 6px;
                margin: 0px;
                position: absolute;
                bottom: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(192, 192, 192, 0.8);
                border-radius: 6px;
                min-width: 20px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(160, 160, 160, 0.9);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QScrollBar:sub-control:corner {
                background: transparent;
            }
        """)
        
        # Layer list widget
        self.layer_list = SafeListWidget(self)
        self.layer_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.layer_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layer_list.setContentsMargins(0, 0, 0, 0)
        self.layer_list.setViewportMargins(0, 0, 0, 0)
        self.layer_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.layer_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.layer_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: none;
                padding: 6px;
                border: 1px solid #e0e0e0;
                border-radius: 2px;
                color: #333;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin: 2px;
                background-color: #ffffff;
                outline: none;
                color: #333;
            }
            QListWidget::item:first-child {
                margin-top: 8px;
            }
            QListWidget::item:last-child {
                margin-bottom: 4px;
                margin-top: 2px;
            }
            QListWidget::item:selected {
                background-color: #4a90e2;
                background-color: #f8f8f8;
                border-color: #e0e0e0;
                color: #000000;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #f8f8f8;
                border-color: #a0a0a0;
                color: #000000;
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
        
        # Set the layer list as the scroll area's widget
        scroll_area.setWidget(self.layer_list)
        layout.addWidget(scroll_area)
        
        # Add spacing between scroll area and buttons
        layout.addSpacing(10)  # Increased spacing to give more room between scroll and buttons
        
        # Buttons - all on same line with reset on right edge
        button_layout = QHBoxLayout()
        
        self.move_up_btn = QPushButton("↑ Up")
        self.move_up_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                border: 1px solid #4a90e2;
                border-radius: 6px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #357ABD;
                border-color: #357ABD;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                border-color: #e0e0e0;
                color: #999999;
            }
        """)
        self.move_up_btn.clicked.connect(self.move_selected_up)
        
        self.move_down_btn = QPushButton("↓ Down")
        self.move_down_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                border: 1px solid #4a90e2;
                border-radius: 6px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #357ABD;
                border-color: #357ABD;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                border-color: #e0e0e0;
                color: #999999;
            }
        """)
        self.move_down_btn.clicked.connect(self.move_selected_down)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #4a90e2;
                border-color: #ccc;
                border-radius: 6px;
                padding: 6px 12px;
                color: #000000;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #ccc;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_default)
        
        button_layout.addWidget(self.move_up_btn)
        button_layout.addSpacing(12)  # Increased spacing between buttons
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
            # Build the list in reverse order for display (background at bottom)
            for layer_id in reversed(self.last_applied_order):
                if layer_id in [config['id'] for config in layer_configs]:
                    used_ids.add(layer_id)
                    config = next(c for c in layer_configs if c['id'] == layer_id)
                    self.layer_items[config['id']] = config
                    item = LayerItem(
                        layer_id=config['id'],
                        display_name=config['name'],
                        enabled=config.get('enabled', True),
                        icon_path=config.get('icon_path'),
                        order_number=len(self.layer_list) + 1
                    )
                    self.layer_list.addItem(item)  # Append to end
            # Add any remaining layers that weren't in the saved order
            for config in reversed(layer_configs):
                if config['id'] not in used_ids:
                    self.layer_items[config['id']] = config
                    item = LayerItem(
                        layer_id=config['id'],
                        display_name=config['name'],
                        enabled=config.get('enabled', True),
                        icon_path=config.get('icon_path'),
                        order_number=len(self.layer_list) + 1
                    )
                    self.layer_list.addItem(item)  # Append to end
        else:
            # Use default order (original behavior)
            print(f"🔧 No saved order, using default order")
            for config in reversed(layer_configs):
                self.layer_items[config['id']] = config
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=config.get('enabled', True),
                    icon_path=config.get('icon_path'),
                    order_number=len(self.layer_list) + 1
                )
                self.layer_list.addItem(item)  # Append to end
        
        # Update order numbers after all items are added
        self.update_order_numbers()

    def update_order_numbers(self):
        """Update the order numbers of all items in the layer list."""
        total_items = self.layer_list.count()
        for i in range(total_items):
            item = self.layer_list.item(i)
            if isinstance(item, LayerItem):
                # Reverse numbering: background (bottom) = 0, top item = highest number
                order_number = total_items - 1 - i
                item.update_order_number(order_number)

    def get_layer_order(self):
        """Get current layer order as list of layer IDs in logical order (background first)"""
        order = []
        # Get items in reverse order since display is reversed (background at bottom)
        for i in range(self.layer_list.count() - 1, -1, -1):
            item = self.layer_list.item(i)
            if isinstance(item, LayerItem):
                order.append(item.layer_id)
        return order
    
    def get_enabled_layers(self):
        """Get list of enabled layer IDs in logical order (background first)"""
        enabled = []
        # Get items in reverse order since display is reversed (background at bottom)
        # This matches the logic in get_layer_order() to maintain consistent ordering
        for i in range(self.layer_list.count() - 1, -1, -1):
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
            # Update order numbers
            self.update_order_numbers()
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
                # Scroll to bottom to show background layer
                self.layer_list.scrollToBottom()
                return  # Don't allow moving past background
            # Get the current item
            current_item = self.layer_list.takeItem(current_row)
            # Insert it one position down
            self.layer_list.insertItem(current_row + 1, current_item)
            # Select the moved item
            self.layer_list.setCurrentRow(current_row + 1)
            # Update order numbers
            self.update_order_numbers()
            # Update button states
            self.update_move_buttons()
            # Notify of reorder
            self.on_layers_reordered()
            # If moved to last position before background, scroll to bottom
            if current_row + 1 == total_items - 2:
                self.layer_list.scrollToBottom()
    

    
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
                self.layer_list.addItem(item)  # Append to end
        # Add any missing items that weren't in the target order
        for layer_id, config in self.layer_items.items():
            if layer_id not in target_order:
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=config.get('enabled', True),
                    icon_path=config.get('icon_path')
                )
                self.layer_list.addItem(item)  # Append to end
    
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
            'intro', 'frame_box', 'frame_mp3cover', 'mp3_cover_overlay', 'song_titles', 'soundwave'
        ]
        
        # Clear and rebuild with default order (display in reverse)
        self.layer_list.clear()
        for layer_id in reversed(default_order):
            if layer_id in self.layer_items:
                config = self.layer_items[layer_id]
                item = LayerItem(
                    layer_id=config['id'],
                    display_name=config['name'],
                    enabled=False,  # Start unchecked, let live sync set the correct state
                    icon_path=config.get('icon_path'),
                    order_number=len(self.layer_list) + 1
                )
                self.layer_list.addItem(item)  # Append to end
        
        # Update order numbers after reset
        self.update_order_numbers()
        
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
    def showEvent(self, event):
        """Ensure the layer list is scrolled to the bottom and up/down buttons are enabled when the dialog is shown. Also position dialog left/right of main UI."""
        super().showEvent(event)
        # Position dialog left/right of main window (not center)
        self.show_and_raise()
        # Scroll to bottom and enable buttons
        if hasattr(self.layer_manager, 'layer_list'):
            self.layer_manager.layer_list.scrollToBottom()
        if hasattr(self.layer_manager, 'move_up_btn'):
            self.layer_manager.move_up_btn.setEnabled(True)
        if hasattr(self.layer_manager, 'move_down_btn'):
            self.layer_manager.move_down_btn.setEnabled(True)
    """Window for managing layer order"""
    
    def __init__(self, parent=None, saved_order=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMinimumSize(500, 520)  # Increased height to give more space for the list
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Enable rounded corners
        self.saved_order = saved_order
        self.main_window = parent  # Store parent reference for live updates
        
        # Load custom layer labels from settings
        self.custom_labels = self.load_custom_labels()
        
        # Default layer configuration with custom labels
        self.default_layers = [
            {'id': 'background', 'name': self.custom_labels.get('background', ' Background :'), 'enabled': True},
            {'id': 'overlay1', 'name': self.custom_labels.get('overlay1', ' Overlay 1 :'), 'enabled': False},
            {'id': 'overlay2', 'name': self.custom_labels.get('overlay2', ' Overlay 2 :'), 'enabled': False},
            {'id': 'overlay3', 'name': self.custom_labels.get('overlay3', ' Overlay 3 :'), 'enabled': False},
            {'id': 'overlay4', 'name': self.custom_labels.get('overlay4', ' Overlay 4 :'), 'enabled': False},
            {'id': 'overlay5', 'name': self.custom_labels.get('overlay5', ' Overlay 5 :'), 'enabled': False},
            {'id': 'overlay6', 'name': self.custom_labels.get('overlay6', ' Overlay 6 :'), 'enabled': False},
            {'id': 'overlay7', 'name': self.custom_labels.get('overlay7', ' Overlay 7 :'), 'enabled': False},
            {'id': 'overlay8', 'name': self.custom_labels.get('overlay8', ' Overlay 8 :'), 'enabled': False},
            {'id': 'overlay9', 'name': self.custom_labels.get('overlay9', ' Overlay 9 :'), 'enabled': False},
            {'id': 'overlay10', 'name': self.custom_labels.get('overlay10', ' Overlay 10 :'), 'enabled': False},            
            {'id': 'intro', 'name': self.custom_labels.get('intro', ' Intro :'), 'enabled': False},
            {'id': 'frame_box', 'name': self.custom_labels.get('frame_box', ' Frame Box :'), 'enabled': False},
            {'id': 'frame_mp3cover', 'name': self.custom_labels.get('frame_mp3cover', ' Frame MP3 Cover :'), 'enabled': False},
            {'id': 'mp3_cover_overlay', 'name': self.custom_labels.get('mp3_cover_overlay', ' MP3 Cover Overlay :'), 'enabled': False},
            {'id': 'song_titles', 'name': self.custom_labels.get('song_titles', ' Song Titles :'), 'enabled': False},
            {'id': 'soundwave', 'name': self.custom_labels.get('soundwave', ' Soundwave :'), 'enabled': False},
        ]
        

        
        self.init_ui()
    
    def load_custom_labels(self):
        """Load custom layer labels from settings"""
        custom_labels = {}
        
        # Import QSettings here to avoid circular imports
        from PyQt6.QtCore import QSettings
        
        # Create settings object - use same configuration as main_ui.py
        settings = QSettings('SuperCut', 'SuperCutUI')
        
        # Load custom labels for each layer type with validation
        custom_labels['background'] = settings.value('background_checkbox_label', ' Background :', type=str) or ' Background :'
        custom_labels['overlay1'] = settings.value('overlay1_checkbox_label', ' Overlay 1 :', type=str) or ' Overlay 1 :'
        custom_labels['overlay2'] = settings.value('overlay2_checkbox_label', ' Overlay 2 :', type=str) or ' Overlay 2 :'
        custom_labels['frame_box'] = settings.value('frame_box_checkbox_label', ' Frame Box :', type=str) or ' Frame Box :'
        custom_labels['song_titles'] = settings.value('song_titles_checkbox_label', ' Song Titles :', type=str) or ' Song Titles :'
        custom_labels['soundwave'] = settings.value('soundwave_checkbox_label', ' Soundwave :', type=str) or ' Soundwave :'
        custom_labels['intro'] = settings.value('intro_checkbox_label', ' Intro :', type=str) or ' Intro :'
        
        # For overlays 3-10, load from settings with consistent default format and validation
        for i in range(3, 11):
            custom_labels[f'overlay{i}'] = settings.value(f'overlay{i}_checkbox_label', f' Overlay {i} :', type=str) or f' Overlay {i} :'
        
        # For frame_mp3cover and mp3_cover_overlay, load from settings with validation
        custom_labels['frame_mp3cover'] = settings.value('frame_mp3cover_checkbox_label', ' Frame MP3 Cover :', type=str) or ' Frame MP3 Cover :'
        custom_labels['mp3_cover_overlay'] = settings.value('mp3_cover_overlay_checkbox_label', ' MP3 Cover Overlay :', type=str) or ' MP3 Cover Overlay :'
        

        
        return custom_labels
    
    def update_layer_labels(self):
        """Update layer labels from settings and refresh the display"""
        
        # Reload custom labels
        self.custom_labels = self.load_custom_labels()
        
        # Update default_layers with new labels
        for layer in self.default_layers:
            layer_id = layer['id']
            if layer_id in self.custom_labels:
                layer['name'] = self.custom_labels[layer_id]
        
        # Rebuild the layer list if it exists, preserving current state
        if hasattr(self, 'layer_manager') and hasattr(self.layer_manager, 'layer_list'):
            # Store current state before rebuilding
            current_states = {}
            for i in range(self.layer_manager.layer_list.count()):
                item = self.layer_manager.layer_list.item(i)
                if isinstance(item, LayerItem):
                    current_states[item.layer_id] = item.checkState() == Qt.CheckState.Checked
            
            # Rebuild with new labels
            self.layer_manager.setup_layers(self.default_layers, self.saved_order)
            
            # Restore current states
            for i in range(self.layer_manager.layer_list.count()):
                item = self.layer_manager.layer_list.item(i)
                if isinstance(item, LayerItem) and item.layer_id in current_states:
                    if current_states[item.layer_id]:
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(Qt.CheckState.Unchecked)
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create draggable header
        self.header = DraggableHeader(self)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        # Header title
        title_label = QLabel("📚 Layer Order")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
                margin: 0px;
                padding: 0px;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Close button in header
        close_btn = QPushButton("X")
        close_btn.setObjectName("exitButton")
        close_btn.setFixedSize(14, 14)
        close_btn.setStyleSheet("""
            #exitButton {
                background-color: #8d8d8d;
                border: 1px solid #8d8d8d;
                border-radius: 7px;
                padding: 0px;
                font-size: 10px;
                font-weight: 700;
                min-width: 16px;
                max-width: 16px;
                min-height: 16px;
                max-height: 16px;
                color: white;
                text-align: center;
                line-height: 16px;
            }
            #exitButton:hover {
                background-color: #f23321;
                border-color: #f23321;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        self.header.setStyleSheet("""
            QWidget {
                background-color: #eff4f9 !important;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #ccc;
            }
        """)
        self.header.setFixedHeight(36)
        layout.addWidget(self.header)
        
        # Main content container
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 0, 12, 12)
        content_layout.setSpacing(0)  # Reduced spacing to give more room for the list
        
        # Layer manager widget
        self.layer_manager = LayerManagerWidget()
        self.layer_manager.setup_layers(self.default_layers, self.saved_order)
        content_layout.addWidget(self.layer_manager)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save && Apply")
        save_btn.setFixedHeight(32)
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #4caf50;
                border-radius: 6px;
                background-color: #4caf50;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a249;
                border-color: #45a249;
            }
        """)
        save_btn.clicked.connect(self.apply_and_close)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(32)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #4a90e2;
                border-radius: 6px;
                background-color: #4a90e2;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #357ABD;
                border-color: #357ABD;
            }
        """)
        cancel_btn.clicked.connect(self.close)
        
        content_layout.addSpacing(32)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        content_layout.addLayout(button_layout)
        content_layout.addSpacing(0)
        
        # Style the content widget
        content_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        
        # Add content widget to main layout
        layout.addWidget(content_widget)
        
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
    
            print(f"🔧 Updated layer order: {order}")
            print(f"Enabled layers: {self.layer_manager.get_enabled_layers()}")
            
            # Save layer order to configuration
            try:
                from src.config import save_layer_order
                save_layer_order(order)
            except Exception as e:
                pass
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
        if hasattr(self.main_window, 'mp3_cover_overlay_checkbox'):
            layer_states['mp3_cover_overlay'] = self.main_window.mp3_cover_overlay_checkbox.isChecked()
        
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
    
    def paintEvent(self, event):
        """Custom paint event to draw rounded corners and background"""
        from PyQt6.QtGui import QPainter, QBrush, QColor, QPainterPath
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create rounded rectangle path for clipping
        path = QPainterPath()
        path.addRoundedRect(self.rect().toRectF(), 10, 10)
        painter.setClipPath(path)
        
        # Paint header area with header color
        header_height = 36
        painter.setBrush(QBrush(QColor("#eff4f9")))
        painter.setPen(Qt.PenStyle.NoPen)
        header_rect = self.rect()
        header_rect.setHeight(header_height)
        painter.drawRect(header_rect)
        
        # Paint content area with main color
        painter.setBrush(QBrush(QColor("#f5f7fa")))
        content_rect = self.rect()
        content_rect.setTop(header_height)
        painter.drawRect(content_rect)
        
        # Draw border
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(Qt.PenStyle.SolidLine)
        painter.setPen(QColor("#a0a0a4"))
        painter.drawRoundedRect(self.rect().toRectF(), 10, 10)
    
    def show_and_raise(self):
        """Show the dialog and bring it to front, positioned like SuperCut Preview dialog."""
        # Position dialog next to main window, similar to SuperCut Preview logic
        if self.main_window:
            main_geometry = self.main_window.geometry()
            dialog_width = self.width() if self.width() > 0 else 500
            dialog_height = self.height() if self.height() > 0 else 520
            # Get screen geometry
            screen = self.main_window.screen() if hasattr(self.main_window, 'screen') and self.main_window.screen() else self.main_window.window().screen() if hasattr(self.main_window, 'window') and hasattr(self.main_window.window(), 'screen') else None
            if screen is not None:
                screen_geometry = screen.geometry()
                screen_width = screen_geometry.width()
                screen_height = screen_geometry.height()
            else:
                screen_width = 1920
                screen_height = 1080
            title_bar_height = 30
            space_on_right = screen_width - (main_geometry.x() + main_geometry.width())
            space_on_left = main_geometry.x()
            available_height = screen_height - title_bar_height
            # Determine optimal position
            if space_on_right >= dialog_width + 10:
                dialog_x = main_geometry.x() + main_geometry.width() + 10
                dialog_y = main_geometry.y() - title_bar_height
            elif space_on_left >= dialog_width + 10:
                dialog_x = main_geometry.x() - dialog_width - 10
                dialog_y = main_geometry.y() - title_bar_height
            else:
                if space_on_right > space_on_left:
                    dialog_x = main_geometry.x() + main_geometry.width() + 5
                    dialog_y = main_geometry.y() - title_bar_height
                else:
                    dialog_x = main_geometry.x() - dialog_width - 5
                    dialog_y = main_geometry.y() - title_bar_height
            # Ensure dialog doesn't go off-screen vertically
            if dialog_y + dialog_height > available_height:
                dialog_y = available_height - dialog_height - 10
            if dialog_y < title_bar_height:
                dialog_y = title_bar_height + 10
            # Ensure dialog doesn't go off-screen horizontally
            if dialog_x + dialog_width > screen_width:
                dialog_x = screen_width - dialog_width - 10
            if dialog_x < 0:
                dialog_x = 10
            self.move(dialog_x, dialog_y)
        self.show()
        self.raise_()
        self.activateWindow()


class DraggableHeader(QWidget):
    """Custom header widget that can be dragged to move the window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.dragging = False
        self.drag_position = QPoint()
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging"""
        # Allow dragging for any QWidget parent (layer dialog)
        if event.button() == Qt.MouseButton.LeftButton and isinstance(self.parent_window, QWidget):
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging and isinstance(self.parent_window, QWidget):
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event) 