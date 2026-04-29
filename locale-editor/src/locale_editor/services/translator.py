"""Translator service using deep-translator (Google backend)."""
from __future__ import annotations

import logging

from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

_LANG_MAP = {
    "ua": "uk",
    "en": "en",
    "ru": "ru",
    "de": "de",
}


class Translator:
    """Wraps GoogleTranslator with app language codes."""

    def translate(self, text: str, source: str, target: str) -> str | None:
        """
        Translate *text* from *source* to *target* (app codes: ua/en/ru/de).
        Returns translated string or None on failure.
        """
        if source == target or not text.strip():
            return text

        src = _LANG_MAP.get(source, source)
        tgt = _LANG_MAP.get(target, target)

        try:
            result = GoogleTranslator(source=src, target=tgt).translate(text)
            return result
        except Exception as exc:
            logger.error("Translation failed (%s->%s): %s", source, target, exc)
            raise
