"""
result_folder_manager.py - Handles result folder opening logic for SuperCutUI
"""
import os
from src.utils import open_folder_in_explorer

def open_result_folder(self):
    """Open the result folder in file explorer"""
    folder = os.path.dirname(self.output_path)
    open_folder_in_explorer(folder)
