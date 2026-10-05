# 채택 글꼴 원천

| ID | 파일 | 출처·버전 | 라이선스 | 용도 |
|---|---|---|---|---|
| FNT-001 | `galmuri/Galmuri11.bdf` | quiple/galmuri v2.40.4 릴리스 zip(sha256 c8b3d986…60e7) | SIL OFL 1.1 (`galmuri/LICENSE.txt`) | 대사 엔진 한글·기호 글리프(11px, 12px 피치) |

파일 해시는 `config/build.json`의 `font.sha256`이 기준이며 빌드가 검증한다. 변환 규칙(ascent 14 기준 배치, 폭 12 미만 글리프 중앙 정렬,
1px 우하단 그림자 값 2)은 `tools/bdffont.py`에 있다. 사람 승인 범위: DEC-001 대기.
