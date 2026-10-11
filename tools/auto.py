# /// script
# requires-python = ">=3.11"
# ///
"""Orca 자동화(그리기 → 검수·커밋)가 쓰는 작은 확인 도구.

    uv run tools/auto.py quota       # Codex 남은 사용량(5시간·주간) 보기
    uv run tools/auto.py can-draw    # 그려도 되면 0, 아니면 1 (Codex 자동화 precheck)
    uv run tools/auto.py can-review  # 검수할 그림이 있고 그리는 중이 아니면 0 (Claude 자동화 precheck)
    uv run tools/auto.py lock|unlock # 그리는 동안 art/.drawing 표시

Codex 사용량은 Codex가 남기는 세션 기록(~/.codex/sessions/**/rollout-*.jsonl)의
마지막 rate_limits 값을 읽는다. 창이 이미 리셋됐으면 사용량 0으로 본다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "art" / ".drawing"
LOCK_STALE = 3 * 3600  # ponytail: 3시간 넘은 표시는 죽은 실행으로 본다
MIN_5H, MIN_WEEK = 30, 20  # 남은 % 하한


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def parse_limits(line: str) -> dict | None:
    """세션 기록 한 줄에서 {'5h': 남은%, 'week': 남은%} 를 얻는다."""
    if '"rate_limits"' not in line:
        return None
    try:
        rl = json.loads(line).get("payload", {}).get("rate_limits")
    except json.JSONDecodeError:
        return None
    if not rl:
        return None
    out, now = {}, time.time()
    for w in (rl.get("primary"), rl.get("secondary")):
        if not w or w.get("used_percent") is None:
            continue
        used = float(w["used_percent"])
        reset = w.get("resets_at")
        if reset is not None and float(reset) <= now:
            used = 0.0  # 이미 리셋된 창
        key = "week" if (w.get("window_minutes") or 0) > 300 else "5h"
        out[key] = 100.0 - used
    return out or None


def remaining() -> dict | None:
    files = sorted((codex_home() / "sessions").rglob("rollout-*.jsonl"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files[:20]:
        for line in reversed(f.read_text(encoding="utf-8", errors="ignore").splitlines()):
            if (r := parse_limits(line)):
                return r
    return None


def locked() -> bool:
    return LOCK.exists() and time.time() - LOCK.stat().st_mtime < LOCK_STALE


def pending() -> list[str]:
    out = subprocess.run(["git", "status", "--porcelain", "--", "img"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [l[3:] for l in out.splitlines() if l.endswith(".webp")]


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "quota"
    if cmd == "lock":
        LOCK.parent.mkdir(exist_ok=True); LOCK.touch(); return 0
    if cmd == "unlock":
        LOCK.unlink(missing_ok=True); return 0
    if cmd == "can-review":
        p = pending()
        print(f"검수 대기 {len(p)}장" + (" (그리는 중)" if locked() else ""))
        return 0 if p and not locked() else 1
    r = remaining()
    print(json.dumps(r, ensure_ascii=False) if r else "사용량 기록 없음")
    if cmd == "quota":
        return 0
    if cmd == "can-draw":
        if locked():
            print("이미 그리는 중"); return 1
        if r is None:
            return 0  # 기록이 없으면 한 번 돌려 본다(돌면 기록이 생긴다)
        ok = r.get("5h", 100) >= MIN_5H and r.get("week", 100) >= MIN_WEEK
        print("그림" if ok else f"멈춤: 5시간 {MIN_5H}% · 주간 {MIN_WEEK}% 하한")
        return 0 if ok else 1
    print(__doc__); return 2


def _check() -> None:
    t = time.time()
    line = json.dumps({"payload": {"type": "token_count", "rate_limits": {
        "primary": {"used_percent": 75, "window_minutes": 300, "resets_at": t + 600},
        "secondary": {"used_percent": 90, "window_minutes": 10080, "resets_at": t - 1}}}})
    assert parse_limits(line) == {"5h": 25.0, "week": 100.0}
    assert parse_limits('{"payload":{}}') is None


if __name__ == "__main__":
    _check()
    sys.exit(main())
