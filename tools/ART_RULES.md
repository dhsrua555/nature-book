# 그림 프롬프트용 종별 형태 정보 쓰기

`tools/art_profiles.py batches` 가 만든 묶음(`cache/art/batch-NN.json`)의 종마다,
이미지 모델이 **그 종을 실제와 같게** 그리도록 영어 형태 정보를 써서 `cache/art/out-NN.json` 에 담는다.
이 글은 책에 실리지 않고 그림 프롬프트(`tools/style.toml`)에만 들어간다.

이미지 모델은 "정확하게 그려라" 같은 일반 지시로는 종마다 다른 체형, 부리 길이와 굽은 정도, 다리 길이,
철·나이·암수에 따른 깃을 맞추지 못한다(예: 민물도요를 붉은갯도요처럼 길고 크게 휜 부리로 그렸다).
그래서 **종마다 그 종만의 특징을 구체적으로** 적는다. 모든 종에 똑같이 붙는 말("정확하게", "사실적으로")은 쓰지 않는다.

## 근거와 정확성

1. 근거는 묶음에 든 책 자료(`points`, `sexes`, `young`, `similar`, `length`, `status`, `habitat`),
   국립생물자원관 원문(`nibr_text`), 그리고 **현장 조류 도감에 널리 실린 식별 특징**(Birds of East Asia, Collins 등의 수준)이다.
2. **확실히 아는 것만 쓴다.** 그 종(한국에 오는 개체군)에 대해 자신 없는 세부(어린새 깃, 암컷 무늬, 홍채 색 등)는 빼고 쓴다.
   지어내느니 빠뜨리는 편이 낫다.
3. 종 전체를 자신 있게 묘사할 수 없으면(드문 아종, 분류가 엇갈리는 종 등) `confidence: "low"` 로 두고 다른 칸은 쓰지 않는다.
   그 종은 그림 차례에서 빠진다.
4. 수치는 책의 `length` 만 쓴다. 다른 길이·무게를 지어 넣지 않는다.
   비율("부리가 머리 길이보다 조금 길다", "날개 끝이 꼬리 끝에 닿는다")은 도감에 널리 실린 것만.
5. 책 자료(동정 포인트·암수·어린새)가 실제와 어긋난다고 판단되면 프롬프트는 실제대로 쓰고, `notes` 에 무엇이 어긋나는지 한국어로 적는다(사람이 확인한다).
6. 한국에 오는 개체군이 생김새가 다른 아종이면 그 아종을 묘사한다. 아종 학명은 확실할 때만 적는다.

## 결과 꼴

`cache/art/out-NN.json` 은 묶음의 모든 종을 같은 순서로 담은 JSON 배열이다.

```json
{
  "id": "calidris-alpina",
  "confidence": "high",
  "subject": "...",
  "build": "...",
  "views": ["...", "..."],
  "avoid": ["...", "..."],
  "pose": "필요할 때만",
  "scene": "필요할 때만",
  "notes": "필요할 때만, 한국어"
}
```

- `confidence`: `high`(잘 알려진 종, 자신 있음) · `medium`(전체는 자신 있으나 일부 세부를 뺐음) · `low`(위 3번, `id`·`confidence`·`notes` 만).
- **subject** (300–900자): 도판(서식지 그림) 주인공 한 마리.
  `"<English name> (<학명>), <나이·암수·철>: …"` 로 시작해 머리 → 등·날개 → 아랫면 → 꼬리 순으로 깃 무늬와 색,
  이어서 부리(색은 부위별로), 홍채·눈테·맨살, 다리 색.
  **철이 도판의 배경과 맞아야 한다**: 한국에서 그 깃을 볼 수 있는 달과 `art_now.scene`(또는 새로 쓴 scene)의 계절이 같게.
  어긋나면 깃을 바꾸거나 scene 의 계절을 바꾸고 `notes` 에 적는다(예: 겨울 갯벌의 민물도요는 겨울깃).
