"""Scanner for locale node directories."""
from __future__ import annotations

from pathlib import Path


class LocalesScanner:
    """Discovers locale nodes (common/ and pages/<page>/) in a locales directory."""

    def __init__(self, locales_dir: Path) -> None:
        self._root = locales_dir

    def scan(self) -> list[str]:
        """
        Return list of relative node paths, e.g.
        ['common', 'pages/home', 'pages/about', 'pages/contacts'].
        """
        nodes: list[str] = []
        common = self._root / "common"
        if common.is_dir():
            nodes.append("common")

        pages_dir = self._root / "pages"
        if pages_dir.is_dir():
            for child in sorted(pages_dir.iterdir()):
                if child.is_dir():
                    nodes.append(f"pages/{child.name}")

        return nodes
