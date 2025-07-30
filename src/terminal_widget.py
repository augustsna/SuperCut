#!/usr/bin/env python3
# This file uses PyQt6
"""
Terminal Widget for SuperCut Video Maker
A sleek, compact terminal window for displaying console output.
"""

import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QFrame, QSizePolicy, QScrollBar, QApplication
)
from PyQt6.QtCore import (
    QTimer, pyqtSignal, QThread, pyqtSlot, QPoint, Qt
)
from PyQt6.QtGui import QFont, QTextCursor, QPalette, QColor, QIcon, QCursor, QMouseEvent, QKeySequence, QPainter, QBrush, QShortcut
import queue
import threading
import time

class ConsoleCapture:
    """Captures stdout and stderr to a queue"""
    
    def __init__(self, queue):
        self.queue = queue
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.current_line = ""
        
    def write(self, text):
        # Handle carriage return for progress bars
        if '\r' in text:
            # Split by carriage return and get the last part
            parts = text.split('\r')
            if len(parts) > 1:
                # The last part after \r is the new content
                self.current_line = parts[-1]
                # Send the full line to be displayed
                self.queue.put(('stdout', f'\r{self.current_line}'))
            else:
                # Just a carriage return, clear the line
                self.current_line = ""
                self.queue.put(('stdout', '\r'))
        else:
            # Regular text, append to current line
            self.current_line += text
            self.queue.put(('stdout', text))
            
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
    def flush(self):
        self.original_stdout.flush()
        
    def restore(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

class DraggableHeader(QWidget):
    """Custom header widget that can be dragged to move the window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.dragging = False
        self.drag_position = QPoint()
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton and self.parent_window:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging and self.parent_window:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class TerminalWidget(QWidget):
    """Sleek terminal widget for displaying console output"""
    
    # Signal emitted when the terminal widget is closed
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_queue = queue.Queue()
        self.console_capture = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_queue)
        self.update_timer.start(100)  # Update every 100ms
        
        self.init_ui()
        self.start_capture()
        
        # Add Ctrl+W shortcut to close terminal
        self.shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcut.activated.connect(self.close_terminal)
        
    def init_ui(self):
        """Initialize the terminal UI"""
        # Remove title bar and make frameless
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(540, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Enable rounded corners for top-level window
        
        # Set modern styling
        self.setStyleSheet("""
            QWidget {
                /* background-color removed to avoid double painting */
                color: #cccccc;
                font-family: 'Cascadia Mono' , 'Consolas', 'Monaco', 'Courier New', monospace; 
                font-size: 13px;
                border-radius: 12px; /* Rounded corners for the main widget */
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 8px;
                font-size: 20;
                color: #cccccc;
                padding: 8px;
                selection-background-color: #58a6ff;
            }
            QTextEdit QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 2px 0 2px 0;
                border-radius: 4px;
            }
            QTextEdit QScrollBar::handle:vertical {
                background: #43464d;
                min-height: 24px;
                border-radius: 4px;
                border: none;
                opacity: 0.7;
            }
            QTextEdit QScrollBar::handle:vertical:hover {
                background: #595d66;
                opacity: 1.0;
            }
            QTextEdit QScrollBar::add-line:vertical,
            QTextEdit QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
                border: none;
            }
            QTextEdit QScrollBar::add-page:vertical, QTextEdit QScrollBar::sub-page:vertical {
                background: none;
            }
            QTextEdit QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                margin: 0 2px 0 2px;
                border-radius: 4px;
            }
            QTextEdit QScrollBar::handle:horizontal {
                background: #43464d;
                min-width: 24px;
                border-radius: 4px;
                border: none;
                opacity: 0.7;
            }
            QTextEdit QScrollBar::handle:horizontal:hover {
                background: #595d66;
                opacity: 1.0;
            }
            QTextEdit QScrollBar::add-line:horizontal,
            QTextEdit QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
                border: none;
            }
            QTextEdit QScrollBar::add-page:horizontal, QTextEdit QScrollBar::sub-page:horizontal {
                background: none;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #505050;
                
            }
            QPushButton:pressed {
                background-color: #404040;
            }
            QLabel {
                color: #b0b0b0;
                font-weight: 500;
            }
            #exitButton {
                background-color: #6e7681;
                border: 1px solid #6e7681;
                border-radius: 8px;
                padding: 0px 2px;
                font-size: 16px;
                font-weight: bold;
                min-width: 14px;
                max-width: 14px;
                min-height: 14px;
                max-height: 14px;
            }
            #exitButton:hover {
                background-color: #da3633;
                border-color: #da3633;
            }
            #headerArea {
                background-color: #404040;
                border-bottom: 1px solid #505050;
                padding: 8px 12px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with drag area
        header_widget = DraggableHeader(self)
        header_widget.setObjectName("headerArea")
        header_widget.setFixedHeight(40)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        # Title
        title_label = QLabel("Main Terminal")
        title_label.setStyleSheet("""
            QLabel {
                color: #f2f2f2;
                font-size: 13px;
                
            }
        """)
        
        # Status indicator
        self.status_label = QLabel("● Active")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #3fb950;
                font-size: 11px;
            }
            
        """)
        
        # Exit button
        self.exit_btn = QPushButton("×")
        self.exit_btn.setObjectName("exitButton")
        self.exit_btn.setToolTip("Close Terminal")
        self.exit_btn.clicked.connect(self.close_terminal)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.exit_btn)
        
        # Content area
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(12, 0, 12, 12)
        content_layout.setSpacing(8)
        
        # Terminal output area
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # Disable horizontal scrollbar
        self.terminal_output.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Set monospace font to look like Windows Terminal
        preferred_fonts = ["Cascadia Mono", "Consolas", "Courier New", "monospace"]
        font = None
        for fam in preferred_fonts:
            f = QFont(fam, 16)
            f.setStyleHint(QFont.StyleHint.Monospace)
            if QFont(fam).exactMatch() or fam == "monospace":
                font = f
                break
        if font is None:
            font = QFont("Consolas", 16)
            font.setStyleHint(QFont.StyleHint.Monospace)
        self.terminal_output.setFont(font)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_output)
        self.clear_btn.setFixedWidth(80)
        
        self.auto_scroll_btn = QPushButton("Auto-scroll: ON")
        self.auto_scroll_btn.setCheckable(True)
        self.auto_scroll_btn.setChecked(True)
        self.auto_scroll_btn.clicked.connect(self.toggle_auto_scroll)
        self.auto_scroll_btn.setFixedWidth(140)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.auto_scroll_btn)
        
        # Assemble content layout
        content_layout.addWidget(self.terminal_output)
        content_layout.addLayout(button_layout)
        
        # Assemble main layout
        layout.addWidget(header_widget)
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
        
        # Add initial message
        self.append_output("💫 SuperCut is ready... \n")
        self.append_output("-" * 25+ "\n")
        
    def close_terminal(self):
        """Close the terminal widget"""
        self.close()
        
    def start_capture(self):
        """Start capturing stdout and stderr"""
        self.console_capture = ConsoleCapture(self.output_queue)
        sys.stdout = self.console_capture
        sys.stderr = self.console_capture
        
    def stop_capture(self):
        """Stop capturing stdout and stderr"""
        if self.console_capture:
            self.console_capture.restore()
            
    def process_queue(self):
        """Process queued output"""
        try:
            while True:
                output_type, text = self.output_queue.get_nowait()
                self.append_output(text)
        except queue.Empty:
            pass
            
    def append_output(self, text):
        """Append text to terminal output"""
        cursor = self.terminal_output.textCursor()
        
        # Handle carriage return for progress bars
        if '\r' in text:
            # Move to the beginning of the last line
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            
            # Get the text after the carriage return
            parts = text.split('\r')
            if len(parts) > 1:
                new_content = parts[-1]
                # Replace the current line with new content
                cursor.insertText(new_content)
            else:
                # Just clear the line
                cursor.removeSelectedText()
        else:
            # Regular text, append normally
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.terminal_output.setTextCursor(cursor)
            
            # Insert the full text without truncation
            self.terminal_output.insertPlainText(text)
        
        # Auto-scroll if enabled
        if self.auto_scroll_btn.isChecked():
            self.terminal_output.ensureCursorVisible()
        
    def clear_output(self):
        """Clear terminal output"""
        self.terminal_output.clear()
        self.append_output("Terminal cleared.\n")
        
    def toggle_auto_scroll(self):
        """Toggle auto-scroll functionality"""
        if self.auto_scroll_btn.isChecked():
            self.auto_scroll_btn.setText("Auto-scroll: ON")
        else:
            self.auto_scroll_btn.setText("Auto-scroll: OFF")
            
    def closeEvent(self, event):
        """Handle close event"""
        self.stop_capture()
        self.update_timer.stop()
        self.closed.emit()
        event.accept()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        brush = QBrush(QColor('#2e2e2e'))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        rect = self.rect()
        painter.drawRoundedRect(rect, 8, 8)  # 18 is the radius, match your stylesheet
        
    
        
    def create_progress_bar(self, current, total, eta="00:00:00", prefix=""):
        """
        Create a formatted progress bar string
        
        Args:
            current (int): Current progress value
            total (int): Total value
            eta (str): Estimated time remaining
            prefix (str): Optional prefix text
            
        Returns:
            str: Formatted progress bar string
        """
        if total == 0:
            percentage = 100.0
        else:
            percentage = (current / total) * 100
            
        progress_text = f"\r{prefix}{percentage:5.1f}% | Frame: {current}/{total} | ETA: {eta}"
        return progress_text
        
    def update_progress(self, current, total, eta="00:00:00", prefix=""):
        """
        Update progress bar in the terminal
        
        Args:
            current (int): Current progress value
            total (int): Total value
            eta (str): Estimated time remaining
            prefix (str): Optional prefix text
        """
        progress_text = self.create_progress_bar(current, total, eta, prefix)
        print(progress_text, end="", flush=True)
        
    def show_and_raise(self):
        """Show the terminal and bring it to front"""
        self.show()
        self.raise_()
        self.activateWindow() 