- **build** (250–700자): 크기와 체형. 반드시 다음을 그 종에 맞게:
  - 크기: 책의 몸길이와 익숙한 새와의 견줌(참새, 직박구리, 비둘기, 까마귀, 청둥오리, 왜가리 등).
  - 전체 모양과 자세(통통한·날씬한, 서 있는 각도), 머리 모양(댕기 유무), 목 길이.
  - 부리: 머리 길이에 견준 길이, 모양(곧음·아래로 휨·위로 휨·갈고리·원뿔·주걱), 굵기. 휘었다면 어디서부터 얼마나.
  - 다리: 길이, 정강이 드러남, 색, 필요하면 발(물갈퀴·판족).
  - 날개: 앉았을 때 날개 끝이 꼬리의 어디까지 오는지, 날 때의 모양과 무늬.
  - 꼬리: 몸에 견준 길이, 모양(각진·갈라진·쐐기·둥근), 무늬, 버릇(까딱임 등).
- **views** (도해, 각 80–350자): `"<나이·암수·철>, <각도·자세>: <꼭 보여야 할 특징>"`.
  - 지금 `art_now.views` 가 있으면 그 순서와 뜻을 살려 자세히 쓴다. `drawn.callouts` 가 true 면 **개수와 순서를 바꾸지 않는다**(번호 위치를 이미 찍었다).
  - 자세는 실제 새가 하는 자연스러운 모습으로. 머리는 몸과 같은 방향(고개를 뒤로 비튼 모습 금지),
    나는 모습은 "위에서 본"·"아래에서 본"을 밝히고 머리·몸·꼬리가 한 줄로.
  - 책의 `points`(동정 포인트)가 모두 어느 모습에서든 보여야 한다.
  - `points` 가 없는 종은 도해를 그리지 않으므로 `[]`.
- **avoid** (2–5개, 각 200자 안): 이 종을 그릴 때 저지르기 쉬운 **구체적인** 잘못. "Do not …" 로.
  닮은 종의 특징(이유와 함께), 이미지 모델이 흔히 넣는 일반적인 새 모습(없는 댕기, 없는 날개띠, 틀린 부리 색) 등.
- **pose** · **scene**: `art_now` 의 것이 비었거나(TODO) 계절을 바로잡아야 할 때만 쓴다.
  pose 는 그 종다운 행동 한 줄, scene 은 한국의 서식지·계절·빛 한 줄 + "no people, buildings or text".
- 영어 칸에 한글을 쓰지 않는다. 화풍·종이·글자 금지 같은 말은 쓰지 않는다(공통 템플릿에 있다).

## 예 (민물도요)

```json
{
  "id": "calidris-alpina",
  "confidence": "high",
  "subject": "Dunlin (Calidris alpina), adult in winter (non-breeding) plumage, as seen on Korean tidal flats from October to March: plain grey-brown upperparts with fine dark shaft streaks, head and neck grey-brown with a faint whitish supercilium, a soft grey-brown wash and fine streaks across the breast, the rest of the underparts clean white; black bill; dark eye; black legs.",
  "build": "Small, compact, round-bodied sandpiper, 17–21cm, a little larger than a sparrow; short neck, rather hunched when feeding. Bill black, clearly longer than the head, straight for most of its length and drooping gently only towards the tip. Legs black, medium length. At rest the wingtips reach about the tail tip. In flight a narrow white wing-bar and a dark centre to the rump and tail with white sides.",
  "views": [
    "adult breeding plumage (April–May), side view standing: rufous-and-black scalloped back and crown, finely streaked whitish breast, large solid black patch on the belly, gently drooping black bill, black legs",
    "adult winter plumage, side view standing: plain grey-brown upperparts, grey-brown breast wash, all-white belly, same bill and legs"
  ],
  "avoid": [
    "Do not paint a long, evenly curved bill — that is Curlew Sandpiper (Calidris ferruginea); the Dunlin's bill droops only near the tip.",
    "Do not give it a white rump patch (Curlew Sandpiper).",
    "Do not show the black belly patch on winter birds; it is breeding plumage only.",
    "Do not paint greenish or yellow legs."
  ],
  "notes": "도판 subject 를 여름깃에서 겨울깃으로 바꿈(배경이 겨울 갯벌)"
}
```

