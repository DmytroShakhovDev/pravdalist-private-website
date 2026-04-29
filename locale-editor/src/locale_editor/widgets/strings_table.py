"""Table widget: key | ua | en | ru | de."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QInputDialog,
    QTableWidget,
    QTableWidgetItem,
)

from locale_editor.services.translator import Translator

_LANGS = ["ua", "en", "ru", "de"]
_COLS = ["key"] + _LANGS


class StringsTable(QTableWidget):
    """Right-pane table of locale strings."""

    def __init__(self) -> None:
        super().__init__(0, len(_COLS))
        self.setHorizontalHeaderLabels(_COLS)
        self.horizontalHeader().setStretchLastSection(True)

    def load_data(self, data: dict[str, dict[str, str]]) -> None:
        """Load {key: {lang: value}} dict into the table."""
        self.setRowCount(0)
        for key, translations in sorted(data.items()):
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(key))
            for col, lang in enumerate(_LANGS, start=1):
                self.setItem(row, col, QTableWidgetItem(translations.get(lang, "")))

    def get_data(self) -> dict[str, dict[str, str]]:
        """Return current table contents as {key: {lang: value}}."""
        result: dict[str, dict[str, str]] = {}
        for row in range(self.rowCount()):
            key_item = self.item(row, 0)
            if not key_item:
                continue
            key = key_item.text().strip()
            if not key:
                continue
            result[key] = {}
            for col, lang in enumerate(_LANGS, start=1):
                cell = self.item(row, col)
                result[key][lang] = cell.text() if cell else ""
        return result

    def key_count(self) -> int:
        return self.rowCount()

    def missing_count(self) -> int:
        count = 0
        for row in range(self.rowCount()):
            for col in range(1, len(_COLS)):
                cell = self.item(row, col)
                if not cell or not cell.text().strip():
                    count += 1
        return count

    def add_key(self) -> None:
        key, ok = QInputDialog.getText(self, "Add key", "Enter new key:")
        if ok and key.strip():
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(key.strip()))
            for col in range(1, len(_COLS)):
                self.setItem(row, col, QTableWidgetItem(""))

    def delete_selected_key(self) -> None:
        rows = sorted({idx.row() for idx in self.selectedIndexes()}, reverse=True)
        for row in rows:
            self.removeRow(row)

    def current_row(self) -> int:
        return self.currentRow()

    def rows_with_empty_cells(self) -> list[int]:
        result = []
        for row in range(self.rowCount()):
            for col in range(1, len(_COLS)):
                cell = self.item(row, col)
                if not cell or not cell.text().strip():
                    result.append(row)
                    break
        return result

    def auto_translate_row(self, row: int, translator: Translator) -> None:
        """Translate empty cells in *row* from first non-empty language."""
        source_text = ""
        source_lang = "ua"
        for col, lang in enumerate(_LANGS, start=1):
            cell = self.item(row, col)
            if cell and cell.text().strip():
                source_text = cell.text().strip()
                source_lang = lang
                break

        if not source_text:
            return

        for col, lang in enumerate(_LANGS, start=1):
            cell = self.item(row, col)
            if cell and cell.text().strip():
                continue
            translated = translator.translate(source_text, source_lang, lang)
            if translated:
                self.setItem(row, col, QTableWidgetItem(translated))
