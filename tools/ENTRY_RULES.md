# 종 설명 원문으로 종 항목 쓰기

`tools/nibr_entries.py batches` 가 만든 묶음(`cache/work/batch-NN.json`)의 종마다
국립생물자원관 종 설명 원문(`text`)**만**을 근거로 도감 항목을 써서 `cache/work/out-NN.json` 에 담는다.
이 책의 원칙은 "종 설명과 수치는 정확해야 하고, 확신이 없는 정보는 지어내지 않고 TODO로 둔다"이다.

## 절대 규칙

1. **원문에 없는 사실은 쓰지 않는다.** 아는 지식으로 보태지 않는다. 원문에 없으면 `"TODO"`(또는 규칙에 적힌 빈 값).
2. **수는 원문 그대로.** 몸길이·날개 편 길이·알 수·달은 원문의 숫자를 바꾸지 않는다. `약`, `~` 같은 표현도 원문을 따른다.
3. **원문 문장을 통째로 옮기지 않는다.** 같은 사실을 우리 문장으로 다시 쓴다(저작권). 문체는 도감체 `~다`.
4. 원문이 스스로 모순되거나, 상식으로 보아 명백히 틀렸거나(예: 참새 몸길이 150cm), 다른 종을 설명한 것으로 보이면
   그 값은 `"TODO"` 로 두고 `todo` 에 까닭을 한 줄 적는다. 고친 값을 지어 넣지는 않는다.
5. 원문의 `[멸종위기 야생생물 I급]` 같은 보호 표시는 옮기지 않는다(보호 표시는 목록 자료에서 따로 붙인다).

## 항목

```json
{
  "id": "묶음의 id 그대로",
  "length": "17cm",
  "wingspan": "원문에 있을 때만 이 키를 쓴다",
  "status": "흔한 여름철새 또는 텃새",
  "habitat": "물가, 물가의 언덕과 흙 벼랑",
  "months": { "seen": "TODO", "breed": [4, 5, 6, 7, 8], "note": "번식기는 4~8월이다." },
  "summary": "…",
  "points": [ { "ko": "…", "en": "…" } ],
  "sexes": { "alike": false, "male": "…", "female": "…" },
  "young": "TODO",
  "similar": [],
  "art": { "subject": "…", "pose": "…", "scene": "…", "views": ["…", "…"] },
  "todo": []
}
```

- **length**: `"17cm"`, `"약 45cm"`, `"15–17cm"`(범위는 en dash), `"수컷 63cm, 암컷 54cm"`. 없으면 `"TODO"`.
- **status**: 원문의 낱말(텃새·여름철새·겨울철새·나그네새·길잃은새)과 원문이 붙인 흔하기 표현(흔한, 드문, 매우 드문, 적은 수가 등)으로 짧게.
  예 `"드문 나그네새"`, `"흔한 겨울철새, 일부 텃새"`. 원문이 국내 상태를 말하지 않으면 `"TODO"`.
- **habitat**: 원문이 말한 사는 곳을 쉼표로 이은 짧은 명사구. 둥지 자리만 있으면 그것이라도. 없으면 `"TODO"`.
- **months** (한국에서의 달, 1–12 정수 목록):
  - `seen`: 원문이 국내에 머무는 달·오는 달·떠나는 달을 말할 때만(예 "3월 하순에 와서 10월에 떠난다" → 3–10).
    상태가 **텃새 하나뿐**이면 `[1,…,12]`. 그 밖에는 `"TODO"`.
  - `breed`: 원문이 번식기·산란기 달을 말하고 **국내에서 번식하는 새**(텃새·여름철새이거나 국내 번식을 말함)일 때 그 달
    (예 "산란기는 5월 하순~6월" → [5, 6]). 나그네새·겨울철새·길잃은새뿐이고 국내 번식 말이 없으면 `[]`
    (국외 번식지의 산란기는 넣지 않는다). 그 밖에는 `"TODO"`.
  - `note`: 시기에 관한 원문 내용을 한 문장으로(선택). 국외 번식지의 산란기는 여기에 "번식지에서는 …" 로 적어도 된다.
- **summary**: 2–4문장. 첫 문장은 어떤 새인지(국내 상태·사는 곳). 이어서 먹이, 번식, 행동, 국내·국외 분포 중 원문에 있는 것.
  "○○목 ○○과에 속하는 조류이다" 같은 분류 문장과 몸길이 숫자는 다른 칸에 있으니 되풀이하지 않는다.
- **points** (동정 포인트): 원문의 생김새 가운데 알아보는 데 쓸 특징 3–6개, 머리 → 몸 → 다리 순.
  `ko` 는 짧은 명사구(18자 안팎), `en` 은 같은 뜻의 영어 조류 용어(예 "white supercilium", "rufous flanks").
  원문에 생김새가 없으면 `[]`.
- **sexes**: 원문이 암수 차이를 말하면 `{"alike": false, "male": "…", "female": "…"}`,
  암수가 같다고 하면 `{"alike": true, "text": "암수 같은 색이다."}`, 말이 없으면 `{"alike": null, "text": "TODO"}`.
  여름깃·겨울깃 차이는 여기가 아니라 points 나 summary 에.
