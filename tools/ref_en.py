# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl"]
# ///
"""국가생물종목록 학명에 IOC World Bird List 영문명과 분류(목·과·차례)를 짝지어 tools/ref/ioc-en.tsv 로 쓴다.
책의 목·과와 차례는 이 표의 ioc_order·ioc_family·ioc_seq 를 따른다(tools/build.py, 목·과 국명은 tools/ref/taxa-ko.tsv).

    curl -L -o cache/ioc-15.2.xlsx https://worldbirdnames.org/master_ioc_list_v15.2.xlsx
    uv run tools/ref_en.py

짝짓기: (1) 속명+종소명이 같으면 그대로. (2) 속이 바뀐 종은 종소명과 명명자·연도가 같고
IOC에 그런 종이 하나뿐일 때만 짝짓는다. 그 밖에는 비워 둔다(화면엔 '조사 중').
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "tools" / "ref" / "nibr-aves-2025.tsv"
OUT = ROOT / "tools" / "ref" / "ioc-en.tsv"
XLSX = ROOT / "cache" / "ioc-15.2.xlsx"


# 자동으로 못 찾은 종: IOC에서 직접 확인한 짝(속 이동·어미 변화·IOC에서는 아종)
MANUAL = {
    "Accipiter gularis": "Tachyspiza gularis",
    "Locustella fasciolata": "Helopsaltes fasciolatus",
    "Dicrurus annectans": "Dicrurus annectens",
    "Sylvia nisoria": "Curruca nisoria",
    "Larus heuglini": "Larus fuscus heuglini",
    "Acanthis hornemanni": "Acanthis flammea hornemanni",
    "Phylloscopus amandii": "Phylloscopus armandii",  # 목록의 철자 오류
}


def norm_auth(a: str | None) -> str:
    a = (a or "").replace("(", "").replace(")", "").replace(" ", "").lower()
    return re.sub(r"[^a-z0-9,&.]", "", a)


def main() -> int:
    sys.stdout.reconfigure(errors="replace")
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb.worksheets[0]
    genus = None
    family = None
    order = None
    seq = 0
    by_bi: dict[str, tuple[str, str]] = {}
    taxa: dict[str, tuple[str, str, int]] = {}  # 종(속명+종소명) → (목, 과, IOC 목록 안의 차례)
    by_ep: dict[str, list[tuple[str, str, str]]] = {}
    for row in ws.iter_rows(min_row=5, values_only=True):
        if row[2]:
            order = row[2].strip().capitalize()
        if row[3]:
            family = row[3].strip()
        if row[5]:
            genus = row[5].strip()
        if row[6] and row[10]:
            ep = row[6].strip()
            bi = f"{genus} {ep}"
            seq += 1
            by_bi[bi] = (row[10].strip(), row[9] or "")
            taxa[bi] = (order, family, seq)
            by_ep.setdefault(ep, []).append((bi, row[10].strip(), norm_auth(row[9]), family))

    lines = [l for l in REF.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    rows = list(csv.DictReader(lines, delimiter="\t"))
    out = []
    miss = []
    for r in rows:
        parts = r["sci"].split()
        bi = " ".join(parts[:2])
        en, ioc, how = "", "", ""
        if bi in by_bi:
            en, ioc, how = by_bi[bi][0], bi, "same"
        else:
            cands = [c for c in by_ep.get(parts[1], []) if c[2] == norm_auth(r["author"]) and c[2]]
            if len(cands) == 1:
                ioc, en, how = cands[0][0], cands[0][1], "epithet+author"
        if not en:
            # 종소명 어미(성 일치)가 바뀐 경우: 어간과 명명 연도가 같고 하나뿐일 때
            stem = re.sub(r"(us|a|um|is|e|i)$", "", parts[1])
            year = re.findall(r"\d{4}", r["author"])
            cands = [c for ep, cs in by_ep.items() if re.sub(r"(us|a|um|is|e|i)$", "", ep) == stem
                     for c in cs if year and year[0] in c[2] and c[3] == r["family"]]
            if len(cands) == 1:
                ioc, en, how = cands[0][0], cands[0][1], "stem+year"
        if not en and bi in MANUAL:
            ioc = MANUAL[bi]
            ib = " ".join(ioc.split()[:2])
            en = by_bi[ib][0] + (f" ({ioc.split()[2]})" if len(ioc.split()) > 2 else "")
            how = "manual"
        if en and len(parts) > 2:
            en = f"{en} ({parts[2]})"
        if not en:
            miss.append(f"{r['ko']} {r['sci']}")
        o, f, q = taxa.get(" ".join(ioc.split()[:2]), ("", "", ""))
        out.append({"sci": r["sci"], "ko": r["ko"], "en": en, "ioc_sci": ioc, "match": how,
                    "ioc_order": o, "ioc_family": f, "ioc_seq": q})
    with OUT.open("w", encoding="utf-8", newline="") as f:
        f.write("# IOC World Bird List v15.2 (doi 10.14344/IOC.ML.15.2) 영문명과 목·과·차례. tools/ref_en.py 가 만듦\n")
        w = csv.DictWriter(f, fieldnames=["sci", "ko", "en", "ioc_sci", "match", "ioc_order", "ioc_family", "ioc_seq"],
                           delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"{len(rows)}행: 같은 학명 {sum(o['match']=='same' for o in out)}, 속 바뀜 {sum(o['match']=='epithet+author' for o in out)}, 어미·연도 {sum(o["match"]=="stem+year" for o in out)}, 못 찾음 {len(miss)}")
    for m in miss:
        print("  ", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
