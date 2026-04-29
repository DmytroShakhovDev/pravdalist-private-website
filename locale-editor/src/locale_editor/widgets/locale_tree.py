"""Tree widget showing locale node structure."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from locale_editor.services.locales_scanner import LocalesScanner


class LocaleTree(QTreeWidget):
    """Left-pane tree of locale nodes."""

    node_selected = pyqtSignal(str)

    def __init__(self, scanner: LocalesScanner) -> None:
        super().__init__()
        self._scanner = scanner
        self.setHeaderLabel("Locales")
        self.itemClicked.connect(self._on_click)
        self.refresh()

    def refresh(self) -> None:
        self.clear()
        for node in self._scanner.scan():
            parts = node.split("/")
            parent = self.invisibleRootItem()
            for part in parts:
                existing = None
                for i in range(parent.childCount()):
                    if parent.child(i).text(0) == part:
                        existing = parent.child(i)
                        break
                if existing is None:
                    item = QTreeWidgetItem([part])
                    item.setData(0, 100, node)
                    parent.addChild(item)
                    parent = item
                else:
                    parent = existing
        self.expandAll()

    def _on_click(self, item: QTreeWidgetItem, _col: int) -> None:
        node_path = item.data(0, 100)
        if node_path:
            self.node_selected.emit(node_path)
