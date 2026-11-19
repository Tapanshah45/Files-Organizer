"""Tests for OrganizerEngine."""

import pytest
from pathlib import Path

from src.config import ConfigManager
from src.history import HistoryManager
from src.logger import OrganizerLogger
from src.organizer import OrganizerEngine


@pytest.fixture
def test_env(tmp_path):
    dl_dir = tmp_path / "Downloads"
    dl_dir.mkdir()

    cfg_file = tmp_path / "config.json"
    hist_file = tmp_path / "history.json"
    log_file = tmp_path / "organizer.log"

    cfg = ConfigManager(config_path=cfg_file)
    cfg.downloads_folder = dl_dir

    logger = OrganizerLogger(log_path=log_file)
    history = HistoryManager(history_path=hist_file)

    engine = OrganizerEngine(config_mgr=cfg, logger=logger, history_mgr=history)
    return {
        "engine": engine,
        "dl_dir": dl_dir,
        "history": history,
        "logger": logger,
        "cfg": cfg,
    }


def test_scan_and_preview_does_not_modify_files(test_env):
    engine = test_env["engine"]
    dl_dir = test_env["dl_dir"]

    # Create dummy files
    (dl_dir / "doc1.pdf").write_text("pdf content")
    (dl_dir / "img1.png").write_text("png content")
    (dl_dir / "temp.crdownload").write_text("downloading")

    # Run preview / scan
    scan = engine.preview(dl_dir)
    assert scan.files_found == 3
    assert scan.files_to_move == 2
    assert scan.files_ignored == 1
    assert scan.category_counts.get("Documents") == 1
    assert scan.category_counts.get("Images") == 1

    # Verify no files were moved during preview
    assert (dl_dir / "doc1.pdf").exists()
    assert (dl_dir / "img1.png").exists()
    assert (dl_dir / "temp.crdownload").exists()
    assert not (dl_dir / "Documents").exists()


def test_organize_moves_files_and_ignores_subfolders(test_env):
    engine = test_env["engine"]
    dl_dir = test_env["dl_dir"]

    # Files to organize
    (dl_dir / "statement.pdf").write_text("statement")
    (dl_dir / "photo.jpg").write_text("photo")
    (dl_dir / "archive.zip").write_text("archive")
    (dl_dir / "unknown.xyz").write_text("unknown")

    # Ignored files
    (dl_dir / "partfile.part").write_text("in progress")
    (dl_dir / "desktop.ini").write_text("[settings]")

    # Subfolder that must NOT be moved
    subfolder = dl_dir / "ExistingSubFolder"
    subfolder.mkdir()
    (subfolder / "subfile.txt").write_text("should stay")

    scan = engine.scan(dl_dir)
    assert scan.files_to_move == 4  # pdf, jpg, zip, xyz (Other)

    res = engine.organize(scan)
    assert res.moved_count == 4
    assert res.error_count == 0

    # Verify category folders created and files moved
    assert (dl_dir / "Documents" / "statement.pdf").exists()
    assert (dl_dir / "Images" / "photo.jpg").exists()
    assert (dl_dir / "Archives" / "archive.zip").exists()
    assert (dl_dir / "Other" / "unknown.xyz").exists()

    # Original files should no longer be at root
    assert not (dl_dir / "statement.pdf").exists()
    assert not (dl_dir / "photo.jpg").exists()

    # Ignored files remain at root
    assert (dl_dir / "partfile.part").exists()
    assert (dl_dir / "desktop.ini").exists()

    # Subfolder and its contents are untouched
    assert subfolder.exists()
    assert (subfolder / "subfile.txt").exists()


def test_does_not_rescan_category_subfolders(test_env):
    engine = test_env["engine"]
    dl_dir = test_env["dl_dir"]

    # Pre-create category folder with a file
    doc_dir = dl_dir / "Documents"
    doc_dir.mkdir()
    (doc_dir / "existing_doc.pdf").write_text("already categorized")

    # Put a new file at root
    (dl_dir / "new_doc.pdf").write_text("new doc")

    scan = engine.scan(dl_dir)
    # Only the root file should be found and planned for move
    assert scan.files_found == 1
    assert scan.files_to_move == 1
    assert scan.planned_moves[0].source_path.name == "new_doc.pdf"
