"""Итерация 4: обратный индекс quotes_in по quotes_out (см. docs/vision.md)."""

from __future__ import annotations


def apply_quotes_in(posts: list[dict]) -> None:
    """
    Если id(A) входит в quotes_out поста B, то id(B) попадает в quotes_in поста A.
    Без дубликатов; порядок — по возрастанию post_index постов-цитировавших (B).
    """
    by_id = {str(p["id"]): p for p in posts}
    # id цитируемого поста -> список (post_index цитирующего, id цитирующего)
    incoming: dict[str, list[tuple[int, str]]] = {}

    for b in posts:
        bpi = b["post_index"]
        bid = str(b["id"])
        for aid in b.get("quotes_out") or []:
            akey = str(aid)
            if akey not in by_id:
                continue
            incoming.setdefault(akey, []).append((bpi, bid))

    for p in posts:
        pid = str(p["id"])
        pairs = incoming.get(pid, [])
        pairs.sort(key=lambda t: t[0])
        out: list[str] = []
        seen: set[str] = set()
        for _, bid in pairs:
            if bid in seen:
                continue
            seen.add(bid)
            out.append(bid)
        p["quotes_in"] = out
