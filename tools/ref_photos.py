# /// script
# requires-python = ">=3.11"
# dependencies = ["ultralytics", "pillow"]
# ///
"""그림 그릴 때 함께 붙일 실제 사진 받기 (iNaturalist 연구 등급 관찰의 CC 사진).

글로만 설명하면 이미지 모델이 종을 제 마음대로 그린다(예: 어치에 없는 뾰족한 댕기, 유럽 아종의 깃).
그래서 그 종의 실제 사진을 함께 붙여 머리 모양·부리·눈 색·체형과 한국에 오는 개체군의 깃을 따르게 한다.
사진은 그림 참고용으로만 쓰고 공개하지 않는다(art/ 는 git 제외). 출처는 사진 옆 meta.json 에 남긴다.

한국 관찰을 먼저 고르고, 모자라면 동아시아(한국·일본·중국 동부·러시아 극동), 그래도 없으면 전 세계에서 고른다.
사진은 관찰자가 겹치지 않게 4장. '좋아요'가 많은 관찰 앞쪽 후보마다 새가 사진에서 차지하는 넓이를 재어(YOLO 새 찾기)
새가 크게 찍힌 사진부터 고른다('좋아요'만 보면 전깃줄 위 점 같은 사진이 뽑힌다). 잰 값은 meta.json 의 bird.
illustrate.py 처럼 ultralytics 없이 불러 쓰면 재지 않고 '좋아요' 순으로 고른다.

    uv run tools/ref_photos.py garrulus-glandarius       # 한 종(이미 있으면 그대로)
    uv run tools/ref_photos.py --next 20                 # 그릴 차례 앞쪽 20종
    uv run tools/ref_photos.py --drawn                   # 이미 그린 종
    uv run tools/ref_photos.py --small                   # 받아 둔 사진에 새가 크게 찍힌 것이 2장이 안 되는 종만 다시 받기
    uv run tools/ref_photos.py garrulus-glandarius --force   # 다시 받기
    uv run tools/ref_photos.py aegypius-monachus --bad 1 --why 소리그림   # 쓸 수 없는 사진 빼기
"""
from __future__ import annotations

import argparse
import io
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
SCAN = 20  # 지역마다 새 크기를 재 볼 후보 수
NEAR = 0.05  # bird_size 가 이만큼 넘으면 가까이 찍은 사진(1024px 사진에서 새가 약 190px 네모. 3%는 아직 덤불 속 작은 새)
_last = 0.0
_yolo = None


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


def yolo():
    """새 찾기 모델(COCO 의 bird 갈래). 처음 한 번 cache/ 에 받는다. ultralytics 가 없으면 None."""
    global _yolo
    if _yolo is None:
        try:
            from ultralytics import YOLO
            _yolo = YOLO(str(ROOT / "cache" / "yolov8s.pt"))
        except ImportError:
            _yolo = False
    return _yolo or None


def bird_size(data: bytes, side: int | None = None) -> float:
    """가장 큰 새의 넓이를 긴 변 1024px 사진에 견준 비율(새를 못 찾으면 0). side 는 원본의 긴 변(없으면 이 사진의 긴 변).
    원본이 작은 사진은 그만큼 깎는다: 작은 사진을 바짝 잘라 올린 흐릿한 새가 크게 잡히지 않게."""
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    r = yolo().predict(im, classes=[14], conf=0.25, verbose=False)[0]
    frac = max([(x2 - x1) * (y2 - y1) for x1, y1, x2, y2 in r.boxes.xyxy.tolist()] or [0]) / (im.width * im.height)
    return round(frac * min(1, (side or max(im.size)) / 1024) ** 2, 4)


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


