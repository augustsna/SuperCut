# This file uses PyQt6
"""
Layer Manager Widget for SuperCut
Handles layer reordering without modifying existing video processing code.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
import os

class LayerManagerWidget(QWidget):
    """Widget for managing layer order with drag-and-drop and button controls."""
    
    # Signal emitted when layer order changes
    layer_order_changed = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layer_order = []  # List of layer indices in current order
        self.layer_data = []   # List of layer information
        self._initialized = False  # Flag to prevent reinitialization
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel("Layer Order")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(title_label)
        
        # Layer list
        self.layer_list = QListWidget()
        self.layer_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.layer_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.layer_list.setMinimumHeight(150)
        self.layer_list.setMaximumHeight(200)
        self.layer_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e0e0e0;
            }
        """)
        layout.addWidget(self.layer_list)
        
        # Button controls
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        self.move_up_btn = QPushButton("↑ Move Up")
        self.move_up_btn.setFixedWidth(80)
        self.move_up_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        self.move_down_btn = QPushButton("↓ Move Down")
        self.move_down_btn.setFixedWidth(80)
        self.move_down_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        button_layout.addWidget(self.move_up_btn)
        button_layout.addWidget(self.move_down_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.move_up_btn.clicked.connect(self.move_layer_up)
        self.move_down_btn.clicked.connect(self.move_layer_down)
        self.layer_list.itemSelectionChanged.connect(self.update_button_states)
        
        # Connect drag-drop signal after model is initialized
        model = self.layer_list.model()
        if model is not None:
            model.rowsMoved.connect(self.on_layer_reordered)
        
        # Override drag behavior to prevent background layer movement
        self.layer_list.dropEvent = self.custom_drop_event
        
        # Initial button states
        self.update_button_states()
        
    def set_layers(self, layer_data):
        """
        Set the layers to be managed.
        
        Args:
            layer_data: List of dictionaries with layer information
                       Each dict should have: 'id', 'name', 'enabled', 'type'
        """
        self.layer_data = layer_data
        
        # Only initialize order if not initialized yet or if layer count changed
        if not self._initialized or len(self.layer_order) != len(layer_data):
            # Create initial order with background at bottom
            background_idx = None
            other_layers = []
            
            for i, layer in enumerate(layer_data):
                if layer.get('type') == 'background':
                    background_idx = i
                else:
                    other_layers.append(i)
            
            # Create order with background at bottom, others in sequence
            if background_idx is not None:
                self.layer_order = [background_idx] + other_layers
            else:
                self.layer_order = list(range(len(layer_data)))
                
            self._initialized = True
            
        self.update_layer_display()
        
    def update_layer_display(self):
        """Update the layer list display."""
        self.layer_list.clear()
        
        if not self.layer_data:
            # No layers available
            item = QListWidgetItem("No layers available")
            item.setForeground(Qt.GlobalColor.gray)
            self.layer_list.addItem(item)
            self.update_button_states()
            return
        
        # Display layers in visual order (first at bottom, last at top)
        visual_order = self.layer_order[::-1]  # Reverse for visual display
        
        for i, layer_idx in enumerate(visual_order):
            if layer_idx < len(self.layer_data):
                layer = self.layer_data[layer_idx]
                # Show visual position (bottom to top)
                visual_pos = len(visual_order) - i
                item_text = f"{visual_pos}. {layer['name']}"
                if not layer.get('enabled', True):
                    item_text += " (disabled)"
                    
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, layer_idx)
                
                # Set item color based on enabled state
                if not layer.get('enabled', True):
                    item.setForeground(Qt.GlobalColor.gray)
                
                # Make background layer non-movable
                if layer.get('type') == 'background':
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    item.setForeground(Qt.GlobalColor.darkGray)
                    item.setBackground(Qt.GlobalColor.lightGray)
                    item_text = f"🔒 {layer['name']} (Background - Fixed)"
                    item.setText(item_text)
                    
                self.layer_list.addItem(item)
        
        # Add helpful message if no layers are enabled
        enabled_count = sum(1 for layer in self.layer_data if layer.get('enabled', True))
        if enabled_count == 0:
            help_item = QListWidgetItem("💡 Tip: Enable some overlays in the main window to see them here")
            help_item.setForeground(Qt.GlobalColor.blue)
            help_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Make it non-selectable
            self.layer_list.addItem(help_item)
                
        self.update_button_states()
        
    def on_layer_reordered(self, parent, start, end, destination, row):
        """Handle when layers are reordered via drag-and-drop."""
        # Update the layer order based on the new list order
        new_order = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item is not None:
                layer_idx = item.data(Qt.ItemDataRole.UserRole)
                new_order.append(layer_idx)
            
        # Convert visual order to internal order (reverse it)
        # Visual order shows top-to-bottom, internal order is bottom-to-top
        self.layer_order = new_order[::-1]
            
        self.update_layer_display()
        self.layer_order_changed.emit(self.layer_order)
        
    def move_layer_up(self):
        """Move the selected layer up in the list."""
        current_row = self.layer_list.currentRow()
        if current_row > 0:
            # Get the visual order (reversed from layer_order)
            visual_order = self.layer_order[::-1]
            
            # Check if current item is background layer
            if current_row < len(visual_order):
                current_layer_idx = visual_order[current_row]
                if (current_layer_idx < len(self.layer_data) and 
                    self.layer_data[current_layer_idx].get('type') == 'background'):
                    return  # Don't move background layer
            
            # Check if previous item is background layer
            if current_row - 1 < len(visual_order):
                prev_layer_idx = visual_order[current_row - 1]
                if (prev_layer_idx < len(self.layer_data) and 
                    self.layer_data[prev_layer_idx].get('type') == 'background'):
                    return  # Don't move over background layer
            
            # Swap in visual order
            visual_order[current_row], visual_order[current_row - 1] = \
                visual_order[current_row - 1], visual_order[current_row]
            
            # Convert back to layer_order
            self.layer_order = visual_order[::-1]
            
            self.update_layer_display()
            self.layer_list.setCurrentRow(current_row - 1)
            self.layer_order_changed.emit(self.layer_order)
            
    def move_layer_down(self):
        """Move the selected layer down in the list."""
        current_row = self.layer_list.currentRow()
        visual_order = self.layer_order[::-1]
        
        if current_row < len(visual_order) - 1:
            # Check if current item is background layer
            if current_row < len(visual_order):
                current_layer_idx = visual_order[current_row]
                if (current_layer_idx < len(self.layer_data) and 
                    self.layer_data[current_layer_idx].get('type') == 'background'):
                    return  # Don't move background layer
            
            # Check if next item is background layer
            if current_row + 1 < len(visual_order):
                next_layer_idx = visual_order[current_row + 1]
                if (next_layer_idx < len(self.layer_data) and 
                    self.layer_data[next_layer_idx].get('type') == 'background'):
                    return  # Don't move over background layer
            
            # Swap in visual order
            visual_order[current_row], visual_order[current_row + 1] = \
                visual_order[current_row + 1], visual_order[current_row]
            
            # Convert back to layer_order
            self.layer_order = visual_order[::-1]
            
            self.update_layer_display()
            self.layer_list.setCurrentRow(current_row + 1)
            self.layer_order_changed.emit(self.layer_order)
            
    def update_button_states(self):
        """Update the enabled state of move buttons."""
        current_row = self.layer_list.currentRow()
        self.move_up_btn.setEnabled(bool(current_row > 0))
        self.move_down_btn.setEnabled(bool(current_row >= 0 and current_row < len(self.layer_order) - 1))
        
    def get_ordered_layers(self):
        """Get the layers in their current order."""
        return [self.layer_data[i] for i in self.layer_order if i < len(self.layer_data)]
        
    def get_layer_order(self):
        """Get the current layer order as a list of indices."""
        return self.layer_order.copy()
    
    def custom_drop_event(self, event):
        """Custom drop event to prevent background layer movement."""
        # Get the source row
        source_row = self.layer_list.currentRow()
        
        # Get the visual order (reversed from layer_order)
        visual_order = self.layer_order[::-1]
        
        # Check if source is background layer
        if (source_row >= 0 and source_row < len(visual_order) and
            visual_order[source_row] < len(self.layer_data) and
            self.layer_data[visual_order[source_row]].get('type') == 'background'):
            # Don't allow background layer to be moved
            event.ignore()
            return
        
        # Allow normal drop behavior for other layers
        # The background layer protection will be handled in on_layer_reordered
        QListWidget.dropEvent(self.layer_list, event) 