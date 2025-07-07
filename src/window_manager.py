"""
window_manager.py - Handles window state, shortcut, and event logic for SuperCutUI
"""
from PyQt6.QtCore import QSettings, QPoint
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QApplication, QMessageBox
import threading
import time

def restore_window_position(self):
    settings = QSettings('SuperCut', 'SuperCutUI')
    pos = settings.value('window_position')
    if isinstance(pos, QPoint):
        self.move(pos)
    elif isinstance(pos, (tuple, list)) and len(pos) == 2:
        self.move(QPoint(pos[0], pos[1]))
    else:
        self.move(0, 0)

def setup_shortcuts(self):
    QShortcut(QKeySequence("Ctrl+W"), self, self.close_window)

def close_window(self):
    self.close()

def closeEvent(self, event):
    # Close terminal widget if it exists
    if hasattr(self, 'terminal_widget') and self.terminal_widget is not None:
        self.terminal_widget.close()
        self.terminal_widget = None
    # If a video creation thread is running, warn the user
    if hasattr(self, '_thread') and self._thread is not None and self._thread.isRunning():
        reply = QMessageBox.question(
            self,
            "Quit Program",
            "Video creation is running. Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            waiting_dialog = QMessageBox(self)
            waiting_dialog.setWindowTitle("Please Wait")
            waiting_dialog.setText("Waiting for current batch to finish...")
            waiting_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
            waiting_dialog.show()
            if hasattr(self, "_worker") and self._worker is not None:
                stop_method = getattr(self._worker, 'stop', None)
                if callable(stop_method):
                    try:
                        stop_method()
                    except RuntimeError:
                        pass
            def wait_and_close():
                if self._thread is not None:
                    self._thread.wait()
                time.sleep(3)
                waiting_dialog.close()
                app_instance = QApplication.instance()
                if app_instance is not None:
                    app_instance.quit()
            threading.Thread(target=wait_and_close, daemon=True).start()
            event.ignore()
            return
        else:
            event.ignore()
            return
    settings = QSettings('SuperCut', 'SuperCutUI')
    settings.setValue('window_position', self.pos())
    super(type(self), self).closeEvent(event)

def moveEvent(self, event):
    super(type(self), self).moveEvent(event)
    if (hasattr(self, 'terminal_widget') and 
        self.terminal_widget is not None and 
        self.terminal_widget.isVisible()):
        self.position_terminal_widget()