## 끝내기

`uv run tools/art_profiles.py check cache/art/out-NN.json` 이 `오류 0` 이 될 때까지 고친다.

## 더 지킬 점 (2026-10-09 추가)

- **한국에 오는 개체군 기준.** 유럽의 지명아종과 깃이 다른 종이 많다. 예: 어치는 한국 개체가 적갈색 머리, 회색 등, 검은 눈이다
  (유럽 개체의 줄무늬 흰 정수리, 분홍빛 등, 옅은 눈이 아니다).
- **잠깐의 상태를 쓰지 않는다.** "깃을 자주 세운다", "부풀린다" 같은 말은 이미지 모델이 늘 그런 모습으로 과장해 그린다.
  늘 있는 댕기·장식깃만 쓴다. 댕기가 없는 종은 "no crest; the crown feathers lie flat" 처럼 분명히 쓴다.
- **marks** (선택): 도해 프롬프트에는 책의 동정 포인트 영어(`points[].en`)가 "꼭 보일 특징"으로 그대로 들어간다.
  그 말이 실제와 어긋나거나 그림을 틀리게 이끌면, `marks` 에 같은 순서·같은 부위를 가리키는 바른 영어를 적는다
  (개수는 동정 포인트와 같게). 책의 글은 그대로 두고 그림만 바르게 그리기 위한 것이다.

## 사진으로 확인하기 (verify)

`tools/art_profiles.py vbatches` 가 만든 `cache/art/vbatch-NN.json` 의 종마다, 실제 사진으로 위 형태 정보를 확인하고 고친다.
결과는 `cache/art/vout-NN.json`(JSON 배열, 묶음과 같은 순서).

1. `photos` 의 사진(`art/ref/photos/<id>/N.jpg`, 대부분 한국 관찰)을 연다. 새가 작거나 흐리거나 가려진 사진은 건너뛴다.
   사진이 드물게 다른 종일 수 있다(관찰 오동정). 널리 알려진 특징과 크게 어긋나면 그 사진을 믿지 말고 `notes` 에 적는다.
2. 지금 형태 정보(`art`: subject·build·views·avoid)와 책의 동정 포인트를 사진과 견준다.
   머리 모양(댕기), 부리 길이·모양, 눈 색, 다리, 몸 비율, 한국 개체군의 깃 색과 무늬가 어긋나면 그 칸을 바르게 다시 쓴다.
3. 동정 포인트 영어가 실제와 어긋나면 `marks` 를 쓴다(위 규칙).
4. `drawn` 에 그림 경로가 있으면(이미 그린 종) 그 그림을 열어 사진·바른 형태 정보와 견주고,
   **실제와 달라 고쳐야 할 점**을 한국어로 구체적으로 적는다(화풍·구도 취향이 아니라 생김새가 틀린 것만). 문제없으면 빈 문자열.

```json
{
  "id": "garrulus-glandarius",
  "verdict": "fixed",
  "photos_used": ["1.jpg", "3.jpg"],
  "subject": "고친 칸만 쓴다(subject·build·views·avoid·pose·scene 중)",
  "marks": ["동정 포인트와 같은 개수, 고칠 때만"],
  "drawn_issues": { "scene": "머리가 유럽 아종처럼 흰 바탕 줄무늬이고 등이 분홍빛 — 한국 개체는 적갈색 머리·회색 등", "plate": "" },
  "notes": "한국어, 필요할 때만"
}
```

- `verdict`: `ok`(고칠 것 없음) · `fixed`(칸을 고침) · `no-photos`(쓸 만한 사진이 없어 지식으로만 확인).
- 고친 칸은 처음 규칙(길이, 영어, 계절, 번호 찍은 도해의 views 수 유지)을 그대로 따른다.
- 끝나면 `uv run tools/art_profiles.py vcheck cache/art/vout-NN.json` 이 `오류 0` 이 될 때까지 고친다.
