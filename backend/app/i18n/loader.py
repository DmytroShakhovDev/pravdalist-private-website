"""Localization loader — merges common + page JSON files with caching."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_LOCALES_DIR = Path(__file__).parent / "locales"
_COMMON_DIR = _LOCALES_DIR / "common"
_PAGES_DIR = _LOCALES_DIR / "pages"

_cache: Dict[tuple[str, str], tuple[Dict[str, Any], float, float]] = {}


def _load_json(path: Path) -> Dict[str, Any]:
    # Resolve the path and verify it stays within the locales directory to
    # prevent any path traversal even if validation above is somehow bypassed.
    try:
        resolved = path.resolve()
        resolved.relative_to(_LOCALES_DIR.resolve())
    except ValueError:
        logger.warning("Path traversal attempt blocked: %s", path)
        return {}
    if not resolved.exists():
        logger.warning("Locale file not found: %s", path)
        return {}
    with resolved.open(encoding="utf-8") as fh:
        return json.load(fh)


def _mtime(path: Path) -> float:
    try:
        resolved = path.resolve()
        resolved.relative_to(_LOCALES_DIR.resolve())
        return resolved.stat().st_mtime
    except (FileNotFoundError, ValueError):
        return 0.0


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into *base* (override wins)."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


_ALLOWED_LANGS = frozenset(["ua", "en", "ru", "de"])
_ALLOWED_PAGE_RE = __import__("re").compile(r"^[a-z0-9_-]+$")

# Dict with literal values so that lookups produce an untainted string for
# static analysis tools — the result is always one of the literal dict values,
# never the raw user-supplied string.
_LANG_MAP: Dict[str, str] = {"ua": "ua", "en": "en", "ru": "ru", "de": "de"}


def load_page(page: str, lang: str) -> Dict[str, Any]:
    """
    Return merged localization dict for *page* + *lang*.
    Common strings form the base; page-specific strings override.
    Result is cached; cache invalidates when file mtimes change.
    """
    if lang not in _ALLOWED_LANGS:
        lang = "ua"
    if not _ALLOWED_PAGE_RE.match(page):
        logger.warning("Invalid page name requested: %s", page)
        return {}

    # Untaint lang: retrieve from a dict of literal values so that static
    # analysis sees only the known-safe dict value flow into path construction,
    # not the raw user-supplied string.
    safe_lang = _LANG_MAP.get(lang, "ua")
    common_path = _COMMON_DIR / f"{safe_lang}.json"
    page_path = _PAGES_DIR / page / f"{safe_lang}.json"

    mtime_c = _mtime(common_path)
    mtime_p = _mtime(page_path)

    key = (page, lang)
    if key in _cache:
        cached_dict, cached_mc, cached_mp = _cache[key]
        if cached_mc == mtime_c and cached_mp == mtime_p:
            return cached_dict

    common = _load_json(common_path)
    page_data = _load_json(page_path)
    merged = _deep_merge(common, page_data)
    _cache[key] = (merged, mtime_c, mtime_p)
    return merged


def available_languages() -> List[str]:
    """Return list of supported language codes."""
    return ["ua", "en", "ru", "de"]


def t(strings: Dict[str, Any], key: str, **fmt: Any) -> str:
    """
    Dotted-key lookup in *strings* dict.
    Missing key returns the key string and logs a warning.
    """
    parts = key.split(".")
    node: Any = strings
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            logger.warning("Missing i18n key: %s", key)
            return key
    if isinstance(node, str) and fmt:
        try:
            return node.format(**fmt)
        except KeyError:
            return node
    return str(node) if not isinstance(node, str) else node
