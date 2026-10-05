# 한국의 새 — 조류 도감

누렇게 바랜 옛 책처럼 넘겨 보는 웹 도감. 한국에서 기록된 새를 국립생물자원관 **국가생물종목록(2025)** 의
분류에 따라 목 → 과 → 종 차례로 엮고, 종마다 서식지를 배경으로 한 수채 도판과 글자 없는 동정 도해를 싣는다.
GitHub Pages에 그대로 올리는 정적 사이트다(빌드 서버 없음).

## 폴더

```
index.html              책 화면
assets/book.js          쪽 엮기·라우팅·넘김 제어
assets/curl.js          책장 넘김(접힌 선 계산, 그림자, 표지 3D 회전)
assets/book.css         종이·표지·쪽 배치
data/library.json       권 목록(지금은 조류 한 권)
data/aves/volume.json   권 정보, 사실 항목·라벨, 목·과 설명과 대표종
data/aves/species/*.json  종 한 장씩 (손으로 고치는 원본)
data/aves/notes/*.notes.md  종 자료의 값마다 근거 문장 인용과 URL (검토용)
data/aves/book.json     tools/build.py 가 만드는 화면용 목차 (고치지 않음)
img/aves/<id>.webp      도판(서식지 배경, 3:2)
img/aves/<id>.id.webp   동정 도해(글자 없음, 2:3)
tools/build.py          국가생물종목록 대조·검증 → book.json
tools/illustrate.py     삽화 생성·가져오기(OpenAI 이미지 API)
tools/style.toml        삽화 프롬프트 템플릿(하나로 톤 통일)
tools/WORK.md           ChatGPT Work가 삽화를 그릴 때 따르는 절차
tools/serve.py          미리보기 서버(검수 모드 저장 포함)
tools/check.html        전 쪽 점검(넘침·깨진 링크·그림·넘김 동작)
tools/ref/nibr-aves-2025.tsv  국가생물종목록 조류 617행(기준표)
art/                    삽화 원본·받은 편지함 (git 제외)
draft/                  처음 받은 초안 (git 제외)
```

