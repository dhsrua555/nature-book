# 직박구리 Hypsipetes amaurotis – 근거 메모

## 이름·분류
- 국명·학명·명명자·목·과·ktsn: nibr_species.json (국가생물종목록 2025). 학명 `Hypsipetes amaurotis (Temminck, 1830)`. 보호 플래그 모두 null이라 protect는 [].
- 영문명 Brown-eared Bulbul: 영어 위키백과 문서 제목 "Brown-eared bulbul" (IOC 표기).
  https://en.wikipedia.org/wiki/Brown-eared_bulbul

## 몸길이
- "몸길이는 약 28cm이다." (국립생물자원관, nibr_text)
- 사이버교육센터 자료 "Res/c L 28cm" (bisp-conts 목록 API)
- 영어 위키 "Reaching a length of about 28 cm" — 일치.

## 국내 상태·서식지
- "평지에서 산지에 이르기까지 수목이 있는 곳에 살며 흔히 볼 수 있는 텃새이다." (nibr_text)
- 환경부 자료: "평지로부터 산지에 이르기까지 수목이 있는 곳이면 어디에서나 서식한다." / 국내분포 "제주도, 울릉도를 포함한 전국"
  https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/list?ktsn=120000530330&stts=Y&srchRelKtsn=Y&pageNo=1&pageSize=100
- 국립생물자원관 철새 DB 구분: "텃새" (https://species.nibr.go.kr/gwsvc/birds/api/v1/public/species/search?schKeyword=amaurotis&pageCount=1&unitCount=10)
- Birds Korea 2014 목록: "직박구리 Hypsipetes amaurotis R1, P2 / 번식 1" (R1 = 널리 서식, ≥100,000; P2 = 통과 철새 10,000–99,999). 텃새이면서 이동 무리도 많다는 뜻.
  http://www.birdskorea.or.kr/Birds/Checklist/BK-CL-Checklist-Apr-2014.shtml
- Birds Korea Birdyear: "Taller trees inevitably contain Brown-eared Bulbuls and Great Tits" (작은 도시 공원 설명 단락)
  http://www.birdskorea.org/Birds/Birding_in_Korea/BK-BK-Birdyear.shtml

## 달
- seen 1–12: 텃새(국립생물자원관·Birds Korea R1).
- breed 5–6: "5-6월에 4~5개의 알을 낳는다." (nibr_text), 환경부 "산란기는 5~6월이고 알은 4~5개 낳는다."
  - 영어 위키 "typically breed between April and July, and sometimes August" — 인용 없는 문장이고 분포 전역(일본 포함) 기준이라 쓰지 않음.
  - 산란기만 확인됨. 육추가 7월까지 이어지는지는 국내 출처를 찾지 못해 todo에 남김.
- note의 무리: 환경부 "이동할 때는 큰 무리를 형성한다", 사이버교육센터 "비번식기에는 무리를 지어 생활한다."

## summary 근거
- 나무 위 생활: "대부분 나무 위에서 생활하여 지상에 내려오는 일은 거의 없다." (nibr_text)
- 먹이: "먹이는 식물의 열매, 곤충류이다." (nibr_text)
- 비행·소리: 사이버교육센터 "전형적인 파도 모양으로 난다." / "소리: '삐-잇, 삐-잇'하고 매우 시끄럽게 울며"

## 동정 포인트·암수
- "머리와 등은 푸른색을 띤 회색이며, 날개는 회갈색이다. 눈 뒤로 밤색의 반점이 있다. 배에서 꼬리 쪽으로 갈수록 흰색 반점이 많아진다." (nibr_text)
- 국립수목원: "암컷과 수컷 모두 머리꼭대기와 뒷목이 남청색을 띤 엷은 잿빛으로 각 깃털 끝은 뾰족하다 … 귀 깃과 앞 목에 이르는 부분은 밤색의 띠 … 윗가슴은 어두운 잿빛으로 각 깃털의 가장자리는 엷은 색이다."
  https://www.nature.go.kr/kbi/brbst/pilbk/selectBridPilbkDtl.do?anmlSpecsId=A000001044
  - 이 문장을 근거로 sexes.alike = true.
- 긴 꼬리: 영어 위키 "grayish-brown, with brown cheeks … and a long tail."

## 어린새
- 공식·학술 출처 없음 → "TODO". (검색에서 나온 oiseaux-birds.com 등 비공식 사이트에만 '어른보다 갈색' 설명이 있어 쓰지 않음.)

## 비슷한 종
- 검은이마직박구리 Pycnonotus sinensis: 영어 위키 "around 19 cm (7.5 in) in length", "black crown and moustachial stripe, with white patches covering the nape and the sides of its black head" https://en.wikipedia.org/wiki/Light-vented_bulbul
  - 국내 희소성: Birds Korea 2014 "검은이마직박구리 S4, P5, R5" vs 직박구리 R1. 국립생물자원관 철새 DB에는 '텃새'로 구분됨.
- 찌르레기: 국립수목원 "머리, 턱 아래 부위, 가슴은 어둔 회색이고 이마와 뺨은 흰색이다 … 부리와 다리는 오렌지색이고 부리는 끝 부분만 검은색이다."
  https://www.nature.go.kr/kbi/brbst/pilbk/selectBridPilbkDtl.do?anmlSpecsId=A000001118
  - 직박구리 부리가 검다는 점은 출처 문장이 아니라 사진으로 확인(아래).

## 그림(art)
- 깃 색은 위 국립생물자원관·국립수목원 문장 기준.
- 부리(검고 가늘며 약간 굽음)·눈(적갈색)·다리(어두운 적갈색)는 Wikimedia 사진으로 확인:
  https://commons.wikimedia.org/wiki/Special:FilePath/The_brown-eared_bulbul_after_playing_with_water.jpg (일본 개체)
- 배경의 감·열매: 먹이가 '식물의 열매'라는 국립생물자원관 문장에 맞춘 연출. 감을 먹는다는 한국어 위키 문장은 인용이 없어 사실 항목에는 쓰지 않음.
- 국내 아종명은 확인하지 못해 art에 아종을 적지 않음(영어 위키 아종 목록에 한국 분포 명시 없음).

## 참고: 출처끼리 차이
- 국립수목원 학명 표기는 옛 속명 Microscelis amaurotis. 국가생물종목록 2025의 Hypsipetes를 따름.
