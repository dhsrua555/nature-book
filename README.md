# 한국의 새 — 조류 도감

화면 전체를 책의 펼침면으로 쓰는 웹 도감. 실물 책을 흉내 내기보다 '책'을 짜임새로 삼는다(머리말·쪽 번호·차례·찾아보기·도판 번호, 쪽 넘김).
한국에서 기록된 새를 국립생물자원관 **국가생물종목록(2025)** 의 분류에 따라 목 → 과 → 종 차례로 엮었다.
목록의 597종과 국명이 따로 붙은 아종 12가지, 모두 609항목을 싣는다. 첫 화면에는 날마다 '오늘의 새'가 바뀐다.
GitHub Pages에 그대로 올리는 정적 사이트다(빌드 서버 없음).

## 폴더

```
index.html              책 화면
assets/book.js          마디별 쪽 엮기·라우팅·넘김·찾기·오늘의 새
assets/turn.js          쪽 넘김(가운데 접힌 자리를 축으로 한 장이 돈다)
assets/book.css         화면 전체 펼침면 배치
data/library.json       권 목록(지금은 조류 한 권)
data/aves/volume.json   권 정보, 사실 항목·라벨, 목·과 설명과 대표종
data/aves/species/*.json  종 한 장씩 (손으로 고치는 원본, 609개)
data/aves/notes/*.notes.md  손으로 조사한 21종의 값마다 근거 문장 인용과 URL (검토용)
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
tools/ref/ioc-en.tsv    학명 → IOC 영문명 짝 (tools/ref_en.py 가 만듦)
tools/fetch_nibr.py     국립생물자원관 종 설명·보호 표시 받기 → cache/nibr/ (git 제외)
tools/nibr_entries.py   종 설명으로 종 파일 만들기(묶음 나누기·검사·합치기)
tools/ENTRY_RULES.md    종 설명 원문으로 항목을 쓸 때의 규칙
art/                    삽화 원본·받은 편지함 (git 제외)
cache/                  받아 둔 원문·작업 묶음 (git 제외)
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

- 첫 화면(책 소개 · **오늘의 새**) → 차례 → (목 표제·과 목록 → 과 표제·종 목록 → 종) … → 찾아보기 → 판권.
- 화면 전체가 책이다. 넓은 가로 화면(폭 900px 이상)은 가운데 접힌 자리를 두고 두 쪽, 그 밖에는 한 쪽씩.
  위쪽 머리말에 갈래(차례 › 목 › 과)와 찾기, 아래쪽 꼬리말에 넘김 단추와 도판 번호가 있다.
- 책은 '마디'(첫 화면, 차례, 목, 과, 종, 찾아보기, 판권)를 이은 것이다. 보러 가는 마디만 그때 화면 크기에 맞춰 쪽을 엮으므로 600여 종이어도 가볍다.
- 종 하나: **도판(왼쪽)** → 해설(필요한 만큼) → **동정 도해(왼쪽)와 동정 포인트(오른쪽)가 마주 봄**. 동정 포인트가 없는 종은 도판과 해설만.
- 쪽 수가 화면마다 달라지므로 차례·찾아보기는 **도판 번호(Pl.)** 로 찾는다. 주소는 `#/aves/<종 id>`, 동정 펼침은 `#/aves/<종 id>/id`.
- 넘김: 화면을 옆으로 밀거나(손가락·마우스), ← → 키, 아래 단추. `/` 키는 새 이름 찾기(국명·학명·영문명, 초성 `ㅁㅊㅅ` 도 된다).
  `prefers-reduced-motion` 이면 넘김 동작 없이 바뀐다.
