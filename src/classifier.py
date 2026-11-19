"""File classification logic for Downloads Organizer.

Determines which category folder a file belongs to based on extension,
or whether it should be ignored according to rules and configuration.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union


@dataclass
class ClassificationResult:
    category: Optional[str]
    is_ignored: bool
    reason: str


class FileClassifier:
    """Classifies files into categories based on file extension and rules."""

    def __init__(
        self,
        categories: Dict[str, List[str]] = None,
        ignored_extensions: List[str] = None,
        ignored_files: List[str] = None,
        organize_unknown_files: bool = True,
        unknown_folder_name: str = "Other",
    ):
        self.categories = categories or {}
        self.ignored_extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in (ignored_extensions or [])
        ]
        self.ignored_files = [f.lower() for f in (ignored_files or [])]
        self.organize_unknown_files = organize_unknown_files
        self.unknown_folder_name = unknown_folder_name
        self._extension_map: Dict[str, str] = {}
        self._build_extension_map()

    def _build_extension_map(self) -> None:
        """Build reverse lookup dictionary mapping normalized extension to category."""
        self._extension_map = {}
        for category, extensions in self.categories.items():
            for ext in extensions:
                norm_ext = ext.strip().lower()
                if not norm_ext.startswith("."):
                    norm_ext = f".{norm_ext}"
                self._extension_map[norm_ext] = category

    def update_rules(
        self,
        categories: Dict[str, List[str]] = None,
        ignored_extensions: List[str] = None,
        ignored_files: List[str] = None,
        organize_unknown_files: bool = None,
        unknown_folder_name: str = None,
    ) -> None:
        """Update classifier rules dynamically."""
        if categories is not None:
            self.categories = categories
        if ignored_extensions is not None:
            self.ignored_extensions = [
                ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                for ext in ignored_extensions
            ]
        if ignored_files is not None:
            self.ignored_files = [f.lower() for f in ignored_files]
        if organize_unknown_files is not None:
            self.organize_unknown_files = organize_unknown_files
        if unknown_folder_name is not None:
            self.unknown_folder_name = unknown_folder_name
        self._build_extension_map()

    def classify(self, file_path: Union[str, Path]) -> ClassificationResult:
        """
        Classify a file by name or path.
        Returns a ClassificationResult detailing category and ignore status.
        """
        path = Path(file_path)
        filename = path.name.lower()

        # Check ignored filenames (case-insensitive)
        if filename in self.ignored_files:
            return ClassificationResult(
                category=None,
                is_ignored=True,
                reason=f"Ignored system file: {path.name}",
            )

        suffix = path.suffix.lower()

        # Check ignored extensions (.lnk, .tmp, .crdownload, etc.)
        if suffix in self.ignored_extensions:
            return ClassificationResult(
                category=None,
                is_ignored=True,
                reason=f"Ignored extension: {suffix or 'no extension'}",
            )

        # Check defined category mapping
        if suffix in self._extension_map:
            cat = self._extension_map[suffix]
            return ClassificationResult(
                category=cat,
                is_ignored=False,
                reason=f"Matched category: {cat}",
            )

        # Handle unknown extensions
        if self.organize_unknown_files:
            return ClassificationResult(
                category=self.unknown_folder_name,
                is_ignored=False,
                reason="Unknown extension mapped to fallback category",
            )
        else:
            return ClassificationResult(
                category=None,
                is_ignored=True,
                reason="Unknown extension handling disabled",
            )
