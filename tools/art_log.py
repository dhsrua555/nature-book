# /// script
# requires-python = ">=3.11"
# ///
"""삽화 기록(ART_LOG.md)을 git 기록에서 다시 만든다.

    uv run tools/art_log.py     # 커밋된 그림 + 지금 스테이징된 그림까지 ART_LOG.md 에 적는다

검수 자동화(tools/REVIEW.md)가 커밋 직전에 돌리고 ART_LOG.md 를 함께 커밋한다.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ART_LOG.md"
PAT = re.compile(r"^img/(?P<vol>[^/]+)/(?P<id>.+?)(?P<plate>\.id)?\.webp$")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def ko_name(vol: str, sid: str, cache: dict) -> str:
    if (vol, sid) not in cache:
        f = ROOT / "data" / vol / "species" / f"{sid}.json"
        try:
            cache[vol, sid] = json.loads(f.read_text(encoding="utf-8")).get("ko") or sid
        except (OSError, json.JSONDecodeError):
            cache[vol, sid] = sid
    return cache[vol, sid]


def parse(lines: list[str]) -> list[tuple[str, str, str, bool, bool]]:
    """name-status 줄 → (vol, id, path, plate, redraw). 추가(A)·바꿈(M)만."""
    out = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) != 2 or parts[0] not in ("A", "M"):
            continue
        if (m := PAT.match(parts[1])):
            out.append((m["vol"], m["id"], parts[1], bool(m["plate"]), parts[0] == "M"))
    return out


def entries() -> list[tuple[str, str, list]]:
    """(날짜, 커밋 짧은 해시, 그림들) — 새것이 먼저."""
    res = []
    staged = parse(git("diff", "--cached", "--name-status", "--", "img").splitlines())
    if staged:
        res.append((date.today().isoformat(), "", staged))
    log = git("log", "--name-status", "--date=short", "--format=@%h %ad", "--", "img")
    for block in log.split("@")[1:]:
        head, *lines = block.strip().splitlines()
        h, d = head.split()
        if (files := parse(lines)):
            res.append((d, h, files))
    return mark_redraws(res)


def mark_redraws(items: list[tuple[str, str, list]]) -> list[tuple[str, str, list]]:
    """내린 그림은 삭제 커밋 뒤 새로 추가(A)되므로, 예전에 올라간 적 있는 경로면 다시 그림으로 본다."""
    seen: set[str] = set()
    for _, _, files in reversed(items):
        for i, (v, s, p, pl, r) in enumerate(files):
            files[i] = (v, s, p, pl, r or p in seen)
            seen.add(p)
    return items


def render(items: list[tuple[str, str, list]]) -> str:
    cache: dict = {}
    total = sum(len(f) for _, _, f in items)
    out = ["# 삽화 기록", "",
           f"그림이 올라간 순서(새것이 위). 지금까지 {total}장. `tools/art_log.py` 가 커밋마다 다시 만든다.", ""]
    for d, h, files in items:
        out.append(f"## {d}" + (f" · `{h}`" if h else "") + f" · {len(files)}장")
        for label, plate in (("도판", False), ("동정 도해", True)):
            names = [f"[{ko_name(v, s, cache)}]({p})" + (" (다시 그림)" if r else "")
                     for v, s, p, pl, r in files if pl == plate]
            if names:
                out.append(f"- {label}: " + ", ".join(names))
        out.append("")
    return "\n".join(out)


def main() -> int:
    OUT.write_text(render(entries()), encoding="utf-8", newline="\n")
    print(f"{OUT.name} 다시 만듦")
    return 0


def _check() -> None:
    got = parse(["A\timg/aves/turdus-eunomus.webp", "M\timg/aves/suthora-webbiana.id.webp",
                 "D\timg/aves/x.webp", "A\tdata/aves/book.json"])
    assert got == [("aves", "turdus-eunomus", "img/aves/turdus-eunomus.webp", False, False),
                   ("aves", "suthora-webbiana", "img/aves/suthora-webbiana.id.webp", True, True)]
    a = ("aves", "x", "img/aves/x.webp", False, False)
    items = mark_redraws([("d2", "h2", [a]), ("d1", "h1", [a])])  # 새것이 먼저
    assert [f[0][4] for _, _, f in items] == [True, False]


if __name__ == "__main__":
    _check()
    raise SystemExit(main())
