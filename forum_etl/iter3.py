"""Итерация 3: заполнение quotes_out через RapidFuzz (см. docs/vision.md)."""

from __future__ import annotations

from rapidfuzz import fuzz

DEFAULT_LINK_THRESHOLD = 85


def _link_score(quote: str, post_text: str) -> int:
    return max(
        fuzz.partial_ratio(quote, post_text),
        fuzz.token_sort_ratio(quote, post_text),
    )


def apply_quotes_out(
    posts: list[dict],
    *,
    threshold: int = DEFAULT_LINK_THRESHOLD,
) -> None:
    """
    Для каждого поста: по каждой нормализованной цитате ищет лучший среди постов
    с меньшим post_index; при score >= threshold добавляет id в множество связей.
    quotes_out — уникальные id, порядок по возрастанию post_index.
    quotes_in не трогает.
    """
    ordered = sorted(posts, key=lambda p: p["post_index"])

    for post in ordered:
        pi = post["post_index"]
        linked_pi: set[int] = set()

        for q in post.get("quotes") or []:
            qs = q if isinstance(q, str) else str(q)
            best_score = -1
            best_pi = -1
            best_id: str | None = None

            for cand in ordered:
                cpi = cand["post_index"]
                if cpi >= pi:
                    break
                text = cand.get("text")
                ts = text if isinstance(text, str) else str(text)
                s = _link_score(qs, ts)
                if s > best_score or (s == best_score and cpi > best_pi):
                    best_score = s
                    best_pi = cpi
                    best_id = str(cand["id"])

            if best_score >= threshold and best_id is not None:
                linked_pi.add(best_pi)

        post["quotes_out"] = [str(p["id"]) for p in ordered if p["post_index"] in linked_pi]
