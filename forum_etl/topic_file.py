"""Чтение файла топика как потока YAML-документов (этап 3)."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import yaml
from yaml import YAMLError


@dataclass
class TopicBundle:
    """Первый документ topic + все сообщения kind: message."""

    topic: dict
    messages: list[dict]


class TopicFileError(Exception):
    """Ошибка чтения или структуры файла топика."""

    def __init__(
        self,
        path: Path,
        detail: str,
        *,
        cause: Exception | None = None,
        stream_doc_index: int | None = None,
        line: int | None = None,
        column: int | None = None,
        context: str | None = None,
    ) -> None:
        self.path = path
        self.detail = detail
        self.cause = cause
        self.stream_doc_index = stream_doc_index
        self.line = line
        self.column = column
        self.context = context
        super().__init__(detail)

    def __str__(self) -> str:
        parts = [self.detail]
        if self.stream_doc_index is not None:
            parts.append(f"индекс документа в потоке YAML (0-based): {self.stream_doc_index}")
        if self.line is not None:
            col = self.column if self.column is not None else "?"
            parts.append(f"позиция: строка {self.line}, колонка {col}")
        return "; ".join(parts)


def format_topic_file_error(exc: TopicFileError) -> str:
    """Текстовый отчёт для CLI / логов (см. docs/vision.md, политика ошибок)."""
    lines = [
        f"файл: {exc.path}",
        f"ошибка: {exc.detail}",
    ]
    if exc.cause is not None:
        lines.append(f"тип исключения: {type(exc.cause).__name__}")
        lines.append(f"текст исключения: {exc.cause}")
    if exc.stream_doc_index is not None:
        lines.append(f"индекс документа в потоке multi-doc (0-based): {exc.stream_doc_index}")
    if exc.line is not None:
        col = exc.column if exc.column is not None else "?"
        lines.append(f"позиция YAML: строка {exc.line}, колонка {col}")
    if exc.context:
        lines.append("контекст:")
        lines.append(exc.context)
    return "\n".join(lines)


def _yaml_mark(exc: YAMLError, raw: str) -> tuple[int | None, int | None, str | None]:
    mark = getattr(exc, "problem_mark", None)
    if mark is None:
        return None, None, None
    line = mark.line + 1
    column = mark.column + 1
    split = raw.splitlines()
    lo = max(0, mark.line - 2)
    hi = min(len(split), mark.line + 3)
    ctx = "\n".join(f"{i + 1:4} | {split[i]}" for i in range(lo, hi)) if split else None
    return line, column, ctx


def _load_all_documents(raw: str, path: Path) -> list[object]:
    """Парсит multi-doc; при YAMLError пробрасывает TopicFileError с контекстом."""
    loader = yaml.safe_load_all(StringIO(raw))
    stream_idx = 0
    out: list[object] = []
    while True:
        try:
            doc = next(loader)
        except StopIteration:
            break
        except YAMLError as e:
            line, column, ctx = _yaml_mark(e, raw)
            raise TopicFileError(
                path=path,
                detail="синтаксическая или структурная ошибка YAML при разборе multi-doc",
                cause=e,
                stream_doc_index=stream_idx,
                line=line,
                column=column,
                context=ctx,
            ) from e
        stream_idx += 1
        out.append(doc)
    return out


def load_topic_bundle(path: Path | str) -> TopicBundle:
    """
    Читает файл топика: первый непустой документ — kind: topic, далее — kind: message.
    Пустые документы (None) в потоке пропускаются.
    """
    path = Path(path).resolve()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise TopicFileError(
            path=path,
            detail=f"не удалось прочитать файл: {e}",
            cause=e,
        ) from e

    docs = _load_all_documents(raw, path)
    stream_index_nonempty: list[int] = []
    for si, d in enumerate(docs):
        if d is None:
            continue
        stream_index_nonempty.append(si)

    payloads = [d for d in docs if d is not None]
    if not payloads:
        raise TopicFileError(path=path, detail="нет ни одного непустого YAML-документа")

    topic = payloads[0]
    sid0 = stream_index_nonempty[0]
    if not isinstance(topic, dict):
        raise TopicFileError(
            path=path,
            detail=f"первый документ должен быть mapping (объект topic), получен {type(topic).__name__}",
            stream_doc_index=sid0,
        )
    if topic.get("kind") != "topic":
        raise TopicFileError(
            path=path,
            detail=f"первый документ: ожидался kind='topic', получено {topic.get('kind')!r}",
            stream_doc_index=sid0,
        )
    for key in ("topic_id", "title"):
        if key not in topic:
            raise TopicFileError(
                path=path,
                detail=f"документ topic: отсутствует обязательное поле {key!r}",
                stream_doc_index=sid0,
            )

    messages: list[dict] = []
    for i, doc in enumerate(payloads[1:], start=1):
        sid = stream_index_nonempty[i]
        if not isinstance(doc, dict):
            raise TopicFileError(
                path=path,
                detail=f"документ #{i} после topic: ожидался mapping, получен {type(doc).__name__}",
                stream_doc_index=sid,
            )
        if doc.get("kind") != "message":
            raise TopicFileError(
                path=path,
                detail=(
                    f"документ #{i} после topic: ожидался kind='message', получено {doc.get('kind')!r}"
                ),
                stream_doc_index=sid,
            )
        messages.append(doc)

    return TopicBundle(topic=topic, messages=messages)