def pick(taxa: list[str], skip: set[str] = frozenset()) -> list[dict]:
    """관찰자가 겹치지 않게 N장, 새가 크게 찍힌 사진부터. 아종 이름으로 없으면 종 이름으로.
    skip: 사람이 쓸 수 없다고 걸러 낸 관찰 주소(다시 뽑지 않는다)."""
    chosen, spare, seen_obs, seen_user = [], [], set(skip), set()

    def take(c: dict) -> None:
        if c["obs"] not in seen_obs and c["observer"] not in seen_user:
            seen_obs.add(c["obs"]); seen_user.add(c["observer"]); chosen.append(c)

    for taxon in taxa:
        tid = taxon_id(taxon)
        for label, area in AREAS:
            if label == "전 세계" and len(chosen) + sum(1 for c in spare if c["bird"]) >= 2:
                break  # 다른 대륙 무리(깃이 다를 수 있음)는 한국·동아시아에 새가 보이는 사진이 2장도 없을 때만
            found = search(taxon, tid, area)
            size = lambda o: max([(p.get("original_dimensions") or {}).get("width") or 0 for p in o.get("photos") or []] or [0])
            # 소리를 올린 관찰은 사진 자리에 소리 그림(스펙트로그램)이 오기 쉽고, 죽은 새(주석 17=19)는 모습이 다르다: 뒤로
            poor = lambda o: bool(o.get("sounds")) or any(a.get("controlled_attribute_id") == 17 and a.get("controlled_value_id") == 19
                                                       for a in o.get("annotations") or [])
            found.sort(key=lambda o: (poor(o), -(o.get("faves_count") or 0), -size(o)))
            cands = []
            for o in found:
                photo = next((p for p in o.get("photos") or [] if p.get("url") and p.get("license_code")), None)
                if not photo or o.get("uri") in seen_obs:
                    continue
                dim = photo.get("original_dimensions") or {}
                cands.append({"obs": o.get("uri"), "observer": (o.get("user") or {}).get("login"), "license": photo["license_code"],
                              "area": label, "date": o.get("observed_on"), "taxon": (o.get("taxon") or {}).get("name"),
                              "url": photo["url"].replace("/square.", "/large."),
                              "side": max(dim.get("width") or 0, dim.get("height") or 0) or None})
                if len(cands) >= SCAN:
                    break
            if yolo():  # 잴 때는 중간 크기(500px)로 받아 잰다
                with ThreadPoolExecutor(4) as ex:
                    for c, data in zip(cands, ex.map(lambda c: get(c["url"].replace("/large.", "/medium."), raw=True), cands)):
                        c["bird"] = bird_size(data, c["side"])
                near = sorted((c for c in cands if c["bird"] >= NEAR), key=lambda c: -c["bird"])
                spare += [c for c in cands if c["bird"] < NEAR]
            else:
                near = cands
            for c in near:
                take(c)
                if len(chosen) >= N:
                    return chosen
            if len(chosen) >= 2:  # 넓은 지역으로 가기 전에 2장이면 충분
                return chosen
    # 가까이 찍은 사진이 2장이 안 되면 멀리 찍은 것 가운데 새가 큰 것으로 채운다(새를 못 찾은 사진은 빼고)
    for c in sorted(spare, key=lambda c: -c["bird"]):
        if len(chosen) >= 2 or not c["bird"]:
            break
        take(c)
    return chosen


def cached(sid: str) -> list[Path] | None:
    """받아 둔 사진(사람이 걸러 낸 --bad 사진은 빼고). 받은 적이 없거나 파일이 빠졌으면 None."""
    d = OUT / sid
    meta = d / "meta.json"
    if not meta.exists():
        return None
    entries = [m for m in json.loads(meta.read_text(encoding="utf-8")) if not m.get("bad")]
    if not entries or not all((d / m["file"]).exists() for m in entries):
        return None
    return [d / m["file"] for m in entries]


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
    # 사람이 --bad 로 걸러 낸 관찰은 다시 뽑지 않고, 파일 없이 meta 에 남겨 다음에 다시 받을 때도 거른다
    bad = [m | {"file": ""} for m in json.loads(meta.read_text(encoding="utf-8")) if m.get("bad")] if meta.exists() else []
    chosen = pick(taxa, {m["obs"] for m in bad})
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
    meta.write_text(json.dumps(chosen + bad, ensure_ascii=False, indent=1), encoding="utf-8")
    return [d / c["file"] for c in chosen]


def near_count(sid: str) -> int:
    """받아 둔 사진 가운데 새가 크게 찍힌 것의 수. 아직 안 잰 사진은 재어 meta.json 의 bird 에 적어 둔다."""
    meta = OUT / sid / "meta.json"
    entries = json.loads(meta.read_text(encoding="utf-8"))
    for m in entries:
        if m.get("file") and "bird" not in m:
            m["bird"] = bird_size((OUT / sid / m["file"]).read_bytes())
    meta.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    return sum(1 for m in entries if not m.get("bad") and m.get("bird", 0) >= NEAR)


def queue_species() -> list[dict]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import illustrate  # 그릴 차례(흔한 종부터)
    return [sp for _, sp in illustrate.all_species()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--next", type=int, default=0, help="아직 그림이 없는 종 가운데 그릴 차례 앞쪽 N종")
    ap.add_argument("--drawn", action="store_true", help="이미 그린 종")
    ap.add_argument("--small", action="store_true", help="받아 둔 사진에 새가 크게 찍힌 것이 2장이 안 되는 종만 다시 받기")
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
    elif args.small:
        if not yolo():
            ap.error("--small 은 새 크기를 재야 해서 uv run tools/ref_photos.py 로 실행")
        rows = [sp for sp in rows if cached(sp["id"]) and near_count(sp["id"]) < 2]
        print(f"새가 크게 찍힌 사진이 2장이 안 되는 종 {len(rows)}개를 다시 받는다", flush=True)
    else:
        ap.error("종 id, --next N, --drawn, --small 중 하나")
    bad = 0
    for sp in rows:
        try:
            files = photos_for(sp, args.force or args.small)
        except Exception as e:  # 망 오류 등: 그 종만 건너뜀
            print(f"{sp['id']:<30} 실패: {e}")
            bad += 1
            continue
        meta = json.loads((OUT / sp["id"] / "meta.json").read_text(encoding="utf-8")) if files else []
        meta = [m for m in meta if not m.get("bad")]
        where = ", ".join(sorted({m["area"] for m in meta})) or "없음"
        near = sum(1 for m in meta if (m.get("bird") or 0) >= NEAR)
        print(f"{sp['id']:<30} {sp['ko']:<10} 사진 {len(files)}장 ({where}) 가까이 {near}장", flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
