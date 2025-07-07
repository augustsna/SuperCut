"""
ui_builder.py - Contains UI construction helpers for SuperCutUI
"""
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QDialog
from PyQt6.QtGui import QIntValidator

def create_folder_inputs(self, layout, FolderDropLineEdit, PROJECT_ROOT):
    folder_row_style = {
        "label_width": 90,
        "edit_min_width": 220,
        "btn_width": 110
    }
    # Media Folder input
    media_sources_layout = QHBoxLayout()
    label_media = QLabel("Media Folder:")
    label_media.setFixedWidth(folder_row_style["label_width"])
    self.media_sources_edit = FolderDropLineEdit()
    self.media_sources_edit.setReadOnly(False)
    self.media_sources_edit.setMinimumWidth(folder_row_style["edit_min_width"])
    self.media_sources_edit.setPlaceholderText("Drag & drop or click Select Folder")
    self.media_sources_edit.setToolTip("Drag and drop a folder here or click 'Select Folder'")
    media_sources_btn = QPushButton("Select Folder")
    media_sources_btn.setFixedWidth(folder_row_style["btn_width"])
    media_sources_btn.clicked.connect(self.select_media_sources_folder)
    self.media_sources_select_btn = media_sources_btn
    media_sources_layout.addWidget(label_media)
    media_sources_layout.addWidget(self.media_sources_edit)
    media_sources_layout.addWidget(media_sources_btn)
    layout.addLayout(media_sources_layout)
    # Output folder selection
    folder_layout = QHBoxLayout()
    label_output = QLabel("Output Folder:")
    label_output.setFixedWidth(folder_row_style["label_width"] + 1)
    self.folder_edit = FolderDropLineEdit()
    self.folder_edit.setReadOnly(False)
    self.folder_edit.setMinimumWidth(folder_row_style["edit_min_width"])
    self.folder_edit.setPlaceholderText("Drag & drop or click Select Folder")
    self.folder_edit.setToolTip("Drag and drop a folder here or click 'Select Folder'")
    folder_btn = QPushButton("Select Folder")
    folder_btn.setFixedWidth(folder_row_style["btn_width"])
    folder_btn.clicked.connect(self.select_output_folder)
    self.output_folder_select_btn = folder_btn
    folder_layout.addWidget(label_output)
    folder_layout.addWidget(self.folder_edit)
    folder_layout.addWidget(folder_btn)
    layout.addLayout(folder_layout)

def create_export_inputs(self, layout, DEFAULT_EXPORT_NAME, DEFAULT_START_NUMBER, DEFAULT_MIN_MP3_COUNT, QIntValidator, NameListDialog):
    part_layout = QHBoxLayout()
    self.part1_edit = QLineEdit(DEFAULT_EXPORT_NAME)
    self.part1_edit.setPlaceholderText("Export Name")
    self.part1_edit.setFixedWidth(100)
    self.part2_edit = QLineEdit(DEFAULT_START_NUMBER)
    self.part2_edit.setPlaceholderText("12345")
    self.part2_edit.setValidator(QIntValidator(1, 9999999, self))
    self.part2_edit.setFixedWidth(60)
    self.name_list_checkbox = QCheckBox("List name:")
    self.name_list_checkbox.setChecked(True)
    self.name_list_enter_btn = QPushButton("Enter")
    self.name_list_enter_btn.setFixedWidth(60)
    self.name_list = []
    self.name_list_dialog = None
    def update_name_list_controls():
        checked = self.name_list_checkbox.isChecked()
        self.name_list_enter_btn.setEnabled(checked)
        self.part1_edit.setEnabled(not checked)
        self.part2_edit.setEnabled(not checked)
        if checked:
            self.name_list_enter_btn.setStyleSheet("")
            self.part1_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
            self.part2_edit.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
        else:
            self.name_list_enter_btn.setStyleSheet("background-color: #f2f2f2; color: #888; border: 1px solid #cfcfcf;")
            self.part1_edit.setStyleSheet("")
            self.part2_edit.setStyleSheet("")
        if not checked:
            self.name_list = []
    self.name_list_checkbox.stateChanged.connect(lambda _: update_name_list_controls())
    update_name_list_controls()
    def open_name_list_dialog():
        dlg = NameListDialog(self, self.name_list)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.name_list = dlg.get_names()
    self.name_list_enter_btn.clicked.connect(open_name_list_dialog)
    self.mp3_count_checkbox = QCheckBox("MP3 #")
    self.mp3_count_checkbox.setChecked(False)
    self.mp3_count_edit = QLineEdit(str(DEFAULT_MIN_MP3_COUNT))
    self.mp3_count_edit.setPlaceholderText("MP3")
    self.mp3_count_edit.setValidator(QIntValidator(1, 999, self))
    self.mp3_count_edit.setEnabled(False)
    self.mp3_count_edit.setFixedWidth(50)
    def set_mp3_count_edit_enabled(state):
        if isinstance(state, int):
            from PyQt6.QtCore import Qt
            state = Qt.CheckState(state)
        checked = state == 2
        self.mp3_count_edit.setEnabled(checked)
        if checked:
            self.mp3_count_edit.setStyleSheet("")
        else:
            self.mp3_count_edit.setStyleSheet("background-color: #f2f2f2; color: #888;")
    self.mp3_count_checkbox.stateChanged.connect(set_mp3_count_edit_enabled)
    def update_mp3_checkbox_style(state):
        self.mp3_count_checkbox.setStyleSheet("")
    self.mp3_count_checkbox.stateChanged.connect(update_mp3_checkbox_style)
    update_mp3_checkbox_style(self.mp3_count_checkbox.checkState())
    set_mp3_count_edit_enabled(self.mp3_count_checkbox.checkState())
    self.part1_edit.textChanged.connect(self.update_output_name)
    self.part2_edit.textChanged.connect(self.update_output_name)
    self.folder_edit.textChanged.connect(self.update_output_name)
    part_layout.addSpacing(20)
    part_layout.addWidget(self.name_list_checkbox)
    part_layout.addSpacing(-50)
    part_layout.addWidget(self.name_list_enter_btn)
    part_layout.addSpacing(20)
    part_layout.addWidget(QLabel("Name:"))
    part_layout.addSpacing(-90)
    part_layout.addWidget(self.part1_edit)
    part_layout.addSpacing(-10)
    part_layout.addWidget(QLabel("#"))
    part_layout.addSpacing(-120)
    part_layout.addWidget(self.part2_edit)
    part_layout.addSpacing(15)
    part_layout.addWidget(self.mp3_count_checkbox)
    part_layout.addSpacing(-70)
    part_layout.addWidget(self.mp3_count_edit)
    part_layout.addSpacing(15)
    layout.addLayout(part_layout)
