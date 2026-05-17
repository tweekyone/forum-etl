"""Точка входа CLI."""

from __future__ import annotations

import sys
from pathlib import Path

from forum_etl.export_json import export_topic_to_json, resolve_output_path
from forum_etl.iter1 import build_posts_iter1
from forum_etl.topic_file import TopicFileError, format_topic_file_error, load_topic_bundle


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        print(
            "usage: forum-etl <path-to-topic.txt> [OUT]\n"
            "       forum-etl --help\n"
            "\n"
            "OUT — необязательно: файл .json или каталог (по умолчанию out/topic_<id>.json).\n"
            "Код выхода: 0 — ок, 1 — ошибка разбора, 2 — неверные аргументы.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if argv[0] in ("-h", "--help"):
        print(
            "forum-etl — экспорт топика в JSON (итерация 1 постов).\n"
            "\n"
            "  forum-etl data/topic_2036930.txt\n"
            "  forum-etl data/topic_2036930.txt out/custom.json\n"
            "  forum-etl data/topic_2036930.txt out/\n",
        )
        raise SystemExit(0)

    if len(argv) > 2:
        print("forum-etl: слишком много аргументов.", file=sys.stderr)
        raise SystemExit(2)

    in_path = Path(argv[0])
    try:
        bundle = load_topic_bundle(in_path)
    except TopicFileError as e:
        print(format_topic_file_error(e), file=sys.stderr)
        raise SystemExit(1) from e

    src = in_path.resolve()
    try:
        posts = build_posts_iter1(bundle, src)
    except TopicFileError as e:
        print(format_topic_file_error(e), file=sys.stderr)
        raise SystemExit(1) from e

    tid = str(bundle.topic["topic_id"]).strip()
    if len(argv) == 2:
        out_path = resolve_output_path(Path(argv[1]), tid)
    else:
        out_path = Path("out") / f"topic_{tid}.json"

    try:
        export_topic_to_json(bundle, posts, out_path, topic_source=src)
    except TopicFileError as e:
        print(format_topic_file_error(e), file=sys.stderr)
        raise SystemExit(1) from e
    except OSError as e:
        print(f"не удалось записать {out_path}: {e}", file=sys.stderr)
        raise SystemExit(1) from e

    out_resolved = out_path.resolve()
    print(
        f"topic_id={tid!r} title={bundle.topic.get('title')!r} posts={len(posts)} -> {out_resolved}",
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()
