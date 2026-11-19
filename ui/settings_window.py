"""Settings Dialog for Downloads Organizer.

Allows editing of paths, categories, extensions, ignore rules,
notifications, and system tray preferences.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QTextEdit,
)

from src.config import ConfigManager
from src.logger import OrganizerLogger
from src.utils import get_log_file_path, get_default_downloads_folder


class SettingsDialog(QDialog):
    """Configuration dialog with tabs for general, categories, and logs."""

    def __init__(self, config_mgr: ConfigManager, logger: OrganizerLogger, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.logger = logger
        self.setWindowTitle("Settings - Downloads Organizer")
        self.resize(680, 500)
        self.setMinimumSize(580, 420)
        self._init_ui()
        self._load_values()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Tabs
        self.tabs = QTabWidget()

        # Tab 1: General
        self.tab_general = QWidget()
        self._setup_general_tab()
        self.tabs.addTab(self.tab_general, "General")

        # Tab 2: Categories & Extensions
        self.tab_categories = QWidget()
        self._setup_categories_tab()
        self.tabs.addTab(self.tab_categories, "Categories & Extensions")

        # Tab 3: Ignore Rules
        self.tab_ignore = QWidget()
        self._setup_ignore_tab()
        self.tabs.addTab(self.tab_ignore, "Ignore Rules")

        # Tab 4: Logs & Diagnostics
        self.tab_logs = QWidget()
        self._setup_logs_tab()
        self.tabs.addTab(self.tab_logs, "Logs & History")

        layout.addWidget(self.tabs)

        # Bottom Buttons
        btn_box = QHBoxLayout()

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.setObjectName("SecondaryButton")
        self.btn_reset.clicked.connect(self._reset_defaults)
        btn_box.addWidget(self.btn_reset)

        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.clicked.connect(self._save_settings)
        btn_box.addWidget(self.btn_save)

        layout.addLayout(btn_box)

    def _setup_general_tab(self) -> None:
        layout = QVBoxLayout(self.tab_general)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Downloads Folder
        lbl_dl = QLabel("Downloads Folder Location:")
        lbl_dl.setStyleSheet("font-weight: 600;")
        layout.addWidget(lbl_dl)

        path_box = QHBoxLayout()
        self.txt_downloads = QLineEdit()
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self._browse_folder)
        path_box.addWidget(self.txt_downloads)
        path_box.addWidget(self.btn_browse)
        layout.addLayout(path_box)

        # Unknown files option
        self.chk_unknown = QCheckBox("Organize unknown file extensions into fallback folder")
        layout.addWidget(self.chk_unknown)

        unknown_box = QHBoxLayout()
        lbl_unk_name = QLabel("Fallback Folder Name:")
        self.txt_unk_name = QLineEdit()
        self.txt_unk_name.setMaximumWidth(160)
        unknown_box.addWidget(lbl_unk_name)
        unknown_box.addWidget(self.txt_unk_name)
        unknown_box.addStretch()
        layout.addLayout(unknown_box)

        # Recursive scan
        self.chk_recursive = QCheckBox("Recursive scan (Scan existing subfolders outside of categories)")
        layout.addWidget(self.chk_recursive)

        # Auto Organize on startup
        self.chk_auto = QCheckBox("Enable Automatic Monitoring on application start")
        layout.addWidget(self.chk_auto)

        # Stability Delay
        delay_box = QHBoxLayout()
        lbl_delay = QLabel("Download stability wait time (seconds):")
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(1, 60)
        self.spin_delay.setValue(3)
        delay_box.addWidget(lbl_delay)
        delay_box.addWidget(self.spin_delay)
        delay_box.addStretch()
        layout.addLayout(delay_box)

        # System tray and notifications
        self.chk_notifications = QCheckBox("Show Windows desktop notifications when files are organized")
        layout.addWidget(self.chk_notifications)

        self.chk_tray = QCheckBox("Minimize application to Windows System Tray on close/minimize")
        layout.addWidget(self.chk_tray)

        layout.addStretch()

    def _setup_categories_tab(self) -> None:
        layout = QVBoxLayout(self.tab_categories)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        info = QLabel(
            "Double-click any category extensions cell to edit extensions (separated by comma or space)."
        )
        info.setObjectName("SubtitleLabel")
        layout.addWidget(info)

        self.table_cats = QTableWidget()
        self.table_cats.setColumnCount(2)
        self.table_cats.setHorizontalHeaderLabels(["Category Folder", "Associated Extensions"])
        self.table_cats.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_cats.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_cats)

        btn_row = QHBoxLayout()
        self.btn_add_cat = QPushButton("+ Add Category")
        self.btn_add_cat.setObjectName("SecondaryButton")
        self.btn_add_cat.clicked.connect(self._add_category_row)
        btn_row.addWidget(self.btn_add_cat)

        self.btn_del_cat = QPushButton("- Remove Selected")
        self.btn_del_cat.setObjectName("SecondaryButton")
        self.btn_del_cat.clicked.connect(self._remove_category_row)
        btn_row.addWidget(self.btn_del_cat)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _setup_ignore_tab(self) -> None:
        layout = QVBoxLayout(self.tab_ignore)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        lbl_ext = QLabel("Ignored Extensions (files with these extensions will never be moved):")
        lbl_ext.setStyleSheet("font-weight: 600;")
        layout.addWidget(lbl_ext)

        self.txt_ignored_exts = QLineEdit()
        self.txt_ignored_exts.setPlaceholderText(".lnk, .url, .tmp, .crdownload, .part, .download")
        layout.addWidget(self.txt_ignored_exts)

        lbl_files = QLabel("Ignored Filenames (exact names, separated by comma):")
        lbl_files.setStyleSheet("font-weight: 600;")
        layout.addWidget(lbl_files)

        self.txt_ignored_files = QLineEdit()
        self.txt_ignored_files.setPlaceholderText("desktop.ini, thumbs.db")
        layout.addWidget(self.txt_ignored_files)

        note = QLabel(
            "Note: In addition to these rules, the application executable itself and Windows hidden/system files are automatically protected."
        )
        note.setObjectName("SubtitleLabel")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()

    def _setup_logs_tab(self) -> None:
        layout = QVBoxLayout(self.tab_logs)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        log_path = get_log_file_path()
        lbl_path = QLabel(f"Log Location: {log_path}")
        lbl_path.setObjectName("SubtitleLabel")
        layout.addWidget(lbl_path)

        self.txt_log_view = QTextEdit()
        self.txt_log_view.setReadOnly(True)
        self.txt_log_view.setPlaceholderText("Recent log entries will display here.")
        layout.addWidget(self.txt_log_view)

        btn_bar = QHBoxLayout()
        self.btn_open_log_folder = QPushButton("Open Logs Folder")
        self.btn_open_log_folder.setObjectName("SecondaryButton")
        self.btn_open_log_folder.clicked.connect(self._open_log_dir)
        btn_bar.addWidget(self.btn_open_log_folder)

        self.btn_refresh_log = QPushButton("Refresh Logs")
        self.btn_refresh_log.setObjectName("SecondaryButton")
        self.btn_refresh_log.clicked.connect(self._refresh_logs)
        btn_bar.addWidget(self.btn_refresh_log)

        self.btn_clear_log = QPushButton("Clear Logs")
        self.btn_clear_log.setObjectName("SecondaryButton")
        self.btn_clear_log.clicked.connect(self._clear_logs)
        btn_bar.addWidget(self.btn_clear_log)

        btn_bar.addStretch()
        layout.addLayout(btn_bar)

    def _load_values(self) -> None:
        self.txt_downloads.setText(str(self.config_mgr.downloads_folder))
        self.chk_unknown.setChecked(self.config_mgr.organize_unknown_files)
        self.txt_unk_name.setText(self.config_mgr.unknown_folder_name)
        self.chk_recursive.setChecked(self.config_mgr.recursive)
        self.chk_auto.setChecked(self.config_mgr.auto_organize)
        self.spin_delay.setValue(self.config_mgr.stability_delay_seconds)
        self.chk_notifications.setChecked(self.config_mgr.enable_notifications)
        self.chk_tray.setChecked(self.config_mgr.minimize_to_tray)

        # Populate categories table
        cats = self.config_mgr.categories
        self.table_cats.setRowCount(len(cats))
        for row, (cat, exts) in enumerate(cats.items()):
            item_cat = QTableWidgetItem(cat)
            item_exts = QTableWidgetItem(", ".join(exts))
            self.table_cats.setItem(row, 0, item_cat)
            self.table_cats.setItem(row, 1, item_exts)

        # Ignore rules
        self.txt_ignored_exts.setText(", ".join(self.config_mgr.ignored_extensions))
        self.txt_ignored_files.setText(", ".join(self.config_mgr.ignored_files))

        # Recent logs
        self._refresh_logs()

    def _browse_folder(self) -> None:
        current = self.txt_downloads.text() or str(get_default_downloads_folder())
        selected = QFileDialog.getExistingDirectory(self, "Select Downloads Folder", current)
        if selected:
            self.txt_downloads.setText(selected)

    def _add_category_row(self) -> None:
        row = self.table_cats.rowCount()
        self.table_cats.insertRow(row)
        self.table_cats.setItem(row, 0, QTableWidgetItem(f"NewCategory{row + 1}"))
        self.table_cats.setItem(row, 1, QTableWidgetItem(".ext1, .ext2"))

    def _remove_category_row(self) -> None:
        current_row = self.table_cats.currentRow()
        if current_row >= 0:
            self.table_cats.removeRow(current_row)

    def _refresh_logs(self) -> None:
        self.txt_log_view.setPlainText(self.logger.get_recent_entries(50))

    def _clear_logs(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear all operation logs?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.logger.clear_logs()
            self._refresh_logs()

    def _open_log_dir(self) -> None:
        log_dir = get_log_file_path().parent
        if sys.platform == "win32":
            os.startfile(str(log_dir))
        else:
            subprocess.run(["xdg-open", str(log_dir)], check=False)

    def _reset_defaults(self) -> None:
        reply = QMessageBox.question(
            self,
            "Reset Defaults",
            "Reset all settings to default values?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.config_mgr.reset_to_defaults()
            self._load_values()

    def _save_settings(self) -> None:
        # Validate downloads path
        folder_str = self.txt_downloads.text().strip()
        if not folder_str:
            QMessageBox.warning(self, "Validation Error", "Please provide a valid Downloads folder.")
            return

        dl_path = Path(folder_str)
        if not dl_path.exists():
            try:
                dl_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(
                    self, "Validation Error", f"Cannot create folder: {dl_path}\n{e}"
                )
                return

        # Parse categories
        new_cats: Dict[str, List[str]] = {}
        for r in range(self.table_cats.rowCount()):
            item_cat = self.table_cats.item(r, 0)
            item_exts = self.table_cats.item(r, 1)
            if not item_cat or not item_cat.text().strip():
                continue
            cat_name = item_cat.text().strip()
            ext_list = []
            if item_exts:
                raw_exts = item_exts.text().replace(" ", ",").split(",")
                for ext in raw_exts:
                    clean = ext.strip().lower()
                    if clean:
                        if not clean.startswith("."):
                            clean = f".{clean}"
                        if clean not in ext_list:
                            ext_list.append(clean)
            new_cats[cat_name] = ext_list

        # Parse ignored extensions
        raw_ign_exts = self.txt_ignored_exts.text().replace(" ", ",").split(",")
        ign_exts = []
        for ext in raw_ign_exts:
            clean = ext.strip().lower()
            if clean:
                if not clean.startswith("."):
                    clean = f".{clean}"
                if clean not in ign_exts:
                    ign_exts.append(clean)

        # Parse ignored files
        raw_ign_files = self.txt_ignored_files.text().replace(";", ",").split(",")
        ign_files = [f.strip().lower() for f in raw_ign_files if f.strip()]

        # Apply to config manager
        self.config_mgr.set("downloads_folder", str(dl_path.resolve()), auto_save=False)
        self.config_mgr.set("organize_unknown_files", self.chk_unknown.isChecked(), auto_save=False)
        self.config_mgr.set(
            "unknown_folder_name", self.txt_unk_name.text().strip() or "Other", auto_save=False
        )
        self.config_mgr.set("recursive", self.chk_recursive.isChecked(), auto_save=False)
        self.config_mgr.set("auto_organize", self.chk_auto.isChecked(), auto_save=False)
        self.config_mgr.set(
            "stability_delay_seconds", self.spin_delay.value(), auto_save=False
        )
        self.config_mgr.set(
            "enable_notifications", self.chk_notifications.isChecked(), auto_save=False
        )
        self.config_mgr.set("minimize_to_tray", self.chk_tray.isChecked(), auto_save=False)
        self.config_mgr.set("categories", new_cats, auto_save=False)
        self.config_mgr.set("ignored_extensions", ign_exts, auto_save=False)
        self.config_mgr.set("ignored_files", ign_files, auto_save=False)

        self.config_mgr.save()
        self.accept()
