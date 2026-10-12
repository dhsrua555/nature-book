# /// script
# requires-python = ">=3.11"
# ///
"""Orca 자동화(그리기 → 검수·커밋)가 쓰는 작은 확인 도구.

    uv run tools/auto.py quota       # Codex 남은 사용량(5시간·주간) 보기
    uv run tools/auto.py can-draw    # 그려도 되면 0, 아니면 1 (Codex 자동화 precheck: 잔여량 + 그리는 중 아님)
    uv run tools/auto.py quota-ok    # 잔여량만 보고 0/1 (그리는 도중 한 장마다)
    uv run tools/auto.py can-review  # 검수할 그림이 있고 그리는 중이 아니면 0 (Claude 자동화 precheck)
    uv run tools/auto.py lock|unlock # 그리는 동안 art/.drawing 표시
    uv run tools/auto.py clean       # 끝난 자동화 세션 기록을 보관 폴더로 (can-review 가 매번 함께 돈다)

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
    # 지운 그림(D)은 검수할 것이 아니다: 다시 그리려고 지운 것이 매시간 검수를 깨우지 않게
    return [l[3:] for l in out.splitlines() if l.endswith(".webp") and "D" not in l[:2]]


AUTO_PROMPTS = ("tools/WORK.md 대로 삽화를 그려 줘", "tools/REVIEW.md 대로 새 삽화를")
FINISHED_AFTER = 3600  # 마지막 기록 뒤 1시간 지난 세션을 끝난 것으로 본다


def is_auto_session(f: Path) -> bool:
    with f.open("rb") as fh:
        head = fh.read(256_000).decode("utf-8", "ignore")
    return "Nature Book" in head and any(p in head for p in AUTO_PROMPTS)


def clean_sessions(home: Path | None = None) -> int:
    """끝난 자동화 세션 기록을 Orca 세션 목록에서 빼려고 보관 폴더로 옮긴다(지우지 않음)."""
    home = home or Path.home()
    codex = sorted((home / ".codex" / "sessions").rglob("rollout-*.jsonl"),
                   key=lambda p: p.stat().st_mtime)
    jobs = [(f, home / ".codex" / "archived_sessions" / f.name) for f in codex[:-1]]  # 최신 1개는 사용량 읽기용
    claude = home / ".claude" / "projects"
    jobs += [(f, home / ".claude" / "archived-automation" / f.relative_to(claude))
             for f in claude.glob("*/*.jsonl")]
    now, moved = time.time(), 0
    for src, dst in jobs:
        try:
            if now - src.stat().st_mtime < FINISHED_AFTER or not is_auto_session(src):
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.replace(dst)
            moved += 1
        except OSError:
            pass  # 쓰는 중이거나 잠긴 파일은 다음에
    return moved


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # Orca 실행 기록에서 한글이 깨지지 않게
    cmd = sys.argv[1] if len(sys.argv) > 1 else "quota"
    if cmd == "lock":
        LOCK.parent.mkdir(exist_ok=True); LOCK.touch(); return 0
    if cmd == "unlock":
        LOCK.unlink(missing_ok=True); return 0
    if cmd == "clean":
        print(f"세션 {clean_sessions()}개 보관"); return 0
    if cmd == "can-review":
        clean_sessions()  # 매시간 도는 김에 정리
        p = pending()
        print(f"검수 대기 {len(p)}장" + (" (그리는 중)" if locked() else ""))
        return 0 if p and not locked() else 1
    r = remaining()
    print(json.dumps(r, ensure_ascii=False) if r else "사용량 기록 없음")
    if cmd == "quota":
        return 0
    if cmd in ("can-draw", "quota-ok"):
        if cmd == "can-draw" and locked():
            print("이미 그리는 중"); return 1
        if r is None:
            return 0  # 기록이 없으면 한 번 돌려 본다(돌면 기록이 생긴다)
        ok = r.get("5h", 100) >= MIN_5H and r.get("week", 100) >= MIN_WEEK
        print("그림" if ok else f"멈춤: 5시간 {MIN_5H}% · 주간 {MIN_WEEK}% 하한")
        return 0 if ok else 1
    print(__doc__); return 2


def _check_clean() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        h, old = Path(d), time.time() - 7200
        def mk(rel, text, age=old):
            f = h / rel; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(text, encoding="utf-8")
            os.utime(f, (age, age)); return f
        auto = '{"cwd":"C:/Users/user/My Apps/Nature Book","text":"tools/REVIEW.md 대로 새 삽화를 검수"}'
        mk(".codex/sessions/2026/10/12/rollout-a.jsonl", auto)
        mk(".codex/sessions/2026/10/12/rollout-b.jsonl", auto, old + 10)   # 최신: 남김
        mk(".claude/projects/p/x.jsonl", auto)
        mk(".claude/projects/p/live.jsonl", auto, time.time())              # 진행 중: 남김
        mk(".claude/projects/p/mine.jsonl", '{"cwd":"Nature Book","text":"직접 한 대화"}')  # 사람 세션: 남김
        assert clean_sessions(h) == 2
        assert (h / ".codex/archived_sessions/rollout-a.jsonl").exists()
        assert (h / ".claude/archived-automation/p/x.jsonl").exists()


def _check() -> None:
    t = time.time()
    line = json.dumps({"payload": {"type": "token_count", "rate_limits": {
        "primary": {"used_percent": 75, "window_minutes": 300, "resets_at": t + 600},
        "secondary": {"used_percent": 90, "window_minutes": 10080, "resets_at": t - 1}}}})
    assert parse_limits(line) == {"5h": 25.0, "week": 100.0}
    assert parse_limits('{"payload":{}}') is None


if __name__ == "__main__":
    _check()
    _check_clean()
    sys.exit(main())
