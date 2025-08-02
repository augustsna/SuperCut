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
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut, QDesktopServices
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
from src.config import get_template_categories, save_template, delete_template, load_template
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
        self.setFixedSize(590, 610)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header with title and buttons
        header_layout = QHBoxLayout()
        title_label = QLabel("Template Manager")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        
        self.new_template_btn = QPushButton("New")
        self.new_template_btn.setFixedWidth(70)
        self.new_template_btn.setFixedHeight(30)
        self.import_btn = QPushButton("Import")
        self.import_btn.setFixedWidth(75)
        self.import_btn.setFixedHeight(30)
        self.export_btn = QPushButton("Export")
        self.export_btn.setFixedWidth(70)
        self.export_btn.setFixedHeight(30)

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
        self.new_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                border: 2px solid #47a4ff;
            }
        """)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                border: 2px solid #47a4ff;
            }
        """)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                border: 2px solid #47a4ff;
            }
        """)

        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.new_template_btn)
        header_layout.addWidget(self.import_btn)
        header_layout.addWidget(self.export_btn)

        
        layout.addLayout(header_layout)
        
        # Main content area with two panels
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel: Template list and filters
        left_panel = self.create_left_panel()
        left_panel.setFixedWidth(260)
        main_layout.addWidget(left_panel)
        
        # Center panel: Template preview and details
        center_panel = self.create_center_panel()
        main_layout.addWidget(center_panel)
        
        layout.addWidget(main_widget)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setFixedWidth(70)
        self.apply_btn.setFixedHeight(30)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setFixedWidth(70)
        self.edit_btn.setFixedHeight(30)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setFixedWidth(80)
        self.delete_btn.setFixedHeight(30)
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedWidth(70)
        self.close_btn.setFixedHeight(30)
        
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
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                border: 2px solid #47a4ff;
            }
        """)
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
        self.template_list.setMaximumHeight(320)
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
        self.template_resources_btn = QPushButton("")
        self.template_reference_btn = QPushButton("")
        
        # Style settings labels with same style as template details
        for label in [self.resolution_label, self.fps_label, self.codec_label, 
                     self.preset_label, self.audio_bitrate_label, self.video_bitrate_label,
                     self.maxrate_label, self.bufsize_label]:
            label.setStyleSheet(label_style)
            label.setFixedWidth(160)
            label.setFixedHeight(26)
        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(71, 164, 255, 0.2);
                border: 1px solid #47a4ff;
                color: #000;
            }
        """
        self.template_resources_btn.setStyleSheet(button_style)
        self.template_resources_btn.setFixedWidth(160)
        self.template_resources_btn.setFixedHeight(26)
        self.template_reference_btn.setStyleSheet(button_style)
        self.template_reference_btn.setFixedWidth(160)
        self.template_reference_btn.setFixedHeight(26)
        
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
        
        resources_name_label = QLabel("Resources:")
        resources_name_label.setFixedWidth(90)
        resources_name_label.setFixedHeight(25)
        
        reference_name_label = QLabel("Reference:")
        reference_name_label.setFixedWidth(90)
        reference_name_label.setFixedHeight(25)
        
        settings_layout.addRow(resolution_name_label, self.resolution_label)
        settings_layout.addRow(fps_name_label, self.fps_label)
        settings_layout.addRow(codec_name_label, self.codec_label)
        settings_layout.addRow(preset_name_label, self.preset_label)
        settings_layout.addRow(audio_bitrate_name_label, self.audio_bitrate_label)
        settings_layout.addRow(video_bitrate_name_label, self.video_bitrate_label)
        settings_layout.addRow(maxrate_name_label, self.maxrate_label)
        settings_layout.addRow(bufsize_name_label, self.bufsize_label)
        settings_layout.addRow(resources_name_label, self.template_resources_btn)
        settings_layout.addRow(reference_name_label, self.template_reference_btn)
        
        center_layout.addWidget(settings_group)
        
        center_layout.addStretch()
        
        return center_widget
        

        
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
        
        # Update resources and reference buttons
        resources_url = template_data.get('resources', 'https://iconsna.xyz/')
        reference_url = template_data.get('reference', 'https://youtube.com/')
        
        self.template_resources_btn.setText(resources_url)
        self.template_reference_btn.setText(reference_url)
        
        # Connect button clicks to open URLs
        self.template_resources_btn.clicked.disconnect() if self.template_resources_btn.receivers(self.template_resources_btn.clicked) > 0 else None
        self.template_reference_btn.clicked.disconnect() if self.template_reference_btn.receivers(self.template_reference_btn.clicked) > 0 else None
        
        self.template_resources_btn.clicked.connect(lambda: self.open_url(resources_url))
        self.template_reference_btn.clicked.connect(lambda: self.open_url(reference_url))
        

        
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
        
    def open_url(self, url: str):
        """Open URL in default browser"""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open URL: {url}\nError: {str(e)}")
            
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
        """Edit the selected template JSON file"""
        if not self.selected_template:
            return
            
        template_name = self.selected_template.get('name', 'Unknown')
        template_filename = template_name.lower().replace(' ', '_')
        
        # Load the current template data
        from src.config import load_template
        template_data = load_template(template_filename)
        
        if not template_data:
            QMessageBox.warning(self, "Error", f"Could not load template '{template_name}'")
            return
        
        # Create edit dialog
        edit_dialog = TemplateEditDialog(self, template_data, template_filename)
        if edit_dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload templates to reflect changes
            self.load_templates()
            # Update preview if this template is still selected
            if self.selected_template and self.selected_template.get('name') == template_name:
                self.selected_template = template_data
                self.update_template_preview(template_data)
        
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
                pass  # Success - no dialog needed
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export template.")


class TemplateEditDialog(QDialog):
    """Dialog for editing template JSON files"""
    
    def __init__(self, parent=None, template_data=None, template_filename=None):
        super().__init__(parent)
        self.template_data = template_data or {}
        self.template_filename = template_filename
        self.original_data = template_data.copy() if template_data else {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Template Editor")
        self.setModal(True)
        self.setFixedSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"{self.template_data.get('name', 'Unknown')}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # JSON Editor
        self.json_editor = QTextEdit()
        self.json_editor.setFont(QFont("Consolas", 10))
        self.json_editor.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        
        # Load current JSON data
        import json
        try:
            json_text = json.dumps(self.template_data, indent=2, ensure_ascii=False)
            self.json_editor.setPlainText(json_text)
        except Exception as e:
            self.json_editor.setPlainText(f"Error formatting JSON: {e}")
        
        layout.addWidget(self.json_editor)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedWidth(80)
        self.save_btn.setFixedHeight(30)
        self.save_btn.setStyleSheet("""
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
        """)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setFixedHeight(30)
        self.cancel_btn.setStyleSheet("""
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
        """)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedWidth(80)
        self.reset_btn.setFixedHeight(30)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                border: 2px solid #47a4ff;
            }
        """)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addSpacing(60)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.save_btn.clicked.connect(self.save_template)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self.reset_to_original)
        
        # Add keyboard shortcuts
        self.add_keyboard_shortcuts()
        
    def save_template(self):
        """Save the edited template"""
        try:
            # Parse JSON from editor
            json_text = self.json_editor.toPlainText()
            import json
            new_template_data = json.loads(json_text)
            
            # Validate the JSON structure
            if not isinstance(new_template_data, dict):
                QMessageBox.warning(self, "Invalid JSON", "Template data must be a JSON object.")
                return
                
            if 'name' not in new_template_data:
                QMessageBox.warning(self, "Invalid Template", "Template must have a 'name' field.")
                return
            
            # Check if name has changed
            new_name = new_template_data.get('name', '')
            old_name = self.template_data.get('name', '')
            
            if new_name != old_name:
                # Name has changed, need to update filename
                new_filename = new_name.lower().replace(' ', '_')
                old_filename = self.template_filename
                
                # Delete old file if it exists
                from src.config import delete_template
                delete_template(old_filename)
                
                # Update filename for saving
                self.template_filename = new_filename
                
                # Update the template data
                self.template_data = new_template_data
                self.original_data = new_template_data.copy()
                
                # Update dialog title
                self.setWindowTitle("Template Editor")
                self.findChild(QLabel).setText(new_name)
            
            # Save the template with new filename
            if save_template(new_template_data, self.template_filename):
                self.template_data = new_template_data
                self.accept()
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save template.")
                
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "Invalid JSON", f"JSON syntax error: {e}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving template: {e}")
    
    def reset_to_original(self):
        """Reset the editor to the original template data"""
        import json
        try:
            json_text = json.dumps(self.original_data, indent=2, ensure_ascii=False)
            self.json_editor.setPlainText(json_text)
        except Exception as e:
            QMessageBox.warning(self, "Reset Error", f"Error resetting to original: {e}")
    
    def add_keyboard_shortcuts(self):
        """Add keyboard shortcuts to the dialog"""
        # Ctrl+W to close dialog
        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(self.reject) 