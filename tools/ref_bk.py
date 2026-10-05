# /// script
# requires-python = ">=3.11"
# dependencies = ["pdfplumber"]
# ///
"""새와 생명의 터(Birds Korea) 조류목록에서 국내 출현 상태를 옮겨 tools/ref/ 에 표로 둔다.

    uv run tools/ref_bk.py

- Birds Korea Checklist 2022 (Moores & Ha, 영문 전체판): 종·아종마다 계절(R 텃새, S 여름, P 통과, W 겨울)과
  해마다 오는 개체 수 범위(1 ≥10만 … 5 10–99마리, V1 해마다 10건 미만, V2 지금까지 1–9건), 번식 여부(BS)
  → tools/ref/bk-2022.tsv
- 새와 생명의 터 조류목록 2024 (하정문·Moores, 국문 간략판): 국명·영명·학명(IOC 14.1)
  → tools/ref/bk-2024-ko.tsv  (국명으로 2022판의 종을 찾는 다리)
PDF 는 cache/bk/ 에 받아 둔다(git 제외).
"""
from __future__ import annotations

import csv
import re
import sys
import urllib.request
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "bk"
URL_2022 = "https://www.birdskoreablog.org/wp-content/uploads/2022/11/2022-Birds-Korea-Checklist-ENG_issn.pdf"
URL_2024_KO = "https://birdskoreablog.org/wp-content/uploads/2024/08/Birds-Korea-checklist-Kor-2024-final-with-quick-fix-20240827.pdf"
CODE = r"(?:[RSPW]?V?\d\??|RE|INT|DD)"
STATUS_RE = rf"{CODE}(?:\s*,\s*{CODE})*"


def fetch(url: str, dest: Path) -> Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "nature-book/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            dest.write_bytes(r.read())
    return dest


def parse_2022(pdf_path: Path) -> list[dict]:
    rows: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn, p in enumerate(pdf.pages):
            text = p.extract_text() or ""
            m = re.search(r"The Birds Korea Checklist - CAT (\d)", text)
            if not m:
                continue
            cat = m.group(1)
            if cat in ("1", "2"):  # 번호가 붙은 표(제1·2군): 글자 위치로 칸을 나눈다
                rows += parse_numbered(p, cat)
            if "CAT 3" in text or "CAT 4" in text or "CAT 5" in text or "REVIEW" in text:
                rows += parse_plain(text)
    return rows


def parse_numbered(p, cat: str) -> list[dict]:
    ws = p.extract_words(extra_attrs=["fontname"])
    lines: list[dict] = []
    for w in sorted(ws, key=lambda w: (w["top"], w["x0"])):
        if not 40 < w["top"] < 780:
            continue
        for L in lines:
            if abs(L["top"] - w["top"]) <= 3.5:
                L["w"].append(w)
                break
        else:
            lines.append({"top": w["top"], "w": [w]})
    lines.sort(key=lambda L: L["top"])

    def col(L, a, b, font=None):
        return " ".join(w["text"] for w in sorted(L["w"], key=lambda w: w["x0"])
                        if a <= w["x0"] < b and (font is None or font in w["fontname"]))

    out, cur, pending = [], None, []
    for i, L in enumerate(lines):
        no, sci = col(L, 55, 84), col(L, 195, 355, "BoldItalic")
        en, status, bs = col(L, 84, 198, "Bold"), col(L, 424, 500), col(L, 500, 540)
        if re.fullmatch(r"\d+", no) and sci:
            cur = {"no": no, "cat": cat if int(no) < 564 else "2", "en": " ".join([*pending, en]).strip(), "sci": sci, "ssp": "",
                   "ncs": col(L, 355, 395), "gcs": col(L, 395, 424), "status": status, "bs": bs}
            pending = []
            out.append(cur)
            continue
        ssp = col(L, 205, 355, "Italic")
        if ssp and not sci and cur and status:
            out.append({**cur, "ssp": ssp.lstrip("*"), "status": status, "bs": bs, "en": cur["en"]})
            continue
        if en and not sci and not status and not re.search(r"formes|idae|NCS", en):
            nxt = lines[i + 1] if i + 1 < len(lines) else None
            prev = lines[i - 1] if i else None
            # 영문명 두 줄: 번호 줄 바로 아래면 앞 종에 붙이고, 아니면 다음 종 앞에 붙인다
            if cur and prev is not None and re.fullmatch(r"\d+", col(prev, 55, 84)) and L["top"] - prev["top"] < 14 \
                    and not (nxt and re.fullmatch(r"\d+", col(nxt, 55, 84)) and nxt["top"] - L["top"] < 14):
                for r in reversed(out):
                    if r["no"] == cur["no"]:
                        r["en"] = f"{r['en']} {en}".strip()
            else:
                pending.append(en)
    for r in out:
        r["en"] = re.sub(r"^\d+\s+", "", r["en"]).replace("*", "").strip()
        r["sci"] = r["sci"].replace("*", "").strip()
    return out


