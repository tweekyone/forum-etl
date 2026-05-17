"""Итерация 1 пайплайна: поля поста из YAML без нормализации (см. docs/vision.md)."""

from __future__ import annotations

import re
from pathlib import Path

from forum_etl.topic_file import TopicBundle, TopicFileError

# Первая строка цитаты: «ник / плейсхолдер» + « писал(а):» (экспорт и шаблон %username%).
_QUOTE_AUTHOR_FIRST_LINE = re.compile(r"^(.+?) писал\(а\):\s*$", re.UNICODE)


def _as_str(value: object, field: str, *, path: Path, post_index: int) -> str:
    if value is None:
        raise TopicFileError(
            path=path,
            detail=f"сообщение post_index={post_index}: отсутствует поле {field!r}",
        )
    if isinstance(value, str):
        return value
    return str(value)


def extract_body_main_text(body: str, *, path: Path, post_index: int) -> str:
    """
    Текст поста — часть body после первой строки, у которой после strip префикс «» или «>>» (дата).
    """
    lines = body.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("»") or stripped.startswith(">>"):
            rest = lines[i + 1 :]
            text = "\n".join(rest)
            return text.lstrip("\n\r").rstrip("\n\r")
    raise TopicFileError(
        path=path,
        detail=(
            f"сообщение post_index={post_index}: в body не найдена строка даты "
            f"(префикс » или >>)"
        ),
    )


def strip_quote_written_by_line(text: str) -> str:
    """
    Убирает служебную первую строку цитаты «… писал(а):» (в т. ч. «%username% писал(а):»)
    и следующие за ней пустые строки до основного текста цитаты.
    """
    lines = text.splitlines()
    if not lines:
        return text
    first = lines[0].strip()
    if not _QUOTE_AUTHOR_FIRST_LINE.match(first):
        return text
    rest = lines[1:]
    while rest and not rest[0].strip():
        rest = rest[1:]
    return "\n".join(rest).lstrip("\n\r").rstrip("\n\r")


def _quotes_raw_depth1(msg: dict, *, path: Path, post_index: int) -> list[str]:
    raw = msg.get("quotes")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise TopicFileError(
            path=path,
            detail=f"сообщение post_index={post_index}: quotes должен быть списком",
        )
    out: list[str] = []
    for item in raw:
        if not isinstance(item, dict):
            raise TopicFileError(
                path=path,
                detail=f"сообщение post_index={post_index}: элемент quotes должен быть объектом",
            )
        if item.get("depth") != 1:
            continue
        t = item.get("text")
        if t is None:
            out.append(strip_quote_written_by_line(""))
        elif isinstance(t, str):
            out.append(strip_quote_written_by_line(t))
        else:
            out.append(strip_quote_written_by_line(str(t)))
    return out


def build_post_iter1(
    msg: dict,
    *,
    topic_id: str,
    topic_title: str,
    path: Path,
) -> dict:
    """Один пост в форме итерации 1 (сырой text и quotes)."""
    post_index_raw = msg.get("post_index")
    if post_index_raw is None:
        raise TopicFileError(path=path, detail="сообщение без поля post_index")
    if not isinstance(post_index_raw, int):
        raise TopicFileError(
            path=path,
            detail=f"сообщение post_index={post_index_raw!r}: post_index должен быть целым числом",
        )
    post_index = post_index_raw

    post_id = _as_str(msg.get("post_id"), "post_id", path=path, post_index=post_index)
    body = msg.get("body")
    if body is None:
        raise TopicFileError(
            path=path,
            detail=f"сообщение post_index={post_index}: отсутствует body",
        )
    if not isinstance(body, str):
        body = str(body)

    text = extract_body_main_text(body, path=path, post_index=post_index)
    quotes = _quotes_raw_depth1(msg, path=path, post_index=post_index)

    tid = str(topic_id).strip()
    pid = str(post_id).strip()
    post_id_full = f"topic_{tid}_post_{pid}"

    return {
        "id": post_id_full,
        "post_index": post_index,
        "title": topic_title if isinstance(topic_title, str) else str(topic_title),
        "text": text,
        "embedding_text": None,
        "quotes": quotes,
        "quotes_out": [],
        "quotes_in": [],
    }


def build_posts_iter1(bundle: TopicBundle, path: Path) -> list[dict]:
    """Все посты топика, отсортированные по post_index."""
    topic = bundle.topic
    topic_id = topic.get("topic_id")
    topic_title = topic.get("title")
    if topic_id is None or topic_title is None:
        raise TopicFileError(path=path, detail="в документе topic нет topic_id или title")

    for m in bundle.messages:
        pi = m.get("post_index")
        if pi is None:
            raise TopicFileError(
                path=path,
                detail="сообщение без поля post_index (до сортировки)",
            )
        if not isinstance(pi, int):
            raise TopicFileError(
                path=path,
                detail=f"post_index должен быть int, получено {type(pi).__name__}: {pi!r}",
            )

    ordered = sorted(bundle.messages, key=lambda m: m["post_index"])
    seen: set[int] = set()
    for m in ordered:
        pidx = m["post_index"]
        if pidx in seen:
            raise TopicFileError(
                path=path,
                detail=f"дублируется post_index={pidx}",
            )
        seen.add(pidx)

    return [
        build_post_iter1(
            m,
            topic_id=str(topic_id).strip(),
            topic_title=topic_title if isinstance(topic_title, str) else str(topic_title),
            path=path,
        )
        for m in ordered
    ]
