# 현재 상태 (2026-10-05)

## 대상과 지원 원본

- Gambler Densetsu Tetsuya - Yomigaeru Densetsu (Japan).gba — 헤더 TETSUYA/ATYJ/E7, 8 MiB,
  SHA-256 `65e8eb749a88c18c02ea8bf783b62f0cd7a39f0e38f550e7be124172016c08bd` (유일한 지원 원본, `config/build.json`).
- 산출물: `out/tetsuya-kr.gba`(16 MiB) + `out/tetsuya-kr.ips` + `out/build-report.json`. 현재 빌드는 **개발 정책(비배포)**.

## 확립된 사실 (근거: `research/text-engine-20261005.md`)

- 본편 대사는 단일 엔진(`0x080325e0`)이 11개 bank → sub → message 포인터 계층으로 읽는 2바이트 글리프 코드 스트림이다.
- 글리프 966개(16×16 8bpp, 12px 피치, 18칸×2줄)는 `config/glyph_table.json`으로 전부 식별했다.
- 모집단: 고유 메시지 2,564개 / 40,799자(정확값). 추출 `tools/extract_script.py` → `assets/translation/`.

## 채택한 설계 (사람 승인 대기: `docs/decisions.md`)

- 16 MiB 확장, 글리프 bank 테이블 재배치(리터럴 2곳), 새 코드 0x400~ (최대 3072 글리프), 메시지 전체 재배치(포인터 테이블만 수정).
- 글꼴 Galmuri11(OFL) → 1px 그림자 합성. 번역 검사 `tools/validate_translation.py`, 빌드 `tools/build.py`(Expected Write 검증 + IPS).

## 검증 상태

- PoC 통과(`research/poc-20261005.md`): 프롤로그 3메시지가 실제 경로에서 한글로 표시(emucap/Mesen2, `work/emucap/poc1`).
- 미검증: 선택지·분기 메시지의 재배치, {BLK} 동적 타일 토큰 표시, 글리프 예산 상한, 실기.

## 미해결 조건과 다음 행동

1. 대사 엔진 밖 텍스트(타이틀 메뉴, 자막, 마작 UI·역 이름·점수)의 소비 경로 — 실행 스크린샷으로 목록화 중(`work/emucap/survey1`).
2. 번역 초벌: 용어집(`assets/translation/glossary.md`) 생성 후 bank 단위 병렬 초벌 → `drafts/` → `tools/merge_drafts.py` → 검사 → 빌드 → 실행 관측.
3. 사람 결정 대기: 글꼴·확장·범위·용어(DEC-001~004). 그 사이 번역·빌드·관측은 개발 정책으로 진행.
