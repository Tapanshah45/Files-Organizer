"""Windows System Tray integration for Downloads Organizer.

Provides quick access context menu, monitoring toggle, manual organization,
and Windows desktop notifications.
"""

from typing import Callable, Optional

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


class DownloadsTrayIcon(QSystemTrayIcon):
    """System tray icon and context menu."""

    def __init__(
        self,
        icon: QIcon,
        parent=None,
        on_toggle_auto: Optional[Callable[[bool], None]] = None,
        on_organize_now: Optional[Callable[[], None]] = None,
        on_pause_monitoring: Optional[Callable[[], None]] = None,
        on_open_downloads: Optional[Callable[[], None]] = None,
        on_open_logs: Optional[Callable[[], None]] = None,
        on_open_settings: Optional[Callable[[], None]] = None,
        on_show_window: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ):
        super().__init__(icon, parent)
        self.setToolTip("Downloads Organizer")
        self.on_toggle_auto = on_toggle_auto
        self.on_organize_now = on_organize_now
        self.on_pause_monitoring = on_pause_monitoring
        self.on_open_downloads = on_open_downloads
        self.on_open_logs = on_open_logs
        self.on_open_settings = on_open_settings
        self.on_show_window = on_show_window
        self.on_exit = on_exit

        self._init_menu()
        self.activated.connect(self._on_tray_activated)

    def _init_menu(self) -> None:
        menu = QMenu()

        # Title Header
        title_action = menu.addAction("Downloads Organizer")
        title_action.setEnabled(False)
        menu.addSeparator()

        # Auto Organize toggle action
        self.action_auto = QAction("Auto Organize", menu)
        self.action_auto.setCheckable(True)
        self.action_auto.setChecked(False)
        self.action_auto.toggled.connect(self._handle_auto_toggled)
        menu.addAction(self.action_auto)

        menu.addSeparator()

        # Organize Now
        self.action_organize = menu.addAction("Organize Now")
        if self.on_organize_now:
            self.action_organize.triggered.connect(self.on_organize_now)

        # Pause / Resume Monitoring
        self.action_pause = menu.addAction("Pause Monitoring")
        if self.on_pause_monitoring:
            self.action_pause.triggered.connect(self.on_pause_monitoring)

        menu.addSeparator()

        # Open Downloads
        action_dl = menu.addAction("Open Downloads")
        if self.on_open_downloads:
            action_dl.triggered.connect(self.on_open_downloads)

        # Open Logs
        action_logs = menu.addAction("Open Logs")
        if self.on_open_logs:
            action_logs.triggered.connect(self.on_open_logs)

        # Settings
        action_settings = menu.addAction("Settings")
        if self.on_open_settings:
            action_settings.triggered.connect(self.on_open_settings)

        menu.addSeparator()

        # Show Window
        action_show = menu.addAction("Show Window")
        if self.on_show_window:
            action_show.triggered.connect(self.on_show_window)

        # Exit
        action_exit = menu.addAction("Exit")
        if self.on_exit:
            action_exit.triggered.connect(self.on_exit)

        self.setContextMenu(menu)

    def _handle_auto_toggled(self, checked: bool) -> None:
        if self.on_toggle_auto:
            self.on_toggle_auto(checked)

    def set_auto_organize_checked(self, checked: bool) -> None:
        self.action_auto.setChecked(checked)

    def set_pause_action_text(self, text: str) -> None:
        self.action_pause.setText(text)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            if self.on_show_window:
                self.on_show_window()

    def show_organize_notification(self, count: int, message: str) -> None:
        """Display desktop notification if notifications are supported and enabled."""
        if count > 0:
            title = "Downloads Organizer"
            msg = f"Moved {count} new file{'s' if count != 1 else ''}.\n{message}"
            self.showMessage(title, msg, QSystemTrayIcon.Information, 4000)