- **오늘의 새**: 한국 시간 날짜로 정해지는 한 종(하루 동안 같다). 해설이 있는 종에서 고르고, 볼 수 있는 달을 아는 종은 이번 달에 보이는 종만 고른다. 도판이 있는 종을 더 자주 고른다. '다른 새'를 누르면 새로 뽑는다.

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
- `"origin": "nibr"` 이 붙은 종은 국립생물자원관 종 설명만을 근거로 정리한 종이다(아래 '609종을 채운 방법'). 손으로 더 조사해 고칠 때는 `origin` 을 지우면 `nibr_entries.py merge` 가 다시 덮어쓰지 않는다.
- `months.breed` 가 `[]` 이면 국내에서 번식하지 않는 종(겨울철새·나그네새 등), `"TODO"` 이면 모름.
- `points[].at` / `label` 은 동정 도해 위 번호·글자 위치(그림 가로·세로 비율 0–1). 아래 검수 모드에서 찍는다.
- `art.*` 는 삽화 프롬프트 재료(영어). 깃 색 묘사가 틀리면 그림이 틀린다.
- 고친 뒤에는 늘 `uv run tools/build.py` → 국명·학명이 목록과 다르거나, 대표종이 그 분류에 없거나, 형식이 어긋나면 오류로 멈춘다. `--todo` 를 붙이면 TODO 위치를 모두 보여 준다.
- 목·과 설명과 대표종(목록 옆 둥근 그림)은 `data/aves/volume.json` 의 `orders`, `families` 에 학명으로 적는다.

**종 추가**: `species/<id>.json` 을 만들고 → `uv run tools/build.py` → `uv run tools/illustrate.py make <id>` → 미리보기에서 검수.

### 609종을 채운 방법

1. `uv run tools/fetch_nibr.py` — 목록의 모든 종에 대해 국립생물자원관 종 설명과 보호 표시(천연기념물, 멸종위기 등급)를 받아 `cache/nibr/` 에 둔다.
   설명이 옛 학명 기록에 달린 종은 그 기록의 보호 표시도 함께 본다(예: 넓적부리도요 Ⅰ급).
2. `uv run tools/ref_en.py` — IOC World Bird List v15.2 에서 학명으로 영문명을 찾는다(속이 바뀐 종은 종소명·명명자로, 못 찾은 몇 종은 손으로 확인).
3. `uv run tools/nibr_entries.py batches` — 원문이 있는 종을 묶음으로 나눈다. 묶음마다 `tools/ENTRY_RULES.md` 규칙대로
   **원문에 있는 사실만** 우리 문장으로 다시 써서 `cache/work/out-NN.json` 을 만든다(원문에 없으면 TODO, 원문이 다른 종을 설명하거나 서로 어긋나면 그 값은 TODO 로 두고 `todo` 에 까닭).
4. `uv run tools/nibr_entries.py check cache/work/out-NN.json` — 몸길이 같은 수와 국내 상태 낱말이 원문에 실제로 있는지 대조한다.
5. `uv run tools/nibr_entries.py merge` → `uv run tools/build.py`.

원문이 없는 종(약 150종, 주로 드물게 찾아오는 새)은 국명·학명·분류·보호 표시만 싣고 '해설을 아직 싣지 못했다'고 밝힌다.

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
동정 도해(plate)는 동정 포인트가 있는 종만 그린다. 그림 재료(art)가 '조사 중'인 종은 건너뛴다.

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
`art/`, `draft/`, `cache/`, `.env` 는 올라가지 않는다. GitHub Actions 는 쓰지 않는다.

그림을 검수해 커밋할 때는 `img/aves/*.webp` 와 함께 `data/aves/book.json` 도 커밋한다(그림이 있다는 표시가 book.json 에 있다).
그림 없이 코드만 올릴 때는 `uv run tools/build.py --tracked` 로 커밋된 그림만 반영한 book.json 을 만든 뒤 올리고, 다시 `uv run tools/build.py` 로 되돌린다.

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
- 해설: 21종은 여러 문헌을 견주어 조사(근거 인용은 `data/aves/notes/`), 나머지는 국립생물자원관 종 설명을 근거로 다시 씀.
- 영문명: IOC World Bird List v15.2 (doi 10.14344/IOC.ML.15.2).
- 종마다 쓴 출처는 각 종 파일 `sources` 와 책의 해설 끝에 있다.
