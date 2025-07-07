from src.ui_components import ScrollableErrorDialog, StoppedDialog, SuccessDialog
from src.utils import open_folder_in_explorer
from PyQt6 import QtWidgets
from src.logger import logger
import os

def handle_worker_error(ui, message):
    """Handle worker errors and show error dialog."""
    if not ui.isVisible():
        return
    ui.progress_bar.setVisible(False)
    ui.stop_btn.setEnabled(False)
    ui.stop_btn.setVisible(False)
    if hasattr(ui, 'spinner_label'):
        ui.spinner_label.setVisible(False)
    if hasattr(ui, 'loading_label'):
        ui.loading_label.setVisible(False)
        movie = ui.loading_label.movie()
        if movie is not None:
            movie.stop()
    if hasattr(ui, 'static_icon'):
        ui.static_icon.setVisible(True)
    ui.create_btn.setEnabled(True)
    ui.codec_combo.setEnabled(True)
    ui.resolution_combo.setEnabled(True)
    ui.fps_combo.setEnabled(True)
    ui.media_sources_edit.setEnabled(True)
    ui.folder_edit.setEnabled(True)
    ui.part1_edit.setEnabled(True)
    ui.part2_edit.setEnabled(True)
    ui.media_sources_select_btn.setEnabled(True)
    ui.output_folder_select_btn.setEnabled(True)
    ui.overlay_checkbox.setEnabled(True)
    dlg = ScrollableErrorDialog(ui, title="❌ Error", message=message)
    dlg.exec()
    ui.cleanup_worker_and_thread()
    ui._worker = None
    ui._thread = None
    if hasattr(ui, '_auto_close_on_stop') and ui._auto_close_on_stop:
        ui._auto_close_on_stop = False
        if hasattr(ui, '_stopping_msgbox') and ui._stopping_msgbox is not None:
            ui._stopping_msgbox.close()
            ui._stopping_msgbox.hide()
            QtWidgets.QApplication.processEvents()
            ui._stopping_msgbox = None
        ui.close()

def handle_worker_finished_with_leftovers(ui, leftover_mp3s, used_images, original_mp3_files, original_image_files, failed_moves=None):
    """Handle worker completion with leftover files and show appropriate dialogs."""
    if not ui.isVisible():
        return
    ui._set_ui_processing_state(False)
    leftover_images = list(set(original_image_files) - set(used_images))
    if ui.mp3_count_checkbox.isChecked():
        try:
            min_mp3_count = int(ui.mp3_count_edit.text())
            if min_mp3_count < 1:
                min_mp3_count = ui.DEFAULT_MIN_MP3_COUNT
        except Exception:
            min_mp3_count = ui.DEFAULT_MIN_MP3_COUNT
    else:
        min_mp3_count = ui.DEFAULT_MIN_MP3_COUNT
    if hasattr(ui, '_stopped_by_user') and ui._stopped_by_user:
        ui._stopped_by_user = False
        if hasattr(ui, '_stopping_msgbox') and ui._stopping_msgbox is not None:
            ui._stopping_msgbox.close()
            ui._stopping_msgbox.hide()
            QtWidgets.QApplication.processEvents()
            ui._stopping_msgbox = None
        batch_count = ui.progress_bar.value() if hasattr(ui, 'progress_bar') else 0
        total_batches = ui.progress_bar.maximum() if hasattr(ui, 'progress_bar') else 0
        dlg = StoppedDialog(ui, batch_count=batch_count, total_batches=total_batches)
        dlg.exec()
    else:
        if leftover_mp3s or leftover_images:
            show_success_options(ui, leftover_files=leftover_mp3s, leftover_images=leftover_images, min_mp3_count=min_mp3_count)
        else:
            show_success_options(ui, min_mp3_count=min_mp3_count)
    if failed_moves:
        QtWidgets.QMessageBox.warning(ui, "Warning: File Move Failed", f"Some files could not be moved to the bin folder:\n\n" + '\n'.join(failed_moves))
    ui.clear_inputs()
    ui.cleanup_worker_and_thread()
    ui._worker = None
    ui._thread = None
    if hasattr(ui, '_auto_close_on_stop') and ui._auto_close_on_stop:
        ui._auto_close_on_stop = False
        if hasattr(ui, '_stopping_msgbox') and ui._stopping_msgbox is not None:
            ui._stopping_msgbox.close()
            ui._stopping_msgbox.hide()
            QtWidgets.QApplication.processEvents()
            ui._stopping_msgbox = None

def show_success_options(ui, leftover_files=None, leftover_images=None, min_mp3_count=None):
    """Show success dialog with options."""
    try:
        QtWidgets.QApplication.beep()
    except RuntimeError as e:
        logger.warning(f"Failed to play notification sound: {e}")
    if min_mp3_count is None:
        if ui.mp3_count_checkbox.isChecked():
            try:
                min_mp3_count = int(ui.mp3_count_edit.text())
                if min_mp3_count < 1:
                    min_mp3_count = ui.DEFAULT_MIN_MP3_COUNT
            except Exception:
                min_mp3_count = ui.DEFAULT_MIN_MP3_COUNT
        else:
            min_mp3_count = ui.DEFAULT_MIN_MP3_COUNT
    dlg = SuccessDialog(
        ui, 
        open_folder=ui.open_result_folder, 
        leftover_files=leftover_files, 
        leftover_images=leftover_images,
        min_mp3_count=min_mp3_count
    )
    dlg.exec()
