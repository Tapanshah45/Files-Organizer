# Build script for Downloads Organizer
# Packages application as a standalone, zero-dependency Windows executable

$ErrorActionPreference = "Stop"

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  Building Downloads Organizer Executable  " -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# 1. Ensure Dependencies
Write-Host "`n[1/3] Verifying and installing requirements..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# 2. Run Tests
Write-Host "`n[2/3] Running automated tests..." -ForegroundColor Yellow
python -m pytest tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed! Aborting build." -ForegroundColor Red
    exit 1
}

# 3. Build Standalone Executable with PyInstaller
Write-Host "`n[3/3] Packaging standalone executable via PyInstaller..." -ForegroundColor Yellow

$PyInstallerArgs = @(
    "--clean",
    "--onefile",
    "--windowed",
    "--icon=assets/icon.ico",
    "--add-data=assets;assets",
    "--add-data=config;config",
    "--name=DownloadsOrganizer",
    "app.py"
)

python -m PyInstaller @PyInstallerArgs

if (Test-Path "dist\DownloadsOrganizer.exe") {
    $exeSize = (Get-Item "dist\DownloadsOrganizer.exe").Length / 1MB
    Write-Host "`n===========================================" -ForegroundColor Green
    Write-Host "  SUCCESS: dist\DownloadsOrganizer.exe generated!  " -ForegroundColor Green
    Write-Host ("  Size: {0:N2} MB" -f $exeSize) -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
} else {
    Write-Host "Build finished, but dist\DownloadsOrganizer.exe was not found." -ForegroundColor Red
    exit 1
}
