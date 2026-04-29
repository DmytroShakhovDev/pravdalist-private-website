"""JSON locale file store — load/save with sorting and validation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_LANGS = ["ua", "en", "ru", "de"]


def _flatten(d: dict[str, Any], prefix: str = "") -> dict[str, str]:
    """Flatten nested dict to dotted keys."""
    result: dict[str, str] = {}
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(_flatten(v, full_key))
        else:
            result[full_key] = str(v)
    return result


def _unflatten(flat: dict[str, str]) -> dict[str, Any]:
    """Convert dotted keys back to nested dict."""
    result: dict[str, Any] = {}
    for key, value in sorted(flat.items()):
        parts = key.split(".")
        node = result
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return result


class JsonStore:
    """Load and save locale JSON files for a node directory."""

    def load_node(self, node_dir: Path) -> dict[str, dict[str, str]]:
        """
        Load all language files in *node_dir*.
        Returns {flat_key: {lang: value}} (union of keys).
        """
        per_lang: dict[str, dict[str, str]] = {}
        for lang in _LANGS:
            path = node_dir / f"{lang}.json"
            if path.exists():
                with path.open(encoding="utf-8") as fh:
                    raw = json.load(fh)
                per_lang[lang] = _flatten(raw)
            else:
                per_lang[lang] = {}

        all_keys: set[str] = set()
        for d in per_lang.values():
            all_keys.update(d.keys())

        return {
            key: {lang: per_lang[lang].get(key, "") for lang in _LANGS}
            for key in sorted(all_keys)
        }

    def save_node(
        self, node_dir: Path, data: dict[str, dict[str, str]]
    ) -> list[str]:
        """
        Save data back to JSON files.
        Returns list of validation warnings (mismatched key sets).
        """
        node_dir.mkdir(parents=True, exist_ok=True)
        per_lang: dict[str, dict[str, str]] = {lang: {} for lang in _LANGS}
        for key, translations in data.items():
            for lang in _LANGS:
                per_lang[lang][key] = translations.get(lang, "")

        key_sets = {lang: set(d.keys()) for lang, d in per_lang.items()}
        issues: list[str] = []
        ref = key_sets[_LANGS[0]]
        for lang in _LANGS[1:]:
            if key_sets[lang] != ref:
                missing = ref - key_sets[lang]
                extra = key_sets[lang] - ref
                if missing:
                    issues.append(f"{lang}: missing keys {missing}")
                if extra:
                    issues.append(f"{lang}: extra keys {extra}")

        for lang in _LANGS:
            path = node_dir / f"{lang}.json"
            nested = _unflatten(per_lang[lang])
            with path.open("w", encoding="utf-8") as fh:
                json.dump(nested, fh, ensure_ascii=False, indent=2, sort_keys=True)
                fh.write("\n")

        return issues
