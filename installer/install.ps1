# 1-Click Installer Script for Downloads Organizer
# Installs to %LOCALAPPDATA%\Programs\DownloadsOrganizer without requiring Admin privileges

$ErrorActionPreference = "Stop"

$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\DownloadsOrganizer"
$DistExe = "dist\DownloadsOrganizer.exe"
$IconFile = "assets\icon.ico"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Installing Downloads Organizer           " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

if (-not (Test-Path $DistExe)) {
    Write-Host "Executable not found at $DistExe. Please run build.ps1 first." -ForegroundColor Red
    exit 1
}

# 1. Create install directory
Write-Host "`nCreating application directory at: $InstallDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $InstallDir "assets") | Out-Null

# 2. Copy binary and icon
Write-Host "Copying application binaries..." -ForegroundColor Yellow
Copy-Item $DistExe -Destination (Join-Path $InstallDir "DownloadsOrganizer.exe") -Force
Copy-Item $IconFile -Destination (Join-Path $InstallDir "assets\icon.ico") -Force

# 3. Create Start Menu Shortcut
$WshShell = New-Object -ComObject WScript.Shell
$StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$StartShortcutPath = Join-Path $StartMenuDir "Downloads Organizer.lnk"

Write-Host "Creating Start Menu shortcut..." -ForegroundColor Yellow
$Shortcut = $WshShell.CreateShortcut($StartShortcutPath)
$Shortcut.TargetPath = Join-Path $InstallDir "DownloadsOrganizer.exe"
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.IconLocation = Join-Path $InstallDir "assets\icon.ico,0"
$Shortcut.Description = "Automated Windows Downloads Organizer"
$Shortcut.Save()

# 4. Create Desktop Shortcut
$DesktopDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$DesktopShortcutPath = Join-Path $DesktopDir "Downloads Organizer.lnk"

Write-Host "Creating Desktop shortcut..." -ForegroundColor Yellow
$DShortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$DShortcut.TargetPath = Join-Path $InstallDir "DownloadsOrganizer.exe"
$DShortcut.WorkingDirectory = $InstallDir
$DShortcut.IconLocation = Join-Path $InstallDir "assets\icon.ico,0"
$DShortcut.Description = "Automated Windows Downloads Organizer"
$DShortcut.Save()

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "  Installation Completed Successfully!       " -ForegroundColor Green
Write-Host "  Location: $InstallDir\DownloadsOrganizer.exe" -ForegroundColor Green
Write-Host "  Desktop & Start Menu shortcuts created!    " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
