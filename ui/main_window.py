"""Main Window for Downloads Organizer.

Implements the complete user interface:
- Downloads folder auto-detection and folder selection
- Statistics overview (Found, To Move, Ignored)
- Category breakdown with badge counts
- Preview / dry-run mode
- Safe organization execution with progress tracking
- Undo functionality
- Automatic monitoring mode with system tray integration
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QApplication,
    QSystemTrayIcon,
)

from src.config import ConfigManager
from src.history import HistoryManager
from src.logger import OrganizerLogger
from src.organizer import OrganizerEngine, ScanResult, OrganizeResult, UndoResult
from src.utils import get_default_downloads_folder, get_log_file_path
from src.watcher import DownloadsWatcher
from ui.preview_dialog import PreviewDialog
from ui.progress_dialog import ProgressDialog
from ui.settings_window import SettingsDialog
from ui.styles import MODERN_STYLE
from ui.tray import DownloadsTrayIcon


# Worker signals for async operations
class WorkerSignals(QObject):
    finished = Signal(object)
    progress = Signal(int, int, str, str)
    error = Signal(str)


class AsyncWorker(QThread):
    """Executes long-running file operations on a background thread."""

    def __init__(self, target_func, *args, **kwargs):
        super().__init__()
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def run(self):
        try:
            # Inject callbacks if expected
            if "progress_callback" in self.kwargs:
                self.kwargs["progress_callback"] = self.signals.progress.emit
            if "is_cancelled" in self.kwargs:
                self.kwargs["is_cancelled"] = self.is_cancelled

            res = self.target_func(*self.args, **self.kwargs)
            self.signals.finished.emit(res)
        except Exception as e:
            self.signals.error.emit(str(e))


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloads Organizer")
        self.resize(650, 720)
        self.setMinimumSize(560, 600)

        # Core Services
        self.config_mgr = ConfigManager()
        self.logger = OrganizerLogger()
        self.history_mgr = HistoryManager()
        self.engine = OrganizerEngine(
            config_mgr=self.config_mgr,
            logger=self.logger,
            history_mgr=self.history_mgr,
        )

        # Watcher
        self.watcher = DownloadsWatcher(
            organizer=self.engine,
            config_mgr=self.config_mgr,
            on_files_organized=self._on_auto_files_organized,
        )

        # State
        self.current_scan: Optional[ScanResult] = None
        self.active_worker: Optional[AsyncWorker] = None
        self.app_icon = self._load_app_icon()
        self.setWindowIcon(self.app_icon)

        # Build UI
        self._init_ui()
        self._setup_tray()

        # Apply Modern Styling
        self.setStyleSheet(MODERN_STYLE)

        # Initial Scan
        self.trigger_scan()

        # Start watcher if configured
        if self.config_mgr.auto_organize:
            self._start_watcher()

    def _load_app_icon(self) -> QIcon:
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            return QIcon(str(icon_path))
        png_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        if png_path.exists():
            return QIcon(str(png_path))
        return QIcon()

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setSpacing(14)
        root_layout.setContentsMargins(22, 20, 22, 20)

        # Top Bar
        top_bar = QHBoxLayout()

        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        lbl_title = QLabel("DOWNLOADS ORGANIZER")
        lbl_title.setObjectName("TitleLabel")
        title_container.addWidget(lbl_title)

        lbl_sub = QLabel("Smart, Safe & Automated File Organization")
        lbl_sub.setObjectName("SubtitleLabel")
        title_container.addWidget(lbl_sub)
        top_bar.addLayout(title_container)

        top_bar.addStretch()

        # Top Bar Buttons
        self.btn_auto_toggle = QPushButton("Auto: OFF")
        self.btn_auto_toggle.setCheckable(True)
        self.btn_auto_toggle.setObjectName("SecondaryButton")
        self.btn_auto_toggle.setToolTip("Toggle real-time automatic monitoring of Downloads")
        self.btn_auto_toggle.clicked.connect(self._toggle_auto_organize)
        top_bar.addWidget(self.btn_auto_toggle)

        self.btn_settings = QPushButton("⚙️ Settings")
        self.btn_settings.setObjectName("SecondaryButton")
        self.btn_settings.clicked.connect(self._open_settings)
        top_bar.addWidget(self.btn_settings)

        root_layout.addLayout(top_bar)

        # Downloads Folder Section
        folder_card = QFrame()
        folder_card.setObjectName("CardPanel")
        folder_card_layout = QVBoxLayout(folder_card)
        folder_card_layout.setSpacing(8)
        folder_card_layout.setContentsMargins(14, 12, 14, 12)

        folder_hdr = QHBoxLayout()
        lbl_folder_title = QLabel("Downloads Folder")
        lbl_folder_title.setObjectName("SectionHeader")
        folder_hdr.addWidget(lbl_folder_title)
        folder_hdr.addStretch()

        btn_open_folder = QPushButton("📂 Open")
        btn_open_folder.setObjectName("SecondaryButton")
        btn_open_folder.setFixedHeight(26)
        btn_open_folder.clicked.connect(self._open_downloads_in_explorer)
        folder_hdr.addWidget(btn_open_folder)

        folder_card_layout.addLayout(folder_hdr)

        path_row = QHBoxLayout()
        self.txt_folder_path = QLineEdit()
        self.txt_folder_path.setText(str(self.config_mgr.downloads_folder))
        self.txt_folder_path.setReadOnly(True)
        path_row.addWidget(self.txt_folder_path)

        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setObjectName("SecondaryButton")
        self.btn_browse.clicked.connect(self._browse_folder)
        path_row.addWidget(self.btn_browse)

        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setObjectName("SecondaryButton")
        self.btn_refresh.setToolTip("Refresh & Rescan")
        self.btn_refresh.setFixedWidth(38)
        self.btn_refresh.clicked.connect(self.trigger_scan)
        path_row.addWidget(self.btn_refresh)

        folder_card_layout.addLayout(path_row)
        root_layout.addWidget(folder_card)

        # Statistics Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        # Files Found Card
        card_found = QFrame()
        card_found.setObjectName("StatCard")
        l_found = QVBoxLayout(card_found)
        l_found.setContentsMargins(10, 8, 10, 8)
        lbl_f_title = QLabel("Files Found")
        lbl_f_title.setObjectName("StatTitle")
        self.lbl_stat_found = QLabel("0")
        self.lbl_stat_found.setObjectName("StatValue")
        l_found.addWidget(lbl_f_title)
        l_found.addWidget(self.lbl_stat_found)
        stats_row.addWidget(card_found)

        # Files To Move Card
        card_move = QFrame()
        card_move.setObjectName("StatCard")
        l_move = QVBoxLayout(card_move)
        l_move.setContentsMargins(10, 8, 10, 8)
        lbl_m_title = QLabel("Files To Move")
        lbl_m_title.setObjectName("StatTitle")
        self.lbl_stat_move = QLabel("0")
        self.lbl_stat_move.setObjectName("StatValue")
        self.lbl_stat_move.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 24px;")
        l_move.addWidget(lbl_m_title)
        l_move.addWidget(self.lbl_stat_move)
        stats_row.addWidget(card_move)

        # Ignored Card
        card_ign = QFrame()
        card_ign.setObjectName("StatCard")
        l_ign = QVBoxLayout(card_ign)
        l_ign.setContentsMargins(10, 8, 10, 8)
        lbl_i_title = QLabel("Ignored")
        lbl_i_title.setObjectName("StatTitle")
        self.lbl_stat_ign = QLabel("0")
        self.lbl_stat_ign.setObjectName("StatValue")
        self.lbl_stat_ign.setStyleSheet("color: #94a3b8; font-weight: 700; font-size: 24px;")
        l_ign.addWidget(lbl_i_title)
        l_ign.addWidget(self.lbl_stat_ign)
        stats_row.addWidget(card_ign)

        root_layout.addLayout(stats_row)

        # Category Breakdown Table
        lbl_cat_head = QLabel("Category Breakdown")
        lbl_cat_head.setObjectName("SectionHeader")
        root_layout.addWidget(lbl_cat_head)

        self.table_categories = QTableWidget()
        self.table_categories.setColumnCount(2)
        self.table_categories.setHorizontalHeaderLabels(["Category", "Files Ready"])
        self.table_categories.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_categories.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_categories.setAlternatingRowColors(True)
        self.table_categories.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_categories.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_categories.verticalHeader().setVisible(False)
        root_layout.addWidget(self.table_categories)

        # Primary Action Buttons
        btn_action_box = QHBoxLayout()
        btn_action_box.setSpacing(12)

        self.btn_preview = QPushButton("Preview Changes")
        self.btn_preview.setObjectName("SecondaryButton")
        self.btn_preview.setFixedHeight(40)
        self.btn_preview.clicked.connect(self._on_preview_clicked)
        btn_action_box.addWidget(self.btn_preview)

        self.btn_organize = QPushButton("Organize Downloads")
        self.btn_organize.setObjectName("PrimaryButton")
        self.btn_organize.setFixedHeight(40)
        self.btn_organize.clicked.connect(self._on_organize_clicked)
        btn_action_box.addWidget(self.btn_organize)

        root_layout.addLayout(btn_action_box)

        # Undo Button Row
        undo_box = QHBoxLayout()
        self.btn_undo = QPushButton("↺ Undo Last Operation")
        self.btn_undo.setObjectName("UndoButton")
        self.btn_undo.setFixedHeight(36)
        self.btn_undo.clicked.connect(self._on_undo_clicked)
        undo_box.addWidget(self.btn_undo)
        root_layout.addLayout(undo_box)

        # Status Bar
        status_bar = QHBoxLayout()
        self.lbl_status = QLabel("Status: Ready")
        self.lbl_status.setObjectName("StatusLabel")
        status_bar.addWidget(self.lbl_status)
        status_bar.addStretch()

        self.lbl_footer_info = QLabel("Offline & Safe")
        self.lbl_footer_info.setStyleSheet("color: #64748b; font-size: 11px;")
        status_bar.addWidget(self.lbl_footer_info)

        root_layout.addLayout(status_bar)

        self._update_undo_button_state()

    def _setup_tray(self) -> None:
        self.tray = DownloadsTrayIcon(
            icon=self.app_icon,
            parent=self,
            on_toggle_auto=self._toggle_auto_organize,
            on_organize_now=self._on_organize_clicked,
            on_pause_monitoring=self._toggle_pause_monitoring,
            on_open_downloads=self._open_downloads_in_explorer,
            on_open_logs=self._open_logs_in_notepad,
            on_open_settings=self._open_settings,
            on_show_window=self._show_window,
            on_exit=self._exit_app,
        )
        self.tray.show()

    def _show_window(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _exit_app(self) -> None:
        self.watcher.stop()
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.config_mgr.minimize_to_tray and self.tray.isVisible():
            self.hide()
            if self.config_mgr.enable_notifications:
                self.tray.showMessage(
                    "Downloads Organizer",
                    "Application minimized to system tray.",
                    QSystemTrayIcon.Information,
                    2000,
                )
            event.ignore()
        else:
            self._exit_app()
            event.accept()

    def _browse_folder(self) -> None:
        current = self.txt_folder_path.text()
        chosen = QFileDialog.getExistingDirectory(self, "Select Downloads Folder", current)
        if chosen:
            self.config_mgr.downloads_folder = Path(chosen)
            self.txt_folder_path.setText(chosen)
            if self.watcher.is_running():
                self.watcher.stop()
                self._start_watcher()
            self.trigger_scan()

    def _open_downloads_in_explorer(self) -> None:
        folder = self.config_mgr.downloads_folder
        if folder.exists():
            if sys.platform == "win32":
                os.startfile(str(folder))
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)

    def _open_logs_in_notepad(self) -> None:
        log_file = get_log_file_path()
        if log_file.exists():
            if sys.platform == "win32":
                os.startfile(str(log_file))
            else:
                subprocess.run(["xdg-open", str(log_file)], check=False)

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self.config_mgr, self.logger, self)
        if dlg.exec() == SettingsDialog.Accepted:
            self.txt_folder_path.setText(str(self.config_mgr.downloads_folder))
            self.engine.refresh_classifier()
            if self.watcher.is_running():
                self.watcher.stop()
                self._start_watcher()
            self.trigger_scan()

    def _update_undo_button_state(self) -> None:
        has_undo = self.history_mgr.has_history()
        self.btn_undo.setEnabled(has_undo)
        if has_undo:
            batch = self.history_mgr.get_last_batch()
            count = len(batch.get("moves", [])) if batch else 0
            self.btn_undo.setText(f"↺ Undo Last Operation ({count} files)")
        else:
            self.btn_undo.setText("↺ Undo Last Operation")

    # ==========================
    # Scanning
    # ==========================
    def trigger_scan(self) -> None:
        self.lbl_status.setText("Status: Scanning Downloads folder...")
        self.btn_organize.setEnabled(False)
        self.btn_preview.setEnabled(False)

        worker = AsyncWorker(self.engine.scan, self.config_mgr.downloads_folder)
        worker.signals.finished.connect(self._on_scan_finished)
        worker.signals.error.connect(self._on_scan_error)
        self.active_worker = worker
        worker.start()

    def _on_scan_finished(self, scan_result: ScanResult) -> None:
        self.current_scan = scan_result
        self.lbl_stat_found.setText(str(scan_result.files_found))
        self.lbl_stat_move.setText(str(scan_result.files_to_move))
        self.lbl_stat_ign.setText(str(scan_result.files_ignored))

        # Populate Category Table
        counts = scan_result.category_counts
        self.table_categories.setRowCount(len(counts))

        sorted_cats = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        for row, (cat, count) in enumerate(sorted_cats):
            item_cat = QTableWidgetItem(cat)
            item_count = QTableWidgetItem(f"{count} files")
            item_count.setTextAlignment(Qt.AlignCenter)
            self.table_categories.setItem(row, 0, item_cat)
            self.table_categories.setItem(row, 1, item_count)

        if scan_result.files_to_move > 0:
            self.btn_organize.setEnabled(True)
            self.btn_preview.setEnabled(True)
            self.lbl_status.setText(f"Status: Ready — {scan_result.files_to_move} files can be organized")
        else:
            self.btn_organize.setEnabled(False)
            self.btn_preview.setEnabled(False)
            if scan_result.files_found == 0:
                self.lbl_status.setText("Status: Downloads folder is clean. No files to organize.")
            else:
                self.lbl_status.setText("Status: All existing files are categorized or ignored.")

        self._update_undo_button_state()

    def _on_scan_error(self, err_msg: str) -> None:
        self.lbl_status.setText(f"Status: Scan error — {err_msg}")
        self.btn_organize.setEnabled(False)
        self.btn_preview.setEnabled(False)

    # ==========================
    # Preview & Organize
    # ==========================
    def _on_preview_clicked(self) -> None:
        if not self.current_scan or self.current_scan.files_to_move == 0:
            QMessageBox.information(self, "Preview", "No files available to organize.")
            return

        dlg = PreviewDialog(self.current_scan, self)
        if dlg.exec() and dlg.proceed:
            self._on_organize_clicked()

    def _on_organize_clicked(self) -> None:
        if not self.current_scan or self.current_scan.files_to_move == 0:
            # Rescan first in case files changed
            self.trigger_scan()
            return

        prog_dlg = ProgressDialog("Organizing Downloads...", self)

        worker = AsyncWorker(
            self.engine.organize,
            scan_result=self.current_scan,
            progress_callback=True,
            is_cancelled=True,
        )

        prog_dlg.cancelled.connect(worker.cancel)

        def on_prog(cur, tot, fn, dst):
            prog_dlg.update_progress(cur, tot, fn, dst)

        def on_finish(result: OrganizeResult):
            prog_dlg.show_completion(
                moved=result.moved_count,
                skipped=result.skipped_count,
                errors=result.error_count,
                details=result.details,
                is_undo=False,
            )
            self.trigger_scan()
            self._update_undo_button_state()

        worker.signals.progress.connect(on_prog)
        worker.signals.finished.connect(on_finish)
        worker.signals.error.connect(lambda err: QMessageBox.critical(self, "Error", err))

        worker.start()
        prog_dlg.exec()

    # ==========================
    # Undo
    # ==========================
    def _on_undo_clicked(self) -> None:
        if not self.history_mgr.has_history():
            QMessageBox.information(self, "Undo", "No previous organization operation to undo.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Undo",
            "Restore files from the last organization operation back to their original locations?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        prog_dlg = ProgressDialog("Restoring Files (Undo)...", self)
        worker = AsyncWorker(
            self.engine.undo,
            progress_callback=True,
        )

        def on_prog(cur, tot, fn, dst):
            prog_dlg.update_progress(cur, tot, fn, dst)

        def on_finish(result: UndoResult):
            prog_dlg.show_completion(
                moved=result.restored_count,
                skipped=0,
                errors=result.error_count,
                details=result.details,
                is_undo=True,
            )
            self.trigger_scan()
            self._update_undo_button_state()

        worker.signals.progress.connect(on_prog)
        worker.signals.finished.connect(on_finish)
        worker.signals.error.connect(lambda err: QMessageBox.critical(self, "Error", err))

        worker.start()
        prog_dlg.exec()

    # ==========================
    # Automatic Mode & Watcher
    # ==========================
    def _toggle_auto_organize(self, enabled: Optional[bool] = None) -> None:
        if enabled is None:
            enabled = not self.btn_auto_toggle.isChecked()

        if enabled:
            self._start_watcher()
        else:
            self._stop_watcher()

    def _start_watcher(self) -> None:
        if self.watcher.start():
            self.btn_auto_toggle.setChecked(True)
            self.btn_auto_toggle.setText("Auto: ON")
            self.btn_auto_toggle.setStyleSheet(
                "background-color: #10b981; color: #ffffff; border-color: #059669;"
            )
            self.tray.set_auto_organize_checked(True)
            self.lbl_status.setText("Status: Automatic Monitoring Active")
        else:
            self.btn_auto_toggle.setChecked(False)
            self.btn_auto_toggle.setText("Auto: OFF")
            self.btn_auto_toggle.setStyleSheet("")
            self.tray.set_auto_organize_checked(False)
            QMessageBox.warning(
                self, "Monitoring", "Could not start automatic monitoring on Downloads folder."
            )

    def _stop_watcher(self) -> None:
        self.watcher.stop()
        self.btn_auto_toggle.setChecked(False)
        self.btn_auto_toggle.setText("Auto: OFF")
        self.btn_auto_toggle.setStyleSheet("")
        self.tray.set_auto_organize_checked(False)
        self.lbl_status.setText("Status: Automatic Monitoring Paused / Stopped")

    def _toggle_pause_monitoring(self) -> None:
        if self.watcher.is_paused():
            self.watcher.resume()
            self.tray.set_pause_action_text("Pause Monitoring")
            self.lbl_status.setText("Status: Automatic Monitoring Resumed")
        else:
            self.watcher.pause()
            self.tray.set_pause_action_text("Resume Monitoring")
            self.lbl_status.setText("Status: Automatic Monitoring Paused")

    def _on_auto_files_organized(self, count: int, filename: str) -> None:
        """Triggered from background watcher thread when files are organized."""
        # Refresh scan on main thread safely
        QThread.msleep(200)
        self.trigger_scan()
        if self.config_mgr.enable_notifications:
            self.tray.show_organize_notification(count, f"Processed {filename}")
