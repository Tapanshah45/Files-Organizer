"""Logging system for Downloads Organizer.

Maintains structured operation records in %LOCALAPPDATA%\\DownloadsOrganizer\\logs\\organizer.log
following the exact specification:
Timestamp
Operation
Original file
Destination
Result
Error message if applicable
"""

import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from src.utils import get_log_file_path


class OrganizerLogger:
    """Thread-safe logger for recording file operations."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = Path(log_path) if log_path else get_log_file_path()
        self._lock = threading.Lock()
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def log_operation(
        self,
        operation: str,
        source: Union[str, Path],
        destination: Union[str, Path],
        success: bool,
        error_message: str = "",
    ) -> None:
        """
        Record a file operation in the structured log.

        Format:
        YYYY-MM-DD HH:MM:SS
        <OPERATION>
        <ORIGINAL FILE>
        <DESTINATION>
        <SUCCESS | FAILED>
        [Error message if failed]
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "FAILED"

        lines = [
            timestamp,
            operation.upper(),
            str(source),
            str(destination),
            status,
        ]
        if not success and error_message:
            lines.append(error_message.strip())

        entry = "\n".join(lines) + "\n\n"

        with self._lock:
            try:
                self._ensure_log_dir()
                # Check file size for rotation if > 10MB
                if self.log_path.exists() and self.log_path.stat().st_size > 10 * 1024 * 1024:
                    backup = self.log_path.with_suffix(".log.1")
                    if backup.exists():
                        backup.unlink(missing_ok=True)
                    self.log_path.rename(backup)

                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(entry)
            except Exception:
                pass

    def get_recent_entries(self, max_entries: int = 50) -> str:
        """Retrieve recent log text for viewing."""
        if not self.log_path.exists():
            return "No log entries found."
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            blocks = content.strip().split("\n\n")
            recent = blocks[-max_entries:] if len(blocks) > max_entries else blocks
            return "\n\n".join(recent)
        except Exception as e:
            return f"Error reading log file: {e}"

    def clear_logs(self) -> bool:
        """Clear current log contents."""
        with self._lock:
            try:
                if self.log_path.exists():
                    self.log_path.write_text("", encoding="utf-8")
                return True
            except Exception:
                return False
