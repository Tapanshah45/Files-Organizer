"""Progress and Completion Dialog for Downloads Organizer.

Displays real-time move feedback during execution and summary of results
with error isolation on completion.
"""

from typing import List, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QFrame,
    QTextEdit,
)


class ProgressDialog(QDialog):
    """Real-time progress dialog during organization and undo operations."""

    cancelled = Signal()

    def __init__(self, title: str = "Organizing...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(520, 320)
        self.setMinimumSize(460, 280)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._is_cancelled = False
        self._init_ui(title)

    def _init_ui(self, title_text: str) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header Title
        self.title_label = QLabel(title_text)
        self.title_label.setObjectName("TitleLabel")
        layout.addWidget(self.title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Activity Card
        self.card = QFrame()
        self.card.setObjectName("CardPanel")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 12, 14, 12)

        self.lbl_action = QLabel("Preparing...")
        self.lbl_action.setObjectName("StatTitle")
        card_layout.addWidget(self.lbl_action)

        self.lbl_filename = QLabel("")
        self.lbl_filename.setStyleSheet("font-weight: 700; color: #ffffff; font-size: 14px;")
        card_layout.addWidget(self.lbl_filename)

        self.lbl_dest = QLabel("")
        self.lbl_dest.setStyleSheet("color: #38bdf8; font-size: 12px;")
        card_layout.addWidget(self.lbl_dest)

        layout.addWidget(self.card)

        # Counter text: "17 / 24 files completed"
        self.lbl_counter = QLabel("0 / 0 completed")
        self.lbl_counter.setAlignment(Qt.AlignCenter)
        self.lbl_counter.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self.lbl_counter)

        # Details log view (initially hidden, shown if errors occur)
        self.details_edit = QTextEdit()
        self.details_edit.setReadOnly(True)
        self.details_edit.setVisible(False)
        self.details_edit.setMaximumHeight(100)
        layout.addWidget(self.details_edit)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_box.addWidget(self.btn_cancel)

        self.btn_close = QPushButton("Close")
        self.btn_close.setObjectName("PrimaryButton")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setVisible(False)
        btn_box.addWidget(self.btn_close)

        layout.addLayout(btn_box)

    def update_progress(self, current: int, total: int, filename: str, destination: str) -> None:
        """Update progress bar, filename, destination, and counter."""
        if total > 0:
            pct = int((current / total) * 100)
            self.progress_bar.setValue(pct)
            self.lbl_counter.setText(f"{current} / {total} files completed")
        self.lbl_action.setText("Moving:")
        self.lbl_filename.setText(filename)
        self.lbl_dest.setText(f"→  {destination}")

    def show_completion(
        self,
        moved: int,
        skipped: int,
        errors: int,
        details: List[Dict[str, str]] = None,
        is_undo: bool = False,
    ) -> None:
        """Switch dialog to completed summary state."""
        action_word = "Restored" if is_undo else "Moved"
        self.progress_bar.setValue(100)
        self.title_label.setText("Operation Complete" if not is_undo else "Undo Complete")

        self.lbl_action.setText("Summary:")
        self.lbl_filename.setText(f"{action_word}: {moved}  |  Skipped: {skipped}  |  Errors: {errors}")
        self.lbl_dest.setText("All files organized according to rules.")

        if errors > 0 and details:
            self.details_edit.setVisible(True)
            error_lines = [
                f"• {d.get('file', '')}: {d.get('error', '')}"
                for d in details
                if d.get("status") == "FAILED"
            ]
            self.details_edit.setPlainText("\n".join(error_lines))

        self.btn_cancel.setVisible(False)
        self.btn_close.setVisible(True)

    def _on_cancel(self) -> None:
        self._is_cancelled = True
        self.cancelled.emit()
        self.lbl_action.setText("Cancelling...")
        self.btn_cancel.setEnabled(False)

    def is_cancelled(self) -> bool:
        return self._is_cancelled
