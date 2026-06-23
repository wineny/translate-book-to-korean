#!/usr/bin/env python3
"""
PDF 텍스트 추출 + 머리말/꼬리말 제거 + 페이지별 덤프.
사용: python extract_pdf.py <input.pdf> <outdir>
출력:
  <outdir>/raw.txt          전체 텍스트(머리말/꼬리말 제거)
  <outdir>/pages.txt        페이지별 구분(=== PAGE n === 마커) — 챕터 경계 판단용
  <outdir>/_meta.txt        쪽수/단어수/반복 머리말 후보
의존: pymupdf (pip install pymupdf)
챕터 분할은 모델이 pages.txt를 보고 판단해 chunks/<NN_slug>.en.txt 로 직접 저장한다.
"""
import sys, os, re
from collections import Counter

def main():
    if len(sys.argv) < 3:
        print("usage: python extract_pdf.py <input.pdf> <outdir>"); sys.exit(1)
    pdf, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    import fitz
    doc = fitz.open(pdf)

    # 1) 반복 머리말/꼬리말 후보 탐지: 각 페이지 첫/끝 줄 빈도
    edge = Counter()
    for pg in doc:
        lines = [l.strip() for l in pg.get_text().split("\n") if l.strip()]
        for l in lines[:2] + lines[-2:]:
            if len(l) < 60:
                edge[l] += 1
    th = max(3, doc.page_count // 4)
    boiler = {l for l, c in edge.items() if c >= th and not l.isdigit()}

    def clean(t):
        out = []
        for l in t.split("\n"):
            s = l.strip()
            if s in boiler: continue
            if re.fullmatch(r'\d{1,4}', s): continue          # 단독 쪽번호
            if re.search(r'(www\.|\.com|\.org|http)', s) and len(s) < 60: continue
            out.append(l)
        return re.sub(r'\n{3,}', '\n\n', "\n".join(out)).strip()

    raw_parts, page_parts = [], []
    for i, pg in enumerate(doc):
        c = clean(pg.get_text())
        raw_parts.append(c)
        page_parts.append(f"=== PAGE {i+1} ===\n{c}")
    raw = "\n\n".join(raw_parts)

    open(os.path.join(outdir, "raw.txt"), "w").write(raw)
    open(os.path.join(outdir, "pages.txt"), "w").write("\n\n".join(page_parts))
    with open(os.path.join(outdir, "_meta.txt"), "w") as f:
        f.write(f"pages: {doc.page_count}\n")
        f.write(f"words(approx): {len(raw.split())}\n")
        f.write(f"chars: {len(raw)}\n")
        f.write("removed boilerplate candidates:\n")
        for l in sorted(boiler): f.write(f"  - {l!r}\n")
    print(f"OK: {doc.page_count}p, ~{len(raw.split())} words -> {outdir}/")
    print("다음: pages.txt에서 챕터 경계를 판단해 chunks/<NN_slug>.en.txt 로 섹션을 나눠 저장하세요.")

if __name__ == "__main__":
    main()
