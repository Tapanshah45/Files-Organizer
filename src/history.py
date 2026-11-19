"""History and Undo Manager for Downloads Organizer.

Records batches of file move operations to %LOCALAPPDATA%\\DownloadsOrganizer\\history.json
to support reverting / undoing operations safely.
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.utils import get_history_file_path


class HistoryManager:
    """Manages history records for undo functionality."""

    def __init__(self, history_path: Optional[Path] = None):
        self.history_path = Path(history_path) if history_path else get_history_file_path()
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.history_path.exists():
                with open(self.history_path, "w", encoding="utf-8") as f:
                    json.dump({"batches": []}, f, indent=2)
        except Exception:
            pass

    def _load_data(self) -> Dict:
        if not self.history_path.exists():
            return {"batches": []}
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"batches": []}

    def _save_data(self, data: Dict) -> bool:
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            temp_file = self.history_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.history_path)
            return True
        except Exception:
            return False

    def record_batch(self, moves: List[Dict[str, str]]) -> bool:
        """
        Record a successful batch of moves into history.
        Each move dict must have 'original' and 'destination' path strings.
        """
        if not moves:
            return False

        with self._lock:
            data = self._load_data()
            batch = {
                "id": datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "moves": moves,
            }
            data.setdefault("batches", []).append(batch)
            # Limit history to last 50 batches to prevent unbounded growth
            if len(data["batches"]) > 50:
                data["batches"] = data["batches"][-50:]
            return self._save_data(data)

    def get_last_batch(self) -> Optional[Dict]:
        """Retrieve the most recent batch without removing it."""
        with self._lock:
            data = self._load_data()
            batches = data.get("batches", [])
            return batches[-1] if batches else None

    def pop_last_batch(self) -> Optional[Dict]:
        """Retrieve and remove the most recent batch from history."""
        with self._lock:
            data = self._load_data()
            batches = data.get("batches", [])
            if not batches:
                return None
            last = batches.pop()
            self._save_data(data)
            return last

    def has_history(self) -> bool:
        """Check if any undo operations are available."""
        with self._lock:
            data = self._load_data()
            return len(data.get("batches", [])) > 0

    def clear(self) -> bool:
        """Clear all stored history."""
        with self._lock:
            return self._save_data({"batches": []})
