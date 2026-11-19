# Downloads Organizer 🚀

A modern, high-performance, and safe Windows desktop application that scans your `Downloads` folder and automatically organizes files into categorized subfolders based on file extensions.

Built with **Python 3**, **PySide6 (Qt)**, and packaged as a **standalone Windows `.exe`** with zero external runtime dependencies.

---

## Key Features

- **Windows Auto-Detection**: Uses Windows Shell Known Folders API (`FOLDERID_Downloads`) to locate your active Downloads folder even if relocated to another drive (e.g. `D:\Downloads`) or synced with OneDrive.
- **Data Safety First**:
  - **MOVE only**: Never permanently deletes, overwrites, or removes files.
  - **Zero Overwrite Collisions**: Automatically handles filename duplicates by generating `report (1).pdf`, `report (2).pdf`, etc.
  - **System File Protection**: Ignores `.tmp`, `.crdownload`, `.part`, `.lnk`, `.url`, `desktop.ini`, `Thumbs.db`, and hidden/system files.
  - **App Protection**: Will never move itself or its own executable.
- **Interactive Dry-Run Preview**: Inspect every planned relocation with source, category, and proposed destination before moving a single file.
- **One-Click Undo**: Revert the most recent organization operation with full collision protection if new files appeared in the original location.
- **Automatic Monitoring**: Powered by Windows filesystem notifications (`watchdog`) with stability checks so in-progress downloads are never prematurely touched.
- **System Tray Integration**: Runs unobtrusively in the Windows taskbar/system tray with quick actions and native notifications.
- **Customizable**: Edit categories, file extensions, ignore rules, and fallback behavior via the built-in Settings dialog or `%LOCALAPPDATA%\DownloadsOrganizer\config.json`.
- **Structured Audit Logging**: Maintains operation history in `%LOCALAPPDATA%\DownloadsOrganizer\logs\organizer.log`.

---

## Default Category Mapping

| Category | Destination Folder | Mapped File Extensions |
| :--- | :--- | :--- |
| **Documents** | `Downloads\Documents` | `.pdf`, `.doc`, `.docx`, `.docm`, `.txt`, `.rtf`, `.odt`, `.pages` |
| **Spreadsheets** | `Downloads\Spreadsheets` | `.xls`, `.xlsx`, `.xlsm`, `.csv`, `.ods` |
| **Presentations** | `Downloads\Presentations` | `.ppt`, `.pptx`, `.pptm`, `.odp` |
| **Images** | `Downloads\Images` | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.svg`, `.ico`, `.tiff` |
| **Videos** | `Downloads\Videos` | `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v` |
| **Audio** | `Downloads\Audio` | `.mp3`, `.wav`, `.flac`, `.aac`, `.m4a`, `.ogg`, `.wma` |
| **Archives** | `Downloads\Archives` | `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz` |
| **Installers** | `Downloads\Installers` | `.exe`, `.msi`, `.msp` |
| **Scripts** | `Downloads\Scripts` | `.ps1`, `.bat`, `.cmd`, `.py`, `.js`, `.ts`, `.psm1`, `.sh` |
| **Web Files** | `Downloads\Web` | `.html`, `.htm`, `.css`, `.json`, `.xml` |
| **Torrents** | `Downloads\Torrents` | `.torrent` |
| **Disk Images** | `Downloads\Disk Images` | `.iso`, `.img`, `.vhd`, `.vhdx` |
| **Other** | `Downloads\Other` | Any unmapped extension (configurable) |

---

## 1. Running the Standalone Executable

If you downloaded or built the standalone binary:

1. Double-click **`dist\DownloadsOrganizer.exe`**.
2. The application will launch immediately without requiring Python, PowerShell, or external libraries.

---

## 2. Running From Source

To run the application from source code:

### Prerequisites
- Python 3.10+ (tested on Python 3.10 through 3.14)
- Windows 10 or Windows 11

### Installation Steps

```powershell
# 1. Clone or navigate to the repository directory
cd d:\mini

# 2. Install required Python packages
python -m pip install -r requirements.txt

# 3. Run the GUI application
python app.py
```

### CLI Quick Mode
You can also trigger a one-shot organization from the command line:

```powershell
python app.py --organize-now
```

---

## 3. Building the Standalone `.exe`

To package the standalone single-file Windows executable:

```powershell
# Run the automated build script
.\build.ps1
```

Or run PyInstaller directly:

```powershell
python -m PyInstaller `
    --clean `
    --onefile `
    --windowed `
    --icon=assets/icon.ico `
    --add-data="assets;assets" `
    --add-data="config;config" `
    --name=DownloadsOrganizer `
    app.py
