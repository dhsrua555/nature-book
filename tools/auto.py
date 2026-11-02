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
    uv run tools/auto.py resume      # 쉬는 중인 두 자동화를 원래 일정으로 (손으로 되돌릴 때)

Codex 사용량은 Codex가 남기는 세션 기록(~/.codex/sessions/**/rollout-*.jsonl)의
마지막 rate_limits 값을 읽는다. 창이 이미 리셋됐으면(2분 안에 리셋되면) 사용량 0으로 본다.

주간 잔여가 하한 아래로 내려가면 쉰다: can-draw 가 그리기 자동화의 일정을 주간 리셋 시각에
일주일에 한 번 도는 것으로 바꾸고 art/.paused 에 리셋 시각을 남긴다. can-review 는 검수할 그림이
남지 않으면 자기 일정을 리셋 15분 뒤 주 1회로 바꾼다. 리셋 뒤 처음 돌 때 둘 다 원래 일정으로 되돌린다.
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
LOCK_STALE = 45 * 60  # ponytail: 45분 넘은 표시는 죽은 실행으로 본다(한 번에 8장 약 12분, 20분마다 돈다)
MIN_5H, MIN_WEEK = 30, 20  # 남은 % 하한
RESET_SOON = 120  # 이만큼(초) 안에 리셋될 창은 리셋된 것으로: 리셋 시각 분에 맞춰 돈 실행이 다시 쉬지 않게
PAUSED = ROOT / "art" / ".paused"  # 주간 하한 아래로 쉬는 중: 주간 리셋 시각(유닉스 초)
# Orca 자동화 id(그리기, 검수·푸시): 같은 노트북 듀얼 부팅이라 윈도우·리눅스 Orca가 따로 가진다
DRAW_ID, REVIEW_ID = {
    "win32": ("ce741a68-9fed-40d3-8e71-38a1c9aba344", "fafbc006-86ec-4e2b-8d62-bd178470e85b"),
    "linux": ("becb7293-9590-4e5e-b382-7d88e6aa93d1", "dfe74e32-fea3-4e1b-bac1-a04b8a8a27a3"),
}[sys.platform]
DRAW_EVERY, REVIEW_EVERY = "15,35,55 * * * *", "10 * * * *"


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
        if reset is not None and float(reset) <= now + RESET_SOON:
            used = 0.0  # 이미 리셋된 창
        key = "week" if (w.get("window_minutes") or 0) > 300 else "5h"
        out[key] = 100.0 - used
        if key == "week" and reset is not None and used:
            out["week_reset"] = int(reset)
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


def weekly_cron(ts: float) -> str:
    """그 시각(분 단위)에 매주 한 번 도는 cron. cron 요일은 일요일이 0."""
    t = time.localtime(ts)
    return f"{t.tm_min} {t.tm_hour} * * {(t.tm_wday + 1) % 7}"


def reschedule(auto_id: str, cron: str) -> bool:
    try:
        return subprocess.run(["orca", "automations", "edit", "--id", auto_id, "--trigger", cron],
                              capture_output=True, timeout=45).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False  # Orca가 없거나(업데이트 중) 멈춤: 다음 실행에서 다시


def paused_until() -> int | None:
    try:
        return int(PAUSED.read_text())
    except (OSError, ValueError):
        return None


def pause(reset: int) -> None:
    """그리기 자동화를 주간 리셋 시각에 주 1회만 돌게 한다."""
    if paused_until() != reset and reschedule(DRAW_ID, weekly_cron(reset)):
        PAUSED.parent.mkdir(exist_ok=True)
        PAUSED.write_text(str(reset))
    print(f"쉼: {time.strftime('%m-%d %H:%M', time.localtime(reset))} 주간 리셋 뒤 다시")


def resume() -> None:
    """두 자동화를 원래 일정으로 되돌린다(이미 되돌렸으면 아무것도 안 함)."""
    if PAUSED.exists() and reschedule(REVIEW_ID, REVIEW_EVERY) and reschedule(DRAW_ID, DRAW_EVERY):
        PAUSED.unlink(missing_ok=True)
        print("다시 시작: 원래 일정으로")


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
    if cmd == "resume":
        resume(); return 0
    if cmd == "can-review":
        clean_sessions()  # 매시간 도는 김에 정리
        p = pending()
        print(f"검수 대기 {len(p)}장" + (" (그리는 중)" if locked() else ""))
        if (reset := paused_until()) and not p and not locked():
            if (remaining() or {}).get("week", 100) < MIN_WEEK:
                reschedule(REVIEW_ID, weekly_cron(reset + 15 * 60)) and print("쉼: 주간 리셋 15분 뒤 다시")
            else:
                resume()
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
        week_ok = r.get("week", 100) >= MIN_WEEK
        if cmd == "can-draw":
            if not week_ok and "week_reset" in r:
                pause(r["week_reset"])
            elif week_ok:
                resume()
        ok = r.get("5h", 100) >= MIN_5H and week_ok
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
    soon = line.replace(str(t - 1), str(t + 60)).replace(str(t + 600), str(t + 7200))
    assert parse_limits(soon) == {"5h": 25.0, "week": 100.0}  # 1분 뒤 리셋: 리셋된 것으로
    later = line.replace(str(t - 1), str(t + 3600))
    assert parse_limits(later) == {"5h": 25.0, "week": 10.0, "week_reset": int(t + 3600)}
    assert parse_limits('{"payload":{}}') is None
    mon = time.mktime((2026, 10, 26, 1, 55, 40, 0, 0, -1))
    assert weekly_cron(mon) == "55 1 * * 1" and weekly_cron(mon + 15 * 60) == "10 2 * * 1"


if __name__ == "__main__":
    _check()
    _check_clean()
    sys.exit(main())
