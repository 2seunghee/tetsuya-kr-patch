# 현재 상태 (2026-10-06, 3차 검수 반영)

## 대상과 지원 원본

- Gambler Densetsu Tetsuya - Yomigaeru Densetsu (Japan).gba — 헤더 TETSUYA/ATYJ/E7, 8 MiB,
  SHA-256 `65e8eb749a88c18c02ea8bf783b62f0cd7a39f0e38f550e7be124172016c08bd` (유일한 지원 원본, `config/build.json`).
- 산출물(개발 정책, **비배포**): `out/tetsuya-kr.gba`(16 MiB) + `out/tetsuya-kr.ips` + `out/build-report.json`
  (`evidence/build-report-dev-20261005.json`에 사본). 빌드 명령 `python tools/build.py --policy development`.

## 확립된 사실

- 대사 엔진(`0x080325e0`): 11 bank → sub → message 포인터 계층, 2바이트 BE 글리프 코드 + 고정폭 제어코드, 0xFD/0xFF 종료, 0xFE 줄바꿈.
  글리프 966개(16×16 8bpp, 12px 피치, 18칸×2줄)를 `config/glyph_table.json`으로 전부 식별(전사 오류 21건은 용어집 에이전트의 문맥 검토로 교정).
- 모집단: 고유 메시지 **2,564개 / 40,799자**(정확값). 대사 엔진 밖 텍스트(G-01~G-06)는 `research/runtime-survey-20261005.md` 참조.

## 번역 상태

- 2,564 / 2,564 메시지 `reviewed`(에이전트 초벌 23청크 → 2차 용어 통일 검수 ~85건 → 3차 어색함·오역 검수 186건, 모두 `assets/translation/drafts/*.reviewed.json`에 반영).
  기계 검사(제어·괄호 토큰 보존, 종료자, 2줄×18칸, 글리프 공급) **전량 통과**. 검수 기록과 사람 결정 보류 항목은 `research/translation-notes-20261005.md`.
- 사람 승인(`approved`)은 아직 없음: 단치 1인칭·의문형 표기, 현대 속어 허용, 리사 쪽지·잰말놀이 창작, 별명 표기 등은 사람 결정 대기. 상태가 `approved`로 오르기 전엔 릴리스 후보가 아니다.

## 빌드·검증 상태

- 빌드: 2,564 메시지 재배치, 새 글리프 839개(bank 4~7), 확장 320,806바이트, Expected Write 2,566건(원본 영역 7,686바이트 변경: 포인터 슬롯 + 리터럴 2곳),
  최종 diff 전수 대조 통과. 산출물 SHA-256은 build-report 참조.
- 실행 관측(emucap/MesenCE, 원본 BIOS): 프롤로그·시장 장면의 한글 표시 확인(`work/emucap/dev1`, `dev2`, `dev3`). 선택지·{BLK} 타일 토큰·분기 메시지의
  실행 관측은 아직 부분적(필드 초반까지). 긴 연속 입력에서 emucap `cleanup_failed`가 산발적으로 발생해 재시도 로직을 추가함.

## 미해결 조건과 다음 행동

1. 사람 검수(DEC-003): 번역 품질·용어·말투 승인 → `reviewed/approved` 전환 → 릴리스 정책 빌드.
2. 실행 QA 확장: 선택지(퀴즈), {BLK} 타일 토큰, 분기(0x70~0x73) 메시지, 1947년 이후 장면, 엔딩까지의 경로. 세이브 스테이트 분할로 긴 경로를 안정화.
3. 대사 엔진 밖 텍스트: 화자 이름표 30종, 타이틀 메뉴 3항목, 슬롯 화면 4문구, 대국 HUD(운/힘)·라운드 라벨(동/남/1~4/국/본장/점/N연장/동남서북/계속/세이브)을 한글 스프라이트로 교체(`research/graphics-text-20261005.md`, DEC-005).
   타이틀 순환 자막 13행은 주제가 가사라 원본 유지. 로고·저작권 표기 유지. 역(役) 이름·점수 결과 화면 등 아직 보지 못한 화면은 미조사.
4. 실기·다른 에뮬레이터(mGBA 등) 호환 확인(16 MiB 확장 ROM).
