# /// script
# requires-python = ">=3.11"
# ///
"""그림 그릴 때 함께 붙일 실제 사진 받기 (iNaturalist 연구 등급 관찰의 CC 사진).

글로만 설명하면 이미지 모델이 종을 제 마음대로 그린다(예: 어치에 없는 뾰족한 댕기, 유럽 아종의 깃).
그래서 그 종의 실제 사진을 함께 붙여 머리 모양·부리·눈 색·체형과 한국에 오는 개체군의 깃을 따르게 한다.
사진은 그림 참고용으로만 쓰고 공개하지 않는다(art/ 는 git 제외). 출처는 사진 옆 meta.json 에 남긴다.

한국 관찰을 먼저 고르고, 모자라면 동아시아(한국·일본·중국 동부·러시아 극동), 그래도 없으면 전 세계에서 고른다.
사진은 관찰자가 겹치지 않게, '좋아요'가 많고 원본이 큰 사진부터 4장.

    uv run tools/ref_photos.py garrulus-glandarius       # 한 종(이미 있으면 그대로)
    uv run tools/ref_photos.py --next 20                 # 그릴 차례 앞쪽 20종
    uv run tools/ref_photos.py --drawn                   # 이미 그린 종
    uv run tools/ref_photos.py garrulus-glandarius --force   # 다시 받기
    uv run tools/ref_photos.py aegypius-monachus --bad 1 --why 소리그림   # 쓸 수 없는 사진 빼기
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "aves" / "species"
OUT = ROOT / "art" / "ref" / "photos"
API = "https://api.inaturalist.org/v1/observations"
UA = "AvesKorea-field-guide/1.0 (https://github.com/dhsrua555/nature-book)"
LICENSES = "cc0,cc-by,cc-by-nc,cc-by-sa,cc-by-nc-sa,cc-by-nd,cc-by-nc-nd"
AREAS = [
    ("한국", {"place_id": 6891}),
    ("동아시아", {"swlat": 24, "swlng": 115, "nelat": 56, "nelng": 150}),
    ("전 세계", {}),
]
TAXA = "https://api.inaturalist.org/v1/taxa"
# 책의 학명이 iNaturalist 에서는 한국에 오지 않는 다른 무리를 가리킬 때, 한국에 오는 무리의 이름으로 찾는다
# (그대로 찾으면 한국 관찰이 없어 다른 대륙의 새 사진이 온다)
KOREA_TAXON = {
    "anthus-rubescens": "Anthus japonicus",              # 밭종다리: 동아시아 무리(아메리카의 American Pipit 아님)
    "larus-cachinnans": "Larus mongolicus",              # 한국재갈매기: Mongolian Gull(카스피해의 Caspian Gull 아님)
    "larus-heuglini": "Larus fuscus heuglini",           # 줄무늬노랑발갈매기: iNaturalist 는 L. fuscus 에 합쳐 유럽 개체가 섞인다
    "ninox-scutulata": "Ninox japonica",                 # 솔부엉이: 북방 무리(남아시아의 Brown Boobook 아님)
    "strix-aluco": "Strix nivicolum",                    # 올빼미: 동아시아 무리(유럽의 Tawny Owl 아님)
    "otus-bakkamoena": "Otus semitorques",               # 큰소쩍새: 한국 개체(인도의 Indian Scops Owl 아님)
    "remiz-pendulinus": "Remiz consobrinus",             # 스윈호오목눈이: 동아시아 무리(유럽의 Eurasian Penduline Tit 아님)
    "acanthis-hornemanni": "Acanthis flammea exilipes",  # 쇠홍방울새: iNaturalist 는 홍방울새에 합쳤다. 아시아에 오는 아종
    "terpsiphone-paradisi": "Terpsiphone incei",          # 북방긴꼬리딱새: Amur Paradise Flycatcher(인도의 Indian Paradise Flycatcher 아님)
    # 목록의 학명 철자가 틀린 것
    "phylloscopus-amandii": "Phylloscopus armandii",     # 쇠긴다리솔새사촌
    "lanius-cristatus-crisatus": "Lanius cristatus cristatus",  # 홍때까치
}
N = 4  # 4장 받아 두고, 그릴 때는 새가 크고 또렷한 2장을 고른다
_last = 0.0


def get(url: str, raw: bool = False, tries: int = 3):
    global _last
    for i in range(tries):
        if url.startswith(API):  # iNaturalist API 권장: 1초에 한 번(사진 파일 서버는 따로)
            wait = 1.0 - (time.monotonic() - _last)
            if wait > 0:
                time.sleep(wait)
            _last = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            return data if raw else json.loads(data)
        except (OSError, ValueError):  # 끊김·시간 초과는 잠시 뒤 다시
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def taxon_id(name: str) -> int | None:
    """학명 → iNaturalist 분류군 id. 옛 학명·동의어도 찾는다(예: Accipiter virgatus → Tachyspiza virgata).
    관찰 검색에 이름(taxon_name)을 그대로 쓰면 비슷한 이름까지 섞여 온다(갈색제비 Riparia riparia → 집게벌레 Labidura riparia,
    꺅도요 → 꼬마도요사촌, 작은새매 → 조롱이). id 로 찾으면 그 분류군과 아래 아종만 온다."""
    q = {"q": name, "per_page": 30}
    for t in get(f"{TAXA}?{urllib.parse.urlencode(q)}").get("results", []):
        if t.get("rank") in ("species", "subspecies") and \
                name.lower() in ((t.get("matched_term") or "").lower(), (t.get("name") or "").lower()):
            return t["id"]
    return None


def search(taxon: str, tid: int | None, area: dict) -> list[dict]:
    q = {"quality_grade": "research", "photos": "true", "order_by": "votes",
         "per_page": 60, "photo_license": LICENSES, **area}
    if tid:
        q["taxon_id"] = tid
        return get(f"{API}?{urllib.parse.urlencode(q)}").get("results", [])
    # id 를 못 찾았을 때(종이 나뉘어 옛 이름이 여러 종을 가리킴, 예: Charadrius mongolus): 이름으로 찾되
    # 새만, 그리고 종소명이 같은 관찰만(속이 바뀐 것은 받아들이고 Gallinago solitaria 같은 이웃 종은 버린다)
    q.update(taxon_name=taxon, iconic_taxa="Aves")
    epithet = taxon.split()[-1]  # 아종 이름이면 아종 소명까지 맞아야
    return [o for o in get(f"{API}?{urllib.parse.urlencode(q)}").get("results", [])
            if epithet in ((o.get("taxon") or {}).get("name") or "").split()[1:]]


def pick(taxa: list[str]) -> list[dict]:
    """관찰자가 겹치지 않게 N장. 아종 이름으로 없으면 종 이름으로."""
    chosen, seen_obs, seen_user = [], set(), set()
    for taxon in taxa:
        tid = taxon_id(taxon)
        for label, area in AREAS:
            found = search(taxon, tid, area)
            size = lambda o: max([(p.get("original_dimensions") or {}).get("width") or 0 for p in o.get("photos") or []] or [0])
            # 소리를 올린 관찰은 사진 자리에 소리 그림(스펙트로그램)이 오기 쉽고, 죽은 새(주석 17=19)는 모습이 다르다: 뒤로
            poor = lambda o: bool(o.get("sounds")) or any(a.get("controlled_attribute_id") == 17 and a.get("controlled_value_id") == 19
                                                       for a in o.get("annotations") or [])
            found.sort(key=lambda o: (poor(o), -(o.get("faves_count") or 0), -size(o)))
            for o in found:
                user = (o.get("user") or {}).get("login")
                photo = next((p for p in o.get("photos") or [] if p.get("url") and p.get("license_code")), None)
                if not photo or o["id"] in seen_obs or user in seen_user:
                    continue
                seen_obs.add(o["id"]); seen_user.add(user)
                chosen.append({"obs": o.get("uri"), "observer": user, "license": photo["license_code"],
                               "area": label, "date": o.get("observed_on"), "taxon": (o.get("taxon") or {}).get("name"),
                               "url": photo["url"].replace("/square.", "/large.")})
                if len(chosen) >= N:
                    return chosen
            if len(chosen) >= 2:  # 넓은 지역으로 가기 전에 2장이면 충분
                return chosen
    return chosen


def cached(sid: str) -> list[Path] | None:
    """받아 둔 사진(사람이 걸러 낸 --bad 사진은 빼고). 받은 적이 없거나 파일이 빠졌으면 None."""
    d = OUT / sid
    meta = d / "meta.json"
    if not meta.exists():
        return None
    entries = json.loads(meta.read_text(encoding="utf-8"))
    if not entries or not all((d / m["file"]).exists() for m in entries):
        return None
    return [d / m["file"] for m in entries if not m.get("bad")]


def photos_for(sp: dict, force: bool = False) -> list[Path]:
    """종의 참고 사진 경로들. 없으면 받는다. 받을 수 없으면 []."""
    d = OUT / sp["id"]
    meta = d / "meta.json"
    if not force and (have := cached(sp["id"])) is not None:
        return have
    words = sp["sci"].split()
    taxa = [" ".join(words[:3])] + ([" ".join(words[:2])] if len(words) > 2 else [])
    if sp["id"] in KOREA_TAXON:
        taxa = [KOREA_TAXON[sp["id"]]]
    chosen = pick(taxa)
    if not chosen:  # 못 찾았으면 전에 받아 둔 사진은 그대로 둔다
        return []
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.jpg"):
        old.unlink()
    for i, c in enumerate(chosen, 1):
        c["file"] = f"{i}.jpg"
    with ThreadPoolExecutor(4) as ex:  # 사진 파일은 한꺼번에 받는다
        for c, data in zip(chosen, ex.map(lambda c: get(c["url"], raw=True), chosen)):
            (d / c["file"]).write_bytes(data)
    meta.write_text(json.dumps(chosen, ensure_ascii=False, indent=1), encoding="utf-8")
    return [d / c["file"] for c in chosen]


def queue_species() -> list[dict]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import illustrate  # 그릴 차례(흔한 종부터)
    return [sp for _, sp in illustrate.all_species()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--next", type=int, default=0, help="아직 그림이 없는 종 가운데 그릴 차례 앞쪽 N종")
    ap.add_argument("--drawn", action="store_true", help="이미 그린 종")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--bad", metavar="N,N", help="한 종의 쓸 수 없는 사진 번호(소리 그림, 죽은 새, 다른 종 등) — 그릴 때 붙이지 않는다")
    ap.add_argument("--why", default="쓸 수 없음", help="--bad 의 까닭")
    args = ap.parse_args()
    if args.bad:
        if len(args.ids) != 1:
            ap.error("--bad 는 종 id 하나와 함께")
        meta = OUT / args.ids[0] / "meta.json"
        entries = json.loads(meta.read_text(encoding="utf-8"))
        for m in entries:
            if m["file"].split(".")[0] in args.bad.split(","):
                m["bad"] = args.why
        meta.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{args.ids[0]}: 쓸 사진 {sum(1 for m in entries if not m.get('bad'))}장")
        return 0
    rows = queue_species()
    img = ROOT / "img" / "aves"
    if args.ids:
        rows = [sp for sp in rows if sp["id"] in args.ids]
    elif args.drawn:
        rows = [sp for sp in rows if (img / f"{sp['id']}.webp").exists() or (img / f"{sp['id']}.id.webp").exists()]
    elif args.next:
        rows = [sp for sp in rows if not (img / f"{sp['id']}.webp").exists()][: args.next]
    else:
        ap.error("종 id, --next N, --drawn 중 하나")
    bad = 0
    for sp in rows:
        try:
            files = photos_for(sp, args.force)
        except Exception as e:  # 망 오류 등: 그 종만 건너뜀
            print(f"{sp['id']:<30} 실패: {e}")
            bad += 1
            continue
        meta = json.loads((OUT / sp["id"] / "meta.json").read_text(encoding="utf-8")) if files else []
        where = ", ".join(sorted({m["area"] for m in meta})) or "없음"
        print(f"{sp['id']:<30} {sp['ko']:<10} 사진 {len(files)}장 ({where})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
