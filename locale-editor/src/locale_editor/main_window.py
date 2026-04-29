"""Main application window."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QToolBar,
    QWidget,
    QMessageBox,
)
from PyQt6.QtGui import QAction

from locale_editor.widgets.locale_tree import LocaleTree
from locale_editor.widgets.strings_table import StringsTable
from locale_editor.services.locales_scanner import LocalesScanner
from locale_editor.services.json_store import JsonStore
from locale_editor.services.translator import Translator

_LOCALES_DIR = Path(__file__).parent.parent.parent.parent.parent / "backend" / "app" / "i18n" / "locales"


class MainWindow(QMainWindow):
    """QMainWindow: tree (left) + table (right)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Locale Editor — Pravdalist")
        self.resize(1200, 700)

        self._scanner = LocalesScanner(_LOCALES_DIR)
        self._store = JsonStore()
        self._translator = Translator()
        self._current_node: str | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = QToolBar("Actions")
        self.addToolBar(toolbar)

        act_add = QAction("Add key", self)
        act_add.triggered.connect(self._on_add_key)
        toolbar.addAction(act_add)

        act_del = QAction("Delete key", self)
        act_del.triggered.connect(self._on_delete_key)
        toolbar.addAction(act_del)

        toolbar.addSeparator()

        act_translate_row = QAction("Auto-translate row", self)
        act_translate_row.triggered.connect(self._on_translate_row)
        toolbar.addAction(act_translate_row)

        act_translate_all = QAction("Auto-translate all empty", self)
        act_translate_all.triggered.connect(self._on_translate_all)
        toolbar.addAction(act_translate_all)

        toolbar.addSeparator()

        act_save = QAction("Save", self)
        act_save.triggered.connect(self._on_save)
        toolbar.addAction(act_save)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._tree = LocaleTree(self._scanner)
        self._tree.node_selected.connect(self._on_node_selected)
        splitter.addWidget(self._tree)

        self._table = StringsTable()
        splitter.addWidget(self._table)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        self.setCentralWidget(splitter)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _on_node_selected(self, node_path: str) -> None:
        self._current_node = node_path
        data = self._store.load_node(_LOCALES_DIR / node_path)
        self._table.load_data(data)
        n_keys = self._table.key_count()
        n_missing = self._table.missing_count()
        self._status.showMessage(f"{node_path}  |  {n_keys} keys, {n_missing} missing translations")

    def _on_add_key(self) -> None:
        self._table.add_key()

    def _on_delete_key(self) -> None:
        self._table.delete_selected_key()

    def _on_translate_row(self) -> None:
        row = self._table.current_row()
        if row < 0:
            return
        self._translate_rows([row])

    def _on_translate_all(self) -> None:
        rows = self._table.rows_with_empty_cells()
        self._translate_rows(rows)

    def _translate_rows(self, rows: list[int]) -> None:
        if not rows:
            return
        progress = QProgressDialog("Translating…", "Cancel", 0, len(rows), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        for i, row in enumerate(rows):
            if progress.wasCanceled():
                break
            progress.setValue(i)
            try:
                self._table.auto_translate_row(row, self._translator)
            except Exception as exc:
                QMessageBox.warning(self, "Translation Error", str(exc))
                break
        progress.setValue(len(rows))

    def _on_save(self) -> None:
        if not self._current_node:
            return
        data = self._table.get_data()
        issues = self._store.save_node(_LOCALES_DIR / self._current_node, data)
        if issues:
            QMessageBox.warning(self, "Key mismatch", "\n".join(issues))
        else:
            self._status.showMessage(f"Saved: {self._current_node}")
