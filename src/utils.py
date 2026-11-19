"""Utility functions for Downloads Organizer.

Handles:
- Windows Downloads folder automatic detection via Shell32 Known Folders API
- Safe duplicate filename collision resolution: name (1).ext, name (2).ext
- AppData path resolution
- Application self-protection (prevent moving the organizer executable itself)
- Windows hidden/system file detection
- File readiness / locking checks for in-progress downloads
"""

import os
import sys
import re
import time
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Tuple, Optional


def get_default_downloads_folder() -> Path:
    """
    Detect the current Windows user's Downloads folder automatically.
    Uses Windows SHGetKnownFolderPath API (FOLDERID_Downloads) to handle
    custom locations (e.g. relocated to D:\\Downloads or OneDrive),
    with robust fallback to %USERPROFILE%\\Downloads.
    """
    if sys.platform == "win32":
        try:
            # FOLDERID_Downloads = {374DE290-123F-4565-9164-39C4925E467B}
            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", wintypes.DWORD),
                    ("Data2", wintypes.WORD),
                    ("Data3", wintypes.WORD),
                    ("Data4", wintypes.BYTE * 8),
                ]

            FOLDERID_Downloads = GUID(
                0x374DE290,
                0x123F,
                0x4565,
                (wintypes.BYTE * 8)(0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B),
            )

            path_ptr = wintypes.LPWSTR()
            # KF_FLAG_DEFAULT = 0
            res = ctypes.windll.shell32.SHGetKnownFolderPath(
                ctypes.byref(FOLDERID_Downloads), 0, None, ctypes.byref(path_ptr)
            )
            if res == 0 and path_ptr.value:
                downloads_path = Path(path_ptr.value)
                ctypes.windll.ole32.CoTaskMemFree(path_ptr)
                if downloads_path.exists():
                    return downloads_path.resolve()
        except Exception:
            pass

    # Fallback to %USERPROFILE%\Downloads or ~/Downloads
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidate = Path(user_profile) / "Downloads"
        if candidate.exists():
            return candidate.resolve()

    candidate = Path.home() / "Downloads"
    return candidate.resolve()


def get_app_data_dir() -> Path:
    """
    Return %LOCALAPPDATA%\\DownloadsOrganizer or fallback to ~/.downloads_organizer.
    Ensures directory exists.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        app_dir = Path(local_app_data) / "DownloadsOrganizer"
    else:
        app_dir = Path.home() / ".downloads_organizer"

    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "logs").mkdir(parents=True, exist_ok=True)
    return app_dir.resolve()


def get_log_file_path() -> Path:
    """Return path to organizer.log."""
    return get_app_data_dir() / "logs" / "organizer.log"


def get_history_file_path() -> Path:
    """Return path to history.json."""
    return get_app_data_dir() / "history.json"


def get_config_file_path() -> Path:
    """Return path to config.json."""
    return get_app_data_dir() / "config.json"


def get_safe_destination_path(target_dir: Path, filename: str) -> Path:
    """
    Generate a safe destination path that avoids overwriting existing files.
    If target_dir / filename does not exist, returns target_dir / filename.
    If it already exists, increments as:
    report (1).pdf, report (2).pdf, report (3).pdf, etc.
    Handles existing filenames with '(n)' patterns correctly.
    """
    target_dir = Path(target_dir)
    target_file = target_dir / filename

    if not target_file.exists():
        return target_file

    stem = target_file.stem
    suffix = target_file.suffix

    # Check if stem already ends with (n)
    pattern = re.compile(r"^(.*?)\s*\((\d+)\)$")
    match = pattern.match(stem)
    if match:
        base_stem = match.group(1).rstrip()
        counter = int(match.group(2)) + 1
    else:
        base_stem = stem
        counter = 1

    while True:
        candidate = target_dir / f"{base_stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def is_app_itself(file_path: Path) -> bool:
    """
    Check if the given file_path is the running application or executable.
    Prevents the organizer from moving itself.
    """
    try:
        name_lower = file_path.name.lower()
        if name_lower in ("downloadsorganizer.exe", "app.py"):
            return True

        if getattr(sys, "frozen", False):
            if name_lower == Path(sys.executable).name.lower():
                if file_path.resolve() == Path(sys.executable).resolve():
                    return True

        for arg in sys.argv:
            try:
                arg_path = Path(arg)
                if arg_path.name and arg_path.name.lower() == name_lower:
                    if arg_path.resolve() == file_path.resolve():
                        return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def is_hidden_or_system(file_path: Path) -> bool:
    """
    Check if a file has Windows hidden or system attributes or begins with a dot.
    """
    name = file_path.name
    if name.startswith(".") and name not in (".", ".."):
        return True

    if sys.platform == "win32":
        try:
            FILE_ATTRIBUTE_HIDDEN = 0x2
            FILE_ATTRIBUTE_SYSTEM = 0x4
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
            if attrs != -1 and (attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)):
                return True
        except Exception:
            pass

    return False


def is_file_ready(file_path: Path, wait_ms: int = 200) -> bool:
    """
    Check if a file is ready to be moved (not locked by an active download or application).
    Returns True if file exists and can be opened with read access without sharing violation.
    """
    if not file_path.exists() or not file_path.is_file():
        return False

    try:
        # Check size stability over a small interval
        initial_size = file_path.stat().st_size
        if wait_ms > 0:
            time.sleep(wait_ms / 1000.0)
            if not file_path.exists():
                return False
            if file_path.stat().st_size != initial_size:
                return False

        # Attempt to open file to test locking
        with open(file_path, "rb") as f:
            f.read(1)
        return True
    except (PermissionError, OSError):
        return False