def parse_plain(text: str) -> list[dict]:
    out, section, cur = [], None, None
    for line in text.splitlines():
        line = line.strip()
        if re.fullmatch(r"CAT [345]|REVIEW", line):
            section = line.replace("CAT ", "")
            continue
        if not section:
            continue
        m = re.fullmatch(rf"(?:[A-F] )?(.+?) ([A-Z][a-z]+ [a-z]+) ([A-Z]{{2,3}}) ([A-Z]{{2}}) ({STATUS_RE}) (\d)", line)
        if m:
            cur = {"no": "", "cat": "R" if section == "REVIEW" else section, "en": m.group(1).strip('"'), "sci": m.group(2), "ssp": "",
                   "ncs": m.group(3), "gcs": m.group(4), "status": m.group(5), "bs": m.group(6)}
            out.append(cur)
            continue
        m = re.fullmatch(rf"(?:\".+?\" )?([a-z]+\??)(?: \*)? ({STATUS_RE}) (\d)", line)
        if m and cur:
            out.append({**cur, "ssp": m.group(1).rstrip("?"), "status": m.group(2), "bs": m.group(3)})
    return out


def parse_2024_ko(pdf_path: Path) -> list[dict]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            for line in (p.extract_text() or "").splitlines():
                m = re.fullmatch(r"(\d+) (R?\d[A-Z0-9,]*)\s*([가-힣]+|\(정해지지 않음\)) (.+?) ([A-Z][a-z]+\*? [a-z]+\*?) ([A-Z]{2}) ([A-Z]{1,2}|Ⅰ|Ⅱ|I{1,2})", line.strip())
                if m:
                    ko = "" if m.group(3).startswith("(") else m.group(3)
                    out.append({"no": m.group(1), "cat": m.group(2), "ko": ko, "en": m.group(4).rstrip("*"), "sci": m.group(5).replace("*", "")})
    return out


def write(path: Path, rows: list[dict], cols: list[str], note: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(f"# {note}\n")
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(errors="replace")
    r22 = parse_2022(fetch(URL_2022, CACHE / "bk-en-2022.pdf"))
    r24 = parse_2024_ko(fetch(URL_2024_KO, CACHE / "bk-ko-2024.pdf"))
    write(ROOT / "tools" / "ref" / "bk-2022.tsv", r22, ["no", "cat", "en", "sci", "ssp", "ncs", "gcs", "status", "bs"],
          f"Moores, N. & Ha, J-M. 2022. The Birds Korea Checklist (2022). {URL_2022} — tools/ref_bk.py 가 옮김")
    write(ROOT / "tools" / "ref" / "bk-2024-ko.tsv", r24, ["no", "cat", "ko", "en", "sci"],
          f"Ha, J-M. & Moores, N. 2024. 새와 생명의 터 조류목록(2024). {URL_2024_KO} — tools/ref_bk.py 가 옮김")
    species = [r for r in r22 if not r["ssp"]]
    print(f"2022판: 종 {len(species)}줄(아종 포함 {len(r22)}줄) · 2024판 국명 {len(r24)}종")
    return 0


if __name__ == "__main__":
    sys.exit(main())
