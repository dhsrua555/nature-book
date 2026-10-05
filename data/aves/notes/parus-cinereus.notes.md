# 박새 Parus cinereus — 근거 노트

## 국명·학명·분류·ktsn·보호
- nibr_species.json: `Parus cinereus Vieillot, 1818`, 참새목 박새과, ktsn 120000155331, flags 모두 null → protect []. nibr_text 없음.
- 국립생물자원관 종 정보 API: `"ktsn":120000155331,"stnm":"Parus cinereus Vieillot, 1818" … "ktsnKrnNm":"박새"` — https://species.nibr.go.kr/gwsvc/ktsn/api/v1/public/txgrp-search/list?ktsn=120000155331
- 설명 API(get-cn-data/120000155331)는 `"data":null`, 콘텐츠 목록 API도 0건.

## 국립생물자원관 옛 설명(중요한 주의점)
- 옛 ktsn 120000001975는 현재 `"stnm":"Parus major Linnaeus, 1758" … "ktsnKrnNm":"노랑배박새"`로 표시됨 — https://species.nibr.go.kr/gwsvc/ktsn/api/v1/public/txgrp-search/list?ktsn=120000001975
- 그러나 이 ktsn에 붙은 2010년 개요(한반도생물자원포털 2010, 집필 현진오)는 국내 박새를 설명한다: 「참새목 박새과에 속하는 조류이다. 몸길이는 14cm이다. 머리는 검은색이고 뺨은 흰색이다. 윗면은 회색이며 등은 연둣빛을 띤다. 아랫면은 흰색이고 가슴부터 배까지 중앙을 따라 검은색 띠가 있다. 인가부터 산림까지 다양한 곳에 살며 나무 구멍이나 건물 틈에 둥지를 튼다. 4월부터 산란을 시작하고 한 해에 두 번 번식한다. 번식 초반인 3월부터 울음소리를 들을 수 있다. 전국에 서식하는 텃새이고 세계적으로는 유라시아 전역에 분포한다.」 — https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/get-cn-data/120000001975
- 판단 근거: '아랫면은 흰색'과 '전국에 서식하는 텃새'는 배가 노란 노랑배박새가 아니라 국내 박새의 특징. 박새를 Parus major로 다루던 시기의 설명이 학명 개정 후 옛 ktsn에 남은 것으로 봄 → todo에 확인 필요로 남김.
- 같은 ktsn 콘텐츠 목록: 국내분포 「전국」, 생태 「나무 구멍이나 건물 틈에 둥지를 튼다. 4월부터 산란을 시작하고 한 해에 두 번 번식한다. 번식 초반인 3월부터 울음소리를 들을 수 있다.」 (한반도의생물다양성시스템고도화 2018) — https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/list?contsTypeMulti=EO,DT,SO,ET,ND,ID,EC,AB&cprgtYn=Y&stts=Y&ktsn=120000001975&pageNo=1&pageSize=50

