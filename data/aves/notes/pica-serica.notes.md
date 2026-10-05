# 까치 Pica serica — 근거 노트

## 국명·학명·분류·ktsn·보호
- nibr_species.json: `Pica serica Gould, 1845`, 참새목 까마귀과, ktsn 120000532854, flags 모두 null → protect [].
- URL: https://species.nibr.go.kr/species-detail/120000532854 (nibr_species.json 제공 값)
- 참고: get-cn-data/120000532854 응답의 본문은 옛 ktsn 120000001958(당시 학명 Pica pica)에 붙은 설명이 연결되어 나온다. 국립생물자원관 목록에서 120000001958은 현재도 「Pica pica (Linnaeus, 1758) 까치」로 표시됨(txgrp-search API로 확인).

## 영명·분류 (IOC)
- IOC 시트: `Species,Oriental Magpie,Pica serica,"Gould, 1845","OR : se Russia and Myanmar to e China, Taiwan and n Indochina",AS,Split (8.2) from Eurasian Magpie follows revision of Pica pica species complex (Lee et al. 2003; Song et al. 2018); monotypic.`
- 아종: `P. s. anderssoni,"Lönnberg, 1923","se Russia, extreme ne China and Korean Pen.",SSP,Add (Song et al. 2018).` → 한반도는 P. s. anderssoni.
- 페이지: https://www.worldbirdnames.org/bow/crows/ (v15.2 표기), 시트 CSV: https://docs.google.com/spreadsheets/d/e/2PACX-1vTmLDAgrFrQXmUSd7-KbWHN6XzJLklmm6HP28wFxbhSzVKPE4yHq-GmroLuqaCWiA/pub?gid=546146977&single=true&output=csv
- 위키백과(Oriental magpie): 「A 2018 study of DNA sequences of all the taxa in the genus Pica led to the split-up of the genus into multiple species, including the Oriental magpie, separated from the Eurasian magpie.」

## 몸길이 — "46cm"
- 국립생물자원관: 「몸 전체 길이는 46cm이다.」 — https://species.nibr.go.kr/gwsvc/digital/api/v1/public/bisp-conts/get-cn-data/120000532854
- 차이: 영문 위키백과 「It is 45 cm long.」 (HBW 인용). 국립생물자원관 값 사용.

## 날개편길이 — TODO (출처 없음)

## 상태 — "텃새" / seen 1–12
- 국립생물자원관: 「도시와 농촌 등 평지에 살며 우리나라 대표적인 텃새이다.」「전국에 서식하고」; 국내분포 「전국」(한반도의생물다양성시스템고도화 2018).
- '흔한'이라는 말은 국립생물자원관 문장에 없어 붙이지 않음('대표적인'만 있음).

## 번식 — breed [2,3,4,5,6]
- 국립생물자원관: 「나무, 전신주 등에 둥지를 틀고 2월부터 번식을 시작한다.」「비번식기에는 무리를 지어 생활한다.」
- Frontiers 2026(서울대 캠퍼스, 1998년부터 장기 조사): 「Breeding of magpies starts from December of previous year, but intense breeding activity usually begins around late January.」, 「Our core fieldwork with accessing the nests is conducted between early March to mid-June.」, 「A breeding event, from nest building to fledging of nestlings, lasts approximately 4.5 months.」 — https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2026.1842756/full
- 참고(홍콩 개체군 P. s. serica, 값에는 안 씀): HKBWS 「Nest construction often begins in December … Young typically fledge between late March and mid-July」(요약 인용).
- 판단: 시작은 국립생물자원관의 2월, 끝은 서울 연구의 둥지 조사 종료(6월 중순)로 둠. 산란~육추만 엄밀히 따지면 2월이 빠질 수 있음 → todo.
- 국문 위키백과의 「산란기는 2-5월」은 각주가 없어 쓰지 않음.

## 서식지
- 국립생물자원관: 「도시와 농촌 등 평지에 살며」, 「나무, 전신주 등에 둥지를 틀고」.

## 형태·동정 포인트·art
- 국립생물자원관: 「윗면은 푸른 광택이 있는 검은색이고 배는 흰색이다. 어깨에는 흰색 반점이 있다. 날 때 흰색의 첫째날개깃이 뚜렷하게 보인다.」
- HKBWS: 「Head to breast and most of upperparts black. Scapulars white. Upperwing black, glossed greenish blue on secondaries and tertials. Flanks and central underparts white. Tail black, glossed with green and reddish purple.」 — https://avifauna.hkbws.org.hk/species/0260/033600
- 위키백과(Oriental magpie): 「slightly smaller, with a proportionally shorter tail and longer bill … darker with less white in the plumage」, 광택은 출처에 따라 「either bluer, less green iridescence … or conversely, more green」, 「The rump plumage is mostly black, with narrow, often greyish-white band」. — https://en.wikipedia.org/wiki/Oriental_magpie
- 위키백과(Eurasian magpie, HBW 인용 [23]): 「the primaries have white inner webs, conspicuous when the wing is open」, 「The legs and bill are black; the iris is dark brown.」 — https://en.wikipedia.org/wiki/Eurasian_magpie (Pica pica 기준이라 todo에 표시)

## 암수
- HKBWS: 「Sexes similar.」

## 어린새
- HKBWS: 「Juvenile is similar to adult but duller, with black areas of plumage sooty matt black, white areas tinged buff. Becoming much as adult by late summer.」
- 위키백과(Eurasian magpie [22]): 「Their tail is shorter than that of the adults'.」

## 유사종
- 물까치: 국립생물자원관 물까치 개요 「몸길이는 37cm」「머리는 검은색, 등은 회색 … 날개와 꼬리는 엷은 청색」.

## art.scene
- 평지 농촌(국립생물자원관), 2월 번식 시작(둥지 있는 늦겨울 나무). 사람·구조물 배제를 위해 전신주는 그리지 않도록 명시.
