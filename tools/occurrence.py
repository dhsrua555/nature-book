# /// script
# requires-python = ">=3.11"
# ///
"""종마다 새와 생명의 터(Birds Korea) 2022 목록의 국내 출현 상태를 찾아 붙인다.

    uv run tools/occurrence.py            # 짝짓기 결과만 보기
    uv run tools/occurrence.py --write    # 종 파일의 status·breeding·occurrence 를 고쳐 쓴다

짝짓기: 국명(2024 국문판) · 학명(국가생물종목록 학명과 IOC 학명) · 영문명 세 갈래로 찾고,
갈래끼리 어긋나면 MANUAL 에 손으로 정한 짝을 쓴다. 아종 항목은 그 아종 줄을 쓴다.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "aves" / "species"
REF = ROOT / "tools" / "ref"
SOURCE = {
    "title": "새와 생명의 터(Birds Korea) 조류목록 2022 – Moores & Ha",
    "url": "https://www.birdskoreablog.org/wp-content/uploads/2022/11/2022-Birds-Korea-Checklist-ENG_issn.pdf",
    "used": "국내 출현 계절·해마다 찾아오는 개체 수 범위·번식 여부",
}

# 갈래가 어긋나거나 이름이 바뀐 종: 우리 학명 → 2022 목록의 (학명, 아종)
MANUAL: dict[str, tuple[str, str]] = {
    "Anser fabalis": ("Anser serrirostris", ""),        # 국가생물종목록의 큰기러기는 큰부리큰기러기(따로 실음)를 뺀 큰기러기
    "Acanthis hornemanni": ("Acanthis hornemanni", ""),  # IOC 15는 홍방울새에 합쳤으나 2022 목록은 따로 둔다
    "Phylloscopus xanthodryas": ("Phylloscopus xanthodryas", ""),  # 학명을 따른다(새와 생명의 터 국명은 일본솔새)
    "Haematopus ostralegus": ("Haematopus osculans", ""),  # 국내에 오는 검은머리물떼새는 osculans
    "Lanius cristatus crisatus": ("Lanius cristatus", "cristatus"),  # 국가생물종목록 학명 오기(crisatus)
    "Charadrius mongolus": ("Charadrius mongolus", ""),  # 학명을 따른다(새와 생명의 터 국명과 엇갈림)
    "Larus cachinnans": ("Larus mongolicus", ""),        # 국가생물종목록의 한국재갈매기(옛 넓은 뜻의 cachinnans) = 국내에 오는 mongolicus
}
# 2022년 10월 이후 처음 기록되어 2024년 목록에 오른 종(2022판에는 상태가 없다)
NEW_2024 = {"Larus brunnicephalus", "Lanius isabellinus", "Phoebastria nigripes"}

SEASON = {"R": "텃새", "S": "여름철새", "P": "나그네새", "W": "겨울철새"}
SEASON_TIME = {"S": "여름", "P": "이동기", "W": "겨울", "R": "한 해 내내 머무는 개체", "R/S": "한 해 내내 또는 여름"}
BAND = {"1": "10만 마리 이상", "2": "수만 마리", "3": "수천 마리", "4": "수백 마리", "5": "수십 마리"}
SPECIAL = {"RE": "국내에서 사라짐(지역 절멸)", "RI": "복원 사업으로 풀어놓은 무리가 텃새로 지냄",
           "INT": "복원 사업으로 들여와 기르고 풀어놓음", "EXT": "국내에서 사라짐", "DD": "자료 부족"}
BREED = {"0": "번식 기록 없음", "1": "2000년 이후 번식 확인", "2": "2000년 이후 번식 추정",
         "3": "2000년 전에만 번식 기록", "4": "2000년 전에만 번식 추정",
         "1 RI": "복원 사업으로 풀어놓은 무리가 번식", "1 or 2": "2000년 이후 번식 확인 또는 추정"}


def tsv(path: Path) -> list[dict]:
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def norm_ssp(s: str) -> str:
    s = s.lower().strip("*?")
    return re.sub(r"(ii|i)$", "", s)  # middendorffi / middendorffii


def clean(r: dict) -> dict:
    """PDF 칸이 밀린 줄 바로잡기: 'P5, SV2, WV2 1' + 'or 2' → 'P5, SV2, WV2' + '1 or 2'"""
    st, bs = r["status"].strip(), r["bs"].strip()
    m = re.fullmatch(r"(.*?)\s+(\d)$", st)
    if m and not re.fullmatch(r"\d", bs):
        st, bs = m.group(1), f"{m.group(2)} {bs}".strip()
    return {**r, "status": st, "bs": bs}


def parse_code(code: str) -> list[tuple[str, str]]:
    """'P1, W2, SV1' → [('P','1'), ('W','2'), ('S','V1')]. 특수 표시(RE, RI, DD …)는 ('', 표시)."""
    out = []
    for part in re.split(r"\s*,\s*", code.strip()):
        part = re.sub(r"[()?\s]", "", part)
        m = re.fullmatch(r"(R/S|[RSPW]?)(V?\d)", part)
        if m:
            out.append((m.group(1), m.group(2)))
        elif part:
            out.append(("", part))
    return out


def breeding(bs: str, cat: str, code: str) -> str:
    """번식 여부. 2000년 이후 기록이 없는 종(제2군)에 '2000년 이후 번식'이 붙으면 앞뒤가 맞지 않으니 비워 둔다."""
    bs = bs.replace("*", "").strip()
    if "INT" in code:
        return "복원 사업으로 풀어놓은 무리가 번식"
    if cat == "2" and bs.startswith(("1", "2")):
        return "TODO"
    return BREED.get(bs, "TODO")


def phrase(code: str, cat: str = "1", bs: str = "0") -> str:
    """국내 상태를 우리말로. 개체 수는 해마다 그 계절에 국내에 있는 수의 범위다."""
    if code == "NEW24":
        return "길잃은새, 2022년 10월 이후 처음 기록되어 2024년 목록에 오름"
    parts = parse_code(code)
    regular = [(s, b) for s, b in parts if s and not b.startswith("V")]
    rare = [(s, b) for s, b in parts if b.startswith("V")]
    special = [b for s, b in parts if not s and not b.startswith("V")]
    bits = []
    if regular:
        if len({b for _, b in regular}) == 1:
            bits.append(f"{'·'.join(SEASON[s] for s, _ in regular)}, 해마다 {BAND[regular[0][1]]}")
        else:
            bits.append(" · ".join(f"{SEASON[s]} {BAND[b]}" for s, b in regular))
    for s, b in rare:
        few = "해마다 10건 미만" if b == "V1" else "지금까지 기록 10건 미만"
        if not s:
            who = "드물게 기록되는 새" if bs.startswith(("1", "2")) else "길잃은새"
            bits.append(f"{who}, {few}")
        elif regular:
            bits.append(f"{SEASON_TIME[s]}{'도' if s == 'R' else '에도'} 드물게 기록" + ("" if b == "V1" else "(10건 미만)"))
        else:
            bits.append(f"{SEASON_TIME[s]}{'가' if s == 'R' else '에'} 드물게 찾아옴, {few}")
    if "INT" in special and cat == "2":
        return "야생 개체는 2000년 이후 확인된 기록 없음 · 복원 사업으로 들여와 기르고 풀어놓음"
    for sp in special:
        if sp == "DD" and cat == "2":
            continue
        bits.append(SPECIAL.get(sp, sp))
    if cat == "2":
        bits.append("2000년 이후 확인된 기록 없음")
    elif cat in ("3", "4"):
        bits.append("사진·표본 없이 관찰 기록만 있음")
    elif cat == "R":
        bits.append("기록을 검토하는 중")
    return " · ".join(bits)


def rarity(code: str, cat: str) -> float:
    """작을수록 흔하다(삽화 순서용). 가장 많은 계절의 개체 수 범위를 쓴다."""
    if code == "NEW24":
        return 7
    if cat in ("3", "4", "R"):
        return 9
    best = 10.0
    for s, b in parse_code(code):
        if b in BAND:
            v = float(b)
        elif b == "V1":
            v = 6
        elif b == "V2":
            v = 7
        else:
            v = 8
        best = min(best, v)
    return best + (0.5 if cat == "2" else 0)


def load() -> tuple[list[dict], dict, dict, dict, dict]:
    bk = [clean(r) for r in tsv(REF / "bk-2022.tsv")]
    by_sci = {r["sci"]: r for r in bk if not r["ssp"]}
    by_ssp = {(r["sci"], norm_ssp(r["ssp"])): r for r in bk if r["ssp"]}
    by_en = {r["en"].lower(): r for r in bk if not r["ssp"]}
    ko24 = {r["ko"]: r for r in tsv(REF / "bk-2024-ko.tsv") if r["ko"]}
    ioc = {r["sci"]: r for r in tsv(REF / "ioc-en.tsv")}
    entries = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(SPECIES.glob("*.json"))]
    return entries, by_sci, by_ssp, by_en, {"ko24": ko24, "ioc": ioc}


def match(d: dict, by_sci, by_ssp, by_en, aux) -> tuple[dict | None, str]:
    parts = d["sci"].split()
    bi = " ".join(parts[:2])
    ioc = aux["ioc"].get(d["sci"], {})
    ioc_bi = " ".join((ioc.get("ioc_sci") or "").split()[:2])
    if d["sci"] in NEW_2024:
        return {"sci": d["sci"], "ssp": "", "status": "NEW24", "bs": "0", "cat": "1"}, "2024판에 새로 오름"
    if d["sci"] in MANUAL:
        sci, ssp = MANUAL[d["sci"]]
        return (by_ssp.get((sci, norm_ssp(ssp))) if ssp else by_sci.get(sci)), "손으로"
    found = {}
    k = aux["ko24"].get(d["ko"])
    if k:
        r = by_sci.get(k["sci"]) or by_en.get(k["en"].lower())
        if r:
            found["국명"] = r
    for name, s in (("학명", bi), ("IOC 학명", ioc_bi)):
        if s and s in by_sci:
            found[name] = by_sci[s]
    en = re.sub(r"\s*\(.*\)$", "", ioc.get("en") or "").lower()
    if en and en in by_en:
        found["영문명"] = by_en[en]
    if not found:
        return None, "없음"
    sciset = {r["sci"] for r in found.values()}
    if len(sciset) > 1:
        return None, "어긋남: " + ", ".join(f"{k}→{r['sci']}" for k, r in found.items())
    r = next(iter(found.values()))
    if len(parts) > 2:  # 아종 항목
        ss = by_ssp.get((r["sci"], norm_ssp(parts[2])))
        if not ss:
            return None, f"아종 {parts[2]} 이 {r['sci']} 아래에 없음"
        return ss, "+".join(found) + " · 아종"
    return r, "+".join(found)


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--show", action="store_true", help="종마다 상태 문장 보기")
    args = ap.parse_args()
    entries, by_sci, by_ssp, by_en, aux = load()
    ok = bad = 0
    fixes = []
    for d in entries:
        r, how = match(d, by_sci, by_ssp, by_en, aux)
        if not r:
            bad += 1
            print(f"  ? {d['ko']} {d['sci']}: {how}")
            if args.write:
                missing(d)
            continue
        ok += 1
        if args.show:
            print(f"  {d['ko']:<10} {r['status']:<16} → {phrase(r['status'], r['cat'], r['bs'])} | {breeding(r['bs'], r['cat'], r['status'])}")
        if args.write:
            fixes += apply(d, r)
    print(f"짝 {ok} · 못 찾음/어긋남 {bad}")
    for f in fixes:
        print("  고침:", f)
    return 0


TODO_TAG = "[새와 생명의 터]"


def save(d: dict) -> None:
    (SPECIES / f"{d['id']}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply(d: dict, r: dict) -> list[str]:
    """종 파일에 국내 상태를 붙이고, 달력과 어긋나는 값을 바로잡는다. 바로잡은 내용을 돌려준다."""
    out = []
    d["occurrence"] = {"code": r["status"], "bs": r["bs"], "cat": r["cat"], "bk": f"{r['sci']}{' ' + r['ssp'] if r['ssp'] else ''}",
                       "rarity": rarity(r["status"], r["cat"])}
    d["status"] = phrase(r["status"], r["cat"], r["bs"])
    d["breeding"] = breeding(r["bs"], r["cat"], r["status"])
    d["todo"] = [t for t in d.get("todo", []) if not t.startswith(TODO_TAG)]
    months = d.setdefault("months", {"seen": "TODO", "breed": "TODO"})
    bs = r["bs"].replace("*", "").strip()
    parts = parse_code(r["status"])
    # 국내 번식 기록이 없는 종: 달력의 번식기를 비운다
    if bs == "0":
        if isinstance(months.get("breed"), list) and months["breed"]:
            out.append(f"{d['ko']}: 번식기 {months['breed']} → 없음")
            d["todo"].append(f"{TODO_TAG} 국내 번식 기록이 없어 국립생물자원관 설명의 번식 달({months['breed']})을 달력에서 뺐다")
        months["breed"] = []
    # 한 해 내내 사는 텃새(개체 수 범위가 붙은 R): 볼 수 있는 달 = 열두 달
    if any(sn == "R" and b.isdigit() for sn, b in parts) and not isinstance(months.get("seen"), list):
        months["seen"] = list(range(1, 13))
    srcs = [s for s in d.get("sources", []) if "Birds Korea" not in s.get("title", "")]
    d["sources"] = srcs + [SOURCE]
    save(d)
    return out


def missing(d: dict) -> None:
    """새와 생명의 터 목록에 없는 종: 국가생물종목록 쪽 상태는 두고 표시만 남긴다."""
    d["occurrence"] = {"code": None, "rarity": 9.5, "note": "새와 생명의 터 목록(2022·2024)에 없음"}
    d.setdefault("breeding", "TODO")
    d["todo"] = [t for t in d.get("todo", []) if not t.startswith(TODO_TAG)]
    d["todo"].append(f"{TODO_TAG} 남한에서 사진·표본으로 확인된 기록을 모은 이 목록에 실리지 않은 종이라 국내 상태를 대조하지 못했다")
    save(d)


if __name__ == "__main__":
    sys.exit(main())
