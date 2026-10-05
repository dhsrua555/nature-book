# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "pillow>=11.0"]
# ///
"""도감 삽화 만들기.

종 파일을 읽어 아직 그림이 없는 종만 OpenAI 이미지 API로 그리고,
웹용 webp(가로 약 1000px)로 줄여 img/<권>/ 에 둔다. 원본 PNG는 art/raw/ 에 남는다(git 제외).
그림은 두 가지다.
  scene  서식지를 배경으로 한 도판        → img/<권>/<id>.webp
  plate  글자 없는 동정 도해(번호는 웹에서) → img/<권>/<id>.id.webp

    uv run tools/illustrate.py status                       # 무엇이 비었는지
    uv run tools/illustrate.py prompt falco-subbuteo        # 완성된 프롬프트 보기(ChatGPT에 붙여 넣어도 됨)
    uv run tools/illustrate.py make falco-subbuteo --quality low   # 한 종 시험
    uv run tools/illustrate.py make                         # 빠진 그림 모두
    uv run tools/illustrate.py make --kind plate --ref art/ref/plate.png   # 기준 그림으로 톤 맞추기
    uv run tools/illustrate.py import                       # art/inbox/ 에 넣은 그림을 webp로
    uv run tools/illustrate.py queue --limit 4              # 남은 작업 목록(JSON) — ChatGPT Work가 tools/WORK.md 대로 쓴다

API 키는 환경 변수 OPENAI_API_KEY 또는 프로젝트 맨 위 .env 파일(OPENAI_API_KEY=...)에서 읽는다.
그린 뒤에는 브라우저에서 살펴보고 직접 커밋한다(자동 커밋 없음).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLE = ROOT / "tools" / "style.toml"
RAW = ROOT / "art" / "raw"
INBOX = ROOT / "art" / "inbox"
KINDS = ("scene", "plate")


# ───────────────────────── 자료 ─────────────────────────
def volumes() -> list[str]:
    lib = json.loads((ROOT / "data" / "library.json").read_text(encoding="utf-8"))
    return [v["id"] for v in lib["volumes"]]


def all_species() -> list[tuple[str, dict]]:
    out = []
    for vid in volumes():
        for f in sorted((ROOT / "data" / vid / "species").glob("*.json")):
            out.append((vid, json.loads(f.read_text(encoding="utf-8"))))
    return out


def web_path(vid: str, sid: str, cfg: dict, kind: str) -> Path:
    return ROOT / "img" / vid / f"{sid}{cfg[kind]['suffix']}.webp"


def has_todo(v) -> bool:
    if isinstance(v, str):
        return "TODO" in v
    if isinstance(v, list):
        return any(has_todo(x) for x in v)
    if isinstance(v, dict):
        return any(has_todo(x) for x in v.values())
    return False


def build_prompt(cfg: dict, sp: dict, kind: str) -> str:
    art = sp.get("art", {})
    views = art.get("views", [])
    fields = {
        "style": cfg["style"].strip(),
        "ko": sp["ko"], "en": sp["en"], "sci": sp["sci"],
        "subject": art.get("subject", "").rstrip(". "), "pose": art.get("pose", "").rstrip(". "), "scene": art.get("scene", "").rstrip(". "),
        "views": "; ".join(f"({i}) {v}" for i, v in enumerate(views, 1)),
        "points": "; ".join(p["en"] for p in sp.get("points", []) if p.get("en")),
    }
    return cfg[kind]["prompt"].format(**fields).strip()


def prompt_problems(sp: dict, kind: str) -> list[str]:
    art = sp.get("art", {})
    need = ["subject", "pose", "scene"] if kind == "scene" else ["views"]
    bad = [f"art.{k}" for k in need if not art.get(k) or has_todo(art.get(k))]
    if has_todo(sp.get("en")):
        bad.append("en")
    if kind == "plate" and any(has_todo(p.get("en")) for p in sp.get("points", [])):
        bad.append("points[].en")
    return bad


# ───────────────────────── 이미지 ─────────────────────────
def to_webp(data: bytes, dest: Path, width: int, quality: int) -> tuple[int, int]:
    from PIL import Image

    im = Image.open(BytesIO(data))
    im = im.convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "WEBP", quality=quality, method=6)
    return im.size


def load_env_key() -> None:
    if os.environ.get("OPENAI_API_KEY"):
        return
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            if k.strip() == "OPENAI_API_KEY" and v.strip():
                os.environ["OPENAI_API_KEY"] = v.strip().strip('"').strip("'")


def rebuild() -> None:
    sys.stdout.flush()
    subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")], check=False)


# ───────────────────────── 명령 ─────────────────────────
def cmd_status(cfg: dict, args) -> int:
    rows = all_species()
    print(f"{'종 id':<28} {'국명':<10} 도판 도해  프롬프트")
    for vid, sp in rows:
        marks = ["✓" if web_path(vid, sp["id"], cfg, k).exists() else "·" for k in KINDS]
        probs = sorted(set(prompt_problems(sp, "scene") + prompt_problems(sp, "plate")))
        print(f"{sp['id']:<28} {sp['ko']:<10} {marks[0]:^4} {marks[1]:^4}  {'준비됨' if not probs else '비어 있음: ' + ', '.join(probs)}")
    return 0


def cmd_prompt(cfg: dict, args) -> int:
    found = {sp["id"]: sp for _, sp in all_species()}
    for sid in args.ids:
        if sid not in found:
            print(f"없는 종 id: {sid}", file=sys.stderr)
            return 1
        for kind in (KINDS if args.kind == "both" else (args.kind,)):
            print(f"── {sid} · {kind} · {cfg[kind]['size']} ──")
            print(build_prompt(cfg, found[sid], kind))
            print()
    return 0


def pick_targets(cfg: dict, args) -> list[tuple[str, dict, str]]:
    rows = all_species()
    known = {sp["id"] for _, sp in rows}
    unknown = [i for i in (args.ids or []) if i not in known]
    if unknown:
        raise SystemExit(f"없는 종 id: {', '.join(unknown)}")
    kinds = KINDS if args.kind == "both" else (args.kind,)
    out = []
    for vid, sp in rows:
        if args.ids and sp["id"] not in args.ids:
            continue
        for kind in kinds:
            if web_path(vid, sp["id"], cfg, kind).exists() and not args.force:
                continue
            probs = prompt_problems(sp, kind)
            if probs:
                print(f"건너뜀 {sp['id']} {kind}: 종 파일에 {', '.join(probs)} 가 비어 있다")
                continue
            out.append((vid, sp, kind))
    return out[: args.limit] if args.limit else out


def cmd_make(cfg: dict, args) -> int:
    model = args.model or os.environ.get("IMAGE_MODEL") or cfg["model"]
    quality = args.quality or cfg["quality"]
    targets = pick_targets(cfg, args)
    if not targets:
        print("새로 그릴 그림이 없다. 다시 그리려면 --force")
        return 0
    print(f"{len(targets)}장 그릴 예정 · 모델 {model} · 품질 {quality}")
    for vid, sp, kind in targets:
        print(f"  {sp['id']} ({sp['ko']}) {kind} {cfg[kind]['size']}")
    if args.dry_run:
        for vid, sp, kind in targets:
            print(f"\n── {sp['id']} · {kind} ──\n{build_prompt(cfg, sp, kind)}")
        return 0
    if len(targets) > 3 and not args.yes:
        if input("API 요금이 듭니다. 계속할까요? [y/N] ").strip().lower() not in ("y", "yes", "ㅛ"):
            return 1

    load_env_key()
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY 가 없다. 환경 변수로 넣거나 프로젝트 맨 위 .env 파일에 OPENAI_API_KEY=sk-... 로 적는다.", file=sys.stderr)
        return 1
    from openai import OpenAI

    client = OpenAI()
    RAW.mkdir(parents=True, exist_ok=True)
    failed = []
    for n, (vid, sp, kind) in enumerate(targets, 1):
        refs = [ROOT / r for r in cfg[kind].get("ref", [])] + [Path(r) for r in (args.ref or [])]
        missing = [str(r) for r in refs if not r.exists()]
        if missing:
            print(f"기준 그림이 없다: {', '.join(missing)}", file=sys.stderr)
            return 1
        prompt = build_prompt(cfg, sp, kind)
        if refs:
            prompt += "\n" + cfg["ref_note"].strip()
        print(f"[{n}/{len(targets)}] {sp['ko']} {kind} … ", end="", flush=True)
        try:
            if refs:
                files = [open(r, "rb") for r in refs]
                try:
                    res = client.images.edit(model=model, image=files, prompt=prompt, size=cfg[kind]["size"], quality=quality)
                finally:
                    for f in files:
                        f.close()
            else:
                res = client.images.generate(model=model, prompt=prompt, size=cfg[kind]["size"], quality=quality)
            data = base64.b64decode(res.data[0].b64_json)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            (RAW / f"{sp['id']}{cfg[kind]['suffix']}-{stamp}.png").write_bytes(data)
            w, h = to_webp(data, web_path(vid, sp["id"], cfg, kind), cfg["web_width"], cfg["webp_quality"])
            print(f"완료 ({w}×{h})")
        except Exception as e:  # 한 장이 실패해도 나머지는 계속
            print(f"실패: {e}")
            failed.append(sp["id"])
    rebuild()
    if failed:
        print(f"\n실패: {' '.join(sorted(set(failed)))}\n다시: uv run tools/illustrate.py make {' '.join(sorted(set(failed)))}")
        return 1
    print("\n끝. uv run tools/serve.py 로 열어 살펴본 뒤 마음에 들면 직접 커밋한다.")
    return 0


def cmd_queue(cfg: dict, args) -> int:
    """API 대신 ChatGPT Work(데스크톱 앱)가 그릴 때 쓰는 작업 목록. 그림마다 저장할 경로와 완성된 프롬프트."""
    args.ids = args.ids or []
    args.force = False
    jobs = []
    for vid, sp, kind in pick_targets(cfg, args):
        suffix = cfg[kind]["suffix"]
        inbox = INBOX / f"{sp['id']}{suffix}.png"
        if inbox.exists():  # 이미 그려 두고 import만 안 한 것
            continue
        w, h = cfg[kind]["size"].split("x")
        jobs.append({
            "id": sp["id"], "ko": sp["ko"], "kind": kind,
            "size": cfg[kind]["size"], "orientation": "landscape" if int(w) > int(h) else "portrait",
            "save_to": inbox.relative_to(ROOT).as_posix(),
            "refs": [r for r in cfg[kind].get("ref", [])],
            "prompt": build_prompt(cfg, sp, kind),
        })
    print(json.dumps(jobs, ensure_ascii=False, indent=1))
    return 0


def cmd_import(cfg: dict, args) -> int:
    """art/inbox/<id>.png(도판) · <id>.id.png(동정 도해)를 웹용으로 옮긴다. ChatGPT에서 받은 그림을 넣을 때 쓴다."""
    known = {sp["id"]: vid for vid, sp in all_species()}
    files = [f for f in sorted(INBOX.glob("*")) if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    if not files:
        print(f"{INBOX.relative_to(ROOT)} 가 비어 있다. <종 id>.png 또는 <종 id>.id.png 로 넣는다.")
        return 0
    RAW.mkdir(parents=True, exist_ok=True)
    bad = 0
    for f in files:
        stem = f.stem
        kind = "plate" if stem.endswith(cfg["plate"]["suffix"]) and cfg["plate"]["suffix"] else "scene"
        sid = stem[: -len(cfg["plate"]["suffix"])] if kind == "plate" else stem
        if sid not in known:
            print(f"건너뜀 {f.name}: 그런 종 id가 없다")
            bad += 1
            continue
        dest = web_path(known[sid], sid, cfg, kind)
        if dest.exists() and not args.force:
            print(f"건너뜀 {f.name}: {dest.relative_to(ROOT)} 가 이미 있다 (--force 로 바꿈)")
            continue
        w, h = to_webp(f.read_bytes(), dest, cfg["web_width"], cfg["webp_quality"])
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.move(str(f), RAW / f"{stem}-{stamp}{f.suffix.lower()}")
        print(f"{f.name} → {dest.relative_to(ROOT)} ({w}×{h})")
    rebuild()
    return 1 if bad else 0


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(errors="replace")
    cfg = tomllib.loads(STYLE.read_text(encoding="utf-8"))
    ap = argparse.ArgumentParser(description="도감 삽화 만들기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="종별 그림·프롬프트 준비 상태")
    p = sub.add_parser("prompt", help="완성된 프롬프트 출력")
    p.add_argument("ids", nargs="+")
    p.add_argument("--kind", choices=[*KINDS, "both"], default="both")
    m = sub.add_parser("make", help="빠진 그림을 API로 그리기")
    m.add_argument("ids", nargs="*", help="이 종만 (없으면 전부)")
    m.add_argument("--kind", choices=[*KINDS, "both"], default="both")
    m.add_argument("--force", action="store_true", help="이미 있는 그림도 다시 그림")
    m.add_argument("--ref", nargs="*", help="톤을 맞출 기준 그림 파일(여러 장 가능)")
    m.add_argument("--model", help=f"모델 (기본 {cfg['model']}, 환경 변수 IMAGE_MODEL)")
    m.add_argument("--quality", choices=["low", "medium", "high", "xhigh", "max", "auto"])
    m.add_argument("--limit", type=int, help="이번에 그릴 최대 장 수")
    m.add_argument("--dry-run", action="store_true", help="API를 부르지 않고 프롬프트만")
    m.add_argument("--yes", "-y", action="store_true", help="확인 묻지 않음")
    q = sub.add_parser("queue", help="남은 그림 작업을 JSON으로(ChatGPT Work용)")
    q.add_argument("ids", nargs="*")
    q.add_argument("--kind", choices=[*KINDS, "both"], default="both")
    q.add_argument("--limit", type=int, help="최대 장 수")
    i = sub.add_parser("import", help="art/inbox 의 그림을 webp로 옮기기")
    i.add_argument("--force", action="store_true", help="이미 있는 그림을 바꿈")
    args = ap.parse_args()
    return {"status": cmd_status, "prompt": cmd_prompt, "make": cmd_make, "queue": cmd_queue, "import": cmd_import}[args.cmd](cfg, args)


if __name__ == "__main__":
    sys.exit(main())
