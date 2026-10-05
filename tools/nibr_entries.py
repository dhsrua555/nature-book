# /// script
# requires-python = ">=3.11"
# ///
"""국가생물종목록의 모든 종을 책에 싣기 위한 도구.

손으로 조사한 종(data/<권>/species/*.json 중 origin 이 없는 것)은 건드리지 않고,
나머지 종은 국립생물자원관 종 설명(cache/nibr, tools/fetch_nibr.py 로 받음)만을 근거로 정리한다.

    uv run tools/nibr_entries.py batches --size 30   # 정리할 종을 cache/work/batch-NN.json 으로 나눔
    (각 묶음을 cache/work/RULES.md 규칙대로 정리해 cache/work/out-NN.json 으로 씀)
    uv run tools/nibr_entries.py merge               # out-*.json + 목록·보호 표시 → 종 파일

merge 는 숫자(몸길이·날개 편 길이)와 국내 상태 낱말이 원문에 실제로 있는지 대조하고,
없으면 그 값을 TODO 로 되돌린다. 원문이 없는 종은 분류·국명·학명·보호 표시만 담은 종 파일이 된다.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "tools" / "ref" / "nibr-aves-2025.tsv"
EN = ROOT / "tools" / "ref" / "ioc-en.tsv"
CACHE = ROOT / "cache" / "nibr"
WORK = ROOT / "cache" / "work"
SPECIES = ROOT / "data" / "aves" / "species"
STATUS_WORDS = ["텃새", "여름철새", "겨울철새", "나그네새", "길잃은새", "미조", "여름새", "겨울새", "통과철새"]
# 원문이 옛 낱말을 쓸 때: 상태 칸에는 오늘날 낱말을 쓰고 원문의 같은 뜻 낱말로 대조한다
SYNONYM = {"겨울철새": ["겨울새", "월동"], "여름철새": ["여름새"], "나그네새": ["통과철새", "통과새"]}
GRADE = {"1": "멸종위기 야생생물 Ⅰ급", "2": "멸종위기 야생생물 Ⅱ급"}


def tsv(path: Path) -> list[dict]:
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def sid(sci: str) -> str:
    return "-".join(sci.lower().split())


def taxa() -> list[dict]:
    """국명 하나에 한 항목. 같은 국명이 종과 아종 두 줄에 있으면 종(이명법) 줄을 쓴다."""
    rows = tsv(REF)
    by_ko: dict[str, list[dict]] = {}
    for r in rows:
        by_ko.setdefault(r["ko"], []).append(r)
    out = []
    for ko, rs in by_ko.items():
        rs.sort(key=lambda r: len(r["sci"].split()))
        main = dict(rs[0])
        main["alt_ktsn"] = [r["ktsn"] for r in rs[1:]]
        out.append(main)
    out.sort(key=lambda r: int(r["no"]))
    return out


def nibr(ktsn: str) -> dict:
    f = CACHE / f"{ktsn}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def source_text(t: dict) -> tuple[str, str]:
    """(원문, 원문을 준 ktsn)"""
    for k in [t["ktsn"], *t["alt_ktsn"]]:
        cn = (nibr(k).get("cn") or "").strip()
        if cn:
            return re.sub(r"<[^>]+>", "", cn), k
    return "", ""


def hand_made() -> set[str]:
    ids = set()
    for f in SPECIES.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if not d.get("origin"):
            ids.add(d["sci"])
    return ids


def cmd_batches(args) -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    skip = hand_made()
    en_by = {r["sci"]: r["en"] for r in tsv(EN)}
    items = []
    for t in taxa():
        if t["sci"] in skip:
            continue
        cn, _ = source_text(t)
        if not cn:
            continue
        items.append({"id": sid(t["sci"]), "ko": t["ko"], "sci": t["sci"], "en": en_by.get(t["sci"], ""),
                      "order": t["order_ko"], "family": t["family_ko"], "text": cn})
    for f in WORK.glob("batch-*.json"):
        f.unlink()
    n = 0
    for i in range(0, len(items), args.size):
        n += 1
        (WORK / f"batch-{n:02d}.json").write_text(json.dumps(items[i:i + args.size], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"원문 있는 종 {len(items)}개 → 묶음 {n}개 (손으로 조사한 종 {len(skip)}개는 뺌)")
    return 0


def nums(s: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?", s or "")


def is_todo(v) -> bool:
    return v is None or (isinstance(v, str) and "TODO" in v)


def check_entry(e: dict, cn: str, warn) -> dict:
    """원문과 어긋나는 값은 TODO 로 되돌린다"""
    plain = cn.replace(" ", "")
    for key in ("length", "wingspan"):
        v = e.get(key)
        if is_todo(v) or not v:
            continue
        missing = [x for x in nums(v) if x not in nums(cn)]
        if missing:
            warn(f"{key} '{v}' 의 수 {missing} 가 원문에 없어 TODO 로 돌림")
            e[key] = "TODO"
    st = e.get("status")
    if not is_todo(st):
        words = [w for w in STATUS_WORDS if w in st]
        bad = [w for w in words if not any(x in plain for x in [w, *SYNONYM.get(w, [])])]
        if not words or bad:
            warn(f"status '{st}' 가 원문 낱말과 맞지 않아 TODO 로 돌림")
            e["status"] = "TODO"
    months = e.get("months") or {}
    for key in ("seen", "breed"):
        v = months.get(key)
        if isinstance(v, list) and v and len(v) < 12:
            ends = {v[0], v[-1]}
            if not all(f"{m}월" in plain or re.search(rf"(?<!\d){m}\s*[-~–]", cn) for m in ends):
                warn(f"months.{key} {v} 의 처음·끝 달이 원문에 없다(확인 필요)")
    return e


def protect_of(t: dict) -> list[str]:
    out = []
    for k in [t["ktsn"], *t["alt_ktsn"]]:
        rec = nibr(k)
        for f in (rec.get("flags") or {}, rec.get("cn_flags") or {}):
            if f.get("ntmYn") == "Y" and "천연기념물" not in out:
                out.append("천연기념물")
            g = GRADE.get(str(f.get("egspcsGrdNo") or ""))
            if g and g not in out:
                out.append(g)
    return sorted(out, key=lambda x: (x != "천연기념물", x))


def skeleton(t: dict, en: dict, cn_ktsn: str) -> dict:
    sci = t["sci"]
    author = t["author"].strip("()") if t["author"].count("(") == 1 and t["author"].startswith("(") else t["author"]
    src = [{"title": f"국립생물자원관 국가생물종목록(2025) – {t['ko']}", "url": f"https://species.nibr.go.kr/species-detail/{t['ktsn']}",
            "used": "국명·학명·분류·보호 표시"}]
    if cn_ktsn:
        src.append({"title": f"국립생물자원관 종 설명 – {t['ko']}",
                    "url": f"https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/get-cn-data/{cn_ktsn}",
                    "used": "몸길이, 국내 상태, 생김새, 사는 곳, 먹이, 번식, 분포"})
    if en.get("en"):
        ioc = en.get("ioc_sci", "")
        note = "" if ioc == " ".join(sci.split()[:2]) else f" (IOC 학명 {ioc})"
        src.append({"title": "IOC World Bird List v15.2", "url": "https://www.worldbirdnames.org/new/ioc-lists/master-list-2/",
                    "used": f"영문명{note}"})
    return {
        "id": sid(sci), "ko": t["ko"], "sci": sci, "author": author, "en": en.get("en") or "TODO",
        "ktsn": int(t["ktsn"]), "origin": "nibr",
        "length": "TODO", "status": "TODO", "habitat": "TODO", "protect": protect_of(t),
        "months": {"seen": "TODO", "breed": "TODO"},
        "summary": "TODO", "points": [], "sexes": {"alike": None, "text": "TODO"}, "young": "TODO", "similar": [],
        "art": {"subject": "TODO", "pose": "TODO", "scene": "TODO", "views": []},
        "sources": src, "todo": [] if cn_ktsn else ["국립생물자원관 종 설명이 없어 분류와 이름만 실었다"],
    }


FIELDS = ["length", "wingspan", "status", "habitat", "months", "summary", "points", "sexes", "young", "similar", "art", "todo"]


def cmd_merge(args) -> int:
    # 종 파일은 그 뒤로 손보거나(국내 상태 tools/occurrence.py, 해설 고침) 하므로 함부로 덮어쓰지 않는다
    done = [f for f in SPECIES.glob("*.json") if json.loads(f.read_text(encoding="utf-8")).get("origin")]
    if done and not args.force:
        print(f"origin 이 붙은 종 파일 {len(done)}개가 이미 있다. 다시 만들려면 --force (그 뒤 tools/occurrence.py --write 를 다시 돌린다)")
        return 1
    en_by = {r["sci"]: r for r in tsv(EN)}
    outs: dict[str, dict] = {}
    for f in sorted(WORK.glob("out-*.json")):
        try:
            for e in json.loads(f.read_text(encoding="utf-8")):
                outs[e["id"]] = e
        except json.JSONDecodeError as err:
            print(f"  {f.name}: JSON 오류 {err}")
    skip = hand_made()
    made = filled = 0
    warnings = []
    for t in taxa():
        if t["sci"] in skip:
            continue
        cn, cn_k = source_text(t)
        d = skeleton(t, en_by.get(t["sci"], {}), cn_k)
        e = outs.get(d["id"])
        if e and cn:
            w = lambda m, i=d["id"]: warnings.append(f"{i} {t['ko']}: {m}")
            e = check_entry(dict(e), cn, w)
            for k in FIELDS:
                if k in e and e[k] is not None:
                    if k == "todo":
                        d["todo"] = [*d["todo"], *e[k]]
                    else:
                        d[k] = e[k]
            filled += 1
        elif cn:
            d["todo"].append("종 설명 원문은 있으나 아직 정리하지 않았다")
        made += 1
        (SPECIES / f"{d['id']}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"종 파일 {made}개 (원문으로 정리 {filled}개, 손으로 조사한 종 {len(skip)}개는 그대로)")
    for m in warnings:
        print("  주의:", m)
    return 0


def cmd_check(args) -> int:
    """정리한 묶음 하나(out-NN.json)를 같은 번호의 batch-NN.json 과 견주어 검사한다"""
    out = Path(args.file)
    batch = out.with_name(out.name.replace("out-", "batch-"))
    try:
        entries = json.loads(out.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        print(f"JSON 오류: {err}")
        return 1
    src = {b["id"]: b for b in json.loads(batch.read_text(encoding="utf-8"))}
    problems = []
    seen = set()
    for e in entries:
        i = e.get("id")
        if i not in src:
            problems.append(f"{i}: 묶음에 없는 id")
            continue
        seen.add(i)
        p = lambda m, i=i: problems.append(f"{i} {src[i]['ko']}: {m}")
        for k in ("length", "status", "habitat", "months", "summary", "points", "sexes", "young", "similar", "art"):
            if k not in e:
                p(f"{k} 없음")
        m = e.get("months") or {}
        for k in ("seen", "breed"):
            v = m.get(k)
            if not (v == "TODO" or (isinstance(v, list) and all(isinstance(x, int) and 1 <= x <= 12 for x in v))):
                p(f"months.{k} 는 1–12 정수 목록, [] 또는 \"TODO\"")
        for j, pt in enumerate(e.get("points") or []):
            if not (isinstance(pt, dict) and pt.get("ko") and pt.get("en")):
                p(f"points[{j}] 에 ko·en 필요")
        sx = e.get("sexes") or {}
        if sx.get("alike") is False and not (sx.get("male") and sx.get("female")):
            p("sexes.alike=false 이면 male·female 필요")
        art = e.get("art") or {}
        for k in ("subject", "pose", "scene", "views"):
            if k not in art:
                p(f"art.{k} 없음")
        if e.get("points") and not art.get("views"):
            p("points 가 있으면 art.views 도 필요")
        check_entry(dict(e), src[i]["text"], p)
    for i in src:
        if i not in seen:
            problems.append(f"{i} {src[i]['ko']}: 빠짐")
    for m in problems:
        print(" -", m)
    print(f"{out.name}: {len(entries)}종, 문제 {len(problems)}개")
    return 1 if problems else 0


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("batches")
    b.add_argument("--size", type=int, default=30)
    mg = sub.add_parser("merge")
    mg.add_argument("--force", action="store_true", help="이미 만든 종 파일도 다시 만든다")
    c = sub.add_parser("check")
    c.add_argument("file")
    args = ap.parse_args()
    return {"batches": cmd_batches, "merge": cmd_merge, "check": cmd_check}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
