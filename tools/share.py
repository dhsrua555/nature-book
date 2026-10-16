# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11.0"]
# ///
"""링크 미리보기(Open Graph): 마디마다 미리보기 쪽과 배너 그림을 만든다.

메신저·SNS 는 링크를 미리 볼 때 자바스크립트를 돌리지 않고 주소의 # 뒤도 보지 않는다. 그래서
  <권>/<마디>/index.html       index.html 을 본뜬 쪽(제목·설명·og 태그만 다르다). 책 주소가 이 꼴이다.
  og/<권>/<이름>.<해시>.jpg    1200×630 배너. 종은 그 종의 도판, 목·과는 대표종, 첫 화면은 오늘의 새.
                               그림이 아직 없으면 책 표제 배너.
  index.html 의 <!-- share --> 칸   첫 화면(오늘의 새)의 og 태그
를 만든다. build.py 가 끝에 부른다. 배너 이름의 해시는 내용(글·그림·모양)이 바뀔 때만 바뀌므로
바뀐 배너만 다시 그리고, 메신저도 바뀐 그림을 새로 읽는다. 쓰지 않게 된 배너와 쪽은 지운다.

오늘의 새는 book.js 와 같은 방법으로 한국 시간 날짜에서 고른다. 첫 화면 배너는 build.py 를 돌린 날의 새다.

    uv run tools/share.py            # 자체 점검
    uv run tools/share.py --readme   # 저장소 README 배너(.github/banner.jpg)
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H = 1200, 630
STYLE = 1  # 배너 모양을 바꾸면 올린다(모두 다시 그린다)
C = {"paper": "#f7f2e7", "hi": "#fcf9f2", "ink": "#1e1914", "label": "#6b5235", "fade": "#8c7558", "deco": "#b8a283", "red": "#a23b26"}
NAMES = {"contents": "차례", "index": "찾아보기", "colophon": "출처와 판권"}
BLOCK = re.compile(r"<!-- share -->.*?<!-- /share -->", re.S)

# ───────────── 오늘의 새 (assets/book.js 의 todayPool·weighted·seeded 와 같게) ─────────────
SEASON_MONTHS = {"R": range(1, 13), "S": [4, 5, 6, 7, 8, 9], "W": [10, 11, 12, 1, 2, 3], "P": [3, 4, 5, 8, 9, 10, 11]}


def kst_today() -> date:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).date()


def in_season(s: dict, m: int) -> bool:
    if isinstance(s.get("seen"), list):
        return m in s["seen"]
    marks = [re.match(r"([RSPW])\d", x.strip()) for x in str(s.get("occ") or "").split(",")]
    return any(m in SEASON_MONTHS[x[1]] for x in marks if x)


def seeded(n: int) -> float:  # JS 의 Math.imul·>>> 를 32비트로 흉내 낸다
    M = 0xFFFFFFFF
    x = (n ^ 0x9E3779B9) & M
    x = ((x ^ (x >> 16)) * 0x85EBCA6B) & M
    x = ((x ^ (x >> 13)) * 0xC2B2AE35) & M
    return ((x ^ (x >> 16)) & M) / 4294967296


def today_bird(species: list[dict], d: date) -> dict:
    pool = [s for s in species if s.get("text") and s.get("rarity", 9) <= 5 and in_season(s, d.month)] \
        or [s for s in species if s.get("text")]
    w = [6 if s["img"]["scene"] else 1 for s in pool]
    r = seeded(d.year * 10000 + d.month * 100 + d.day) * sum(w)
    for s, x in zip(pool, w):
        r -= x
        if r <= 0:
            return s
    return pool[-1]


# ───────────── 배너 ─────────────
FONT_DIRS = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
             Path(os.environ.get("LOCALAPPDATA", "~")) / "Microsoft" / "Windows" / "Fonts"]
# 책(book.css)과 같은 글꼴, 없으면 그 글꼴 차례에 있는 비슷한 것
FACES = {
    "serif": (["NotoSerifKR-VF.ttf", "NotoSerifKR-Bold.otf", "HANBatangB.ttf", "batang.ttc"], 700),
    "la": (["SourceSerif4-It.ttf", "georgiai.ttf"], None),
    "title": (["SourceSerif4-Regular.ttf", "georgia.ttf"], None),
    "titleb": (["SourceSerif4-Semibold.ttf", "georgiab.ttf"], None),
    "sans": (["PretendardVariable.ttf", "NotoSansKR-VF.ttf", "malgun.ttf"], 500),
    "sansb": (["PretendardVariable.ttf", "NotoSansKR-VF.ttf", "malgunbd.ttf"], 700),
}


@cache
def font(face: str, size: int) -> ImageFont.FreeTypeFont:
    names, wght = FACES[face]
    for n in names:
        for d in FONT_DIRS:
            if (d / n).exists():
                f = ImageFont.truetype(str(d / n), size)
                if wght:
                    try:
                        f.set_variation_by_axes([wght])
                    except OSError:
                        pass  # 굵기가 정해진 글꼴
                return f
    raise FileNotFoundError(f"배너 글꼴이 없다: {', '.join(names)}")


def fit(face: str, s: str, maxw: float, size: int, least: int) -> ImageFont.FreeTypeFont:
    while size > least and font(face, size).getlength(s) > maxw:
        size -= 2
    return font(face, size)


def put(d: ImageDraw.ImageDraw, x: float, y: float, runs: list[tuple], track: float = 0) -> float:
    """runs = [(글, 글꼴, 색)] 을 한 줄로 이어 쓴다(y 는 글자 바닥선). 끝난 x 를 돌려준다."""
    for s, f, fill in runs:
        for ch in (s if track else [s]):
            d.text((x, y), ch, font=f, fill=fill, anchor="ls")
            x += f.getlength(ch) + track
    return x


def width(runs: list[tuple], track: float = 0) -> float:
    return sum(f.getlength(s) + track * len(s) for s, f, _ in runs) - (track if track else 0)


def ornament(d: ImageDraw.ImageDraw, x: float, y: float) -> None:  # 책의 ── ✦ ── 구분 장식
    d.line((x, y, x + 46, y), fill=C["deco"], width=2)
    cx = x + 60
    d.polygon([(cx, y - 7), (cx + 7, y), (cx, y + 7), (cx - 7, y)], fill=C["deco"])
    d.line((cx + 14, y, cx + 60, y), fill=C["deco"], width=2)


def cover(src: Path, w: int, h: int, focus) -> Image.Image:
    im = Image.open(src).convert("RGB")
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    fx, fy = focus or (0.5, 0.5)
    x = min(max(round(im.width * fx - w / 2), 0), im.width - w)
    y = min(max(round(im.height * fy - h / 2), 0), im.height - h)
    return im.crop((x, y, x + w, y + h))


def brand(d: ImageDraw.ImageDraw, x: float, title: str, kicker: str) -> None:
    x = put(d, x, H - 48, [(title, font("titleb", 25), C["ink"])])
    put(d, x + 12, H - 48, [(kicker, font("sans", 19), C["fade"])])


def draw_card(spec: dict, img: Path | None, out: Path) -> None:
    """spec: kicker=[(글, 글꼴 이름, 색 이름)], ko, sci, sub, meta, focus, oval, book"""
    im = Image.new("RGB", (W, H), C["paper"])
    d = ImageDraw.Draw(im)
    if spec.get("book") and not img:  # 그림이 없는 쪽: 책 표제(첫 쪽과 같은 차림)
        mid = W / 2
        k = [("조류 도감", font("sansb", 24), C["label"])]
        put(d, mid - width(k, 9) / 2, 200, k, track=9)
        t = [(spec["title"].split(" (")[0], font("title", 104), C["ink"]), (" (" + spec["title"].split(" (")[1], font("title", 104), C["label"])] \
            if " (" in spec["title"] else [(spec["title"], font("title", 104), C["ink"])]
        put(d, mid - width(t) / 2, 330, t)
        ornament(d, mid - 60, 385)
        m = [(spec["meta"], font("sans", 26), C["fade"])]
        put(d, mid - width(m) / 2, 455, m)
        im.save(out, quality=84, optimize=True, progressive=True)
        return
    x0 = 56
    if img:  # 왼쪽: 종은 도판(모서리를 살짝 둥글린 직사각), 목·과는 대표종(책의 표제 쪽처럼 타원)
        box = (70, 100, 600, 530) if spec.get("oval") else (40, 40, 640, 590)
        w, h = box[2] - box[0], box[3] - box[1]
        mask = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(mask)
        if spec.get("oval"):
            md.ellipse((0, 0, w - 1, h - 1), fill=255)
        else:
            md.rounded_rectangle((0, 0, w - 1, h - 1), radius=8, fill=255)
        im.paste(cover(img, w, h, spec.get("focus")), box[:2], mask)
        if spec.get("oval"):
            d.ellipse(box, outline=C["deco"], width=2)
        x0 = 694
    maxw = W - 56 - x0
    kick = [(s, font(f, 23), C[c]) for s, f, c in spec["kicker"]]
    ko = fit("serif", spec["ko"], maxw, 92, 40)
    la = fit("la", spec["sci"], maxw, 38, 24)
    sub = font("sans", 23)
    meta = font("sans", 23)
    # 위에서 아래로: 머리 글 → 국명 → 학명 → 영문명 → 장식 → 갈래. 가운데에 놓는다.
    steps = [23, 30 + ko.size * 0.92, 20 + la.size, (16 + sub.size) if spec.get("sub") else 0, 44, 40 + meta.size]
    y = (H - 70 - sum(steps)) / 2
    y += steps[0]; put(d, x0, y, kick, track=4 if len(kick) == 1 else 0)  # '오늘의 새'·'Pl. 12' 는 벌려, '과 Familia' 는 책처럼
    y += steps[1]; d.text((x0, y), spec["ko"], font=ko, fill=C["ink"], anchor="ls")
    y += steps[2]; d.text((x0, y), spec["sci"], font=la, fill=C["ink"], anchor="ls")
    if spec.get("sub"):
        y += steps[3]; d.text((x0, y), spec["sub"], font=sub, fill=C["fade"], anchor="ls")
    y += steps[4]; ornament(d, x0, y - 8)
    y += steps[5]; d.text((x0, y), spec["meta"], font=fit("sans", spec["meta"], maxw, 23, 16), fill=C["label"], anchor="ls")
    brand(d, x0, spec["title"], spec["kicker_book"])
    im.save(out, quality=84, optimize=True, progressive=True)


# ───────────── 미리보기 쪽 ─────────────
def clip(s: str, n: int = 150) -> str:
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def block(base: str, title: str, desc: str, url: str, image: str, alt: str) -> str:
    e = lambda s: html.escape(s, quote=True)
    return "\n".join([
        "<!-- share -->",
        f'<base href="{base}">',
        f"<title>{e(title)}</title>",
        f'<meta name="description" content="{e(desc)}">',
        f'<link rel="canonical" href="{e(url)}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:locale" content="ko_KR">',
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:image" content="{e(image)}">',
        f'<meta property="og:image:width" content="{W}">',
        f'<meta property="og:image:height" content="{H}">',
        f'<meta property="og:image:alt" content="{e(alt)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        "<!-- /share -->",
    ])


def write_if_changed(p: Path, text: str) -> None:
    if not p.exists() or p.read_text(encoding="utf-8") != text:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")


def write(vid: str, book: dict, summaries: dict[str, str], site: str, day: date | None = None) -> int:
    """book: build.py 가 만든 book.json 내용, summaries: 종 id → 해설 첫머리. 배너를 새로 그린 수를 돌려준다."""
    day = day or kst_today()
    title, kicker = book["title"], book.get("kicker", "")
    species = [s for o in book["tree"] for f in o["children"] for s in f["children"]]
    parent = {s["id"]: (o, f) for o in book["tree"] for f in o["children"] for s in f["children"]}
    pl = {s["id"]: i + 1 for i, s in enumerate(species)}
    odir = ROOT / "og" / vid
    odir.mkdir(parents=True, exist_ok=True)
    keep, drawn = set(), 0

    def scene(sid: str) -> Path | None:
        p = ROOT / "img" / vid / f"{sid}.webp"
        return p if p.exists() else None

    def card(name: str, spec: dict, img: Path | None) -> str:
        nonlocal drawn
        spec = {**spec, "title": title, "kicker_book": kicker}
        h = hashlib.sha1(json.dumps([STYLE, spec], ensure_ascii=False).encode() + (img.read_bytes() if img else b"")).hexdigest()[:8]
        fn = f"{name}.{h}.jpg"
        if not (odir / fn).exists():
            draw_card(spec, img, odir / fn)
            drawn += 1
        keep.add(fn)
        return f"{site}og/{vid}/{fn}"

    n_sp = len(species)
    book_card = card("book", {"book": True, "meta": f"한국에서 기록된 새 {n_sp}종 · 목과 과의 차례로 엮은 수채 도감"}, None)

    def species_card(s: dict, name: str, kick: list) -> str:
        img = scene(s["id"]) if s["img"]["scene"] else None
        if not img:
            return book_card
        o, f = parent[s["id"]]
        return card(name, {"kicker": kick, "ko": s["ko"], "sci": s["sci"], "sub": s.get("en", ""),
                           "meta": f"{o['ko']} › {f['ko']}" + (f" · Pl. {pl[s['id']]}" if name == "today" else ""),
                           "focus": s.get("focus")}, img)

    def plates(n: dict) -> str:
        ids = [x["id"] for x in (n["children"] if n["rank"] == "family" else [s for f in n["children"] for s in f["children"]])]
        a, b = pl[ids[0]], pl[ids[-1]]
        return f"{len(ids)}종 · Pl. {a}" + (f"–{b}" if b != a else "")

    def group_card(n: dict, up: dict | None) -> str:
        members = n["children"] if n["rank"] == "family" else [s for f in n["children"] for s in f["children"]]
        by = {s["id"]: s for s in members}
        pick = by.get(n.get("rep"))
        if not (pick and pick["img"]["scene"] and scene(pick["id"])):
            pick = next((s for s in members if s["img"]["scene"] and scene(s["id"])), None)
        if not pick:
            return book_card
        rank = ("과", "Familia") if n["rank"] == "family" else ("목", "Ordo")
        meta = (f"{up['ko']} · " if up else f"{len(n['children'])}과 · ") + plates(n)
        return card(n["id"], {"kicker": [(rank[0] + "  ", "sansb", "label"), (rank[1], "la", "label")],
                              "ko": n["ko"], "sci": n["sci"], "meta": meta, "focus": pick.get("focus"), "oval": True}, scene(pick["id"]))

    tpl = (ROOT / "index.html").read_text(encoding="utf-8")
    if not BLOCK.search(tpl):
        raise ValueError("index.html 에 <!-- share --> … <!-- /share --> 칸이 없다")
    intro = book.get("intro", "")
    pages: dict[str, tuple[str, str, str, str]] = {}  # key → (제목, 설명, 배너, 배너 설명)
    for k, nm in NAMES.items():
        pages[k] = (f"{nm} — {title}", clip(intro), book_card, title)
    for o in book["tree"]:
        pages[o["id"]] = (f"{o['ko']} {o['sci']} — {title}", clip(o.get("desc") or plates(o)), group_card(o, None), f"{o['ko']} 대표종")
        for f in o["children"]:
            pages[f["id"]] = (f"{f['ko']} {f['sci']} — {title}", clip(f"{o['ko']} › {f['ko']}. " + (f.get("desc") or plates(f))),
                              group_card(f, o), f"{f['ko']} 대표종")
            for s in f["children"]:
                pages[s["id"]] = (f"{s['ko']} {s['sci']} — {title}",
                                  clip(f"{o['ko']} › {f['ko']}. " + (summaries.get(s["id"]) or s.get("status") or "")),
                                  species_card(s, s["id"], [(f"Pl. {pl[s['id']]}", "sansb", "label")]), f"{s['ko']} 도판")

    t = today_bird(species, day)
    home = block("./", f"{title} — {kicker}", clip(f"오늘의 새, {t['ko']} {t['sci']}. {intro}"), site,
                 species_card(t, "today", [("오늘의 새", "sansb", "red")]), f"오늘의 새 {t['ko']}")
    write_if_changed(ROOT / "index.html", BLOCK.sub(lambda _: home, tpl, count=1))

    vdir = ROOT / vid
    for key, (ttl, desc, image, alt) in pages.items():
        write_if_changed(vdir / key / "index.html",
                         BLOCK.sub(lambda _: block("../../", ttl, desc, f"{site}{vid}/{key}/", image, alt), tpl, count=1))
    for d in vdir.iterdir() if vdir.exists() else []:
        if d.is_dir() and d.name not in pages and [x.name for x in d.iterdir()] == ["index.html"]:
            (d / "index.html").unlink()
            d.rmdir()
    for p in odir.glob("*.jpg"):
        if p.name not in keep:
            p.unlink()
    return drawn


# ───────────── 저장소 README 배너 ─────────────
README_BIRDS = ["aix-galericulata", "alcedo-atthis", "sittiparus-varius", "hirundo-rustica"]


def readme_banner(out: Path, vid: str = "aves") -> None:
    """README 맨 위 배너: 왼쪽에 책 표제, 오른쪽에 도판 넷(3:2 그대로). 그림을 바꾸고 싶을 때만 다시 만든다."""
    bw, bh, cw, ch, gap = 1280, 460, 285, 190, 12
    im = Image.new("RGB", (bw, bh), C["paper"])
    d = ImageDraw.Draw(im)
    n = len([s for o in json.loads((ROOT / "data" / vid / "book.json").read_text(encoding="utf-8"))["tree"]
             for f in o["children"] for s in f["children"]])
    x = 72
    put(d, x, 150, [("조류 도감", font("sansb", 22), C["label"])], track=8)
    put(d, x, 250, [("Aves", font("title", 96), C["ink"]), (" (Korea)", font("title", 96), C["label"])])
    ornament(d, x, 296)
    put(d, x, 352, [(f"한국에서 기록된 새 {n}종", font("sans", 25), C["fade"])])
    put(d, x, 390, [("수채 도판과 동정 도해로 엮은 웹 책", font("sans", 25), C["fade"])])
    x0, y0 = bw - 40 - (2 * cw + gap), (bh - (2 * ch + gap)) // 2
    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), radius=6, fill=255)
    for i, sid in enumerate(README_BIRDS):
        im.paste(cover(ROOT / "img" / vid / f"{sid}.webp", cw, ch, None), (x0 + i % 2 * (cw + gap), y0 + i // 2 * (ch + gap)), mask)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=86, optimize=True, progressive=True)


# ───────────── 자체 점검 ─────────────
def _check() -> None:
    # book.js 의 seeded() 를 node 로 돌린 값
    for n, want in [(20261012, 0.7855095835402608), (20260101, 0.1921404309105128), (20271231, 0.06204715138301253)]:
        assert abs(seeded(n) - want) < 1e-15, (n, seeded(n), want)
    assert in_season({"seen": [4, 5]}, 4) and not in_season({"seen": [4, 5]}, 6)
    assert in_season({"seen": None, "occ": "WV2, P1"}, 4) and not in_season({"seen": None, "occ": "WV2"}, 4)
    assert in_season({"seen": None, "occ": "W2"}, 1) and not in_season({"seen": None, "occ": "W2"}, 6)
    print("share.py 점검 OK")


if __name__ == "__main__":
    import sys
    if "--readme" in sys.argv:  # uv run tools/share.py --readme → .github/banner.jpg
        readme_banner(ROOT / ".github" / "banner.jpg")
    else:
        _check()
