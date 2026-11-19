"""Organizer Engine for Downloads Organizer.

Performs scanning, categorization, dry-run previews, safe file moves,
and undo restorations. Adheres strictly to safety rules:
- NEVER overwrite or permanently delete files.
- Safe duplicate filename collision handling.
- Graceful error isolation (one failing file never crashes the job).
"""

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.classifier import FileClassifier
from src.config import ConfigManager
from src.history import HistoryManager
from src.logger import OrganizerLogger
from src.utils import (
    get_safe_destination_path,
    is_app_itself,
    is_hidden_or_system,
    is_file_ready,
)


@dataclass
class PlannedMove:
    source_path: Path
    category: str
    target_dir: Path
    proposed_destination: Path
    file_size: int = 0


@dataclass
class ScanResult:
    downloads_folder: Path
    files_found: int = 0
    files_to_move: int = 0
    files_ignored: int = 0
    category_counts: Dict[str, int] = field(default_factory=dict)
    planned_moves: List[PlannedMove] = field(default_factory=list)
    ignored_items: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class OrganizeResult:
    moved_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    details: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class UndoResult:
    success: bool
    restored_count: int = 0
    error_count: int = 0
    message: str = ""
    details: List[Dict[str, str]] = field(default_factory=list)


class OrganizerEngine:
    """Core engine responsible for scanning, organizing, and undoing file operations."""

    def __init__(
        self,
        config_mgr: Optional[ConfigManager] = None,
        logger: Optional[OrganizerLogger] = None,
        history_mgr: Optional[HistoryManager] = None,
    ):
        self.config_mgr = config_mgr or ConfigManager()
        self.logger = logger or OrganizerLogger()
        self.history_mgr = history_mgr or HistoryManager()
        self.classifier = FileClassifier(
            categories=self.config_mgr.categories,
            ignored_extensions=self.config_mgr.ignored_extensions,
            ignored_files=self.config_mgr.ignored_files,
            organize_unknown_files=self.config_mgr.organize_unknown_files,
            unknown_folder_name=self.config_mgr.unknown_folder_name,
        )

    def refresh_classifier(self) -> None:
        """Update classifier with latest configuration."""
        self.classifier.update_rules(
            categories=self.config_mgr.categories,
            ignored_extensions=self.config_mgr.ignored_extensions,
            ignored_files=self.config_mgr.ignored_files,
            organize_unknown_files=self.config_mgr.organize_unknown_files,
            unknown_folder_name=self.config_mgr.unknown_folder_name,
        )

    def scan(self, target_folder: Optional[Path] = None) -> ScanResult:
        """
        Scan downloads folder and prepare classification and planned moves.
        Does NOT alter or move any files.
        """
        self.refresh_classifier()
        folder = Path(target_folder) if target_folder else self.config_mgr.downloads_folder
        result = ScanResult(downloads_folder=folder)

        if not folder.exists() or not folder.is_dir():
            return result

        known_category_names = set(self.config_mgr.categories.keys())
        known_category_names.add(self.config_mgr.unknown_folder_name)

        # Collect files based on recursive option
        file_candidates: List[Path] = []
        try:
            if self.config_mgr.recursive:
                # Walk recursively, skipping category folders
                for root, dirs, files in folder.walk():
                    # Avoid descending into category subfolders
                    dirs[:] = [
                        d for d in dirs
                        if d not in known_category_names and not d.startswith(".")
                    ]
                    for f in files:
                        file_candidates.append(root / f)
            else:
                # Top-level scan only, ignoring all subfolders
                for item in folder.iterdir():
                    if item.is_file():
                        file_candidates.append(item)
        except Exception as e:
            self.logger.log_operation("SCAN", str(folder), "", False, str(e))
            return result

        # Category counts tracking
        counts: Dict[str, int] = {}
        for cat in self.config_mgr.categories.keys():
            counts[cat] = 0
        if self.config_mgr.organize_unknown_files:
            counts[self.config_mgr.unknown_folder_name] = 0

        for file_path in file_candidates:
            result.files_found += 1

            # Ignore the application executable itself
            if is_app_itself(file_path):
                result.files_ignored += 1
                result.ignored_items.append({
                    "file": file_path.name,
                    "reason": "Application executable",
                })
                continue

            # Ignore hidden and system files
            if is_hidden_or_system(file_path):
                result.files_ignored += 1
                result.ignored_items.append({
                    "file": file_path.name,
                    "reason": "Hidden or system file",
                })
                continue

            # Classify file
            cls_res = self.classifier.classify(file_path)
            if cls_res.is_ignored or not cls_res.category:
                result.files_ignored += 1
                result.ignored_items.append({
                    "file": file_path.name,
                    "reason": cls_res.reason,
                })
                continue

            # Eligible for moving
            category = cls_res.category
            target_dir = folder / category
            proposed_dest = get_safe_destination_path(target_dir, file_path.name)

            file_size = 0
            try:
                file_size = file_path.stat().st_size
            except Exception:
                pass

            counts[category] = counts.get(category, 0) + 1
            result.files_to_move += 1
            result.planned_moves.append(
                PlannedMove(
                    source_path=file_path,
                    category=category,
                    target_dir=target_dir,
                    proposed_destination=proposed_dest,
                    file_size=file_size,
                )
            )

        # Only retain categories with count > 0 or all active categories
        result.category_counts = {k: v for k, v in counts.items() if v > 0}
        return result

    def preview(self, target_folder: Optional[Path] = None) -> ScanResult:
        """Alias for scan(); provides safe dry-run inspection."""
        return self.scan(target_folder)

    def organize(
        self,
        scan_result: Optional[ScanResult] = None,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> OrganizeResult:
        """
        Execute file organization safely based on scanned moves.
        Guarantees no overwrite, records history, and handles locked/missing files gracefully.
        """
        if scan_result is None:
            scan_result = self.scan()

        total = len(scan_result.planned_moves)
        res = OrganizeResult()
        successful_moves: List[Dict[str, str]] = []

        for idx, planned in enumerate(scan_result.planned_moves, start=1):
            if is_cancelled and is_cancelled():
                res.skipped_count += (total - idx + 1)
                break

            source = planned.source_path
            filename = source.name

            # Check if source file still exists
            if not source.exists():
                res.skipped_count += 1
                res.details.append({
                    "file": filename,
                    "status": "SKIPPED",
                    "error": "File disappeared before processing",
                })
                continue

            # Check if file is ready and not locked by another process
            if not is_file_ready(source, wait_ms=50):
                res.error_count += 1
                res.details.append({
                    "file": filename,
                    "status": "FAILED",
                    "error": "File is locked or currently being written to",
                })
                self.logger.log_operation(
                    "MOVE",
                    str(source),
                    str(planned.proposed_destination),
                    False,
                    "File is locked or in-use by another application",
                )
                continue

            try:
                # Ensure category directory exists
                planned.target_dir.mkdir(parents=True, exist_ok=True)

                # Re-calculate safe destination at move-time to prevent race collisions
                final_dest = get_safe_destination_path(planned.target_dir, filename)

                # Perform safe move (shutil.move handles cross-drive or same-drive cleanly)
                shutil.move(str(source), str(final_dest))

                successful_moves.append({
                    "original": str(source.resolve()),
                    "destination": str(final_dest.resolve()),
                })

                self.logger.log_operation("MOVE", str(source), str(final_dest), True)
                res.moved_count += 1
                res.details.append({
                    "file": filename,
                    "status": "SUCCESS",
                    "destination": str(final_dest),
                })

                if progress_callback:
                    progress_callback(idx, total, filename, final_dest.name)

            except Exception as e:
                res.error_count += 1
                err_msg = str(e)
                res.details.append({
                    "file": filename,
                    "status": "FAILED",
                    "error": err_msg,
                })
                self.logger.log_operation(
                    "MOVE",
                    str(source),
                    str(planned.proposed_destination),
                    False,
                    err_msg,
                )

        # Store successful moves into history for undo
        if successful_moves:
            self.history_mgr.record_batch(successful_moves)

        return res

    def undo(
        self,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
    ) -> UndoResult:
        """
        Revert the most recent organization batch.
        Restores files to original locations safely, preventing collisions.
        """
        batch = self.history_mgr.pop_last_batch()
        if not batch or not batch.get("moves"):
            return UndoResult(
                success=False,
                message="No recent organization operation found to undo.",
            )

        moves = batch["moves"]
        total = len(moves)
        restored = 0
        errors = 0
        details = []

        for idx, item in enumerate(reversed(moves), start=1):
            original_path = Path(item["original"])
            destination_path = Path(item["destination"])

            # Check if file exists at moved destination
            if not destination_path.exists():
                errors += 1
                err_str = f"File not found at destination: {destination_path.name}"
                details.append({
                    "file": destination_path.name,
                    "status": "FAILED",
                    "error": err_str,
                })
                self.logger.log_operation(
                    "UNDO_MOVE", str(destination_path), str(original_path), False, err_str
                )
                continue

            try:
                # Ensure original folder exists
                orig_dir = original_path.parent
                orig_dir.mkdir(parents=True, exist_ok=True)

                # Ensure safe destination (do not overwrite if something took original place)
                safe_restore_path = get_safe_destination_path(orig_dir, original_path.name)

                shutil.move(str(destination_path), str(safe_restore_path))
                restored += 1
                details.append({
                    "file": destination_path.name,
                    "status": "SUCCESS",
                    "destination": str(safe_restore_path),
                })
                self.logger.log_operation(
                    "UNDO_MOVE", str(destination_path), str(safe_restore_path), True
                )

                if progress_callback:
                    progress_callback(idx, total, destination_path.name, safe_restore_path.name)

            except Exception as e:
                errors += 1
                err_str = str(e)
                details.append({
                    "file": destination_path.name,
                    "status": "FAILED",
                    "error": err_str,
                })
                self.logger.log_operation(
                    "UNDO_MOVE", str(destination_path), str(original_path), False, err_str
                )

        msg = f"Restored {restored} files."
        if errors > 0:
            msg += f" {errors} errors encountered."

        return UndoResult(
            success=(restored > 0 or errors == 0),
            restored_count=restored,
            error_count=errors,
            message=msg,
            details=details,
        )
