# 승부사전설 테쯔야 ~되살아나는 전설~ 한글 패치

Game Boy Advance 『勝負師伝説 哲也 甦る伝説』(Gambler Densetsu Tetsuya: Yomigaeru Densetsu, 일본판)의 비공식 한글 패치 프로젝트다.
패치 파일(IPS)만 배포하며, 게임 ROM·BIOS 등 저작권이 있는 원본은 포함하지 않는다. 원본은 직접 준비해야 한다.

## 지원 원본

| 항목 | 값 |
|---|---|
| 헤더 | `TETSUYA` / 게임 코드 `ATYJ` |
| 크기 | 8 MiB (8,388,608 bytes) |
| SHA-256 | `65e8eb749a88c18c02ea8bf783b62f0cd7a39f0e38f550e7be124172016c08bd` |

다른 덤프(트레이너·헤더 변형 등)에는 적용을 보장하지 않는다.

## 적용 방법

1. [Releases](../../releases)에서 `tetsuya-kr.ips`를 받는다.
2. Flips(Floating IPS), Lunar IPS 등 IPS 패처로 위 원본에 적용한다. 결과 ROM은 **16 MiB**로 확장된다(패치가 8 MiB를 덧붙인다).
3. 결과 파일의 SHA-256이 릴리스 노트의 값과 같은지 확인한다.

패치된 ROM은 Mesen2 계열(emucap/MesenCE)에서 프롤로그부터 대국 화면까지 한글 표시를 확인했다. mGBA·VBA-M·실기(플래시 카트)는 아직 검증하지 않았다.
16 MiB ROM을 지원하는 환경이어야 한다.

## 한글화 범위

- **대사 엔진 전체**: 시나리오·필드·대국 중 메시지 2,564개(40,799자). 나무위키 「마작의 제왕 테쯔야」 정발 표기(테쯔야, 바이닌, 제비뒤집기 등)를 우선한 용어집으로 번역했다.
- **그래픽 텍스트**: 화자 이름표 30종, 타이틀 메뉴(프리 대국/시나리오 대국/옵션), 슬롯 화면(처음부터/이어하기/시나리오 선택/대국 중), 대국 HUD(운/힘), 라운드 라벨(동·남·1~4국·본장·점·N연장·동남서북·계속·세이브).
- **원본 유지**: 타이틀 로고·저작권 표기(브랜딩), 타이틀 순환 자막(주제가 가사), 숫자·패 그래픽. 역(役) 이름과 점수 결과 화면 등 아직 조사하지 못한 화면은 일본어가 남아 있을 수 있다.

번역은 에이전트 초벌 → 용어 통일 검수 → 자연스러움·오역 검수의 3단계를 거쳤고, 기계 검사(제어 토큰 보존, 2줄×18칸, 글리프 공급)를 전량 통과했다.
남은 판단 항목(단치의 1인칭 표기, 일부 별명 표기 등)은 [research/translation-notes-20261005.md](research/translation-notes-20261005.md)에 있다.

## 기술 요약

- 대사 엔진: 2바이트 글리프 코드 + 고정폭 제어 코드. 글리프 테이블을 `0x08800000`으로 재배치해 16×16 한글 글리프 842개를 확장 영역에 추가했다.
- 글꼴: [Galmuri](https://github.com/quiple/galmuri) 11 (SIL OFL 1.1), 1px 그림자 처리. 이름표·스프라이트는 Galmuri 7/9/11/11-Bold를 크기에 맞게 썼다.
- 빌드: 원본을 읽기 전용으로 두고 모든 변경을 Expected Write 계획(겹침·전수 diff 검증)으로 적용한 뒤 ROM과 IPS를 낸다.
- 자세한 분석은 [research/](research/)의 텍스트 엔진·그래픽 텍스트·PoC 기록을 참고한다.

## 직접 빌드하기

```bash
# originals/ 에 지원 원본 ROM을 둔다 (git에 포함되지 않는다)
python tools/build.py --policy release
# 산출물: out/tetsuya-kr.gba, out/tetsuya-kr.ips, out/build-report.json
```

Python 3.10 이상이 필요하다. `tools/validate_translation.py`로 번역 데이터의 기계 검사를, `tools/emucap_nav.py`로 emucap 실행 검증을 할 수 있다(별도 설치 필요).

## 저장소 구성

| 위치 | 내용 |
|---|---|
| `assets/translation/` | 용어집, 추출 스크립트(원문·번역·상태), 검수 드래프트 |
| `assets/fonts/` | Galmuri BDF 원천과 라이선스 |
| `config/` | 원본 식별, 글리프 테이블, 이름표·스프라이트 텍스트 설정 |
| `tools/` | 추출·검증·빌드·실행 검증 스크립트 |
| `docs/` | 현재 상태와 사람 결정 기록 |
| `research/` | 분석 기록 |
| `evidence/` | 빌드 보고서, 검수 기록, 실행 스크린샷 |

## 크레딧과 라이선스

- 글꼴: Galmuri (quiple, SIL Open Font License 1.1)
- 프로젝트 템플릿·방법론: [create-retro-game-kr-patch](https://github.com/mcpads/create-retro-game-kr-patch)
- 실행 검증: emucap + Mesen2
- 용어 참고: 나무위키 「마작의 제왕 테쯔야」 문서의 정발 표기

이 저장소의 도구·문서·번역 데이터는 MIT 라이선스([LICENSE](LICENSE))를 따른다. 게임의 모든 권리는 원 권리자에게 있으며, 이 프로젝트는 권리자와 무관한 비공식 팬 번역이다.
