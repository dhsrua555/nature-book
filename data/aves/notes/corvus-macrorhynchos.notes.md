# 큰부리까마귀 Corvus macrorhynchos — 근거 노트

## 국명·학명·분류·ktsn·보호
- nibr_species.json: `Corvus macrorhynchos Wagler, 1827`, 참새목 까마귀과, ktsn 120000001967, flags 모두 null → protect [].
- URL: https://species.nibr.go.kr/species-detail/120000001967 (nibr_species.json 제공 값)

## 영명·아종 (IOC)
- IOC 시트: `Species,Large-billed Crow,Corvus macrorhynchos,"Wagler, 1827"` … 주석 「Corvus macrorhynchos, as currently configured, may be comprised of multiple species-level taxa. However, further genetic analysis … is desirable before a revision of this species is proposed」.
- 아종: `C. m. mandshuricus,"Buturlin, 1913","e, se Siberia, n Sakhalin I., Korean Pen. and ne China"` → 한반도는 C. m. mandshuricus. (일본은 C. m. japonensis)
- IOC는 Eastern Jungle Crow(C. levaillantii)·Indian Jungle Crow(C. culminatus)·Philippine Jungle Crow(C. philippinus)를 별종으로 두지만 한반도 개체군과는 무관.
- 페이지: https://www.worldbirdnames.org/bow/crows/ (v15.2 표기) / 시트 CSV: https://docs.google.com/spreadsheets/d/e/2PACX-1vTmLDAgrFrQXmUSd7-KbWHN6XzJLklmm6HP28wFxbhSzVKPE4yHq-GmroLuqaCWiA/pub?gid=546146977&single=true&output=csv
- 보도자료 붙임1: 「영 명 : Large-billed Crow」.

## 몸길이 — "약 57cm"
- 국립생물자원관 개요: 「몸길이는 57cm쯤이다.」 — https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/get-cn-data/120000001967
- 차이: 2026 보도자료 붙임1 「몸길이 56.5cm로 국내 까마귀류 중 가장 크며」; 영문 위키백과 「46–59 cm」. 국립생물자원관 값 사용.
- summary의 '가장 크다'는 보도자료 문장을 따르되, 드문 큰까마귀(Corvus corax)도 국내 기록이 있어 '우리 주변에서 흔히 보는 까마귀류 가운데'로 범위를 좁혀 씀.

## 날개편길이 — TODO (출처 없음)

## 상태 — "흔한 텃새" / seen 1–12
- 국립생물자원관 국내분포(한국의새소리 2010): 「우리나라에는 흔한 텃새이다.」
- 국립생물자원관 생태(한국의새소리 2010): 「주로 산림에서 번식하고 겨울에는 저지대로 이동한다.」 — https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/list?contsTypeMulti=EO,DT,SO,ET,ND,ID,EC,AB&cprgtYn=Y&stts=Y&ktsn=120000001967&pageNo=1&pageSize=50
- 보도자료 본문: 「텃새인 큰부리까마귀는 지능이 높고 적응력이 뛰어나 최근 도심지에서 번식이 꾸준히 확인되고 있다.」 붙임1: 「국내 대표적인 텃새로 전국에 서식」.
- 차이: 국립생물자원관 개요(2011)는 「한반도의 중부 이북 지역, 주로 북한 지역에서 흔히 번식하나 중부 이남 지역에서는 드물게 번식하는 편이다」라고 적었으나, 2026 보도자료는 전국 서식·도심 번식을 말함. 오래된 서술로 보고 status에는 반영하지 않음.

