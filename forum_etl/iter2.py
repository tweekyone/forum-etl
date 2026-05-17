"""Итерация 2: нормализация text и quotes (см. docs/vision.md)."""

from __future__ import annotations

import re


# Плейсхолдеры и ник (в т. ч. несколько слов) перед « писал(а):».
_WRITTEN_BY_FRAGMENT = re.compile(
    r"(?:%user%|%username%|(?:\S+(?:\s+\S+)*))\s+писал\(а\):\s*",
    re.IGNORECASE | re.UNICODE,
)

# Строка даты в стиле экспорта после шага 1 — одна «строка» без переносов.
_DATE_FRAGMENT = re.compile(
    r"(?:»|>>)\s*\d{1,2}\s+\S+\s+\d{4}(?:,\s*\d{1,2}:\d{2})?",
    re.UNICODE,
)

_WS_RUN = re.compile(r"\s+")


def _collapse_whitespace(s: str) -> str:
    s = _WS_RUN.sub(" ", s)
    return s.strip()


def normalize_text_iter2(text: str) -> str:
    """
    Четыре шага vision: схлопнуть пробелы → убрать «… писал(а):» → убрать фрагменты даты »/>> … → снова схлопнуть.
    """
    s = _collapse_whitespace(text)
    s = _WRITTEN_BY_FRAGMENT.sub("", s)
    s = _DATE_FRAGMENT.sub("", s)
    s = _collapse_whitespace(s)
    return s


def apply_iter2_to_posts(posts: list[dict]) -> None:
    """Нормализует text и каждый элемент quotes на месте (тот же порядок и длины)."""
    for post in posts:
        raw = post.get("text")
        post["text"] = normalize_text_iter2(raw if isinstance(raw, str) else str(raw))
        quotes = post.get("quotes")
        if not quotes:
            continue
        post["quotes"] = [
            normalize_text_iter2(q if isinstance(q, str) else str(q)) for q in quotes
        ]
