"""Modern Windows 11 Fluent Dark Stylesheet for Downloads Organizer.

Provides a clean, professional, state-of-the-art UI with subtle glassmorphic
depth, curved borders, vivid accents, crisp typography, and fluid hover states.
"""

MODERN_STYLE = """
/* Global Window & Fonts */
QWidget {
    background-color: #0f172a; /* Slate 900 */
    color: #f8fafc;            /* Slate 50 */
    font-family: "Segoe UI Variable Text", "Segoe UI", -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}

/* Main Window Container */
QMainWindow {
    background-color: #0f172a;
}

QDialog {
    background-color: #0f172a;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1e293b;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #475569;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #64748b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: #1e293b;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #475569;
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #64748b;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Card Panels */
QFrame#CardPanel {
    background-color: #1e293b; /* Slate 800 */
    border: 1px solid #334155; /* Slate 700 */
    border-radius: 12px;
}

QFrame#StatCard {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 10px;
}
QFrame#StatCard:hover {
    border-color: #3b82f6;
    background-color: #243247;
}

/* Typography & Labels */
QLabel {
    color: #f1f5f9;
}
QLabel#TitleLabel {
    font-size: 19px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
}
QLabel#SubtitleLabel {
    font-size: 12px;
    color: #94a3b8;
}
QLabel#SectionHeader {
    font-size: 13px;
    font-weight: 600;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QLabel#StatValue {
    font-size: 24px;
    font-weight: 700;
    color: #38bdf8; /* Sky 400 */
}
QLabel#StatTitle {
    font-size: 12px;
    font-weight: 500;
    color: #94a3b8;
}
QLabel#StatusLabel {
    font-size: 12px;
    color: #38bdf8;
    font-weight: 500;
}

/* Input Fields */
QLineEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 12px;
    color: #f8fafc;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #0f172a;
}
QLineEdit:disabled {
    background-color: #162032;
    color: #64748b;
    border-color: #1e293b;
}

/* Push Buttons */
QPushButton {
    background-color: #334155;
    color: #ffffff;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #475569;
    border-color: #64748b;
}
QPushButton:pressed {
    background-color: #1e293b;
}
QPushButton:disabled {
    background-color: #1e293b;
    color: #64748b;
    border-color: #334155;
}

/* Primary Action Buttons */
QPushButton#PrimaryButton {
    background-color: #2563eb; /* Blue 600 */
    border: 1px solid #3b82f6;
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
    padding: 10px 20px;
    border-radius: 8px;
}
QPushButton#PrimaryButton:hover {
    background-color: #1d4ed8;
    border-color: #60a5fa;
}
QPushButton#PrimaryButton:pressed {
    background-color: #1e40af;
}
QPushButton#PrimaryButton:disabled {
    background-color: #1e293b;
    color: #64748b;
    border-color: #334155;
}

/* Secondary Action Buttons */
QPushButton#SecondaryButton {
    background-color: #1e293b;
    border: 1px solid #475569;
    color: #e2e8f0;
    font-size: 13px;
    font-weight: 600;
    padding: 9px 18px;
    border-radius: 8px;
}
QPushButton#SecondaryButton:hover {
    background-color: #334155;
    border-color: #94a3b8;
    color: #ffffff;
}
QPushButton#SecondaryButton:pressed {
    background-color: #0f172a;
}

/* Undo Button */
QPushButton#UndoButton {
    background-color: #1e293b;
    border: 1px solid #f59e0b; /* Amber 500 */
    color: #fbbf24;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 8px;
}
QPushButton#UndoButton:hover {
    background-color: rgba(245, 158, 11, 0.15);
    border-color: #fbbf24;
    color: #fef3c7;
}
QPushButton#UndoButton:pressed {
    background-color: rgba(245, 158, 11, 0.3);
}
QPushButton#UndoButton:disabled {
    border-color: #334155;
    color: #64748b;
    background-color: #1e293b;
}

/* Lists and Tables */
QTableWidget, QListWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #334155;
    color: #f8fafc;
    padding: 4px;
}
QTableWidget::item, QListWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #283548;
    border-radius: 4px;
}
QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #0f172a;
    color: #94a3b8;
    font-weight: 600;
    font-size: 12px;
    padding: 6px;
    border: none;
    border-bottom: 2px solid #334155;
}

/* Progress Bar */
QProgressBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: 600;
    height: 18px;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #10b981);
    border-radius: 5px;
}

/* Checkboxes */
QCheckBox {
    color: #e2e8f0;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #475569;
    border-radius: 4px;
    background-color: #1e293b;
}
QCheckBox::indicator:hover {
    border-color: #3b82f6;
}
QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #3b82f6;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #1e293b;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #94a3b8;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #1e293b;
    color: #38bdf8;
    border-color: #334155;
}
QTabBar::tab:hover:!selected {
    background-color: #162032;
    color: #f1f5f9;
}

/* Badges / Chips */
QLabel#BadgeCount {
    background-color: #334155;
    color: #38bdf8;
    border-radius: 10px;
    padding: 2px 10px;
    font-weight: 700;
    font-size: 12px;
}

/* Context Menu */
QMenu {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
    color: #f8fafc;
}
QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background-color: #334155;
    margin: 4px 8px;
}
"""
