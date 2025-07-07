from PyQt6.QtCore import QThread
from src.video_worker import VideoWorker
from src.ui_components import PleaseWaitDialog, StoppedDialog, SuccessDialog, ScrollableErrorDialog
from PyQt6.QtWidgets import QMessageBox
import os
import threading
import time

def setup_worker_and_thread(ui, media_sources, export_name, number, folder, codec, resolution, fps, original_mp3_files, original_image_files, min_mp3_count):
    """Set up the VideoWorker and QThread, connect signals, and start processing."""
    ui._thread = QThread()
    use_name_list = hasattr(ui, 'name_list_checkbox') and ui.name_list_checkbox.isChecked()
    name_list = ui.name_list if use_name_list else None
    ui._worker = VideoWorker(
        media_sources, export_name, number, folder, codec, resolution, fps,
        ui.overlay_checkbox.isChecked(), min_mp3_count, ui.overlay1_path, ui.overlay1_size_percent, ui.overlay1_position,
        ui.overlay2_checkbox.isChecked(), ui.overlay2_path, ui.overlay2_size_percent, ui.overlay2_position,
        ui.intro_checkbox.isChecked(), ui.intro_path, ui.intro_size_percent, ui.intro_position,
        ui.selected_effect, ui.overlay_duration,
        ui.intro_effect, ui.intro_duration,
        name_list=name_list
    )
    ui._worker.moveToThread(ui._thread)
    ui._thread.started.connect(ui._worker.run)
    ui._worker.progress.connect(ui.on_worker_progress)
    ui._worker.error.connect(ui.on_worker_error)
    ui._worker.finished.connect(
        lambda leftover_mp3s, used_images, failed_moves: ui.on_worker_finished_with_leftovers(
            leftover_mp3s, used_images, original_mp3_files, original_image_files, failed_moves
        )
    )
    ui._worker.finished.connect(ui._thread.quit)
    ui._worker.finished.connect(ui._worker.deleteLater)
    ui._thread.finished.connect(ui._thread.deleteLater)
    ui._thread.start()

def stop_video_creation(ui):
    if hasattr(ui, "_worker") and ui._worker is not None:
        stop_method = getattr(ui._worker, 'stop', None)
        if callable(stop_method):
            try:
                stop_method()
            except RuntimeError:
                pass  # Worker already deleted
    ui.stop_btn.setEnabled(False)
    ui.stop_btn.setVisible(False)
    ui._stopping_msgbox = PleaseWaitDialog(ui)
    ui._stopping_msgbox.show()
    ui.progress_bar.setVisible(False)
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
    ui._auto_close_on_stop = False
    ui._stopped_by_user = True

def cleanup_worker_and_thread(ui):
    if hasattr(ui, '_worker') and ui._worker is not None:
        try:
            ui._worker.progress.disconnect(ui.on_worker_progress)
        except (TypeError, RuntimeError):
            pass
        try:
            ui._worker.error.disconnect(ui.on_worker_error)
        except (TypeError, RuntimeError):
            pass
        try:
            ui._worker.finished.disconnect()
        except (TypeError, RuntimeError):
            pass
    if hasattr(ui, '_thread') and ui._thread is not None:
        try:
            ui._thread.started.disconnect()
        except (TypeError, RuntimeError):
            pass
