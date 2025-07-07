from src.ui_components import SettingsDialog
from PyQt6.QtWidgets import QDialog

def show_settings_dialog(ui, DEFAULT_FPS_OPTIONS):
    dlg = SettingsDialog(ui, settings=ui.settings, fps_options=DEFAULT_FPS_OPTIONS)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        apply_settings(ui, DEFAULT_FPS_OPTIONS)

def apply_settings(ui, DEFAULT_FPS_OPTIONS):
    settings = ui.settings
    default_fps = settings.value('default_fps', type=int)
    if default_fps is not None:
        idx = next((i for i, (label, value) in enumerate(DEFAULT_FPS_OPTIONS) if value == default_fps), 0)
        ui.fps_combo.setCurrentIndex(idx)
    default_intro_enabled = settings.value('default_intro_enabled', True, type=bool)
    ui.intro_checkbox.setChecked(default_intro_enabled)
    if default_intro_enabled:
        default_intro_path = settings.value('default_intro_path', '', type=str)
        default_intro_position = settings.value('default_intro_position', 'center', type=str)
        default_intro_size = settings.value('default_intro_size', 50, type=int)
        if not ui.intro_edit.text().strip():
            ui.intro_edit.setText(default_intro_path)
        idx = next((i for i in range(ui.intro_position_combo.count()) if ui.intro_position_combo.itemData(i) == default_intro_position), 0)
        ui.intro_position_combo.setCurrentIndex(idx)
        idx = next((i for i in range(ui.intro_size_combo.count()) if ui.intro_size_combo.itemData(i) == default_intro_size), 9)
        ui.intro_size_combo.setCurrentIndex(idx)
    default_overlay1_path = settings.value('default_overlay1_path', '', type=str)
    default_overlay1_position = settings.value('default_overlay1_position', 'bottom_left', type=str)
    default_overlay1_size = settings.value('default_overlay1_size', 15, type=int)
    if ui.overlay1_checkbox.isChecked():
        if not ui.overlay1_edit.text().strip():
            ui.overlay1_edit.setText(default_overlay1_path)
        idx = next((i for i in range(ui.overlay1_position_combo.count()) if ui.overlay1_position_combo.itemData(i) == default_overlay1_position), 3)
        ui.overlay1_position_combo.setCurrentIndex(idx)
        idx = next((i for i in range(ui.overlay1_size_combo.count()) if ui.overlay1_size_combo.itemData(i) == default_overlay1_size), 2)
        ui.overlay1_size_combo.setCurrentIndex(idx)
    default_overlay2_path = settings.value('default_overlay2_path', '', type=str)
    default_overlay2_position = settings.value('default_overlay2_position', 'top_right', type=str)
    default_overlay2_size = settings.value('default_overlay2_size', 15, type=int)
    if ui.overlay2_checkbox.isChecked():
        if not ui.overlay2_edit.text().strip():
            ui.overlay2_edit.setText(default_overlay2_path)
        idx = next((i for i in range(ui.overlay2_position_combo.count()) if ui.overlay2_position_combo.itemData(i) == default_overlay2_position), 2)
        ui.overlay2_position_combo.setCurrentIndex(idx)
        idx = next((i for i in range(ui.overlay2_size_combo.count()) if ui.overlay2_size_combo.itemData(i) == default_overlay2_size), 2)
        ui.overlay2_size_combo.setCurrentIndex(idx)