- **young**: 어린새 생김새가 원문에 있으면 한두 문장, 없으면 `"TODO"`.
- **similar**: 원문이 직접 견준 종만 `{"ko": "국명", "how": "어떻게 다른지"}`. 없으면 `[]`.
- **art** (그림 생성용, 영어):
  - `subject`: `"<English name> (<학명>), adult[ male]: …"` 에 원문의 깃 색·부리·다리 색을 영어로. 원문에 없는 색은 넣지 않는다.
    원문에 생김새가 없으면 `"TODO"`.
  - `pose`: 원문의 행동과 맞는 자연스러운 자세 한 줄(예 "wading in shallow water, probing the mud with its bill").
    행동 말이 없으면 `"perched, side view"` 처럼 무난하게.
  - `scene`: 원문의 사는 곳과 머무는 계절로 한국 풍경 한 줄, 끝에 `"; no people, buildings or text"`.
    사는 곳 말이 없으면 `"TODO"`.
  - `views`: 동정 도해에 그릴 모습 2–3개(`"adult, side view perched: …"`, 원문에 여름깃·겨울깃이 있으면 둘 다,
    암수가 다르면 수컷·암컷). points 가 `[]` 이면 `[]`.
- **todo**: 확인이 필요한 점(모순, 의심 값 등)만 한국어 한 줄씩. 비어 있으면 `[]`.

## 예 (물총새 원문으로 쓴 항목)

원문: "파랑새목 물총새과에 속하는 조류이다. 몸길이는 17cm이다. 머리는 어두운 녹색으로 청백색 반점이 있다. … 등과 허리는 파란색이며, 꼬리는 청록색이다. … 눈의 앞과 뒷부분에는 주황색 반점이 있다. 턱과 목의 측면은 흰색이다. 아랫면은 주황색이고, 다리는 붉은색이다. 수컷은 아랫부리와 윗부리가 검은색이고, 암컷은 윗부리가 검은색이지만 아랫부리는 붉은색을 띤다. 한국 전역에서 흔히 번식하는 여름철새 또는 텃새이다. 주로 물가에 있는 언덕 또는 절벽의 흙 벼랑에 둥지를 튼다. 둥지는 흙 절벽에 옆으로 파서 만들며 깊이 1m에 달한다. 번식기는 4-8월이며, 4~7개의 알을 낳는다. 암수가 교대로 품으며, 야간에는 주로 암컷이 담당한다. 먹이는 주로 물고기이며, 양서류, 수서 곤충류, 갑각류 등도 먹는다. 전국에 서식하고 세계적으로는 중국 북서부 산지를 제외한 유라시아와 아프리카 북부, 일본 등에 분포한다."

```json
{
  "id": "alcedo-atthis",
  "length": "17cm",
  "status": "흔한 여름철새 또는 텃새",
  "habitat": "물가, 물가의 언덕과 흙 벼랑",
  "months": { "seen": "TODO", "breed": [4, 5, 6, 7, 8], "note": "번식기는 4~8월이다." },
  "summary": "전국의 물가에서 흔히 번식하는 작은 새로, 여름철새로 오거나 텃새로 머문다. 물가 언덕이나 흙 벼랑에 옆으로 깊이 1m에 이르는 굴을 파서 둥지로 쓰고, 알 4~7개를 암수가 번갈아 품되 밤에는 주로 암컷이 맡는다. 물고기를 주로 먹고 양서류, 물속 곤충, 갑각류도 잡는다. 국외에서는 중국 북서부 산지를 뺀 유라시아와 아프리카 북부, 일본 등지에 산다.",
  "points": [
    { "ko": "청백색 반점이 있는 짙은 녹색 머리", "en": "dark green crown spotted pale blue" },
    { "ko": "눈 앞뒤의 주황색 무늬", "en": "orange loral and ear patches" },
    { "ko": "흰 턱과 목 옆", "en": "white chin and neck sides" },
    { "ko": "선명한 파란색 등과 허리", "en": "vivid blue back and rump" },
    { "ko": "주황색 아랫면", "en": "orange underparts" },
    { "ko": "붉은 다리", "en": "red legs" }
  ],
  "sexes": { "alike": false, "male": "윗부리와 아랫부리가 모두 검다.", "female": "윗부리는 검고 아랫부리는 붉은색을 띤다." },
  "young": "TODO",
  "similar": [],
  "art": {
    "subject": "Common Kingfisher (Alcedo atthis), adult male: dark green crown and wings with pale blue spots, vivid blue back and rump, blue-green tail, orange patches in front of and behind the eye, white chin and neck sides, orange underparts, red legs, all-black bill",
    "pose": "perched on a low twig over water, watching for fish",
    "scene": "Korean summer waterside: an earthen bank above a quiet stream where a nest burrow could be dug, reeds along the water; no people, buildings or text",
    "views": [
      "adult male, side view perched: dark green crown with pale blue spots, orange eye patches, white throat, blue back, orange underparts, red legs, black bill",
      "adult female, head detail: black upper mandible and reddish lower mandible"
    ]
  },
  "todo": []
}
```

## 끝내기

1. 묶음의 모든 종을 같은 순서로 담은 JSON 배열을 `cache/work/out-NN.json`(UTF-8)에 쓴다.
2. `uv run tools/nibr_entries.py check cache/work/out-NN.json` 을 돌려 문제를 모두 고친다
   ("원문에 없다"는 경고는 값을 원문 숫자대로 고치거나 `"TODO"` 로).
3. 다른 파일(`data/`, 코드, 다른 묶음)은 건드리지 않는다. git 명령은 쓰지 않는다.
