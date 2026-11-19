"""Tests for HistoryManager and Undo functionality."""

import pytest
from pathlib import Path

from src.config import ConfigManager
from src.history import HistoryManager
from src.logger import OrganizerLogger
from src.organizer import OrganizerEngine


@pytest.fixture
def undo_env(tmp_path):
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
        "history": history,
    }


def test_full_round_trip_undo(undo_env):
    engine = undo_env["engine"]
    dl_dir = undo_env["dl_dir"]

    # Create files
    f1 = dl_dir / "invoice.pdf"
    f2 = dl_dir / "setup.exe"
    f1.write_text("invoice content")
    f2.write_text("setup content")

    # Organize
    scan = engine.scan(dl_dir)
    res = engine.organize(scan)
    assert res.moved_count == 2

    # Verify moved to categories
    dest_pdf = dl_dir / "Documents" / "invoice.pdf"
    dest_exe = dl_dir / "Installers" / "setup.exe"
    assert dest_pdf.exists()
    assert dest_exe.exists()
    assert not f1.exists()
    assert not f2.exists()

    # Now Undo
    undo_res = engine.undo()
    assert undo_res.success
    assert undo_res.restored_count == 2
    assert undo_res.error_count == 0

    # Files should be back in original locations
    assert f1.exists()
    assert f2.exists()
    assert f1.read_text() == "invoice content"
    assert f2.read_text() == "setup content"

    # Category destinations should now be gone
    assert not dest_pdf.exists()
    assert not dest_exe.exists()


def test_undo_with_collision_at_original_path(undo_env):
    engine = undo_env["engine"]
    dl_dir = undo_env["dl_dir"]

    # Move a file
    f1 = dl_dir / "data.csv"
    f1.write_text("original data")
    scan = engine.scan(dl_dir)
    engine.organize(scan)

    dest_csv = dl_dir / "Spreadsheets" / "data.csv"
    assert dest_csv.exists()

    # Simulate user creating a NEW data.csv at the original root location before undoing
    f1.write_text("new conflicting file")

    # Perform Undo: must NOT overwrite new conflicting file!
    undo_res = engine.undo()
    assert undo_res.success
    assert undo_res.restored_count == 1

    # Original new conflicting file is preserved
    assert f1.read_text() == "new conflicting file"

    # Restored file is placed as data (1).csv
    restored_collision = dl_dir / "data (1).csv"
    assert restored_collision.exists()
    assert restored_collision.read_text() == "original data"


def test_undo_when_no_history(undo_env):
    engine = undo_env["engine"]
    undo_res = engine.undo()
    assert not undo_res.success
    assert undo_res.restored_count == 0
    assert "No recent organization" in undo_res.message
