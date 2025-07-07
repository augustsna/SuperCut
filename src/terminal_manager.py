from src.terminal_widget import TerminalWidget
from PyQt6.QtWidgets import QApplication

def show_terminal(parent):
    """Show or create the terminal widget for the parent window."""
    if parent.terminal_widget is None:
        parent.terminal_widget = TerminalWidget()
        parent.terminal_widget.closed.connect(parent.on_terminal_closed)
        position_terminal_widget(parent)
        parent.terminal_widget.show_and_raise()
        parent.terminal_btn.setText("💻 Terminal ON")
    else:
        parent.terminal_widget.close()
        parent.terminal_widget = None
        parent.terminal_btn.setText("💻 Terminal")

def position_terminal_widget(parent):
    """Position the terminal widget intelligently based on main window position and screen space."""
    if not parent.terminal_widget:
        return
    main_pos = parent.pos()
    main_width = parent.width()
    main_height = parent.height()
    terminal_width = parent.terminal_widget.width()
    terminal_height = parent.terminal_widget.height()
    screen = parent.screen() if hasattr(parent, 'screen') and parent.screen() else QApplication.primaryScreen()
    if screen is not None:
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
    else:
        screen_width = 1920
        screen_height = 1080
    space_on_right = screen_width - (main_pos.x() + main_width)
    space_on_left = main_pos.x()
    if space_on_right >= terminal_width + 10:
        terminal_x = main_pos.x() + main_width + 10
        terminal_y = main_pos.y()
        position_side = "right"
    elif space_on_left >= terminal_width + 10:
        terminal_x = main_pos.x() - terminal_width - 10
        terminal_y = main_pos.y()
        position_side = "left"
    else:
        if space_on_right > space_on_left:
            terminal_x = main_pos.x() + main_width + 5
            terminal_y = main_pos.y()
            position_side = "right (tight)"
        else:
            terminal_x = main_pos.x() - terminal_width - 5
            terminal_y = main_pos.y()
            position_side = "left (tight)"
    if terminal_y + terminal_height > screen_height:
        terminal_y = screen_height - terminal_height - 10
    if terminal_y < 0:
        terminal_y = 10
    if terminal_x + terminal_width > screen_width:
        terminal_x = screen_width - terminal_width - 10
    if terminal_x < 0:
        terminal_x = 10
    parent.terminal_widget.move(terminal_x, terminal_y)
    parent.terminal_widget.setWindowTitle(f"SuperCut Terminal [{position_side}]")