준비물은 [uv](https://docs.astral.sh/uv/) 하나다. `uv run` 이 파이썬과 필요한 꾸러미를 알아서 받는다.

## 미리보기

```
uv run tools/serve.py          # http://localhost:8000
```

`index.html` 을 더블클릭하면 브라우저가 자료 읽기를 막으므로 꼭 서버로 연다.
`http://localhost:8000/tools/check.html` 을 열면 모든 쪽을 넓은 화면·좁은 화면으로 펼쳐 보며 넘친 쪽, 깨진 링크, 빠진 그림, 넘김 오류를 점검한다(끝에 `RESULT OK`).

## 책의 짜임

- 표지 → 면지 → 속표지 → 일러두기 → 차례 → (목 표제·과 목록 → 과 표제·종 목록 → 종) … → 찾아보기 → 판권.
- 넓은 화면은 펼친 두 쪽, 좁은 화면(폭 760px 미만)은 한 쪽씩. 쪽은 화면 크기에 맞춰 다시 엮는다.
- 종 하나: **도판(왼쪽)** → 해설(필요한 만큼 이어지는 쪽) → **동정 도해(왼쪽)와 동정 포인트(오른쪽)가 마주 봄**. 해설이 길어 왼쪽에서 끝나면 뒤쪽 글(어린새·비슷한 종)을 당겨 채워, 도해와 포인트가 늘 한 펼침에 오게 한다.
- 쪽 수가 화면마다 달라지므로 차례·찾아보기는 **도판 번호(Pl.)** 로 찾는다. 주소는 `#/aves/<종 id>`, 동정 펼침은 `#/aves/<종 id>/id`.
- 넘김: 쪽 모서리를 끌거나(손가락·마우스), ← → 키, 아래 단추. 마우스를 모서리에 대면 살짝 들린다. `prefers-reduced-motion` 이면 넘김 동작 없이 바뀐다.

넘김 효과는 영상이 아니라 계산으로 그린다. 모서리가 지나는 점과 원래 모서리의 수직이등분선을 접힌 선으로 삼아
앞면을 그 선에서 자르고, 다음 쪽 내용을 선에 대해 뒤집어 붙인 뒤 그림자 띠를 얹는다(turn.js와 같은 방식).
실제 쪽 내용이 그대로 접히고, 손으로 끌 수 있고, 어떤 화면 크기에서도 선명하다. 표지만 단단한 판처럼 3D로 돈다.

## 종 자료

종 파일 하나가 한 종이다. 목·과는 적지 않는다 — `build.py` 가 학명으로 국가생물종목록에서 찾아 자동으로 묶고,
목·과·종의 차례도 그 목록의 일련번호를 따른다.

```jsonc
{
  "id": "falco-subbuteo",            // 파일 이름과 같게 (속명-종소명)
  "ko": "새호리기", "sci": "Falco subbuteo", "author": "Linnaeus, 1758",
  "en": "Eurasian Hobby", "ktsn": 120000001575,
  "length": "약 34cm", "wingspan": "TODO",
  "status": "여름철새", "habitat": "…", "protect": ["멸종위기 야생생물 Ⅱ급"],
  "months": { "seen": [4,5,6,7,8,9,10], "breed": [6,7,8], "note": "…" },
  "summary": "…", "sexes": { "alike": false, "male": "…", "female": "…" }, "young": "…",
  "points": [ { "ko": "청회색 등과 날개", "en": "slate-grey back and wings", "at": [0.5, 0.2], "label": [0.3, 0.1] } ],
  "similar": [ { "ko": "매", "how": "…" } ],
  "art": { "subject": "…", "pose": "…", "scene": "…", "views": ["…"], "focus": [0.5, 0.45] },
  "sources": [ { "title": "…", "url": "…", "used": "몸길이·상태" } ],
  "todo": ["확인하지 못한 점"]
}
```

- **확인하지 못한 값은 `"TODO"`** 로 둔다. 화면에는 ‘조사 중’으로 보인다. 지어내지 않는다.
- `points[].at` / `label` 은 동정 도해 위 번호·글자 위치(그림 가로·세로 비율 0–1). 아래 검수 모드에서 찍는다.
- `art.*` 는 삽화 프롬프트 재료(영어). 깃 색 묘사가 틀리면 그림이 틀린다.
- 고친 뒤에는 늘 `uv run tools/build.py` → 국명·학명이 목록과 다르거나, 대표종이 그 분류에 없거나, 형식이 어긋나면 오류로 멈춘다. `--todo` 를 붙이면 TODO 위치를 모두 보여 준다.
- 목·과 설명과 대표종(목록 옆 둥근 그림)은 `data/aves/volume.json` 의 `orders`, `families` 에 학명으로 적는다.

**종 추가**: `species/<id>.json` 을 만들고 → `uv run tools/build.py` → `uv run tools/illustrate.py make <id>` → 미리보기에서 검수.

## 삽화

```
uv run tools/illustrate.py status                     # 종마다 도판·도해가 있는지, 프롬프트 재료가 다 찼는지
uv run tools/illustrate.py prompt falco-subbuteo      # 완성된 프롬프트 보기
uv run tools/illustrate.py make falco-subbuteo --quality low   # 한 종 시험(싸게)
uv run tools/illustrate.py make                       # 빠진 그림 모두 (4장 이상이면 확인을 묻는다)
uv run tools/illustrate.py make --kind plate          # 동정 도해만
uv run tools/illustrate.py make --ref art/ref/좋은그림.png    # 기준 그림으로 톤 맞추기
uv run tools/illustrate.py make falco-subbuteo --force       # 다시 그리기
```

- 그림이 없는 종만 그린다. 원본 PNG는 `art/raw/` 에 날짜를 붙여 남고(git 제외), 웹용은 가로 1000px webp 로 `img/aves/` 에 들어간다. 끝나면 `build.py` 가 저절로 돈다.
- 톤은 `tools/style.toml` 한 곳에서 관리한다. 마음에 든 그림을 `art/ref/` 에 두고 `[scene] ref = ["art/ref/…png"]` 처럼 적어 두면 매번 기준 그림으로 함께 넘긴다.
- 동정 도해에는 글자를 넣지 않는다(이미지 모델은 글자·사실을 틀리게 쓸 수 있다). 번호와 설명은 종 파일의 `points` 에서 웹이 얹는다.
- 자동 커밋은 없다. 그린 뒤 미리보기로 살펴보고 직접 커밋한다.

### GPT(OpenAI 이미지 API) 연결

ChatGPT 구독(Plus 등)과 API 요금은 따로다. 스크립트로 그리려면 API 계정이 필요하다.

1. platform.openai.com 에 ChatGPT 계정으로 로그인한다.
2. **조직 인증(Organization verification)** 을 마친다. GPT Image 모델은 인증한 조직만 쓸 수 있다(Settings → Organization).
3. **Billing** 에서 크레딧을 조금 충전한다(시험은 몇 달러면 충분).
4. **API keys** 에서 새 키를 만든다.
5. 프로젝트 맨 위에 `.env` 파일을 만들고 한 줄 적는다 (`.gitignore` 에 들어 있어 올라가지 않는다):
   ```
   OPENAI_API_KEY=sk-...
   ```
   또는 PowerShell 에서 `setx OPENAI_API_KEY "sk-..."` 후 새 터미널.
6. `uv run tools/illustrate.py make falco-subbuteo --kind scene --quality low` 로 한 장 시험.

모델은 `tools/style.toml` 의 `model`(기본 `gpt-image-2.5-flare`, 기준 그림 편집이 중요하면 `gpt-image-2.5-sunburst`).
값은 크기·품질에 따라 다르다. 참고로 gpt-image-2 의 1536×1024 한 장은 low 약 $0.005, medium 약 $0.04, high 약 $0.17(2026년 10월 OpenAI 문서 기준).
21종 × 2장을 high 로 그리면 대략 7달러 안팎이다. 정확한 값은 OpenAI 가격표를 확인한다.

### ChatGPT Work로 자동으로 그릴 때 (API 없이)

ChatGPT 데스크톱 앱의 Work는 이 폴더에서 명령을 실행하고 앱 안의 이미지 생성(`$imagegen`, gpt-image-2)으로 그림을 그릴 수 있다.
요금은 API가 아니라 요금제 사용량에서 나간다(그림은 일반 대화보다 사용량을 3–5배 빨리 쓴다).

1. Work 탭 → **프로젝트 선택**에서 이 폴더(`Nature Book`)를 고르고, 접근 권한을 명령 실행이 되는 수준(전체 액세스)으로 둔다.
2. 이렇게 맡긴다: `tools/WORK.md 대로 삽화를 4장 그려 줘.`
   Work가 `uv run tools/illustrate.py queue --limit 4` 로 남은 작업과 프롬프트를 받아 그리고, `art/inbox/` 에 저장한 뒤 `import` 까지 돌린다.
3. 매일 조금씩 돌리려면: `매일 오전 9시에 tools/WORK.md 대로 4장씩 그려 줘.` (예약 작업은 사람 없이 돈다)
4. 아침에 `uv run tools/serve.py` 로 살펴보고, 마음에 들지 않는 그림은 `img/` 에서 지운 뒤 다시 맡긴다. 커밋은 직접.

### ChatGPT 앱에서 손으로 그릴 때

자동화 없이 ChatGPT 대화창에서 그려도 된다.

1. `uv run tools/illustrate.py prompt <종 id>` 로 나온 프롬프트를 ChatGPT에 붙여 넣는다(도판은 가로 3:2, 동정 도해는 세로 2:3으로 요청).
2. 받은 그림을 `art/inbox/<종 id>.png`(도판) 또는 `art/inbox/<종 id>.id.png`(동정 도해)로 저장한다.
3. `uv run tools/illustrate.py import` → webp 로 줄여 `img/aves/` 에 넣고 원본은 `art/raw/` 로 옮긴다.

## 검수 모드

`http://localhost:8000/?edit` 로 열면

- **동정 도해**: 오른쪽 위 판에서 항목을 고르고 그림을 누르면 번호 위치(at), 한 번 더 누르면 글자 위치(label)가 정해진다.
- **도판**: 그림을 누르면 목록·차례의 둥근 그림이 그 점을 가운데로 잘린다(focus).
- **저장**을 누르면 `tools/serve.py` 가 종 파일을 고쳐 쓴다. 그다음 `uv run tools/build.py`.

## 배포 (GitHub Pages)

정적 파일 그대로 올린다. 저장소의 Settings → Pages → Deploy from a branch → `main` / `(root)`.
`art/`, `draft/`, `.env` 는 올라가지 않는다. GitHub Actions 는 쓰지 않는다.

## 다른 생물군으로 넓히기

1. 국가생물종목록에서 그 분류군 목록을 받아 `tools/ref/nibr-<id>-2025.tsv` 로 둔다(같은 열 이름).
2. `data/<id>/volume.json` (예: `insecta`) — `fields`(사실 항목: 곤충이면 날개 편 길이·출현 시기 등)와 `labels`(관찰 시기 → 출현 시기, 어린새 → 애벌레 …)를 그 생물군에 맞게.
3. `data/<id>/species/*.json`, `img/<id>/`.
4. `data/library.json` 의 `volumes` 에 추가. 주소 `#/<id>/…` 로 그 권이 열린다.
5. `tools/style.toml` 의 프롬프트는 새를 전제로 쓰였으므로 생물군에 맞는 템플릿을 덧붙인다.

## 기준과 출처

- 분류·국명·학명: 국립생물자원관 국가생물종목록 2025, 조류(species.nibr.go.kr 목록 내려받기, 2026-10-04).
  이 목록은 백로과·저어새과를 황새목에, 수리과를 매목에 두며, 박새를 *Parus cinereus* 로 적는다.
- 보호 등급: 같은 누리집의 종 정보(천연기념물, 멸종위기 야생생물 Ⅰ·Ⅱ급).
- 종마다 쓴 출처는 각 종 파일 `sources` 와 책의 해설 끝에 있다.
