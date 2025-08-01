#!/usr/bin/env python3
"""
Template Manager Dialog for SuperCut
Provides a visual interface for managing video templates
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
    QComboBox, QLineEdit, QTextEdit, QMessageBox, QFileDialog,
    QSplitter, QWidget, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtGui import QIcon, QPixmap, QFont
from typing import Dict, List, Optional, Any
import os

from src.template_utils import (
    get_available_templates,
    get_templates_by_category,
    get_template_by_name,
    create_template_from_current_settings,
    apply_template_to_settings,
    validate_template,
    export_template,
    import_template,
    get_template_preview_info
)
from src.config import get_template_categories, save_template, delete_template
from src.layer_manager import LayerManagerWidget

class TemplateManagerDialog(QDialog):
    """Dialog for managing video templates"""
    
    template_applied = pyqtSignal(dict)  # Emits template data when applied
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.current_settings = current_settings or {}
        self.selected_template = None
        self.init_ui()
        self.load_templates()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Template Manager")
        self.setModal(True)
        self.setFixedSize(850, 564)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header with title and buttons
        header_layout = QHBoxLayout()
        title_label = QLabel("Template Manager")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        self.new_template_btn = QPushButton("New Template")
        self.import_btn = QPushButton("Import")
        self.export_btn = QPushButton("Export")

        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            
        """
        self.new_template_btn.setStyleSheet(button_style)
        self.import_btn.setStyleSheet(button_style)
        self.export_btn.setStyleSheet(button_style)

        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.new_template_btn)
        header_layout.addWidget(self.import_btn)
        header_layout.addWidget(self.export_btn)

        
        layout.addLayout(header_layout)
        
        # Main content area with three fixed panels
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel: Template list and filters (270px fixed)
        left_panel = self.create_left_panel()
        left_panel.setFixedWidth(260)
        main_layout.addWidget(left_panel)
        
        # Center panel: Template preview and details (270px fixed)
        center_panel = self.create_center_panel()
        center_panel.setFixedWidth(300)
        main_layout.addWidget(center_panel)
        
        # Right panel: Additional details (270px fixed)
        right_panel = self.create_right_panel()
        right_panel.setFixedWidth(260)
        main_layout.addWidget(right_panel)
        
        layout.addWidget(main_widget)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.edit_btn = QPushButton("Edit Template")
        self.delete_btn = QPushButton("Delete Template")
        self.close_btn = QPushButton("Close")
        
        # Style bottom buttons
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }

        """)
        self.edit_btn.setStyleSheet(button_style)
        self.close_btn.setStyleSheet(button_style)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                
                border: 2px solid #e24a4a;
            }
        """)
        
        button_layout.addSpacing(9)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addSpacing(5)
        
        # Connect signals
        self.new_template_btn.clicked.connect(self.create_new_template)
        self.import_btn.clicked.connect(self.import_template_file)
        self.export_btn.clicked.connect(self.export_template_file)

        self.apply_btn.clicked.connect(self.apply_selected_template)
        self.edit_btn.clicked.connect(self.edit_selected_template)

        self.delete_btn.clicked.connect(self.delete_selected_template)
        self.close_btn.clicked.connect(self.accept)
        
        # Add keyboard shortcuts
        self.add_keyboard_shortcuts()
        
        # Initial button states
        self.update_button_states()
        
    def create_left_panel(self):
        """Create the left panel with template list and filters"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Combined filters group
        filters_group = QGroupBox("Filters")
        filters_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        filters_layout = QVBoxLayout(filters_group)
        filters_layout.setContentsMargins(15, 12, 15, 17)
        filters_layout.setSpacing(10)
        
        # Search box (label and text input on same line)
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setFixedWidth(70)
        search_label.setFixedHeight(30)
        self.search_edit = QLineEdit()
        self.search_edit.setFixedWidth(125)
        self.search_edit.setFixedHeight(30)
        self.search_edit.setPlaceholderText("Search templates by name or description...")
        self.search_edit.textChanged.connect(self.filter_templates)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        filters_layout.addLayout(search_layout)

        # Add spacing between search and category
        filters_layout.addSpacing(6)

        # Category filter (label and dropdown on same line)
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setFixedWidth(70)
        category_label.setFixedHeight(30)
        self.category_combo = QComboBox()
        self.category_combo.setFixedWidth(125)
        self.category_combo.setFixedHeight(30)
        self.category_combo.addItem("All Categories", "all")
        
        # Load categories
        categories = get_template_categories()
        for category_id, category_info in categories.get('categories', {}).items():
            icon = category_info.get('icon', '')
            name = category_info.get('name', category_id)
            self.category_combo.addItem(f"{icon} {name}", category_id)
        
        self.category_combo.currentTextChanged.connect(self.filter_templates)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        
        filters_layout.addLayout(category_layout)
        
        # Advanced filters
        # Resolution filter (first line)
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Resolution:")
        resolution_label.setFixedWidth(70)
        resolution_label.setFixedHeight(30)
        self.resolution_filter = QComboBox()
        self.resolution_filter.setFixedWidth(120)
        self.resolution_filter.setFixedHeight(30)
        self.resolution_filter.addItem("All Resolutions", "")
        self.resolution_filter.addItem("1080p", "1920x1080")
        self.resolution_filter.addItem("720p", "1280x720")
        self.resolution_filter.addItem("4K", "3840x2160")
        self.resolution_filter.currentTextChanged.connect(self.filter_templates)
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_filter)
        #filters_layout.addLayout(resolution_layout)
        
        # FPS filter (second line)
        fps_layout = QHBoxLayout()
        fps_label = QLabel("FPS:")
        fps_label.setFixedWidth(70)
        fps_label.setFixedHeight(30)
        self.fps_filter = QComboBox()
        self.fps_filter.setFixedWidth(120)
        self.fps_filter.setFixedHeight(30)
        self.fps_filter.addItem("All FPS", "")
        self.fps_filter.addItem("24 FPS", "24")
        self.fps_filter.addItem("30 FPS", "30")
        self.fps_filter.addItem("60 FPS", "60")
        self.fps_filter.currentTextChanged.connect(self.filter_templates)
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_filter)       
        left_layout.addWidget(filters_group)
        
        # Add spacing between filters and templates
        left_layout.addSpacing(10)
        
        # Template list
        list_group = QGroupBox("Templates")
        list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        
        self.template_list = QListWidget()
        self.template_list.setFixedWidth(230)
        self.template_list.setMaximumHeight(250)
        self.template_list.itemClicked.connect(self.on_template_selected)
        self.template_list.setStyleSheet("""
            QListWidget {
                background-color: #f5f7fa;                
                padding: 6px;
                border: none;
                border-radius: 2px;
                color: #333;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin: 2px;
                background-color: #ffffff;
                outline: none;
                color: #333;
                height: 10px;
            }
            QListWidget::item:first-child {
                margin-top: 4px;
            }
            QListWidget::item:last-child {
                margin-bottom: 4px;
                margin-top: 2px;
            }
            QListWidget::item:selected {                
                background-color: #ffffff;
                border: 2px solid #47a4ff;
                color: #000000;                
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #ffffff;
                border: 2px solid #47a4ff;
                color: #000000;
                outline: none;
            }
            QListWidget::item:focus {
                outline: none;
            }
            QListWidget::item:selected:focus {
                outline: none;
            }
            QListWidget::item:selected:active {
                outline: none;
            }
            QListWidget::item:selected:!focus {
                outline: none;
            }
            QListWidget::item:selected:!active {
                outline: none;
            }
            QListWidget::item:selected:!hover {
                outline: none;
            }
            QScrollBar:vertical {
                background: rgba(240, 240, 240, 0.8);
                width: 12px;
                border-radius: 4px;
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
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(5, 0, 0, 0)
        list_layout.setSpacing(0)
        list_layout.addWidget(self.template_list)
        left_layout.addWidget(list_group)
        
        return left_widget
        
    def create_center_panel(self):
        """Create the center panel with template preview and details"""
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        
        # Template details
        details_group = QGroupBox("Template Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        details_layout = QFormLayout(details_group)
        
        self.template_name_label = QLabel("")
        self.template_desc_label = QLabel("")
        self.template_category_label = QLabel("")
        
        # Style labels
        label_style = "QLabel { padding: 4px; background-color: #ffffff; border-radius: 4px; border: 1px solid #cccccc; }"
        self.template_name_label.setStyleSheet(label_style)
        self.template_name_label.setFixedWidth(160)
        self.template_name_label.setFixedHeight(25)
        self.template_desc_label.setStyleSheet(label_style)
        self.template_desc_label.setFixedWidth(160)
        self.template_desc_label.setFixedHeight(25)
        self.template_category_label.setStyleSheet(label_style)
        self.template_category_label.setFixedWidth(160)
        self.template_category_label.setFixedHeight(25)
        
        # Create individual labels for each field
        name_label = QLabel("Name:")
        name_label.setFixedWidth(90)
        name_label.setFixedHeight(25)
        
        desc_label = QLabel("Description:")
        desc_label.setFixedWidth(90)
        desc_label.setFixedHeight(25)
        
        category_label = QLabel("Category:")
        category_label.setFixedWidth(90)
        category_label.setFixedHeight(25)
        
        details_layout.addRow(name_label, self.template_name_label)
        details_layout.addRow(desc_label, self.template_desc_label)
        details_layout.addRow(category_label, self.template_category_label)
        
        center_layout.addWidget(details_group)

        center_layout.addSpacing(10)
        
        # Video settings preview
        settings_group = QGroupBox("Video Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        settings_layout = QFormLayout(settings_group)
        
        self.resolution_label = QLabel("")
        self.fps_label = QLabel("")
        self.codec_label = QLabel("")
        self.preset_label = QLabel("")
        self.audio_bitrate_label = QLabel("")
        self.video_bitrate_label = QLabel("")
        self.maxrate_label = QLabel("")
        self.bufsize_label = QLabel("")
        
        # Style settings labels with same style as template details
        for label in [self.resolution_label, self.fps_label, self.codec_label, 
                     self.preset_label, self.audio_bitrate_label, self.video_bitrate_label,
                     self.maxrate_label, self.bufsize_label]:
            label.setStyleSheet(label_style)
            label.setFixedWidth(160)
            label.setFixedHeight(26)
        
        # Create individual labels for video settings fields
        resolution_name_label = QLabel("Resolution:")
        resolution_name_label.setFixedWidth(90)
        resolution_name_label.setFixedHeight(25)
        
        fps_name_label = QLabel("FPS:")
        fps_name_label.setFixedWidth(90)
        fps_name_label.setFixedHeight(25)
        
        codec_name_label = QLabel("Codec:")
        codec_name_label.setFixedWidth(90)
        codec_name_label.setFixedHeight(25)
        
        preset_name_label = QLabel("Preset:")
        preset_name_label.setFixedWidth(90)
        preset_name_label.setFixedHeight(25)
        
        audio_bitrate_name_label = QLabel("Audio Bitrate:")
        audio_bitrate_name_label.setFixedWidth(90)
        audio_bitrate_name_label.setFixedHeight(25)
        
        video_bitrate_name_label = QLabel("Video Bitrate:")
        video_bitrate_name_label.setFixedWidth(90)
        video_bitrate_name_label.setFixedHeight(25)
        
        maxrate_name_label = QLabel("Maxrate:")
        maxrate_name_label.setFixedWidth(90)
        maxrate_name_label.setFixedHeight(25)
        
        bufsize_name_label = QLabel("Bufsize:")
        bufsize_name_label.setFixedWidth(90)
        bufsize_name_label.setFixedHeight(25)
        
        settings_layout.addRow(resolution_name_label, self.resolution_label)
        settings_layout.addRow(fps_name_label, self.fps_label)
        settings_layout.addRow(codec_name_label, self.codec_label)
        settings_layout.addRow(preset_name_label, self.preset_label)
        settings_layout.addRow(audio_bitrate_name_label, self.audio_bitrate_label)
        settings_layout.addRow(video_bitrate_name_label, self.video_bitrate_label)
        settings_layout.addRow(maxrate_name_label, self.maxrate_label)
        settings_layout.addRow(bufsize_name_label, self.bufsize_label)
        
        center_layout.addWidget(settings_group)
        
        center_layout.addStretch()
        
        return center_widget
        
    def create_right_panel(self):
        """Create the right panel with layer preview and visual icons"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Layer Preview with Visual Icons
        layer_preview_group = QGroupBox("Layer Preview")
        layer_preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        layer_preview_layout = QVBoxLayout(layer_preview_group)
        
        # Create layer preview widget
        self.layer_preview_widget = QWidget()
        self.layer_preview_widget.setMinimumHeight(300)
        self.layer_preview_widget.setMaximumHeight(400)
        
        # Layer preview layout
        self.layer_preview_layout = QVBoxLayout(self.layer_preview_widget)
        self.layer_preview_layout.setSpacing(2)
        self.layer_preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add placeholder text
        self.layer_preview_placeholder = QLabel("Select a template to view layer preview")
        self.layer_preview_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_preview_placeholder.setStyleSheet("""
            QLabel {
                color: #999999;
                font-style: italic;
                padding: 20px;
            }
        """)
        self.layer_preview_layout.addWidget(self.layer_preview_placeholder)
        
        layer_preview_layout.addWidget(self.layer_preview_widget)
        right_layout.addWidget(layer_preview_group)
        
        right_layout.addStretch()
        
        return right_widget
        
    def add_keyboard_shortcuts(self):
        """Add keyboard shortcuts to the dialog"""
        # Ctrl+W to close the dialog
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.accept)
        
    def load_templates(self):
        """Load all available templates"""
        self.templates = get_available_templates()
        self.filter_templates()
        
    def filter_templates(self):
        """Filter templates based on category, search, and advanced filters"""
        self.template_list.clear()
        
        selected_category = self.category_combo.currentData()
        search_text = self.search_edit.text().lower()
        selected_resolution = self.resolution_filter.currentData()
        selected_fps = self.fps_filter.currentData()
        
        for template in self.templates:
            # Filter by category
            if selected_category != "all" and template.get('category', '') != selected_category:
                continue
                
            # Filter by search text
            template_name = template.get('name', '').lower()
            template_desc = template.get('description', '').lower()
            if search_text and search_text not in template_name and search_text not in template_desc:
                continue
                
            # Filter by resolution
            if selected_resolution:
                video_settings = template.get('video_settings', {})
                template_resolution = video_settings.get('resolution', '')
                if template_resolution != selected_resolution:
                    continue
                    
            # Filter by FPS
            if selected_fps:
                video_settings = template.get('video_settings', {})
                template_fps = str(video_settings.get('fps', ''))
                if template_fps != selected_fps:
                    continue
                    

                
            # Add to list
            item = QListWidgetItem()
            template_name = template.get('name', 'Unknown Template')
            
            item.setText(template_name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            
            # Add category icon
            categories = get_template_categories()
            category_info = categories.get('categories', {}).get(template.get('category', ''), {})
            icon = category_info.get('icon', '')
            if icon:
                item.setText(f"{icon} {template_name}")
            
            self.template_list.addItem(item)
            
    def on_template_selected(self, item):
        """Handle template selection"""
        template_data = item.data(Qt.ItemDataRole.UserRole)
        self.selected_template = template_data
        self.update_template_preview(template_data)
        self.update_button_states()
        
    def update_template_preview(self, template_data):
        """Update the template preview with selected template data"""
        if not template_data:
            return
            
        # Update basic info
        self.template_name_label.setText(template_data.get('name', 'Unknown'))
        self.template_desc_label.setText(template_data.get('description', 'No description'))
        
        # Get category info
        categories = get_template_categories()
        category_info = categories.get('categories', {}).get(template_data.get('category', ''), {})
        category_name = category_info.get('name', template_data.get('category', 'Unknown'))
        category_icon = category_info.get('icon', '')
        self.template_category_label.setText(f"{category_icon} {category_name}")
        

        
        # Update video settings
        video_settings = template_data.get('video_settings', {})
        self.resolution_label.setText(video_settings.get('resolution', 'Unknown'))
        self.fps_label.setText(str(video_settings.get('fps', 'Unknown')))
        self.codec_label.setText(video_settings.get('codec', 'Unknown'))
        self.preset_label.setText(video_settings.get('preset', 'Unknown'))
        self.audio_bitrate_label.setText(video_settings.get('audio_bitrate', 'Unknown'))
        self.video_bitrate_label.setText(video_settings.get('video_bitrate', 'Unknown'))
        self.maxrate_label.setText(video_settings.get('maxrate', 'Unknown'))
        self.bufsize_label.setText(video_settings.get('bufsize', 'Unknown'))
        

        
        # Update layer preview with visual icons
        self.update_layer_preview(template_data)
    
    def update_layer_preview(self, template_data):
        """Update the layer preview with compact design"""
        # Clear existing layer preview (but preserve placeholder)
        for i in reversed(range(self.layer_preview_layout.count())):
            child = self.layer_preview_layout.itemAt(i).widget()
            if child and child != self.layer_preview_placeholder:
                child.deleteLater()
        
        # Hide placeholder
        if hasattr(self, 'layer_preview_placeholder') and self.layer_preview_placeholder:
            self.layer_preview_placeholder.hide()
        
        # Get layer data
        layer_order = template_data.get('layer_order', [])
        layer_settings = template_data.get('layer_settings', {})
        
        # Create layer preview items
        for i, layer_id in enumerate(layer_order):
            # Get layer state
            layer_config = layer_settings.get(layer_id, {})
            enabled = layer_config.get('enabled', True)
            
            # Create layer item widget
            layer_item = QWidget()
            layer_item.setFixedHeight(28)
            layer_item.setStyleSheet(f"""
                QWidget {{
                    background-color: {'#f8fff8' if enabled else '#fff8f8'};
                    border: 1px solid {'#4CAF50' if enabled else '#f44336'};
                    border-radius: 3px;
                    margin: 1px;
                }}
            """)
            
            # Layer item layout
            item_layout = QHBoxLayout(layer_item)
            item_layout.setContentsMargins(6, 2, 6, 2)
            item_layout.setSpacing(6)
            
            # Layer number (smaller)
            number_label = QLabel(f"{len(layer_order) - i}")
            number_label.setFixedWidth(18)
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number_label.setStyleSheet("""
                QLabel {
                    background-color: #555555;
                    color: white;
                    border-radius: 9px;
                    font-weight: bold;
                    font-size: 9px;
                }
            """)
            
            # Layer name (compact)
            name_label = QLabel(layer_id.replace('_', ' ').title())
            name_label.setStyleSheet(f"""
                QLabel {{
                    color: {'#2E7D32' if enabled else '#C62828'};
                    font-weight: bold;
                    font-size: 10px;
                }}
            """)
            
            # Status indicator (smaller)
            status_label = QLabel("●" if enabled else "○")
            status_label.setFixedWidth(12)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet(f"""
                QLabel {{
                    color: {'#4CAF50' if enabled else '#f44336'};
                    font-weight: bold;
                    font-size: 10px;
                }}
            """)
            
            # Add widgets to layout
            item_layout.addWidget(number_label)
            item_layout.addWidget(name_label)
            item_layout.addStretch()
            item_layout.addWidget(status_label)
            
            # Add layer item to preview
            self.layer_preview_layout.addWidget(layer_item)
        
        # Add stretch to push items to top
        self.layer_preview_layout.addStretch()
            
    def update_button_states(self):
        """Update button enabled states based on selection"""
        has_selection = self.selected_template is not None
        self.apply_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)

        self.delete_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)
        

        
    def create_new_template(self):
        """Create a new template from current settings"""
        if not self.current_settings:
            QMessageBox.warning(self, "No Settings", "No current settings available to create template from.")
            return
            
        # Create a simple dialog for template details
        from PyQt6.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Template")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Enter template name")
        
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(80)
        desc_edit.setPlaceholderText("Enter template description")
        
        category_combo = QComboBox()
        categories = get_template_categories()
        for category_id, category_info in categories.get('categories', {}).items():
            icon = category_info.get('icon', '')
            name = category_info.get('name', category_id)
            category_combo.addItem(f"{icon} {name}", category_id)
        
        form_layout.addRow("Name:", name_edit)
        form_layout.addRow("Description:", desc_edit)
        form_layout.addRow("Category:", category_combo)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            description = desc_edit.toPlainText().strip()
            category = category_combo.currentData()
            
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Template name cannot be empty.")
                return
                
            # Create template
            template_data = create_template_from_current_settings(name, description, category, self.current_settings)
            
            # Save template
            template_name = name.lower().replace(' ', '_')
            if save_template(template_data, template_name):
                QMessageBox.information(self, "Success", f"Template '{name}' created successfully!")
                self.load_templates()
            else:
                QMessageBox.warning(self, "Error", "Failed to create template.")
                
    def apply_selected_template(self):
        """Apply the selected template to current settings"""
        if not self.selected_template:
            return
            
        # Emit the template data for the parent to handle
        self.template_applied.emit(self.selected_template)
        # Close the dialog after applying
        self.accept()
        
    def edit_selected_template(self):
        """Edit the selected template - temporarily disabled"""
        if not self.selected_template:
            return
            
        # Temporary: Show message that edit dialog is disabled
        QMessageBox.information(
            self, 
            "Edit Template", 
            f"Edit dialog for template '{self.selected_template.get('name', 'Unknown')}' is temporarily disabled.\n\n"
            "The edit functionality will be restored in a future update."
        )
                

        
    def delete_selected_template(self):
        """Delete the selected template"""
        if not self.selected_template:
            return
            
        template_name = self.selected_template.get('name', 'Unknown')
        reply = QMessageBox.question(
            self, 
            "Delete Template", 
            f"Are you sure you want to delete template '{template_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            template_filename = template_name.lower().replace(' ', '_')
            if delete_template(template_filename):
                QMessageBox.information(self, "Success", f"Template '{template_name}' deleted successfully!")
                self.load_templates()
                self.selected_template = None
                self.update_template_preview(None)
                self.update_button_states()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete template.")
                
    def import_template_file(self):
        """Import a template from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Import Template", 
            "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            success, message = import_template(file_path)
            if success:
                QMessageBox.information(self, "Success", message)
                self.load_templates()
            else:
                QMessageBox.warning(self, "Import Error", message)
                
    def export_template_file(self):
        """Export the selected template to a file"""
        if not self.selected_template:
            return
            
        template_name = self.selected_template.get('name', 'Unknown')
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Template", 
            f"{template_name}.json", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if export_template(template_name, file_path):
                QMessageBox.information(self, "Success", f"Template exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export template.") 