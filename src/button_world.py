# This file uses PyQt6
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout

def print_world():
    print("World")

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle('PyQt6 Button Example')

layout = QVBoxLayout()

button = QPushButton('Click Me')
button.clicked.connect(print_world)
layout.addWidget(button)

window.setLayout(layout)
window.show()

sys.exit(app.exec()) 