## 영명·IOC 처리 (확인됨)
- IOC 시트 행: `Species,Cinereous Tit,Parus cinereus,"Vieillot, 1818","OR, PAL, AU : s, e, se Asia to e Lesser Sundas","AS, AL, TAX"`, 주석: 「Parus cinereus and Parus minor were previously split from P. major as two species: Cinereous Tit and Japanese Tit (…). But the genetic analyses by Päckert & Martens (2008), Zhao et al. (2012) and Song et al. (2020) suggest that the Parus major complex may be better interpreted as comprising two species: East Asian P. cinereus (cinereus + minor) which forms a sister clade to Palearctic P. major (major + bokharensis). (WGAC #1100). "Cinereous Tit" is tentatively assigned as the English name for the lumped species.」
- 아종: `P. c. minor,"Temminck & Schlegel, 1848","e Siberia, s Sakhalin I., ec, ne China, Korean Pen. and Japan",SSP,"Includes kagoshimae …, wladiwostokensis and artatus …"` / `P. c. dageletensis,"Kuroda, Nm & Mori, 1920",Ulleungdo I. (off South Korea)`.
- 병합 시점: 영문 위키백과(Cinereous tit) 각주 「Gill, Frank; Donsker, David; Rasmussen, Pamela, eds. (August 2024). "Waxwings and their allies, tits & penduline tits". IOC World Bird List Version 14.2.」, 본문 「The final eight subspecies on the above list (beginning with P. c. minor) were formerly treated as a separate species, the Japanese tit (Parus minor).」 — https://en.wikipedia.org/wiki/Cinereous_tit
- 페이지: https://www.worldbirdnames.org/new/bow/waxwings/ (「v15.2」「Updated April 13, 2026 with version 15.2」, 같은 구글 시트 내장) / 시트 CSV: https://docs.google.com/spreadsheets/d/e/2PACX-1vTmLDAgrFrQXmUSd7-KbWHN6XzJLklmm6HP28wFxbhSzVKPE4yHq-GmroLuqaCWiA/pub?gid=546146977&single=true&output=csv
- 결론: sci는 지시대로 국립생물자원관의 Parus cinereus를 유지. IOC도 현재 같은 학명 Parus cinereus(Cinereous Tit)로 다루므로 en = "Cinereous Tit". 이 내용은 JSON의 taxon_note(추가 필드)에 적음.

## 몸길이 — "14cm"
- 국립생물자원관 옛 개요(위): 「몸길이는 14cm이다.」 HKBWS: 「12-14 cm」.

## 날개편길이 — TODO

## 상태 — "텃새" / seen 1–12
- 국립생물자원관 옛 개요: 「전국에 서식하는 텃새」. 국립수목원 웹진: 「곤줄박이 10개 + 박새 1개(이상 텃새)」 — https://www.forest.go.kr/kna/webzine/2023/vol_150/s2.html
- '흔한'을 명시한 공식 출처를 찾지 못해 붙이지 않음.

## 번식 — breed [4,5,6]
- 국립생물자원관 옛 설명: 「4월부터 산란을 시작하고 한 해에 두 번 번식한다. 번식 초반인 3월부터 울음소리를 들을 수 있다.」
- 영남대 학위논문(정혜진 2012, 대구 도시녹지): 「2010년과 2011년 박새의 번식시기인 4월부터 6월말까지의 시기 동안 실시되었다.」, 초록에 1차·2차 번식 구분 — https://scienceon.kisti.re.kr/srch/selectPORSrchArticle.do?cn=DIKO0012736942&dbt=DIKO
- 국립공원공단(2020.4.23, 소백산): 「2011년 이후 가장 빠른 시점인 4월 2일 첫 산란을 확인했다」, 「박새의 경우 기후변화 등 외부 환경변화에 민감하게 반응하여 환경부 '기후변화 생물지표 100종'에 포함되어 있다」 — https://www.knps.or.kr/front/research/open/pnewsDtl.do?menuNo=8000315&pnewsId=PNEWSM015829
- 국문 위키백과 「산란 기간은 4월~7월까지」는 각주가 IOC 분류 페이지를 가리키는 것으로 보여 근거로 쓰지 않음.

## 서식지
- 국립생물자원관 옛 개요: 「인가부터 산림까지 다양한 곳에 살며 나무 구멍이나 건물 틈에 둥지를 튼다.」 도시 녹지는 학위논문 주제(도시녹지 번식).

## 형태·동정 포인트·art
- 국립생물자원관 옛 개요(위): 검은 머리·흰 뺨·회색 윗면·연둣빛 등·흰 아랫면·가운데 검은 띠.
- HKBWS: 「12-14 cm. Black head, apart from large white cheek patch and hind neck distinctive. Black covers entire throat and extends down centre of underbody, which is otherwise pale dull greyish-white.」, 「the greater coverts are broadly tipped white forming a striking wing bar」, 원명아종 P. m. minor: 「greenish in the upper mantle and a bluish tinge to the median coverts and edges to the remiges and rectrices」 — https://avifauna.hkbws.org.hk/species/0270/034800
- 위키백과: 「distinct in having a grey-back, black hood, white cheek patch and a white wing-bar」.
- 부리·다리·홍채 색: 확인한 출처에 없음 → art에 색을 쓰지 않음(todo).

## 암수
- HKBWS: 「Males have extensive black between the legs.」
- 위키백과(Cinereous tit, 각주 Rasmussen & Anderton 2005): 「The female has a narrower ventral line and is slightly duller.」

## 어린새
- HKBWS: 「Juveniles have a similar plumage pattern to adults but are tinged olive above and yellowish below and usually have an obvious pale gape.」
- 위키백과(각주 Baker 1924): 「young birds show some green on the back and yellowish on the underside」.

## 유사종
- 쇠박새(국립생물자원관 ktsn 120000001979): 「몸길이 약 12.5cm」「윗면은 갈색을 띤 연한 회색으로 날개에는 흰 줄이 없다」「멱은 검은색」, 배 「회색을 띤 흰색」.
- 진박새(국립생물자원관 ktsn 120000001977): 「몸길이는 11cm쯤」「뒷목의 중앙은 흰색」「머리꼭대기의 깃털은 작은 모관을 형성」「가슴 이하의 아랫면은 전부 크림색」.
