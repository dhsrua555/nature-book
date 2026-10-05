# /// script
# requires-python = ">=3.11"
# ///
"""도감 데이터 빌드·검증.

data/<권>/volume.json 과 data/<권>/species/*.json 을 읽어
  1) 국가생물종목록(tools/ref/*.tsv)과 국명·학명·목·과를 대조하고
  2) 빠진 항목·TODO·삽화 유무를 점검한 뒤
  3) 화면이 읽는 data/<권>/book.json 을 만든다.

    uv run tools/build.py            # 검사 + book.json 생성
    uv run tools/build.py --todo     # TODO 목록까지 자세히

종의 목·과는 종 파일에 적지 않는다. 학명으로 국가생물종목록에서 찾아 자동으로 묶는다.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["id", "ko", "sci", "en", "length", "status", "habitat", "months", "summary",
            "points", "sexes", "art", "sources"]
ART_REQUIRED = ["subject", "pose", "scene", "views"]


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def load_ref(path: Path) -> list[dict]:
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def binomial(sci: str) -> str:
    return " ".join(sci.split()[:2])


def todo_paths(value, path="") -> list[str]:
    """값 안의 'TODO' 위치를 모두 찾는다."""
    found = []
    if isinstance(value, str):
        if "TODO" in value:
            found.append(path or "(값)")
    elif isinstance(value, dict):
        for k, v in value.items():
            if k in ("todo", "sources"):
                continue
            found += todo_paths(v, f"{path}.{k}" if path else k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found += todo_paths(v, f"{path}[{i}]")
    return found


_tracked: set[str] | None = None


def has_img(path: Path, args) -> bool:
    """그림이 있는지. --tracked 이면 git 에 올라간 그림만 친다(검수 전 그림이 공개 판에 걸리지 않도록)."""
    global _tracked
    if not path.exists():
        return False
    if not getattr(args, "tracked", False):
        return True
    if _tracked is None:
        import subprocess
        res = subprocess.run(["git", "ls-files", "img"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        _tracked = set(res.stdout.split())
    return path.relative_to(ROOT).as_posix() in _tracked


def has_todo_str(v) -> bool:
    return v is None or v == "" or (isinstance(v, str) and "TODO" in v)


def check_months(sp: dict, rep: Report) -> None:
    months = sp.get("months")
    if not isinstance(months, dict):
        rep.err(f"{sp['id']}: months 는 객체여야 한다")
        return
    for key in ("seen", "breed"):
        v = months.get(key)
        if v == "TODO" or v is None:
            continue
        if not (isinstance(v, list) and all(isinstance(m, int) and 1 <= m <= 12 for m in v)):
            rep.err(f"{sp['id']}: months.{key} 는 1–12 정수 목록이거나 \"TODO\"")


def check_points(sp: dict, rep: Report) -> None:
    pts = sp.get("points")
    if not isinstance(pts, list) or (not pts and not sp.get("origin")):
        rep.err(f"{sp['id']}: points(동정 포인트)가 비어 있다")
        return
    for i, p in enumerate(pts):
        if not isinstance(p, dict) or not p.get("ko") or not p.get("en"):
            rep.err(f"{sp['id']}: points[{i}] 에 ko·en 이 모두 있어야 한다")
            continue
        for key in ("at", "label"):
            xy = p.get(key)
            if xy is None:
                continue
            if not (isinstance(xy, list) and len(xy) == 2 and all(isinstance(t, (int, float)) and 0 <= t <= 1 for t in xy)):
                rep.err(f"{sp['id']}: points[{i}].{key} 는 [x, y] (0–1)")


def build_volume(vol_entry: dict, args, rep: Report) -> dict:
    vid = vol_entry["id"]
    vdir = ROOT / "data" / vid
    meta = json.loads((vdir / "volume.json").read_text(encoding="utf-8"))
    ref_rows = load_ref(ROOT / meta["basis"]["ref"])
    by_sci = {}
    for r in ref_rows:
        by_sci.setdefault(r["sci"], r)

    # 차례: 목·과·속은 목록에 처음 나오는 자리를 따른다. 목록 끝에 덧붙은 종(이름이 바뀐 종 등)은
    # 속이 처음 나오는 자리로 당겨 오고, 그래도 어긋나는 종은 volume.json 의 seq 로 자리를 정한다.
    first: dict[str, int] = {}
    for r in ref_rows:
        for key in ("order", "family", "genus"):
            first.setdefault(f"{key}:{r[key]}", int(r["no"]))
    seq_override = meta.get("seq", {})

    def sort_key(row: dict) -> tuple:
        pos = seq_override.get(binomial(row["sci"]))
        g = pos if pos is not None else first[f"genus:{row['genus']}"]
        return (first[f"order:{row['order']}"], first[f"family:{row['family']}"], g,
                pos if pos is not None else int(row["no"]))

    # 국가생물종목록의 목·과별 종 수(아종 행은 속명+종소명으로 묶어 한 번만 센다)
    seen_bi: dict[str, tuple[str, str]] = {}
    for r in ref_rows:
        seen_bi.setdefault(binomial(r["sci"]), (r["order"], r["family"]))
    ref_count = {"total": len(seen_bi), "order": {}, "family": {}}
    for order, family in seen_bi.values():
        ref_count["order"][order] = ref_count["order"].get(order, 0) + 1
        ref_count["family"][family] = ref_count["family"].get(family, 0) + 1

    img_dir = ROOT / "img" / vid
    species = []
    todo_total = 0
    for f in sorted((vdir / "species").glob("*.json")):
        try:
            sp = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            rep.err(f"{f.name}: JSON 오류 {e}")
            continue
        sid = sp.get("id")
        if sid != f.stem:
            rep.err(f"{f.name}: id({sid})가 파일 이름과 다르다")
            continue
        missing = [k for k in REQUIRED if k not in sp]
        if missing:
            rep.err(f"{sid}: 빠진 항목 {', '.join(missing)}")
            continue
        art = sp.get("art") or {}
        art_missing = [k for k in ART_REQUIRED if not art.get(k)]
        if art_missing and not sp.get("origin"):
            rep.err(f"{sid}: art 에 빠진 항목 {', '.join(art_missing)}")

        row = by_sci.get(sp["sci"])
        if not row:
            rep.err(f"{sid}: 학명 {sp['sci']} 이 국가생물종목록에 없다")
            continue
        if row["ko"] != sp["ko"]:
            rep.err(f"{sid}: 국명 '{sp['ko']}' ≠ 국가생물종목록 '{row['ko']}' ({sp['sci']})")
        if sp.get("ktsn") and str(sp["ktsn"]) != row["ktsn"]:
            rep.warn(f"{sid}: ktsn {sp['ktsn']} ≠ 목록 {row['ktsn']}")

        check_months(sp, rep)
        check_points(sp, rep)
        todos = todo_paths(sp) + [f"todo: {t}" for t in sp.get("todo", [])]
        todo_total += len(todos)
        if args.todo and todos:
            for t in todos:
                rep.warn(f"{sid}: TODO {t}")

        species.append({
            "sp": sp, "row": row, "todos": len(todos),
            "img": {
                "scene": has_img(img_dir / f"{sid}.webp", args),
                "plate": has_img(img_dir / f"{sid}.id.webp", args),
            },
        })

    ids = {s["sp"]["id"] for s in species}
    ko_to_id = {s["sp"]["ko"]: s["sp"]["id"] for s in species}
    for s in species:
        for sim in s["sp"].get("similar", []):
            if sim.get("id") and sim["id"] not in ids:
                rep.warn(f"{s['sp']['id']}: 비슷한 종 id {sim['id']} 가 책에 없다")

    # 목 → 과 → 종 트리
    species.sort(key=lambda s: sort_key(s["row"]))
    orders: dict[str, dict] = {}
    for s in species:
        r = s["row"]
        o = orders.setdefault(r["order"], {"rank": "order", "sci": r["order"], "ko": r["order_ko"], "families": {}})
        fam = o["families"].setdefault(r["family"], {"rank": "family", "sci": r["family"], "ko": r["family_ko"], "species": []})
        sp = s["sp"]
        fam["species"].append({
            "id": sp["id"], "ko": sp["ko"], "sci": sp["sci"], "en": sp["en"],
            "status": sp.get("status"), "length": sp.get("length"),
            "no": int(r["no"]), "img": s["img"], "focus": (sp.get("art") or {}).get("focus", [0.5, 0.5]),
            "todo": s["todos"],
            # 첫 화면 '오늘의 새'가 고를 때 쓰는 값: 해설이 있는지, 볼 수 있는 달
            "text": not has_todo_str(sp.get("summary")),
            "seen": (sp.get("months") or {}).get("seen") if isinstance((sp.get("months") or {}).get("seen"), list) else None,
            **({"origin": sp["origin"]} if sp.get("origin") else {}),
        })

    by_id = {s["sp"]["id"]: s for s in species}

    def default_rep(members: list[str]) -> str:
        # 그림이 있는 종 → 손으로 조사한 종 → 해설이 있는 종 → 첫 종
        for test in (lambda s: s["img"]["scene"], lambda s: not s["sp"].get("origin"),
                     lambda s: not has_todo_str(s["sp"].get("summary"))):
            for m in members:
                if test(by_id[m]):
                    return m
        return members[0]

    def meta_for(kind: str, sci: str, members: list[str]) -> dict:
        m = meta.get(kind, {}).get(sci, {})
        rep_id = m.get("rep") or default_rep(members)
        if rep_id not in members:
            rep.err(f"{kind} {sci}: 대표종 {rep_id} 가 이 분류에 없다 (있는 종: {', '.join(members)})")
            rep_id = default_rep(members)
        return {"rep": rep_id, **({"desc": m["desc"]} if m.get("desc") else {})}

    tree = []
    for o in orders.values():
        fams = []
        o_members = []
        for fam in o["families"].values():
            members = [x["id"] for x in fam["species"]]
            o_members += members
            fams.append({
                "rank": "family", "id": fam["sci"].lower(), "sci": fam["sci"], "ko": fam["ko"],
                **meta_for("families", fam["sci"], members),
                "nibr": ref_count["family"].get(fam["sci"], 0),
                "children": fam["species"],
            })
        tree.append({
            "rank": "order", "id": o["sci"].lower(), "sci": o["sci"], "ko": o["ko"],
            **meta_for("orders", o["sci"], o_members),
            "nibr": ref_count["order"].get(o["sci"], 0),
            "children": fams,
        })

    for key in ("orders", "families"):
        used = {n["sci"] for n in tree} if key == "orders" else {f["sci"] for n in tree for f in n["children"]}
        for sci in meta.get(key, {}):
            if sci not in used:
                rep.warn(f"volume.json {key}.{sci}: 이 분류에 든 종이 없어 쓰이지 않는다")

    vol_rep = meta.get("rep") or (species[0]["sp"]["id"] if species else None)
    if vol_rep and vol_rep not in ids:
        rep.err(f"volume.json rep {vol_rep} 가 책에 없다")

    book = {k: meta[k] for k in ("id", "title", "kicker", "en", "sci", "edition", "basis", "intro", "fields", "labels") if k in meta}
    book.update({
        "rep": vol_rep,
        "built": date.today().isoformat(),
        "counts": {"species": len(species), "orders": len(tree),
                   "families": sum(len(o["children"]) for o in tree), "nibr": ref_count["total"],
                   "text": sum(not has_todo_str(s["sp"].get("summary")) for s in species),
                   "hand": sum(not s["sp"].get("origin") for s in species),
                   "scenes": sum(s["img"]["scene"] for s in species),
                   "plates": sum(s["img"]["plate"] for s in species)},
        "similar": {s["sp"]["id"]: [ko_to_id.get(x.get("ko")) for x in s["sp"].get("similar", [])] for s in species},
        "tree": tree,
    })
    out = vdir / "book.json"
    out.write_text(json.dumps(book, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    n = len(species)
    scenes = sum(s["img"]["scene"] for s in species)
    plates = sum(s["img"]["plate"] for s in species)
    print(f"[{vid}] {meta['title']}: {len(tree)}목 {book['counts']['families']}과 {n}종 "
          f"(국가생물종목록 {ref_count['total']}종) · 도판 {scenes}/{n} · 동정 도해 {plates}/{n} · TODO {todo_total}개")
    print(f"  → {out.relative_to(ROOT)}")
    return book


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="도감 데이터 빌드·검증")
    ap.add_argument("--todo", action="store_true", help="TODO 위치를 모두 출력")
    ap.add_argument("--tracked", action="store_true", help="git 에 커밋된 그림만 있는 것으로 친다(커밋 전 확인용)")
    args = ap.parse_args()
    lib = json.loads((ROOT / "data" / "library.json").read_text(encoding="utf-8"))
    rep = Report()
    for v in lib["volumes"]:
        build_volume(v, args, rep)
    for w in rep.warnings:
        print("  주의:", w)
    for e in rep.errors:
        print("  오류:", e, file=sys.stderr)
    if rep.errors:
        print(f"오류 {len(rep.errors)}개 — 고친 뒤 다시 돌리세요.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
