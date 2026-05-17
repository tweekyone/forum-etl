"""Сборка корневого JSON топика и запись в UTF-8 (этап 5)."""

from __future__ import annotations

import json
from pathlib import Path

from forum_etl.topic_file import TopicBundle, TopicFileError


def build_topic_json_root(
    bundle: TopicBundle,
    posts: list[dict],
    *,
    topic_source: Path,
) -> dict:
    """Корень документа: topic_id, title, posts (см. docs/vision.md)."""
    tid = bundle.topic.get("topic_id")
    title = bundle.topic.get("title")
    if tid is None or title is None:
        raise TopicFileError(
            path=topic_source,
            detail="в документе topic нет topic_id или title",
        )
    return {
        "topic_id": str(tid).strip(),
        "title": title if isinstance(title, str) else str(title),
        "posts": posts,
    }


def write_topic_json(root: dict, out_path: Path) -> None:
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(root, ensure_ascii=False, indent=2) + "\n"
    out_path.write_text(payload, encoding="utf-8")


def resolve_output_path(out_arg: Path, topic_id: str) -> Path:
    """
    Если out_arg — путь к .json, пишем в этот файл.
    Иначе считаем out_arg каталогом: topic_<topic_id>.json внутри.
    """
    if out_arg.suffix.lower() == ".json":
        return out_arg
    return out_arg / f"topic_{topic_id}.json"


def export_topic_to_json(
    bundle: TopicBundle,
    posts: list[dict],
    out_path: Path,
    *,
    topic_source: Path,
) -> None:
    root = build_topic_json_root(bundle, posts, topic_source=topic_source)
    write_topic_json(root, out_path)
