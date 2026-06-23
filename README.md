# translate-book-to-korean

영어 원서/문서 **PDF를 자연스러운 한국어로 번역**하고, **출판물 같은 단행본 PDF로 디자인**까지 한 번에 해주는 Claude Code 스킬입니다.

> 번역투 없는 존댓말 + 핵심 용어 병기 + 에디토리얼 단행본 디자인이 기본 산출물입니다.

## 무엇을 하나

| 단계 | 내용 |
|---|---|
| 1. 추출 | PDF 텍스트 추출 + 머리말/꼬리말 자동 제거, 챕터 분할 |
| 2. 용어집 | 전권 일관성을 위한 용어집·스타일 시트(SSOT) 작성 |
| 3. 번역 | 섹션별 **병렬 에이전트**가 *번역 → 자기비평 → 개선* 3단계로 번역 (번역투 금지 규칙 적용) |
| 4. 검증 | 원문 대비 충실성·자연스러움·일관성 점검 후 수정 |
| 5. 디자인 | 크림 종이 + 세리프 본문의 **에디토리얼 단행본 PDF** 생성 (표지·차례·챕터 표지·드롭캡·쪽번호) |

## 설치

Claude Code에서:

```
/plugin marketplace add wineny/translate-book-to-korean
/plugin install translate-book-to-korean@translate-book-to-korean
```

## 사용

영어 PDF를 주면서 이렇게 말하면 됩니다:

```
이 PDF 한국어로 번역해서 책으로 만들어줘  (파일 경로 첨부)
```

문체(존댓말/한다체)나 디자인 테마는 시작할 때 바꿀 수 있습니다.

## 요구 사항

- Python: `pip install pymupdf markdown`
- **Google Chrome** (PDF 렌더링, headless)
- 한글 폰트: 나눔명조 · G마켓 산스 권장 (없으면 Noto Serif/Sans KR로 폴백)

## 디자인 테마

`cream-vermillion`(기본) · `ivory-navy` · `paper-forest` · `linen-plum` · `snow-charcoal`

## 구성

```
plugins/translate-book-to-korean/skills/translate-book-to-korean/
├── SKILL.md                       워크플로 + 기본값
├── scripts/extract_pdf.py         PDF → 텍스트/페이지 덤프
├── scripts/build_book.py          config 기반 단행본 PDF 빌더
└── references/translation_playbook.md  3단계 번역법·번역투 금지표·용어집 템플릿
```

## 참고

- 번역 품질은 원문을 직접 옮기되 의미를 보존하며, 화폐·수치·고유명사는 원문을 유지합니다.
- 이 스킬은 **번역 파이프라인 도구**만 제공합니다. 저작권이 있는 책을 번역해 배포하는 것은 사용자 책임입니다.

## 라이선스

MIT
