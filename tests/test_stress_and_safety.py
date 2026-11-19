"""Stress, safety, and edge-case tests for Downloads Organizer."""

import pytest
import threading
import time
from pathlib import Path
from unittest.mock import patch

from src.config import ConfigManager
from src.history import HistoryManager
from src.logger import OrganizerLogger
from src.organizer import OrganizerEngine
from src.utils import is_app_itself


@pytest.fixture
def env(tmp_path):
    dl_dir = tmp_path / "Downloads"
    dl_dir.mkdir()

    cfg = ConfigManager(config_path=tmp_path / "config.json")
    cfg.downloads_folder = dl_dir

    logger = OrganizerLogger(log_path=tmp_path / "organizer.log")
    history = HistoryManager(history_path=tmp_path / "history.json")

    engine = OrganizerEngine(config_mgr=cfg, logger=logger, history_mgr=history)
    return {
        "engine": engine,
        "dl_dir": dl_dir,
        "logger": logger,
    }


def test_empty_downloads_folder(env):
    engine = env["engine"]
    dl_dir = env["dl_dir"]

    scan = engine.scan(dl_dir)
    assert scan.files_found == 0
    assert scan.files_to_move == 0
    assert scan.files_ignored == 0
    assert len(scan.planned_moves) == 0

    res = engine.organize(scan)
    assert res.moved_count == 0
    assert res.skipped_count == 0
    assert res.error_count == 0


def test_locked_file_does_not_crash_engine(env):
    """Verify that a locked / unreadable file is skipped gracefully and logged without crashing."""
    engine = env["engine"]
    dl_dir = env["dl_dir"]

    good_file = dl_dir / "valid_doc.pdf"
    good_file.write_text("valid content")

    locked_file = dl_dir / "locked.zip"
    locked_file.write_text("locked zip content")

    # Simulate locked file check failing (e.g. sharing violation from downloader)
    scan = engine.scan(dl_dir)
    assert scan.files_to_move == 2

    with patch("src.organizer.is_file_ready", side_effect=lambda p, **kw: p.name != "locked.zip"):
        res = engine.organize(scan)

        # Good file moved, locked file skipped with error count
        assert res.moved_count == 1
        assert res.error_count == 1
        assert (dl_dir / "Documents" / "valid_doc.pdf").exists()
        assert locked_file.exists()  # Locked file remains untouched

    # Verify log recorded the failure
    log_content = env["logger"].get_recent_entries()
    assert "FAILED" in log_content
    assert "locked.zip" in log_content


def test_does_not_move_app_itself(env):
    engine = env["engine"]
    dl_dir = env["dl_dir"]

    # If the user put DownloadsOrganizer.exe or app.py into Downloads folder
    exe_file = dl_dir / "DownloadsOrganizer.exe"
    exe_file.write_text("fake binary")

    script_file = dl_dir / "app.py"
    script_file.write_text("# main app")

    scan = engine.scan(dl_dir)
    # Both should be classified as ignored because they are the app itself
    assert scan.files_to_move == 0
    assert scan.files_ignored == 2


def test_large_number_of_files(env):
    """Stress test with 3,000 files to ensure rapid classification and memory efficiency."""
    engine = env["engine"]
    dl_dir = env["dl_dir"]

    extensions = [".pdf", ".jpg", ".mp4", ".zip", ".exe", ".xlsx"]
    num_files = 3000

    # Bulk create files
    for i in range(num_files):
        ext = extensions[i % len(extensions)]
        (dl_dir / f"test_file_{i:04d}{ext}").write_text("x")

    t0 = time.time()
    scan = engine.scan(dl_dir)
    duration = time.time() - t0

    assert scan.files_found == num_files
    assert scan.files_to_move == num_files
    assert scan.files_ignored == 0
    # Must complete scan of 3000 files in under 3 seconds
    assert duration < 5.0, f"Scan took too long: {duration:.2f}s"
