"""Test: i18n loader."""
from __future__ import annotations

import pytest

from app.i18n.loader import load_page, t, available_languages


def test_available_languages():
    langs = available_languages()
    assert "ua" in langs
    assert "en" in langs
    assert "ru" in langs
    assert "de" in langs


def test_load_page_returns_dict():
    data = load_page("home", "en")
    assert isinstance(data, dict)


def test_page_strings_override_common():
    """Page-specific keys must exist and common keys must also be present."""
    data = load_page("home", "en")
    assert t(data, "common.site.name") == "Pravdalist"
    assert t(data, "page.title") != "page.title"


def test_missing_key_returns_key():
    data = load_page("home", "en")
    result = t(data, "this.key.does.not.exist")
    assert result == "this.key.does.not.exist"
