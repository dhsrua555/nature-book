# /// script
# requires-python = ">=3.11"
# ///
"""그림 프롬프트에 넣을 종별 형태 정보(art.subject · build · views · avoid) 정리 도구.

이미지 모델은 일반 지시("정확하게 그려라")만으로는 종마다 다른 체형·부리 길이와 모양·깃 무늬를 맞추지 못한다.
그래서 종마다 크기와 체형, 부리·다리 비율, 철·나이·암수별 깃, 헷갈리기 쉬운 종과 다른 점을 영어로 따로 적어
tools/style.toml 의 프롬프트에 끼운다. 쓰는 규칙은 tools/ART_RULES.md.

    uv run tools/art_profiles.py batches --size 30      # 종을 cache/art/batch-NN.json 으로 나눔(그릴 차례 순)
    (각 묶음을 ART_RULES.md 대로 정리해 cache/art/out-NN.json 으로 씀)
    uv run tools/art_profiles.py check cache/art/out-01.json
    uv run tools/art_profiles.py merge                  # out-*.json → 종 파일의 art
    uv run tools/art_profiles.py notes                  # 정리하며 남긴 메모(책 자료와 어긋나는 점 등)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nibr_entries as ne  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "aves" / "species"
IMG = ROOT / "img" / "aves"
WORK = ROOT / "cache" / "art"
HANGUL = re.compile(r"[가-힣]")
CONF = ("high", "medium", "low")


def is_todo(v) -> bool:
    return v is None or v == "" or (isinstance(v, str) and "TODO" in v)


def queue_order() -> list[dict]:
    """illustrate.py 의 그릴 차례(흔한 종부터)와 같은 순서"""
    book = json.loads((ROOT / "data" / "aves" / "book.json").read_text(encoding="utf-8"))
    ids = [s["id"] for o in book["tree"] for f in o["children"] for s in f["children"]]
    pos = {sid: i for i, sid in enumerate(ids)}
    rows = [json.loads(f.read_text(encoding="utf-8")) for f in SPECIES.glob("*.json")]
    rows.sort(key=lambda sp: ((sp.get("occurrence") or {}).get("rarity", 9.5), pos.get(sp["id"], 10**6), sp["id"]))
    return rows


_TAXA: dict[str, dict] = {}


def nibr_text(sp: dict) -> str:
    """해설을 실은 종만 원문을 함께 준다(해설이 없는 종의 원문은 다른 종 설명인 경우가 있었다)"""
    if is_todo(sp.get("summary")):
        return ""
    if not _TAXA:
        _TAXA.update({ne.sid(t["sci"]): t for t in ne.taxa()})
    t = _TAXA.get(sp["id"])
    return ne.source_text(t)[0] if t else ""


def item(sp: dict) -> dict:
    art = sp.get("art") or {}
    pts = sp.get("points") or []
    return {
        "id": sp["id"], "ko": sp["ko"], "sci": sp["sci"], "en": sp.get("en"),
        "length": sp.get("length"), "status": sp.get("status"), "habitat": sp.get("habitat"),
        "summary": sp.get("summary"), "sexes": sp.get("sexes"), "young": sp.get("young"),
        "points": [{"ko": p.get("ko"), "en": p.get("en")} for p in pts],
        "similar": sp.get("similar") or [],
        "art_now": {k: art.get(k) for k in ("subject", "pose", "scene", "views") if k in art},
        "drawn": {"scene": (IMG / f"{sp['id']}.webp").exists(), "plate": (IMG / f"{sp['id']}.id.webp").exists(),
                  "callouts": any(p.get("at") for p in pts)},
        "nibr_text": nibr_text(sp),
    }


def cmd_batches(args) -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    for f in WORK.glob("batch-*.json"):
        f.unlink()
    rows = queue_order()
    n = 0
    for i in range(0, len(rows), args.size):
        n += 1
        (WORK / f"batch-{n:02d}.json").write_text(
            json.dumps([item(sp) for sp in rows[i:i + args.size]], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"종 {len(rows)}개 → 묶음 {n}개 (cache/art/batch-NN.json, 흔한 종부터)")
    return 0


def check_entries(entries: list, batch: list[dict], say) -> int:
    bad = 0
    def err(sid, m):
        nonlocal bad
        bad += 1
        say(f"  오류 {sid}: {m}")
    want = {b["id"]: b for b in batch}
    got = [e.get("id") for e in entries]
    for sid in set(want) - set(got):
        err(sid, "결과에 없다")
    for sid in set(got) - set(want):
        err(sid, "묶음에 없는 id")
    if len(got) != len(set(got)):
        err("-", "같은 id 가 두 번 나온다")
    for e in entries:
        sid, b = e.get("id"), want.get(e.get("id"))
        if not b:
            continue
        conf = e.get("confidence")
        if conf not in CONF:
            err(sid, f"confidence 는 {CONF} 중 하나")
            continue
        extra = set(e) - {"id", "confidence", "subject", "build", "views", "avoid", "pose", "scene", "notes"}
        if extra:
            err(sid, f"모르는 키 {sorted(extra)}")
        if conf == "low":
            continue
        for k, lo, hi in (("subject", 120, 1400), ("build", 120, 1000)):
            v = e.get(k)
            if not isinstance(v, str) or is_todo(v):
                err(sid, f"{k} 가 비었다")
            elif not lo <= len(v) <= hi:
                err(sid, f"{k} 길이 {len(v)}자 (권장 {lo}–{hi})")
        av = e.get("avoid")
        if not isinstance(av, list) or not 1 <= len(av) <= 6 or not all(isinstance(x, str) and 5 < len(x) <= 300 for x in av):
            err(sid, "avoid 는 1–6개의 짧은 문장 목록")
        views = e.get("views")
        if b["points"]:
            if not isinstance(views, list) or not 1 <= len(views) <= 4 or not all(isinstance(x, str) and 10 < len(x) <= 500 for x in views):
                err(sid, "동정 포인트가 있는 종은 views 1–4개(각 500자 안)")
            elif b["drawn"]["callouts"] and len(views) != len(b["art_now"].get("views") or []):
                err(sid, f"번호 위치를 찍은 도해가 있으니 views 수를 지금({len(b['art_now'].get('views') or [])}개)과 같게")
        elif views not in (None, []):
            err(sid, "동정 포인트가 없는 종은 views 를 쓰지 않는다([])")
        for k in ("pose", "scene"):
            now = b["art_now"].get(k)
            if is_todo(now) and is_todo(e.get(k)):
                err(sid, f"지금 art.{k} 가 비어 있어 {k} 를 새로 써야 한다")
            if e.get(k) is not None and (not isinstance(e[k], str) or len(e[k]) > 400):
                err(sid, f"{k} 는 400자 안의 한 줄")
        texts = [e.get("subject"), e.get("build"), e.get("pose"), e.get("scene"), *(e.get("views") or []), *(e.get("avoid") or [])]
        for t in texts:
            if isinstance(t, str) and HANGUL.search(t):
                err(sid, f"영어 칸에 한글: {t[:40]}…")
                break
            if isinstance(t, str) and "TODO" in t:
                err(sid, "high/medium 인데 TODO 가 있다")
                break
        binom = " ".join(b["sci"].split()[:2])
        if isinstance(e.get("subject"), str) and binom not in e["subject"]:
            err(sid, f"subject 에 학명 {binom} 이 없다")
    return bad


def load_batch(out: Path) -> list[dict]:
    m = re.search(r"out-(\d+)", out.name)
    if not m:
        raise SystemExit(f"{out.name}: out-NN.json 꼴이 아니다")
    return json.loads((WORK / f"batch-{m.group(1)}.json").read_text(encoding="utf-8"))


def cmd_check(args) -> int:
    out = Path(args.file)
    entries = json.loads(out.read_text(encoding="utf-8"))
    bad = check_entries(entries, load_batch(out), print)
    low = [e["id"] for e in entries if e.get("confidence") == "low"]
    print(f"{out.name}: {len(entries)}종, 오류 {bad}" + (f", 확신 낮음 {len(low)}: {', '.join(low)}" if low else ""))
    return 1 if bad else 0


def cmd_merge(args) -> int:
    outs = sorted(WORK.glob("out-*.json"))
    total = bad_files = 0
    for out in outs:
        entries = json.loads(out.read_text(encoding="utf-8"))
        if check_entries(entries, load_batch(out), lambda m: None):
            print(f"건너뜀 {out.name}: check 를 통과하지 못했다")
            bad_files += 1
            continue
        for e in entries:
            f = SPECIES / f"{e['id']}.json"
            sp = json.loads(f.read_text(encoding="utf-8"))
            art = sp.setdefault("art", {})
            if e["confidence"] == "low":
                art["build"] = "TODO"
                art["confidence"] = "low"
            else:
                art["subject"] = e["subject"].strip()
                for k in ("pose", "scene"):
                    if isinstance(e.get(k), str) and e[k].strip():
                        art[k] = e[k].strip()
                if e.get("views"):
                    art["views"] = [v.strip() for v in e["views"]]
                art["build"] = e["build"].strip()
                art["avoid"] = [a.strip() for a in e["avoid"]]
                art["confidence"] = e["confidence"]
            art["basis"] = "형태: 조류 도감 일반 지식(현장 식별 특징)과 국립생물자원관 종 설명 · tools/ART_RULES.md"
            f.write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            total += 1
    print(f"art 정리 {total}종 반영 (out 파일 {len(outs)}개, 건너뛴 파일 {bad_files}개)")
    return 1 if bad_files else 0


def cmd_notes(args) -> int:
    for out in sorted(WORK.glob("out-*.json")):
        for e in json.loads(out.read_text(encoding="utf-8")):
            if e.get("notes") or e.get("confidence") != "high":
                print(f"{e['id']}\t{e.get('confidence')}\t{e.get('notes') or ''}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("batches")
    b.add_argument("--size", type=int, default=30)
    c = sub.add_parser("check")
    c.add_argument("file")
    sub.add_parser("merge")
    sub.add_parser("notes")
    args = ap.parse_args()
    return {"batches": cmd_batches, "check": cmd_check, "merge": cmd_merge, "notes": cmd_notes}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
