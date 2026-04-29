# Locale Editor

A PyQt6 desktop application for editing `backend/app/i18n/locales/` JSON files.

## Usage

```bash
pip install -e .
python -m locale_editor
```

## Features

- Tree pane: shows `common/` and `pages/<page>/` nodes
- Table pane: `key | ua | en | ru | de` — union of all keys across languages
- Add / Delete key
- Auto-translate row (ua → en/ru/de) using Google Translate (no API key)
- Auto-translate all empty cells
- Save with key-set validation and sorted JSON
