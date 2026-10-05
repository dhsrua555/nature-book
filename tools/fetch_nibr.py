# /// script
# requires-python = ">=3.11"
# ///
"""국가생물종지식정보시스템에서 종 해설과 보호 표시를 받아 cache/nibr/ 에 저장한다.

    uv run tools/fetch_nibr.py            # 아직 받지 않은 종만
    uv run tools/fetch_nibr.py --force    # 모두 다시

받은 원문은 종 자료를 쓸 때 근거로만 쓰고 저장소에는 올리지 않는다(cache/ 는 git 제외).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "tools" / "ref" / "nibr-aves-2025.tsv"
OUT = ROOT / "cache" / "nibr"
BASE = "https://species.nibr.go.kr/gwsvc"
UA = {"User-Agent": "nature-book/1.0 (personal study site)"}


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(2 + attempt * 3)
    return {}


def pick(f: dict) -> tuple[dict, list]:
    keep = {key: f.get(key) for key in ("ktsnKrnNm", "stnm", "corsynSeNm", "specsTypeNm", "egspcsGrdNo",
                                        "ntmYn", "korUnqBispYn", "phspSpcsYn", "sttsNm") if key in f}
    return keep, sorted(k for k, v in f.items() if v not in (None, "", "N"))


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--flags", action="store_true", help="받아 둔 종의 보호 표시만 다시 받기")
    args = ap.parse_args()
    lines = [l for l in REF.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
    rows = list(csv.DictReader(lines, delimiter="\t"))
    OUT.mkdir(parents=True, exist_ok=True)

    todo = [r for r in rows if args.force or args.flags or not (OUT / f"{r['ktsn']}.json").exists()]
    print(f"{len(rows)}행 중 {len(todo)}행 받기")
    # 보호 표시는 여러 종을 한 번에
    flags: dict[str, dict] = {}
    for i in range(0, len(todo), 40):
        chunk = [r["ktsn"] for r in todo[i:i + 40]]
        data = get(f"{BASE}/ktsn/api/v1/public/txgrp-search/list?ktsnList={','.join(chunk)}&pageSize=100")
        for item in (data.get("data") or {}).get("content", []):
            flags[str(item["ktsn"])] = item
        time.sleep(0.4)

    if args.flags:
        recs = {}
        for r in todo:
            f = OUT / f"{r['ktsn']}.json"
            if f.exists():
                recs[f] = json.loads(f.read_text(encoding="utf-8"))
        # 종 설명이 옛 학명(이명) 기록에 달려 있으면, 보호 표시도 그 기록에 남아 있는 일이 있다(예: 넓적부리도요)
        old = sorted({str(rec["cn_ktsn"]) for rec in recs.values() if rec.get("cn_ktsn") and str(rec["cn_ktsn"]) != rec["ktsn"]})
        old_flags: dict[str, dict] = {}
        for i in range(0, len(old), 40):
            data = get(f"{BASE}/ktsn/api/v1/public/txgrp-search/list?ktsnList={','.join(old[i:i + 40])}&pageSize=100")
            for item in (data.get("data") or {}).get("content", []):
                old_flags[str(item["ktsn"])] = item
            time.sleep(0.4)
        for f, rec in recs.items():
            rec["flags"], rec["flags_raw_keys"] = pick(flags.get(rec["ktsn"], {}))
            ck = str(rec.get("cn_ktsn") or "")
            if ck in old_flags:
                rec["cn_flags"], _ = pick(old_flags[ck])
            f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"보호 표시 {len(flags)}종 갱신, 옛 학명 기록 {len(old_flags)}개 대조")
        return 0

    for n, r in enumerate(todo, 1):
        k = r["ktsn"]
        try:
            cn = get(f"{BASE}/digital/api/v1/public/bisp-conts/get-cn-data/{k}").get("data")
        except Exception as e:  # noqa: BLE001
            print(f"  실패 {r['ko']} {k}: {e}")
            continue
        keep, raw_keys = pick(flags.get(k, {}))
        rec = {
            "ktsn": k, "ko": r["ko"], "sci": r["sci"],
            "cn": (cn or {}).get("cn"), "cn_ktsn": (cn or {}).get("ktsn"), "src": (cn or {}).get("src"),
            "biz": (cn or {}).get("bizNm"), "modified": (cn or {}).get("mdfcnDt"),
            "flags": keep, "flags_raw_keys": raw_keys,
        }
        (OUT / f"{k}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        if n % 50 == 0:
            print(f"  {n}/{len(todo)}")
        time.sleep(0.25)
    print("끝")
    return 0


if __name__ == "__main__":
    sys.exit(main())
