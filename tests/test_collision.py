"""Tests for duplicate filename collision handling."""

from pathlib import Path
from src.utils import get_safe_destination_path


def test_no_collision_when_destination_absent(tmp_path):
    target_dir = tmp_path / "Documents"
    target_dir.mkdir()

    res = get_safe_destination_path(target_dir, "report.pdf")
    assert res == target_dir / "report.pdf"


def test_duplicate_collision_sequence(tmp_path):
    target_dir = tmp_path / "Documents"
    target_dir.mkdir()

    # First file created
    p1 = get_safe_destination_path(target_dir, "file.pdf")
    assert p1.name == "file.pdf"
    p1.write_text("v1")

    # Second identical file
    p2 = get_safe_destination_path(target_dir, "file.pdf")
    assert p2.name == "file (1).pdf"
    p2.write_text("v2")

    # Third identical file
    p3 = get_safe_destination_path(target_dir, "file.pdf")
    assert p3.name == "file (2).pdf"
    p3.write_text("v3")

    # Fourth identical file
    p4 = get_safe_destination_path(target_dir, "file.pdf")
    assert p4.name == "file (3).pdf"


def test_collision_with_existing_numbered_filename(tmp_path):
    target_dir = tmp_path / "Images"
    target_dir.mkdir()

    # Create photo (1).jpg
    f1 = target_dir / "photo (1).jpg"
    f1.write_text("content")

    # Moving photo (1).jpg into target_dir should find next available: photo (2).jpg
    res = get_safe_destination_path(target_dir, "photo (1).jpg")
    assert res.name == "photo (2).jpg"


def test_gap_in_numbering(tmp_path):
    target_dir = tmp_path / "Videos"
    target_dir.mkdir()

    # Exists: clip.mp4 and clip (2).mp4 (gap at 1)
    (target_dir / "clip.mp4").write_text("base")
    (target_dir / "clip (2).mp4").write_text("num2")

    # Adding clip.mp4 should fill clip (1).mp4
    res = get_safe_destination_path(target_dir, "clip.mp4")
    assert res.name == "clip (1).mp4"
