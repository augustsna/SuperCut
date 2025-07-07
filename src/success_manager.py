"""
success_manager.py - Handles success and leftover dialogs for SuperCutUI
"""
from PyQt6 import QtWidgets
from src.logger import logger
from src.ui_components import SuccessDialog
from src.utils import open_folder_in_explorer
import os

def show_success_options(self, leftover_files=None, leftover_images=None, min_mp3_count=None):
    """Show success dialog with options. All UI updates are performed in the main thread via signals/slots."""
    try:
        QtWidgets.QApplication.beep()
    except RuntimeError as e:
        logger.warning(f"Failed to play notification sound: {e}")
    if min_mp3_count is None:
        if self.mp3_count_checkbox.isChecked():
            try:
                min_mp3_count = int(self.mp3_count_edit.text())
                if min_mp3_count < 1:
                    min_mp3_count = self.DEFAULT_MIN_MP3_COUNT if hasattr(self, 'DEFAULT_MIN_MP3_COUNT') else 1
            except Exception:
                min_mp3_count = self.DEFAULT_MIN_MP3_COUNT if hasattr(self, 'DEFAULT_MIN_MP3_COUNT') else 1
        else:
            min_mp3_count = self.DEFAULT_MIN_MP3_COUNT if hasattr(self, 'DEFAULT_MIN_MP3_COUNT') else 1
    dlg = SuccessDialog(
        self, 
        open_folder=self.open_result_folder, 
        leftover_files=leftover_files, 
        leftover_images=leftover_images,
        min_mp3_count=min_mp3_count
    )
    dlg.exec()

def open_result_folder(self):
    folder = os.path.dirname(self.output_path)
    open_folder_in_explorer(folder)
