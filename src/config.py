"""Configuration Manager for Downloads Organizer.

Handles loading, validating, and saving configuration to %LOCALAPPDATA%\\DownloadsOrganizer\\config.json.
Falls back to default settings when configuration is absent or corrupted.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from src.utils import get_config_file_path, get_default_downloads_folder


DEFAULT_CATEGORIES = {
    "Documents": [".pdf", ".doc", ".docx", ".docm", ".txt", ".rtf", ".odt", ".pages"],
    "Spreadsheets": [".xls", ".xlsx", ".xlsm", ".csv", ".ods"],
    "Presentations": [".ppt", ".pptx", ".pptm", ".odp"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "Installers": [".exe", ".msi", ".msp"],
    "Scripts": [".ps1", ".bat", ".cmd", ".py", ".js", ".ts", ".psm1", ".sh"],
    "Web": [".html", ".htm", ".css", ".json", ".xml"],
    "Torrents": [".torrent"],
    "Disk Images": [".iso", ".img", ".vhd", ".vhdx"],
}

DEFAULT_IGNORED_EXTENSIONS = [
    ".lnk",
    ".url",
    ".tmp",
    ".crdownload",
    ".part",
    ".download",
]

DEFAULT_IGNORED_FILES = [
    "desktop.ini",
    "thumbs.db",
]


class ConfigManager:
    """Manages application settings persistence and defaults."""

    def __init__(self, config_path: Path = None):
        self.config_path = Path(config_path) if config_path else get_config_file_path()
        self.data: Dict[str, Any] = {}
        self.load()

    def get_defaults(self) -> Dict[str, Any]:
        """Generate default configuration dictionary."""
        downloads_dir = get_default_downloads_folder()
        return {
            "downloads_folder": str(downloads_dir),
            "organize_unknown_files": True,
            "unknown_folder_name": "Other",
            "create_categories": True,
            "recursive": False,
            "auto_organize": False,
            "enable_notifications": True,
            "minimize_to_tray": True,
            "stability_delay_seconds": 3,
            "categories": {k: list(v) for k, v in DEFAULT_CATEGORIES.items()},
            "ignored_extensions": list(DEFAULT_IGNORED_EXTENSIONS),
            "ignored_files": list(DEFAULT_IGNORED_FILES),
        }

    def load(self) -> Dict[str, Any]:
        """Load configuration from disk, creating default file if missing."""
        defaults = self.get_defaults()
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Merge missing keys from defaults
                for key, val in defaults.items():
                    if key not in loaded:
                        loaded[key] = val

                # Ensure downloads_folder exists or fallback
                dl_folder = loaded.get("downloads_folder")
                if not dl_folder or not Path(dl_folder).exists():
                    loaded["downloads_folder"] = str(get_default_downloads_folder())

                self.data = loaded
                return self.data
            except Exception:
                pass

        self.data = defaults
        self.save()
        return self.data

    def save(self) -> bool:
        """Save current configuration to disk."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            return True
        except Exception:
            return False

    def reset_to_defaults(self) -> Dict[str, Any]:
        """Reset configuration to defaults and persist."""
        self.data = self.get_defaults()
        self.save()
        return self.data

    def get(self, key: str, default: Any = None) -> Any:
        """Get config property with fallback."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """Set config property and optionally persist."""
        self.data[key] = value
        if auto_save:
            self.save()

    @property
    def downloads_folder(self) -> Path:
        """Return configured Downloads folder as Path."""
        folder_str = self.data.get("downloads_folder")
        if folder_str:
            p = Path(folder_str)
            if p.exists():
                return p.resolve()
        return get_default_downloads_folder()

    @downloads_folder.setter
    def downloads_folder(self, path: Path) -> None:
        self.data["downloads_folder"] = str(Path(path).resolve())
        self.save()

    @property
    def categories(self) -> Dict[str, List[str]]:
        return self.data.get("categories", DEFAULT_CATEGORIES)

    @property
    def ignored_extensions(self) -> List[str]:
        return self.data.get("ignored_extensions", DEFAULT_IGNORED_EXTENSIONS)

    @property
    def ignored_files(self) -> List[str]:
        return self.data.get("ignored_files", DEFAULT_IGNORED_FILES)

    @property
    def organize_unknown_files(self) -> bool:
        return bool(self.data.get("organize_unknown_files", True))

    @property
    def unknown_folder_name(self) -> str:
        return str(self.data.get("unknown_folder_name", "Other"))

    @property
    def recursive(self) -> bool:
        return bool(self.data.get("recursive", False))

    @property
    def auto_organize(self) -> bool:
        return bool(self.data.get("auto_organize", False))

    @property
    def enable_notifications(self) -> bool:
        return bool(self.data.get("enable_notifications", True))

    @property
    def minimize_to_tray(self) -> bool:
        return bool(self.data.get("minimize_to_tray", True))

    @property
    def stability_delay_seconds(self) -> int:
        return int(self.data.get("stability_delay_seconds", 3))
