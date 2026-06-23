---
name: translate-book-to-korean
description: >
  영어 원서/문서 PDF를 자연스러운 한국어로 번역하고, 출판물 같은 단행본 PDF로 디자인까지 한 번에 만든다.
  사용자가 영어 PDF·원서·전자책·논문·문서를 "한국어로 번역해줘", "번역해서 책으로 만들어줘",
  "원서 번역", "PDF 번역", "자연스럽게 번역", "번역본 PDF", "ebook 번역", "영한 번역해서 정리해줘"
  라고 하거나, 영어로 된 긴 문서 파일을 주며 한국어 결과물을 원할 때 반드시 사용한다.
  번역투 없는 자연스러운 한국어 + 존댓말 + 핵심 용어 병기 + 에디토리얼 단행본 디자인이 기본 산출물이다.
  단순 한두 문장 번역이나 이미 한국어인 글 윤문(→humanize-korean)과는 구분된다.
---

# 영어 원서 PDF → 자연스러운 한국어 단행본

영어 PDF를 (1) 자연스러운 한국어로 번역하고 (2) 출판물 같은 PDF로 디자인하는 엔드투엔드 파이프라인.

## 기본값 (사용자가 다르게 말하지 않으면 이대로)
- **문체**: `~합니다/하세요` 존댓말, 저자의 목소리 유지
- **형식**: 한국어 본문 + 핵심 용어 첫 등장에만 영어 병기 — `맘 테스트(The Mom Test)`
- **디자인**: 따뜻한 에디토리얼 단행본 (크림 종이 + 버밀리언 액센트, 본문 나눔명조 + 제목 G마켓 산스)
- 시작할 때 문체·디자인 테마를 바꿀지 한 번만 가볍게 확인하고, 답이 없으면 기본값으로 진행한다.

## 의존성
- `pip install pymupdf markdown` · 렌더링에 **Google Chrome**(headless) 필요
- 한글 폰트: 나눔명조·G마켓 산스 권장(없으면 Noto Serif/Sans KR로 폴백)

## 워크플로

### 0. 준비
작업 폴더를 만든다(예: `<book>-translation/`). 하위에 `chunks/ translated/ glossary/ final/`.
사용자에게 문체/테마 기본값을 쓸지 한 번 확인.

### 1. 추출 + 구조 파악
```
python <skill>/scripts/extract_pdf.py <input.pdf> <work>/source
```
`source/pages.txt`를 읽어 **챕터/섹션 경계**를 판단하고, 섹션별 원문을 `chunks/NN_slug.en.txt`로 저장한다(서문·각 장·결론 등). 섹션이 너무 길면(>4000단어) 단락 경계로 더 쪼갠다.

### 2. 용어집 + 스타일 시트 (SSOT)
`references/translation_playbook.md`를 읽는다. 원문을 훑어 반복되는 핵심 용어·고유명사를 뽑아 `glossary/style_and_glossary.md`에 용어집 표 + 문체 규칙을 작성한다. **전권 일관성의 단일 기준**이며 모든 번역 에이전트가 공유한다.

### 3. 번역 (병렬 에이전트)
먼저 **파일럿 1~2개 섹션**을 번역해 톤을 확인받는다. OK면 나머지 섹션을 **병렬 서브에이전트**(executor, model=opus)로 번역한다. 각 에이전트 지시에 반드시 포함:
- `glossary/style_and_glossary.md` 필독
- **3단계 번역**(번역→자기비평→개선) + 번역투 금지 + 충실성(통화·수치 원문 유지)
- 결과를 `translated/NN_slug.ko.md`에 저장, 첫 줄에 `# <장 제목>`
(상세 규칙은 `references/translation_playbook.md`)

### 4. 검증 + 수정
검증 서브에이전트(verifier)로 섹션을 원문과 대조: **충실성·자연스러움·일관성**. 발견 이슈는 SSOT 용어를 확정한 뒤 수정 에이전트로 반영한다. 섹션 간 용어 불일치(예: 같은 단어 다른 역어)를 특히 잡는다.
(선택) `humanize-korean` 스킬이 있으면 번역 후 윤문 패스로 연결.

### 5. 조립 + 책 디자인
`build_book.py`용 `config.json`을 작성하고 실행한다:
```
python <skill>/scripts/build_book.py <work>/config.json
```
표지 제목·부제·저자·섹션 목록(파일/라벨/제목/한줄부제)·테마를 config에 채운다. 스크립트가 HTML 생성 → Chrome 렌더 → **크림 풀블리드 + 쪽번호/러닝푸터**(PyMuPDF)까지 처리해 `final/...book.pdf`를 만든다.
config 스키마와 테마 목록은 `scripts/build_book.py` 상단 주석 참고. 테마: `cream-vermillion`(기본), `ivory-navy`, `paper-forest`, `linen-plum`, `snow-charcoal`.

### 6. 확인 + 전달
PDF의 표지·차례·챕터 표지·대화/콜아웃 페이지를 이미지로 렌더해 **눈으로 확인**(`fitz` get_pixmap)하고, 어긋난 부분을 고친 뒤 사용자에게 전달한다. 마크다운 번역본(`final/*.md`)도 함께 제공.

## 산출물
- `final/<book>_book.pdf` — 디자인 단행본 (메인)
- `final/<book>.md` — 한국어 번역 마크다운
- `translated/*.ko.md` — 섹션별 번역, `chunks/*.en.txt` — 추출 원문, `glossary/` — 용어집

## 팁
- 번역·검증은 **서브에이전트 병렬**로 (메인 컨텍스트 보존, 속도↑).
- 디자인은 **렌더링 → 눈으로 확인 → 수정** 반복이 핵심. 한 번에 완벽하길 기대하지 말 것.
- 통화/단위 임의 현지화는 충실성 위반. 원문 유지가 기본.
