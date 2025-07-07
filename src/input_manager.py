"""
input_manager.py - Handles input field change logic and input clearing for SuperCutUI
"""

def on_media_folder_changed(self):
    """When media folder is changed, set output folder to same only if output folder is empty"""
    folder = self.media_sources_edit.text().strip()
    if folder and not self.folder_edit.text().strip():
        self.folder_edit.setText(folder)
        self.output_folder_manual = False  # Auto-set, so mark as not manual
        self.update_output_name()

def on_output_folder_changed(self, text):
    """Reset manual flag if output folder is cleared"""
    if not text.strip():
        self.output_folder_manual = False

def clear_inputs(self):
    """Clear input fields"""
    self.media_sources_edit.setText("")
    self.folder_edit.setText("")
    self.part2_edit.setText("")
