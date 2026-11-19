"""Tests for FileClassifier."""

import pytest
from src.classifier import FileClassifier
from src.config import DEFAULT_CATEGORIES, DEFAULT_IGNORED_EXTENSIONS, DEFAULT_IGNORED_FILES


@pytest.fixture
def classifier():
    return FileClassifier(
        categories=DEFAULT_CATEGORIES,
        ignored_extensions=DEFAULT_IGNORED_EXTENSIONS,
        ignored_files=DEFAULT_IGNORED_FILES,
        organize_unknown_files=True,
        unknown_folder_name="Other",
    )


def test_standard_classifications(classifier):
    # Documents
    res = classifier.classify("test.pdf")
    assert res.category == "Documents"
    assert not res.is_ignored

    res = classifier.classify("notes.docx")
    assert res.category == "Documents"

    # Images
    res = classifier.classify("photo.jpg")
    assert res.category == "Images"

    res = classifier.classify("icon.png")
    assert res.category == "Images"

    # Videos
    res = classifier.classify("video.mp4")
    assert res.category == "Videos"

    # Archives
    res = classifier.classify("archive.zip")
    assert res.category == "Archives"

    # Installers
    res = classifier.classify("program.exe")
    assert res.category == "Installers"

    res = classifier.classify("setup.msi")
    assert res.category == "Installers"

    # Scripts
    res = classifier.classify("script.ps1")
    assert res.category == "Scripts"

    res = classifier.classify("build.bat")
    assert res.category == "Scripts"

    # Spreadsheets
    res = classifier.classify("budget.xlsx")
    assert res.category == "Spreadsheets"

    # Audio
    res = classifier.classify("song.mp3")
    assert res.category == "Audio"

    # Web
    res = classifier.classify("page.html")
    assert res.category == "Web"

    # Torrents
    res = classifier.classify("linux.torrent")
    assert res.category == "Torrents"

    # Disk Images
    res = classifier.classify("windows11.iso")
    assert res.category == "Disk Images"


def test_case_insensitivity(classifier):
    res = classifier.classify("REPORT.PDF")
    assert res.category == "Documents"

    res = classifier.classify("PHOTO.JPG")
    assert res.category == "Images"

    res = classifier.classify("SETUP.EXE")
    assert res.category == "Installers"


def test_unknown_extension_handling(classifier):
    # With unknown handling enabled
    res = classifier.classify("unknown.xyz")
    assert res.category == "Other"
    assert not res.is_ignored

    # With unknown handling disabled
    classifier.update_rules(organize_unknown_files=False)
    res = classifier.classify("unknown.xyz")
    assert res.category is None
    assert res.is_ignored


def test_ignored_files_and_extensions(classifier):
    # Ignored extensions
    for ext in [".lnk", ".url", ".tmp", ".crdownload", ".part", ".download"]:
        res = classifier.classify(f"sample{ext}")
        assert res.is_ignored, f"Expected {ext} to be ignored"
        assert res.category is None

    # Ignored exact files
    assert classifier.classify("desktop.ini").is_ignored
    assert classifier.classify("DESKTOP.INI").is_ignored
    assert classifier.classify("thumbs.db").is_ignored
    assert classifier.classify("Thumbs.db").is_ignored
