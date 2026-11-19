"""Preview / Dry-Run Dialog for Downloads Organizer.

Displays planned file relocations without moving anything.
Allows the user to inspect destinations, filter by text, and proceed or cancel.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
)

from src.organizer import ScanResult


class PreviewDialog(QDialog):
    """Modal dialog displaying the dry-run inspection of planned file moves."""

    def __init__(self, scan_result: ScanResult, parent=None):
        super().__init__(parent)
        self.scan_result = scan_result
        self.proceed = False
        self.setWindowTitle("Preview File Organization (Dry Run)")
        self.resize(760, 520)
        self.setMinimumSize(600, 400)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Title
        title_box = QHBoxLayout()
        title = QLabel("Planned Organization Changes")
        title.setObjectName("TitleLabel")
        title_box.addWidget(title)
        title_box.addStretch()

        count_badge = QLabel(f"{self.scan_result.files_to_move} files to move")
        count_badge.setObjectName("BadgeCount")
        title_box.addWidget(count_badge)
        layout.addLayout(title_box)

        sub = QLabel(
            "Review proposed moves below. No files will be modified until you click 'Proceed with Organization'."
        )
        sub.setObjectName("SubtitleLabel")
        layout.addWidget(sub)

        # Search / Filter Bar
        filter_box = QHBoxLayout()
        filter_label = QLabel("Filter:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by filename or category...")
        self.search_input.textChanged.connect(self._apply_filter)
        filter_box.addWidget(filter_label)
        filter_box.addWidget(self.search_input)
        layout.addLayout(filter_box)

        # Table of Planned Moves
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Original File",
            "Category",
            "Planned Destination",
            "Size",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self._populate_table()
        layout.addWidget(self.table)

        # Ignored files summary note if any
        if self.scan_result.files_ignored > 0:
            ignored_note = QLabel(
                f"ℹ️ {self.scan_result.files_ignored} files (temporary, shortcuts, system files) will be safely ignored."
            )
            ignored_note.setStyleSheet("color: #94a3b8; font-size: 11px;")
            layout.addWidget(ignored_note)

        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_proceed = QPushButton("Proceed with Organization")
        self.btn_proceed.setObjectName("PrimaryButton")
        self.btn_proceed.clicked.connect(self._on_proceed)
        btn_box.addWidget(self.btn_proceed)

        layout.addLayout(btn_box)

    def _populate_table(self) -> None:
        moves = self.scan_result.planned_moves
        self.table.setRowCount(len(moves))

        for row, move in enumerate(moves):
            # Original file
            item_orig = QTableWidgetItem(move.source_path.name)
            item_orig.setToolTip(str(move.source_path))

            # Category
            item_cat = QTableWidgetItem(move.category)
            item_cat.setTextAlignment(Qt.AlignCenter)

            # Planned Destination (relative to downloads for clean display)
            try:
                rel_dest = move.proposed_destination.relative_to(self.scan_result.downloads_folder)
                display_dest = str(rel_dest)
            except Exception:
                display_dest = str(move.proposed_destination)

            item_dest = QTableWidgetItem(f"→  {display_dest}")
            item_dest.setToolTip(str(move.proposed_destination))

            # File size
            size_str = self._format_size(move.file_size)
            item_size = QTableWidgetItem(size_str)
            item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row, 0, item_orig)
            self.table.setItem(row, 1, item_cat)
            self.table.setItem(row, 2, item_dest)
            self.table.setItem(row, 3, item_size)

        self.table.setColumnWidth(0, 220)

    def _apply_filter(self, query: str) -> None:
        query = query.strip().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(3):
                item = self.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def _on_proceed(self) -> None:
        self.proceed = True
        self.accept()
