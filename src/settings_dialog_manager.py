"""
settings_dialog_manager.py - Handles settings dialog logic for SuperCutUI
"""
from src.settings_manager import show_settings_dialog, apply_settings

def show_settings_dialog_ui(self):
    show_settings_dialog(self, self.DEFAULT_FPS_OPTIONS if hasattr(self, 'DEFAULT_FPS_OPTIONS') else None)

def apply_settings_ui(self):
    apply_settings(self, self.DEFAULT_FPS_OPTIONS if hasattr(self, 'DEFAULT_FPS_OPTIONS') else None)
