"""Automatic filesystem watcher for Downloads folder using watchdog.

Monitors the downloads folder for new file arrivals.
Implements stability checks to avoid touching files while they are actively
being downloaded (e.g. .crdownload, .part, .download, or locked files).
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.classifier import FileClassifier
from src.config import ConfigManager
from src.organizer import OrganizerEngine
from src.utils import is_file_ready, is_hidden_or_system


class DownloadsEventHandler(FileSystemEventHandler):
    """Handles file system events for new files in Downloads."""

    def __init__(
        self,
        organizer: OrganizerEngine,
        config_mgr: ConfigManager,
        on_files_organized: Optional[Callable[[int, str], None]] = None,
    ):
        super().__init__()
        self.organizer = organizer
        self.config_mgr = config_mgr
        self.on_files_organized = on_files_organized
        self._pending_files: Set[Path] = set()
        self._lock = threading.Lock()
        self._paused = False

    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    def is_paused(self) -> bool:
        return self._paused

    def on_created(self, event: FileSystemEvent) -> None:
        self._handle_event(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        # Handles downloads finishing and being renamed from .crdownload to final name
        dest_path = getattr(event, "dest_path", None)
        if dest_path:
            self._queue_file(Path(dest_path))

    def _handle_event(self, event: FileSystemEvent) -> None:
        if event.is_directory or self._paused:
            return
        self._queue_file(Path(event.src_path))

    def _queue_file(self, file_path: Path) -> None:
        if self._paused:
            return

        # Do not queue if file is in category folder
        known_categories = set(self.config_mgr.categories.keys())
        known_categories.add(self.config_mgr.unknown_folder_name)
        if file_path.parent.name in known_categories:
            return

        # Ignore hidden/system files
        if is_hidden_or_system(file_path):
            return

        # Ignore known temporary/in-progress extensions
        ext = file_path.suffix.lower()
        if ext in self.config_mgr.ignored_extensions:
            return

        with self._lock:
            if file_path not in self._pending_files:
                self._pending_files.add(file_path)
                threading.Thread(
                    target=self._process_file_worker,
                    args=(file_path,),
                    daemon=True,
                ).start()

    def _process_file_worker(self, file_path: Path) -> None:
        """Wait for file stability, then trigger organization."""
        delay = self.config_mgr.stability_delay_seconds
        time.sleep(delay)

        # Wait until file is unlocked and size is stable
        max_attempts = 15
        stable = False
        for _ in range(max_attempts):
            if not file_path.exists():
                break
            # Still in-progress extension?
            if file_path.suffix.lower() in self.config_mgr.ignored_extensions:
                break
            if is_file_ready(file_path, wait_ms=400):
                stable = True
                break
            time.sleep(1.0)

        with self._lock:
            self._pending_files.discard(file_path)

        if stable and file_path.exists() and not self._paused:
            # Run scan and organize for Downloads
            scan_res = self.organizer.scan(self.config_mgr.downloads_folder)
            if scan_res.files_to_move > 0:
                org_res = self.organizer.organize(scan_res)
                if org_res.moved_count > 0 and self.on_files_organized:
                    self.on_files_organized(org_res.moved_count, file_path.name)


class DownloadsWatcher:
    """Manages watchdog observer lifecycle for Downloads folder monitoring."""

    def __init__(
        self,
        organizer: OrganizerEngine,
        config_mgr: ConfigManager,
        on_files_organized: Optional[Callable[[int, str], None]] = None,
    ):
        self.organizer = organizer
        self.config_mgr = config_mgr
        self.on_files_organized = on_files_organized
        self.observer: Optional[Observer] = None
        self.handler: Optional[DownloadsEventHandler] = None
        self._running = False

    def start(self) -> bool:
        """Start monitoring downloads directory."""
        if self._running:
            return True

        folder = self.config_mgr.downloads_folder
        if not folder.exists():
            return False

        try:
            self.handler = DownloadsEventHandler(
                organizer=self.organizer,
                config_mgr=self.config_mgr,
                on_files_organized=self.on_files_organized,
            )
            self.observer = Observer()
            # Non-recursive watch on Downloads root
            self.observer.schedule(
                self.handler,
                str(folder),
                recursive=self.config_mgr.recursive,
            )
            self.observer.start()
            self._running = True
            return True
        except Exception as e:
            self.organizer.logger.log_operation(
                "WATCHER_START", str(folder), "", False, str(e)
            )
            return False

    def pause(self) -> None:
        """Pause processing new events."""
        if self.handler:
            self.handler.set_paused(True)

    def resume(self) -> None:
        """Resume processing new events."""
        if self.handler:
            self.handler.set_paused(False)

    def is_paused(self) -> bool:
        return self.handler.is_paused() if self.handler else False

    def stop(self) -> None:
        """Stop watcher thread cleanly."""
        if self.observer and self._running:
            try:
                self.observer.stop()
                self.observer.join(timeout=2)
            except Exception:
                pass
            self._running = False
            self.observer = None
            self.handler = None

    def is_running(self) -> bool:
        return self._running
