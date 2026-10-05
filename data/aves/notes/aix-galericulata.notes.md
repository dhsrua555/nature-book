# 원앙 (Aix galericulata) — 근거 노트

## 이름·분류
- 국명·학명·목·과·ktsn: nibr_species.json (국가생물종목록 2025). 학명 표기 "Aix galericulata (Linnaeus, 1758)".
- 영문명: IOC 마스터 리스트(사이트 표시 v15.2, 내려받은 시트 머리글 v15.1)에서 "Mandarin Duck, Aix galericulata, (Linnaeus, 1758)" 확인.
  - https://www.worldbirdnames.org/new/bow/waterfowl/ (표 본문은 같은 사이트가 삽입한 Google 시트 CSV로 확인)

## 몸길이
- NIBR: "몸길이 약 45cm." → length = "약 45cm".
- 차이: 국가유산포털 "몸길이는 보통 43㎝정도", 한국민족문화대백과 "전장 수컷 48㎝, 암컷 41㎝", 영문 위키백과 "41–49 cm". 규칙대로 NIBR 값 사용.

## 날개 편 길이
- 영문 위키백과(각주 [11] 달림): "41–49 cm (16–19 in) long with a 65–75 cm (26–30 in) wingspan" → "65–75cm".
  - https://en.wikipedia.org/wiki/Mandarin_duck

## 국내 상태
- NIBR: "비교적 흔한 텃새이자 겨울철새이다." → status 그대로.
- 백과: "비교적 드문 텃새이다" / "우리나라에도 겨울철에 많은 무리가 중부 이남으로 남하, 이동해 온다." (흔함 정도는 NIBR과 다름 → NIBR 따름)
  - https://encykorea.aks.ac.kr/Article/E0040744
- 서울시 미디어허브: "원래 철새이지만 우리나라에서는 많은 수가 텃새화돼 전국에서 만날 수 있는 새"
  - https://mediahub.seoul.go.kr/archives/2010073

## 볼 수 있는 달 (seen 1–12)
- 텃새+겨울철새(NIBR). 백과: 광릉 숲 물가에서 "언제나 볼 수 있을 정도로 해마다 번식하고 있으며 5월 하순에는 새끼도 볼 수 있다."

## 번식기 (breed 4–7)
- 백과: "4∼7월 한배에 7∼12개의 알을 낳아 28∼30일간 포란한다." → 산란 달 4–7월을 그대로 씀. (7월 산란분의 육추는 8월까지 갈 수 있으나 출처가 말하지 않아 넣지 않음)
- 참고: 영문 위키백과(각주 [12]) "A single clutch of nine to twelve eggs is laid in April or May" — 국외 일반 서술이라 보조로만.

## 서식지·생태(summary)
- NIBR: "산림 주변의 늪지대나 계곡, 냇가 등에서 각종 식물의 열매나 수서곤충, 연체동물, 작은 어류 등을 먹는다. 냇가와 인접한 오래된 나무 위나 바위틈에서 번식한다." / "겨울철에는 전국의 호소, 하천, 해안 등"
- 국가유산포털: "삼림이 울창한 산골짜기 계곡", 겨울에는 "저수지, 호수와 늪, 해변, 냇가에서 무리로 겨울을 난다", "주로 활엽수 나무구멍에서 번식", "천연기념물로 지정하여 보호"
  - https://www.heritage.go.kr/DATA1/heritage/hub_img/html/cul_1369903270000.html
- 백과: "어미새는 도토리를 즐겨 먹으며 농작물과 나무열매, 수생 곤충류도 먹는다."

## 보호
- flags: ntmYn "Y" → "천연기념물". egspcsGrdNo 없음.

## 암수(sexes)
- NIBR: "수컷의 부리는 붉은색이며 끝은 흰색이다. 암컷은 전체적으로 어두운 회색 바탕에 몸 아랫면에 흰색 얼룩점이 있으며, 눈 뒤로 흰색의 가는 눈선이 있고 부리는 검은색이다. 수컷의 겨울깃은 암컷과 비슷하지만 부리가 붉은색이다."
  - 주: NIBR은 '겨울깃'이라 썼으나 내용은 번식 후 갈아입는 에클립스깃(비번식깃)이다. 위키백과: "the male undergoes a moult after the mating season into eclipse plumage ... bright yellow-orange or red beak" → JSON에는 '번식이 끝나면 … 에클립스깃'으로 적음.
- 위키백과 수컷: "small red bill, large white crescent above the eye and reddish face and 'whiskers'. The male's breast is purple with two vertical white bars, the flanks ruddy, and has two orange 'sail' feathers" (돛깃 문장에 Tang et al. 2025 각주, 단락 끝 각주 Aix).
- 위키백과 암컷(각주 [11]): "slender white eye-ring and stripe running back from the eye ... a pale tip to its bill."
- 백과: "부리는 홍색, 부리끝은 백색, 발은 등색(橙色), 배는 흰색이다." → 그림의 주황 다리 근거.

## 어린새
- TODO. 위키백과의 새끼(duckling) 구별 문장은 "{{Citation needed}}" 표시라 쓰지 않음.

## 비슷한 종
- 청둥오리 암컷: 위키백과 Mallard(각주 [28]) "buff cheeks, eyebrow, throat, and neck, with a darker crown and eye-stripe", 부리(각주 [32]) "black to mottled orange and brown"; NIBR 청둥오리 "암컷 … 부리는 오렌지색 바탕에 검은색의 반점".
  - https://en.wikipedia.org/wiki/Mallard

## 그림(art)
- 수컷 묘사는 위 NIBR·위키백과·백과 근거. 정수리 녹자색·뒷머리 주황 밤색 댕기: 위키백과 "the purple crest is more pronounced on the male", 국가유산포털 "뒷머리깃과 윗가슴은 밤색". 가슴 흰 줄 양옆의 검은 테, 홍채 색(어두움)은 인용 출처로 따로 확인하지 못함 → 검토 권장.
- 장면: 서식지(산림 계곡·냇가)와 도토리 먹이(백과)에 맞춤.
