from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox
from PyQt6.QtCore import Qt
from src.ui_components import ImageDropLineEdit
import os
from src.config import DEFAULT_MIN_MP3_COUNT, PROJECT_ROOT
from PyQt6.QtGui import QIntValidator

# This module manages the creation and logic for intro and overlay controls.
def create_intro_overlay_controls(parent):
    """
    Create and return all intro and overlay controls as a dict.
    This function is meant to be called from SuperCutUI.__init__ or init_ui.
    All event handlers and state logic are encapsulated here.
    """
    controls = {}
    # --- INTRO OVERLAY CONTROLS ---
    intro_layout = QHBoxLayout()
    intro_layout.setSpacing(4)
    intro_checkbox = QCheckBox(" Intro :")
    intro_checkbox.setFixedWidth(70)
    intro_checkbox.setChecked(True)
    intro_edit = ImageDropLineEdit()
    intro_edit.setPlaceholderText("Intro image path (*.gif, *.png)")
    intro_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
    intro_edit.setFixedWidth(125)
    intro_path = ""
    def on_intro_changed():
        nonlocal intro_path
        intro_path = intro_edit.text().strip()
    intro_edit.textChanged.connect(on_intro_changed)
    intro_btn = QPushButton("Select")
    intro_btn.setFixedWidth(60)
    def select_intro_image():
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(parent, "Select Intro Image", "", "Image Files (*.gif *.png)")
        if file_path:
            intro_edit.setText(file_path)
    intro_btn.clicked.connect(select_intro_image)
    intro_size_label = QLabel("S:")
    intro_size_label.setFixedWidth(18)
    intro_size_combo = QComboBox()
    intro_size_combo.setFixedWidth(90)
    for percent in range(5, 101, 5):
        intro_size_combo.addItem(str(percent), percent)
    intro_size_combo.setCurrentIndex(1)  # Default 10%
    intro_size_percent = 10
    def on_intro_size_changed(idx):
        nonlocal intro_size_percent
        intro_size_percent = intro_size_combo.itemData(idx)
        if idx >= 0:
            intro_size_combo.setEditText(f"{intro_size_percent}%")
    intro_size_combo.setEditable(True)
    intro_line_edit = intro_size_combo.lineEdit()
    if intro_line_edit is not None:
        intro_line_edit.setReadOnly(True)
        intro_line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
    intro_size_combo.currentIndexChanged.connect(on_intro_size_changed)
    on_intro_size_changed(intro_size_combo.currentIndex())
    intro_position_label = QLabel("P:")
    intro_position_label.setFixedWidth(18)
    intro_position_combo = QComboBox()
    intro_position_combo.setFixedWidth(130)
    intro_positions = [
        ("Center", "center"),
        ("Top Left", "top_left"),
        ("Top Right", "top_right"),
        ("Bottom Left", "bottom_left"),
        ("Bottom Right", "bottom_right")
    ]
    for label, value in intro_positions:
        intro_position_combo.addItem(label, value)
    intro_position_combo.setCurrentIndex(0)
    intro_position = "center"
    def on_intro_position_changed(idx):
        nonlocal intro_position
        intro_position = intro_position_combo.itemData(idx)
    intro_position_combo.currentIndexChanged.connect(on_intro_position_changed)
    on_intro_position_changed(intro_position_combo.currentIndex())
    combo_width = 130
    intro_effect_label = QLabel("Intro:")
    intro_effect_label.setFixedWidth(40)
    intro_effect_combo = QComboBox()
    intro_effect_combo.setFixedWidth(combo_width)
    intro_effect_options = [
        ("Fade in & out", "fadeinout"),
        ("Fade in", "fadein"),
        ("Fade out", "fadeout"),
        ("Zoompan", "zoompan"),
        ("None", "none")
    ]
    for label, value in intro_effect_options:
        intro_effect_combo.addItem(label, value)
    intro_effect_combo.setCurrentIndex(0)
    intro_effect = "fadeinout"
    def on_intro_effect_changed(idx):
        nonlocal intro_effect
        intro_effect = intro_effect_combo.itemData(idx)
    intro_effect_combo.currentIndexChanged.connect(on_intro_effect_changed)
    on_intro_effect_changed(intro_effect_combo.currentIndex())
    intro_duration_label = QLabel("For (s): ")
    intro_duration_label.setFixedWidth(45)
    intro_duration_edit = QLineEdit("5")
    intro_duration_edit.setFixedWidth(40)
    intro_duration_edit.setValidator(QIntValidator(1, 999, parent))
    intro_duration_edit.setPlaceholderText("5")
    intro_duration = 5
    def on_intro_duration_changed():
        nonlocal intro_duration
        try:
            intro_duration = int(intro_duration_edit.text())
        except Exception:
            intro_duration = 5
    intro_duration_edit.textChanged.connect(on_intro_duration_changed)
    on_intro_duration_changed()
    def set_intro_enabled(state):
        enabled = state == Qt.CheckState.Checked
        intro_edit.setEnabled(enabled)
        intro_btn.setEnabled(enabled)
        intro_size_combo.setEnabled(enabled)
        intro_position_combo.setEnabled(enabled)
        intro_effect_combo.setEnabled(enabled)
        intro_duration_label.setEnabled(enabled)
        intro_duration_edit.setEnabled(enabled)
        if enabled:
            intro_btn.setStyleSheet("")
            intro_edit.setStyleSheet("")
            intro_size_combo.setStyleSheet("")
            intro_position_combo.setStyleSheet("")
            intro_effect_combo.setStyleSheet("")
            intro_duration_label.setStyleSheet("")
            intro_duration_edit.setStyleSheet("")
            intro_size_label.setStyleSheet("")
            intro_position_label.setStyleSheet("")
            intro_effect_label.setStyleSheet("")
        else:
            grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
            intro_btn.setStyleSheet(grey_btn_style)
            intro_edit.setStyleSheet(grey_btn_style)
            intro_size_combo.setStyleSheet(grey_btn_style)
            intro_position_combo.setStyleSheet(grey_btn_style)
            intro_effect_combo.setStyleSheet(grey_btn_style)
            intro_duration_label.setStyleSheet("color: grey;")
            intro_duration_edit.setStyleSheet(grey_btn_style)
            intro_size_label.setStyleSheet("color: grey;")
            intro_position_label.setStyleSheet("color: grey;")
            intro_effect_label.setStyleSheet("color: grey;")
    intro_checkbox.stateChanged.connect(lambda _: set_intro_enabled(intro_checkbox.checkState()))
    set_intro_enabled(intro_checkbox.checkState())
    intro_layout.addWidget(intro_checkbox)
    intro_layout.addSpacing(10)
    intro_layout.addWidget(intro_edit)
    intro_layout.addSpacing(4)
    intro_layout.addWidget(intro_btn)
    intro_layout.addSpacing(4)
    intro_layout.addWidget(intro_position_label)
    intro_layout.addSpacing(0)
    intro_layout.addWidget(intro_position_combo)
    intro_layout.addSpacing(6)
    intro_layout.addWidget(intro_size_label)
    intro_layout.addWidget(intro_size_combo)
    controls['intro_checkbox'] = intro_checkbox
    controls['intro_edit'] = intro_edit
    controls['intro_btn'] = intro_btn
    controls['intro_size_combo'] = intro_size_combo
    controls['intro_position_combo'] = intro_position_combo
    controls['intro_effect_combo'] = intro_effect_combo
    controls['intro_duration_edit'] = intro_duration_edit
    controls['intro_layout'] = intro_layout
    # --- OVERLAY 1 CONTROLS ---
    overlay1_layout = QHBoxLayout()
    overlay1_layout.setSpacing(4)
    overlay1_checkbox = QCheckBox("Overlay 1:")
    overlay1_checkbox.setFixedWidth(82)
    overlay1_checkbox.setChecked(True)
    overlay1_edit = ImageDropLineEdit()
    overlay1_edit.setPlaceholderText("Overlay 1 image path (*.gif, *.png)")
    overlay1_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
    overlay1_edit.setFixedWidth(125)
    overlay1_path = ""
    def on_overlay1_changed():
        nonlocal overlay1_path
        overlay1_path = overlay1_edit.text().strip()
    overlay1_edit.textChanged.connect(on_overlay1_changed)
    overlay1_btn = QPushButton("Select")
    overlay1_btn.setFixedWidth(60)
    def select_overlay1_image():
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(parent, "Select Overlay 1 Image", "", "Image Files (*.gif *.png)")
        if file_path:
            overlay1_edit.setText(file_path)
    overlay1_btn.clicked.connect(select_overlay1_image)
    overlay1_size_label = QLabel("S:")
    overlay1_size_label.setFixedWidth(18)
    overlay1_size_combo = QComboBox()
    overlay1_size_combo.setFixedWidth(90)
    for percent in range(5, 101, 5):
        overlay1_size_combo.addItem(str(percent), percent)
    overlay1_size_combo.setCurrentIndex(1)
    overlay1_size_percent = 10
    def on_overlay1_size_changed(idx):
        nonlocal overlay1_size_percent
        overlay1_size_percent = overlay1_size_combo.itemData(idx)
        if idx >= 0:
            overlay1_size_combo.setEditText(f"{overlay1_size_percent}%")
    overlay1_size_combo.setEditable(True)
    overlay1_line_edit = overlay1_size_combo.lineEdit()
    if overlay1_line_edit is not None:
        overlay1_line_edit.setReadOnly(True)
        overlay1_line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
    overlay1_size_combo.currentIndexChanged.connect(on_overlay1_size_changed)
    on_overlay1_size_changed(overlay1_size_combo.currentIndex())
    overlay1_position_label = QLabel("P:")
    overlay1_position_label.setFixedWidth(18)
    overlay1_position_combo = QComboBox()
    overlay1_position_combo.setFixedWidth(130)
    positions = [
        ("Center", "center"),
        ("Top Left", "top_left"),
        ("Top Right", "top_right"),
        ("Bottom Left", "bottom_left"),
        ("Bottom Right", "bottom_right")
    ]
    for label, value in positions:
        overlay1_position_combo.addItem(label, value)
    overlay1_position_combo.setCurrentIndex(0)
    overlay1_position = "center"
    def on_overlay1_position_changed(idx):
        nonlocal overlay1_position
        overlay1_position = overlay1_position_combo.itemData(idx)
    overlay1_position_combo.currentIndexChanged.connect(on_overlay1_position_changed)
    on_overlay1_position_changed(overlay1_position_combo.currentIndex())
    def set_overlay1_enabled(state):
        enabled = state == Qt.CheckState.Checked
        overlay1_edit.setEnabled(enabled)
        overlay1_btn.setEnabled(enabled)
        overlay1_size_combo.setEnabled(enabled)
        overlay1_position_combo.setEnabled(enabled)
        if enabled:
            overlay1_btn.setStyleSheet("")
            overlay1_edit.setStyleSheet("")
            overlay1_size_combo.setStyleSheet("")
            overlay1_position_combo.setStyleSheet("")
            overlay1_size_label.setStyleSheet("")
            overlay1_position_label.setStyleSheet("")
        else:
            grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
            overlay1_btn.setStyleSheet(grey_btn_style)
            overlay1_edit.setStyleSheet(grey_btn_style)
            overlay1_size_combo.setStyleSheet(grey_btn_style)
            overlay1_position_combo.setStyleSheet(grey_btn_style)
            overlay1_size_label.setStyleSheet("color: grey;")
            overlay1_position_label.setStyleSheet("color: grey;")
    overlay1_checkbox.stateChanged.connect(lambda _: set_overlay1_enabled(overlay1_checkbox.checkState()))
    set_overlay1_enabled(overlay1_checkbox.checkState())
    overlay1_layout.addWidget(overlay1_checkbox)
    overlay1_layout.addWidget(overlay1_edit)
    overlay1_layout.addSpacing(6)
    overlay1_layout.addWidget(overlay1_btn)
    overlay1_layout.addSpacing(4)
    overlay1_layout.addWidget(overlay1_position_label)
    overlay1_layout.addSpacing(2)
    overlay1_layout.addWidget(overlay1_position_combo)
    overlay1_layout.addSpacing(6)
    overlay1_layout.addWidget(overlay1_size_label)
    overlay1_layout.addWidget(overlay1_size_combo)
    controls['overlay1_checkbox'] = overlay1_checkbox
    controls['overlay1_edit'] = overlay1_edit
    controls['overlay1_btn'] = overlay1_btn
    controls['overlay1_size_combo'] = overlay1_size_combo
    controls['overlay1_position_combo'] = overlay1_position_combo
    controls['overlay1_layout'] = overlay1_layout

    # --- OVERLAY 2 CONTROLS ---
    overlay2_layout = QHBoxLayout()
    overlay2_layout.setSpacing(4)
    overlay2_checkbox = QCheckBox("Overlay 2:")
    overlay2_checkbox.setFixedWidth(82)
    overlay2_checkbox.setChecked(True)
    overlay2_edit = ImageDropLineEdit()
    overlay2_edit.setPlaceholderText("Overlay 2 image path (*.gif, *.png)")
    overlay2_edit.setToolTip("Drag and drop a GIF or PNG file here or click 'Select Image'")
    overlay2_edit.setFixedWidth(125)
    overlay2_path = ""
    def on_overlay2_changed():
        nonlocal overlay2_path
        overlay2_path = overlay2_edit.text().strip()
    overlay2_edit.textChanged.connect(on_overlay2_changed)
    overlay2_btn = QPushButton("Select")
    overlay2_btn.setFixedWidth(60)
    def select_overlay2_image():
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(parent, "Select Overlay 2 Image", "", "Image Files (*.gif *.png)")
        if file_path:
            overlay2_edit.setText(file_path)
    overlay2_btn.clicked.connect(select_overlay2_image)
    overlay2_size_label = QLabel("S:")
    overlay2_size_label.setFixedWidth(18)
    overlay2_size_combo = QComboBox()
    overlay2_size_combo.setFixedWidth(90)
    for percent in range(5, 101, 5):
        overlay2_size_combo.addItem(str(percent), percent)
    overlay2_size_combo.setCurrentIndex(1)
    overlay2_size_percent = 10
    def on_overlay2_size_changed(idx):
        nonlocal overlay2_size_percent
        overlay2_size_percent = overlay2_size_combo.itemData(idx)
        if idx >= 0:
            overlay2_size_combo.setEditText(f"{overlay2_size_percent}%")
    overlay2_size_combo.setEditable(True)
    overlay2_line_edit = overlay2_size_combo.lineEdit()
    if overlay2_line_edit is not None:
        overlay2_line_edit.setReadOnly(True)
        overlay2_line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
    overlay2_size_combo.currentIndexChanged.connect(on_overlay2_size_changed)
    on_overlay2_size_changed(overlay2_size_combo.currentIndex())
    overlay2_position_label = QLabel("P:")
    overlay2_position_label.setFixedWidth(18)
    overlay2_position_combo = QComboBox()
    overlay2_position_combo.setFixedWidth(130)
    for label, value in positions:
        overlay2_position_combo.addItem(label, value)
    overlay2_position_combo.setCurrentIndex(0)
    overlay2_position = "center"
    def on_overlay2_position_changed(idx):
        nonlocal overlay2_position
        overlay2_position = overlay2_position_combo.itemData(idx)
    overlay2_position_combo.currentIndexChanged.connect(on_overlay2_position_changed)
    on_overlay2_position_changed(overlay2_position_combo.currentIndex())
    def set_overlay2_enabled(state):
        enabled = state == Qt.CheckState.Checked
        overlay2_edit.setEnabled(enabled)
        overlay2_btn.setEnabled(enabled)
        overlay2_size_combo.setEnabled(enabled)
        overlay2_position_combo.setEnabled(enabled)
        if enabled:
            overlay2_btn.setStyleSheet("")
            overlay2_edit.setStyleSheet("")
            overlay2_size_combo.setStyleSheet("")
            overlay2_position_combo.setStyleSheet("")
            overlay2_size_label.setStyleSheet("")
            overlay2_position_label.setStyleSheet("")
        else:
            grey_btn_style = "background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;"
            overlay2_btn.setStyleSheet(grey_btn_style)
            overlay2_edit.setStyleSheet(grey_btn_style)
            overlay2_size_combo.setStyleSheet(grey_btn_style)
            overlay2_position_combo.setStyleSheet(grey_btn_style)
            overlay2_size_label.setStyleSheet("color: grey;")
            overlay2_position_label.setStyleSheet("color: grey;")
    overlay2_checkbox.stateChanged.connect(lambda _: set_overlay2_enabled(overlay2_checkbox.checkState()))
    set_overlay2_enabled(overlay2_checkbox.checkState())
    overlay2_layout.addWidget(overlay2_checkbox)
    overlay2_layout.addWidget(overlay2_edit)
    overlay2_layout.addSpacing(6)
    overlay2_layout.addWidget(overlay2_btn)
    overlay2_layout.addSpacing(4)
    overlay2_layout.addWidget(overlay2_position_label)
    overlay2_layout.addSpacing(2)
    overlay2_layout.addWidget(overlay2_position_combo)
    overlay2_layout.addSpacing(6)
    overlay2_layout.addWidget(overlay2_size_label)
    overlay2_layout.addWidget(overlay2_size_combo)
    controls['overlay2_checkbox'] = overlay2_checkbox
    controls['overlay2_edit'] = overlay2_edit
    controls['overlay2_btn'] = overlay2_btn
    controls['overlay2_size_combo'] = overlay2_size_combo
    controls['overlay2_position_combo'] = overlay2_position_combo
    controls['overlay2_layout'] = overlay2_layout

    # --- EFFECT CONTROL FOR INTRO & OVERLAY ---
    combo_width = 130
    edit_width = 50
    effect_layout = QHBoxLayout()
    effect_layout.setContentsMargins(0, 0, 0, 0)
    # --- Intro Effect Controls ---
    intro_effect_label2 = QLabel("Intro Effect:")
    intro_effect_label2.setFixedWidth(80)
    intro_effect_combo2 = QComboBox()
    intro_effect_combo2.setFixedWidth(combo_width)
    for label, value in intro_effect_options:
        intro_effect_combo2.addItem(label, value)
    intro_effect_combo2.setCurrentIndex(0)
    intro_effect2 = "fadeinout"
    def on_intro_effect2_changed(idx):
        nonlocal intro_effect2
        intro_effect2 = intro_effect_combo2.itemData(idx)
    intro_effect_combo2.currentIndexChanged.connect(on_intro_effect2_changed)
    on_intro_effect2_changed(intro_effect_combo2.currentIndex())
    intro_duration_label2 = QLabel("For (s): ")
    intro_duration_label2.setFixedWidth(45)
    intro_duration_edit2 = QLineEdit("5")
    intro_duration_edit2.setFixedWidth(40)
    intro_duration_edit2.setValidator(QIntValidator(1, 999, parent))
    intro_duration_edit2.setPlaceholderText("5")
    intro_duration2 = 5
    def on_intro_duration2_changed():
        nonlocal intro_duration2
        try:
            intro_duration2 = int(intro_duration_edit2.text())
        except Exception:
            intro_duration2 = 5
    intro_duration_edit2.textChanged.connect(on_intro_duration2_changed)
    on_intro_duration2_changed()
    effect_layout.addSpacing(10)
    effect_layout.addWidget(intro_effect_label2)
    effect_layout.addSpacing(-15)
    effect_layout.addWidget(intro_effect_combo2)
    effect_layout.addSpacing(0)
    effect_layout.addWidget(intro_duration_label2)
    effect_layout.addSpacing(-15)
    effect_layout.addWidget(intro_duration_edit2)
    effect_layout.addSpacing(10)
    # --- Overlay Effect Controls (existing) ---
    effect_label = QLabel("Overlay:")
    effect_label.setFixedWidth(55)
    effect_combo = QComboBox()
    effect_combo.setFixedWidth(combo_width)
    effect_options = [
        ("Fade in & out", "fadeinout"),
        ("Fade in", "fadein"),
        ("Fade out", "fadeout"),
        ("Zoompan", "zoompan"),
        ("None", "none")
    ]
    for label, value in effect_options:
        effect_combo.addItem(label, value)
    effect_combo.setCurrentIndex(1)
    selected_effect = "fadein"
    def on_effect_changed(idx):
        nonlocal selected_effect
        selected_effect = effect_combo.itemData(idx)
    effect_combo.currentIndexChanged.connect(on_effect_changed)
    on_effect_changed(effect_combo.currentIndex())
    overlay_duration_label = QLabel("at (s):")
    overlay_duration_label.setFixedWidth(40)
    overlay_duration_edit = QLineEdit("5")
    overlay_duration_edit.setFixedWidth(40)    
    overlay_duration_edit.setValidator(QIntValidator(0, 999, parent))
    overlay_duration_edit.setPlaceholderText("5")
    overlay_duration = 5
    def on_overlay_duration_changed():
        nonlocal overlay_duration
        try:
            overlay_duration = int(overlay_duration_edit.text())
        except Exception:
            overlay_duration = 5
    overlay_duration_edit.textChanged.connect(on_overlay_duration_changed)
    on_overlay_duration_changed()
    effect_layout.addSpacing(-10)
    effect_layout.addWidget(effect_label)
    effect_layout.addSpacing(-10)
    effect_layout.addWidget(effect_combo)
    effect_layout.addSpacing(0)
    effect_layout.addWidget(overlay_duration_label)
    effect_layout.addSpacing(-15)
    effect_layout.addWidget(overlay_duration_edit)    
    effect_layout.addStretch()
    controls['effect_combo'] = effect_combo
    controls['effect_layout'] = effect_layout
    controls['overlay_duration_edit'] = overlay_duration_edit
    controls['intro_effect_combo2'] = intro_effect_combo2
    controls['intro_duration_edit2'] = intro_duration_edit2
    # Add extra vertical spacing before the action buttons
    controls['spacing'] = 6
    return controls