```

The resulting executable will be saved at:
```text
dist\DownloadsOrganizer.exe
```

### Optional 1-Click Installer
To install the application with Desktop and Start Menu shortcuts:
```powershell
powershell -ExecutionPolicy Bypass -File installer\install.ps1
```

If you use Inno Setup Compiler, you can compile `installer\setup_script.iss` to generate `DownloadsOrganizer-Setup.exe`.

---

## 4. How to Use the GUI

```text
┌──────────────────────────────────────────────┐
│          DOWNLOADS ORGANIZER                 │
├──────────────────────────────────────────────┤
│                                              │
│ Downloads Folder                             │
│ [ C:\Users\User\Downloads            ]       │
│ [Browse]                                     │
│                                              │
│ Files Found:       27                        │
│ Files To Move:    21                         │
│ Ignored:            6                        │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Documents              5                 │ │
│ │ Images                 8                 │ │
│ │ Videos                 3                 │ │
│ │ Archives               4                 │ │
│ │ Installers             1                 │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ [ Preview Changes ] [ Organize Downloads ]   │
│                                              │
│ [ Undo Last Operation ]                      │
│                                              │
│ Status: Ready                                │
└──────────────────────────────────────────────┘
```

1. **Verify or Change Folder**: The current Downloads folder is automatically populated. Click **Browse** if you wish to organize a different folder.
2. **Review Stats**: View the real-time count of total files found, files eligible to be moved, and files ignored.
3. **Category Breakdown**: Displays the destination categories and how many files are destined for each.
4. **Preview Changes**: Click **Preview Changes** to open the Dry-Run table. This lets you inspect source and destination paths before committing.
5. **Organize Downloads**: Click to execute the move. A real-time progress bar displays current files being relocated.
6. **Undo Last Operation**: Made a mistake or want files back? Click **↺ Undo Last Operation** to restore all moved files to their original locations.

---

## 5. How Automatic Mode Works

1. Click **Auto: OFF** in the top-right header or choose **Auto Organize** from the system tray menu.
2. The application begins monitoring the Downloads folder using the Windows filesystem event pipeline.
3. **Stability & Anti-Corruption Guard**:
   - Files with `.crdownload`, `.part`, `.tmp`, or `.download` extensions are completely ignored until the browser or torrent client finishes downloading and renames the file.
   - Newly appeared files are subject to a **stability delay** (default 3 seconds) and checked for read/write file handle locks to guarantee the file is fully saved before being organized.
4. Once verified, the file is moved to its designated category subfolder and an optional desktop notification is sent.

---

## 6. Where Configuration Is Stored

Settings are stored in standard Windows JSON configuration format:

```text
%LOCALAPPDATA%\DownloadsOrganizer\config.json
```

Example content:
```json
{
    "downloads_folder": "C:\\Users\\User\\Downloads",
    "organize_unknown_files": true,
    "unknown_folder_name": "Other",
    "create_categories": true,
    "recursive": false,
    "auto_organize": false,
    "enable_notifications": true,
    "minimize_to_tray": true,
    "stability_delay_seconds": 3,
    "categories": { ... },
    "ignored_extensions": [".lnk", ".url", ".tmp", ".crdownload", ".part", ".download"],
    "ignored_files": ["desktop.ini", "thumbs.db"]
}
```

You can customize these options anytime via the GUI **⚙️ Settings** button without editing JSON manually.

---

## 7. Where Logs Are Stored

Every file operation is recorded to an audit log:

```text
%LOCALAPPDATA%\DownloadsOrganizer\logs\organizer.log
```

Log entry format:
```text
2026-09-29 16:40:12
MOVE
C:\Users\User\Downloads\report.pdf
C:\Users\User\Downloads\Documents\report.pdf
SUCCESS

2026-09-29 16:41:03
MOVE
C:\Users\User\Downloads\locked.zip
C:\Users\User\Downloads\Archives\locked.zip
FAILED
File is locked or in-use by another application
```

To view or clear logs, click **⚙️ Settings** → **Logs & History** tab, or right-click the system tray icon and select **Open Logs**.

---

## 8. How Undo Works

1. Every successful organization batch is recorded in `%LOCALAPPDATA%\DownloadsOrganizer\history.json`.
2. When you click **Undo Last Operation**:
   - The last batch is retrieved.
   - Each file is moved from its category subfolder back to its original path.
   - If the original directory was deleted, it is automatically recreated.
   - **Collision Protection**: If a new file with the original name was created at the root directory in the meantime, the restored file is saved as `filename (1).ext` so no data is ever overwritten.
   - The operation is logged as `UNDO_MOVE`.

---

## 9. How to Customize File Categories

1. Open **Settings** (click **⚙️ Settings** in the top bar).
2. Go to the **Categories & Extensions** tab.
3. To add a new category: click **+ Add Category**, type a category folder name (e.g. `Books`), and enter extensions (e.g. `.epub, .mobi, .azw3`).
4. To edit existing categories: double-click the extensions cell and add or remove extensions.
5. Click **Save Settings**.

---

## 10. Troubleshooting Common Issues

### A file wasn't moved during organization
- **Is the file locked?** If another program (browser, PDF reader, video player) has the file open with an exclusive lock, the organizer skips it and logs an error to protect data integrity. Close the file and click **Organize Downloads** again.
- **Is it an ignored extension?** Files with `.crdownload`, `.part`, `.tmp`, `.lnk`, or `.url` are ignored by default.
- **Is it a hidden or system file?** Hidden and system files are excluded from organization to prevent breaking Windows file associations.
- **Is it an unrecognized extension?** Check if "Organize unknown file extensions into fallback folder" is checked in Settings.

### Application does not minimize to System Tray
- Verify that **Minimize application to Windows System Tray** is enabled in Settings.
- Check the Windows notification area overflow tray (arrow `^` icon near the clock).

### Running Tests
To run all automated unit tests:
```powershell
python -m pytest tests/ -v
```

---

## License

MIT License. See [LICENSE](LICENSE) for full details.
