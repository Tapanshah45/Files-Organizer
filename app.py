"""Downloads Organizer - Application Entry Point.

Starts the PySide6 modern Windows application with high-DPI awareness,
AppUserModelID registration for taskbar branding, and CLI flags.
"""

import os
import sys
import ctypes
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from src.organizer import OrganizerEngine
from src.config import ConfigManager


def setup_windows_environment():
    """Enable Windows DPI awareness and register Taskbar AppUserModelID."""
    if sys.platform == "win32":
        try:
            # Set high DPI awareness
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        try:
            # Set taskbar icon and group identity
            app_id = "DownloadsOrganizer.ModernApp.1.0.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass


def main():
    setup_windows_environment()

    # Enable Qt High-DPI attributes
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Downloads Organizer")
    app.setApplicationDisplayName("Downloads Organizer")
    app.setOrganizationName("DownloadsOrganizer")

    # Set Application Icon
    icon_path = BASE_DIR / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Handle quick CLI flags
    if "--organize-now" in sys.argv:
        print("Running quick organization in CLI mode...")
        engine = OrganizerEngine()
        scan = engine.scan()
        print(f"Files found: {scan.files_found}, to move: {scan.files_to_move}")
        if scan.files_to_move > 0:
            res = engine.organize(scan)
            print(f"Complete: Moved {res.moved_count}, Skipped {res.skipped_count}, Errors {res.error_count}")
        sys.exit(0)

    # Launch GUI
    window = MainWindow()

    # Start minimized if requested or configured
    if "--minimized" in sys.argv:
        window.hide()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