## 번식 — breed [3,4,5,6,7]
- 국립생물자원관 개요: 「알은 3월 하순~6월 하순, 연 1회, 한배에 3~6개 낳는다.」
- 보도자료 붙임1: 「번식기 3~7월, 새끼 독립시기 5~7월」, 「산란수 4~6개, 포란 … 20일, 육추 … 30~35일」.
- 서울시 누리집(수정일 2026-05-22): 「번식기인 3월~7월에 새끼를 지키려는 방어행동 때문에 나타날 수 있는데, 특히 새끼가 독립하는 5월~7월 이소기에 더 잦아질 수 있습니다.」 — https://news.seoul.go.kr/env/?p=569372
- 보도자료 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156762515&call_from=rsslink (첨부 HWPX: https://www.korea.kr/common/download.do?fileId=198467136&tblKey=GMN)
- 산란수 차이(국립생물자원관 3~6개 / 보도자료 4~6개)는 JSON에 쓰지 않음.

## 서식지
- 보도자료 붙임1: 「단독 또는 작은 무리를 이뤄 산림, 숲에 주로 서식하며, 주거지 및 농경지 등 다양한 환경에도 서식」, 위해성 항목 「최근 도심 주거지 인근의 녹지공원에서 번식하면서」.

## summary 근거
- 먹이: 붙임1 「잡식성으로 낟알, 과실, 죽은 동물의 사체, 곤충류, 조류의 알과 새끼 등 다양한 종류를 먹음」; 국립생물자원관 개요 「썩은 고기와 찌꺼기 등도 즐겨 먹는다」.
- 방어 행동: 보도자료 「매년 5월이면 아직 비행이 서툰 새끼가 둥지를 떠나 … 부모 새는 둥지나 새끼 주변으로 접근하는 사람을 위협으로 인식해 머리와 목 부위를 향해 날아드는 등 강한 방어 행동을 보인다.」

## 형태·동정 포인트·art
- 보도자료 붙임1: 「전체적으로 검고 광택이 있음. 윗부리가 크고 굽어 있으며, 이마와 부리의 경사가 심해 직각으로 보임」.
- 국립생물자원관 개요: 「멱의 깃털은 버드나무 잎 모양」, 「온몸은 광택이 강한 검은색이다. 꽁지는 얕은 둥근꽁지이다.」, 「여름깃은 봄철 털갈이하지 않기 때문에 광택이 감소되고 갈색을 띠게 된다.」
- 영문 위키백과(HBW 인용 [11]): 「It has a large black bill with an arched culmen. The base of the culmen is hidden by a layer of overlapping black rictal bristles.」「The glossy black plumage has a purple sheen.」「The throat has elongated hackle feathers.」「The irises are dark brown and the legs are black.」 — https://en.wikipedia.org/wiki/Large-billed_crow

## 암수
- 위키백과 [11]: 「The sexes are similar in plumage but the female, on average, is smaller than the male and has a less arched culmen.」
- 국립생물자원관: 「암컷은 수컷과 같으나 다소 작다.」

## 어린새
- 위키백과 [11]: 「The juvenile has less glossy plumage and has smoky blue rather than brown irises.」

## 유사종
- 까마귀(ktsn 120000001966, 한반도생물자원포털 2010): 「전체 길이는 50cm이다.」「부리는 가늘고 검은색이며」 — https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/list?contsTypeMulti=EO,DT,SO,ET,ND,ID,EC,AB&cprgtYn=Y&stts=Y&ktsn=120000001966&pageNo=1&pageSize=50
- 울음 비교: 국립생물자원관(큰부리까마귀 생태) 「까마귀와 유사하게 ‘꺄악’하고 울지만 그 울림이나 소리 크기가 더 강하고 크다.」
- 떼까마귀(ktsn 120000001965, 2011): 「봄과 가을에 통과하는 흔한 나그네새이며 한반도의 남단 지역에서는 많은 큰 무리가 월동하는 겨울새」, 「콧구멍과 부리 주위는 잿빛 피부가 나출」, 「부리는 까마귀보다 더욱 가늘고」 — https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/list?contsTypeMulti=EO,DT,SO,ET,ND,ID,EC,AB&cprgtYn=Y&stts=Y&ktsn=120000001965&pageNo=1&pageSize=50
- 까마귀 이마 모양을 직접 설명한 국내 출처는 찾지 못해, 이마 대비는 큰부리까마귀 쪽 특징(보도자료)으로만 적음.

## art.scene
- 산림·숲 중심 서식(보도자료), 번식기 시작 3월(보도자료). 소나무·참나무 혼효림은 일반적인 국내 산림 묘사.
