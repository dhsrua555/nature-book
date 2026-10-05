# 물까치 Cyanopica cyanus — 근거 노트

## 국명·학명·분류·ktsn·보호
- nibr_species.json: `Cyanopica cyanus (Pallas, 1776)`, Passeriformes 참새목 / Corvidae 까마귀과, ktsn 120000001956, flags 모두 null(천연기념물·멸종위기 아님) → protect [].
- URL: https://species.nibr.go.kr/species-detail/120000001956 (nibr_species.json 제공 값)

## 영명 (IOC)
- IOC 마스터 시트 행: `Species,Azure-winged Magpie,Cyanopica cyanus,"(Pallas, 1776)","PAL : e, c Asia"`
- 아종: `C. c. cyanus ... "e Siberia, Mongolia, n, c, e China and Korean Pen." ... "Includes stegmanni, koreensis, kansuensis, interposita, and swinhoei (Kryukov et al. 2004)."` → 한반도는 C. c. cyanus(옛 koreensis 포함).
- 페이지 https://www.worldbirdnames.org/bow/crows/ 는 「v15.2」「Updated April 13, 2026 with version 15.2」라 적혀 있고, 내장된 구글 시트 머리글은 v15.1 인용문을 담고 있음.
- 시트 CSV: https://docs.google.com/spreadsheets/d/e/2PACX-1vTmLDAgrFrQXmUSd7-KbWHN6XzJLklmm6HP28wFxbhSzVKPE4yHq-GmroLuqaCWiA/pub?gid=546146977&single=true&output=csv

## 몸길이 — "37cm"
- 국립생물자원관(get-cn-data/120000001956, 한반도생물자원포털 2011): 「몸길이는 37cm이다.」
- 차이: 영문 위키백과 「31–35 cm long」, Bird Research News(일본 개체 실측, Kuzu 1942) 「Total length: 366.8mm (319-390)」. 규칙대로 국립생물자원관 값 사용.
- URL: https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/get-cn-data/120000001956

## 날개편길이 — TODO
- 확인한 출처 어디에도 없음.

## 상태 — "흔한 텃새" / months.seen 1–12
- 국립생물자원관 개요: 「한반도 전역에 흔한 텃새이다.」
- 국립생물자원관 국내분포(한국의새소리 2010): 「한국 전역에 분포하는 흔한 텃새이다.」
- PeerJ 2022: 「resident bird species that lives in colonies and is widely distributed throughout the Republic of Korea」
- URL: https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/list?contsTypeMulti=EO,DT,SO,ET,ND,ID,EC,AB&cprgtYn=Y&stts=Y&ktsn=120000001956&pageNo=1&pageSize=50

## 번식 — breed [5,6,7]
- 국립생물자원관 개요: 「산란기는 5~7월이며, 한배의 산란수는 6~9개이다.」
- 국립생물자원관 생태(한국의새소리 2010): 「번식 시기에도 무리를 지어 번식하며 낙엽송 등 나무와 대나무숲에 둥우리를 튼다. 5월부터 산란을 시작한다.」
- 참고(국내 현장 연구, 남양주 조안면 2018–2019): 「The Azure-winged magpies in our study area started building nests in late April and fledged nestlings in mid or late June.」 — https://pmc.ncbi.nlm.nih.gov/articles/PMC9250309/
- 참고(일본 개체군): Bird Research News 「The egg-laying period is from mid-May to mid-August」「the last nestlings fledge in mid-September」. 일본 자료라 달 값에는 쓰지 않음.
- 판단: 국립생물자원관 산란기 5~7월을 그대로 씀. 8월 육추 여부는 국내 출처 없음 → todo.

## 서식지
- 국립생물자원관: 「산지나 평지의 숲 또는 시가지 공원에서 서식한다.」「산지 또는 마을 부근의 숲에서 2~6m 높이의 나뭇가지에 … 밥그릇 모양의 둥지」, 생태: 「낙엽송 등 나무와 대나무숲에 둥우리를 튼다」.

## summary 근거
- 무리 생활: 국립생물자원관 「일반적으로 무리 지어 생활하며 특히 번식기 이외에는 5~10마리의 작은 무리」, 「번식 시기에도 무리를 지어 번식」.
- 협동 번식: PeerJ 「cooperative breeding system during the breeding season, meaning that helpers may assist in all reproductive stages」; Bird Research News 「Azure-winged Magpies are known to have helpers which assist breeding pairs in raising their nestlings.」
- 먹이: 국립생물자원관 「잡식성으로 동물성과 식물성을 혼식하나, 특히 곤충을 좋아한다.」

## 형태·동정 포인트·art
- 국립생물자원관: 「머리는 검은색, 등은 회색, 턱 밑과 뺨, 멱은 흰색, 몸의 아랫면은 엷은 회색, 등 아래쪽의 날개와 꼬리는 엷은 청색이다. 부리와 다리는 검은색이다. 꼬리는 쐐기 모양이다.」
- 위키백과: 「a glossy black top to the head and a white throat」, 「light grey-fawn」 underparts and back, wings and tail 「azure blue」; 이베리아까치와 「the white-tipped tail being a prominent indicator」[2][3]. — https://en.wikipedia.org/wiki/Azure-winged_magpie
- Bird Research News (Vol.6 No.6, 2009, Harada S.): 「similar in plumage coloration in males and females. Males are slightly larger than females」, 「The flight feathers are black in the inner vane and pale blue in the outer one. The primary flight feathers are white from the middle to the tip in the outer vane. There is a long white patch of about 2 cm at the tip of the central rectrix. The bill and feet are black. The iris is dark brown.」 — https://www.bird-research.jp/1_shiryo/seitai/onaga.pdf
- Andalucia Bird Society: 「Eastern birds are marginally larger, distinctly greyer and have those white tail tips.」 — https://www.andaluciabirdsociety.org/article-library/about-birds/bird-of-the-month-november-2021/
- 주의: Bird Research News는 일본 아종(C. c. japonica) 자료. 깃 색 구성은 국립생물자원관 설명과 일치함.

## 암수
- Bird Research News(위 인용). 국내 출처에서는 암수 차이 언급 없음.

## 어린새
- Bird Research News: 「The tail feathers of juveniles are characteristically short in the center, with white edge band of about several millimeters. The greater wing coverts and alula are also white at the tip.」
- 어린새 머리 깃 묘사는 블로그·비전문 사이트에만 있어 쓰지 않음 → todo.

## 유사종
- 까치: 국립생물자원관 까치 개요 「몸 전체 길이는 46cm」「윗면은 푸른 광택이 있는 검은색이고 배는 흰색」「어깨에는 흰색 반점」.
- 어치: 국립생물자원관(ktsn 120000001954) 「등과 배는 분홍빛을 띤 갈색」「허리의 흰색과 꼬리의 검은색이 대조적이고, 날개덮깃에는 청색과 검은색 가로띠」「폭넓은 검은색의 뺨 선」. — https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/list?contsTypeMulti=EO,DT,SO,ET,ND,ID,EC,AB&cprgtYn=Y&stts=Y&ktsn=120000001954&pageNo=1&pageSize=50

## art.scene
- 낙엽송·대나무숲(국립생물자원관 생태), 뽕나무 등 섞인 숲과 농경지(PeerJ 조사지: 「mulberry, wild rose, and Japanese yew」, 「surrounded by agricultural land」), 번식기 5월.
