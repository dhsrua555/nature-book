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
