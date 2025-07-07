"""
leftover_manager.py - Handles leftover/cleanup logic for SuperCutUI
"""
from PyQt6 import QtWidgets

def cleanup_leftovers(self):
    """Cleanup leftover UI state and dialogs after processing or stop."""
    self._auto_close_on_stop = False
    if hasattr(self, '_stopping_msgbox') and self._stopping_msgbox is not None:
        self._stopping_msgbox.close()
        self._stopping_msgbox.hide()
        QtWidgets.QApplication.processEvents()
        self._stopping_msgbox = None
