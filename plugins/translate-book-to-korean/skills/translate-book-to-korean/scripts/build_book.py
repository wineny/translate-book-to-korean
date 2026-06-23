#!/usr/bin/env python3
"""
번역된 섹션(.ko.md)들을 '에디토리얼 단행본' PDF로 디자인.
사용: python build_book.py <config.json>
의존: pymupdf, markdown (pip install pymupdf markdown), 그리고 Google Chrome(headless 렌더용).

config.json 스키마:
{
  "translated_dir": "translated",          # .ko.md 들이 있는 폴더
  "output": "final/Book_KO_book.pdf",
  "theme": "cream-vermillion",             # 아래 THEMES 키 (또는 custom 색 dict)
  "page": "152x226",                       # mm, 신국판 기본
  "cover": {
    "title_lines": ["THE","MOM","TEST"],   # 표지 큰 제목 (행 단위)
    "kicker": "스타트업 고전 · 한국어판",
    "subtitle": "여러 줄 가능\\n<br>로 줄바꿈",
    "author": "Rob Fitzpatrick 지음",
    "footer": "비공식 한국어 번역본 · 학습용"
  },
  "running": {"ko": "맘 테스트", "en": "THE MOM TEST"},
  "sections": [
    {"file":"00_introduction.ko.md","label":"여는 글","title":"서문","sub":"진실은 캐내는 것"},
    {"file":"01_..ko.md","label":"1","title":"맘 테스트","sub":"엄마도 못 속이는 질문법"}
  ]
}
label 이 숫자면 챕터(고스트 숫자 표시), 아니면 라벨 그대로.
각 .ko.md 의 첫 H1은 표지 디자인으로 대체되므로 제거된다.
"""
import sys, os, re, json, glob, shutil, subprocess

THEMES = {
    # paper, paper2, ink, ink2, accent, accent2, rule, rule2
    "cream-vermillion": ["#f7f1e6","#f1e8d6","#231d15","#6b6052","#c23a23","#8f2916","#dccdb2","#cbb893"],
    "ivory-navy":       ["#f6f3ec","#ece6d8","#1c2331","#54607a","#2f4a73","#1d3457","#d6ceba","#c2b79c"],
    "paper-forest":     ["#f4f2e9","#e7e6d5","#1f2419","#555f4a","#3f6b3a","#2a4a27","#d2d2b8","#bcbd99"],
    "linen-plum":       ["#f6f1ee","#ece1da","#241b22","#675a62","#7d3552","#5a2138","#dccbcf","#cab2bb"],
    "snow-charcoal":    ["#f7f5f1","#e9e6df","#1a1a1a","#5c5c5c","#b4452e","#8a3320","#d8d4ca","#c3bdaf"],
}

def hex2rgb(h):
    h=h.lstrip("#"); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))

def md_section(path):
    txt = open(path).read().strip()
    txt = re.sub(r'^#\s+.*\n', '', txt, count=1).strip()   # 첫 H1 제거
    import markdown
    return markdown.markdown(txt, extensions=['extra','sane_lists','nl2br'])

def classify_blockquotes(htmltext):
    def repl(m):
        inner = m.group(1)
        if '경험 법칙' in inner or '경험법칙' in inner:
            x = re.sub(r'<strong>\s*경험\s*법칙\s*:?\s*</strong>\s*','',inner)
            x = re.sub(r'경험\s*법칙\s*:?\s*','',x)
            x = re.sub(r'(<p>)\s*[:：]\s*', r'\1', x, count=1)
            x = re.sub(r'^\s*[:：]\s*','',x)
            return f'<aside class="rule"><span class="rule-tag">경험 법칙</span><div class="rule-body">{x}</div></aside>'
        if re.search(r'<strong>[^<]{1,10}:</strong>', inner):
            return f'<blockquote class="dialogue">{inner}</blockquote>'
        return f'<blockquote class="quote">{inner}</blockquote>'
    return re.sub(r'<blockquote>(.*?)</blockquote>', repl, htmltext, flags=re.S)

def drop_cap(body):
    m = re.search(r'<p>(.)', body)
    if m:
        ch=m.group(1)
        body=body.replace(f'<p>{ch}', f'<p class="lead"><span class="dropcap">{ch}</span>',1)
    return body

CSS_TMPL = r'''
:root{ --paper:%(paper)s; --paper-2:%(paper2)s; --ink:%(ink)s; --ink-2:%(ink2)s;
  --accent:%(accent)s; --accent-2:%(accent2)s; --rule:%(rule)s; --rule-2:%(rule2)s; }
@page{ size:%(pw)smm %(ph)smm; margin:16mm 18mm 20mm 18mm; }
*{ box-sizing:border-box; } html,body{ margin:0; padding:0; }
body{ background:var(--paper); color:var(--ink);
  font-family:'나눔명조','Nanum Myeongjo','AppleMyungjo','Noto Serif KR',serif;
  font-size:11pt; line-height:1.8; word-break:keep-all; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
h1,h2,h3{ font-family:'Gmarket Sans','G마켓 산스 TTF','배달의민족 도현','Noto Sans CJK KR',sans-serif; }
.cover{ height:%(coverh)smm; display:flex; align-items:center; justify-content:center;
  background:radial-gradient(120%% 90%% at 50%% 8%%, #ffffff10 0%%, var(--paper) 55%%, var(--paper-2) 100%%);
  page-break-after:always; position:relative; }
.cover:before{ content:""; position:absolute; inset:9mm; border:1.4pt solid var(--accent); opacity:.85; }
.cover:after{ content:""; position:absolute; inset:11mm; border:.6pt solid var(--rule-2); }
.cover-frame{ text-align:center; padding:0 12mm; position:relative; z-index:2; }
.cover-kicker{ font-family:'Gmarket Sans',sans-serif; letter-spacing:.42em; font-size:9pt; color:var(--accent-2); margin-bottom:7mm; text-indent:.42em; }
.cover-title{ font-family:'Gmarket Sans',sans-serif; font-size:62pt; line-height:.98; margin:2mm 0 0; font-weight:700; letter-spacing:.01em; color:var(--ink); }
.cover-title:after{ content:""; display:block; width:26mm; height:2.2pt; background:var(--accent); margin:6mm auto 0; }
.cover-sub{ font-size:11.5pt; line-height:1.85; color:var(--ink-2); margin:11mm auto 0; max-width:80%%; }
.cover-author{ font-family:'Gmarket Sans',sans-serif; font-size:11pt; margin-top:12mm; color:var(--ink); }
.cover-foot{ font-size:8.5pt; color:var(--ink-2); letter-spacing:.12em; margin-top:3mm; }
.toc{ page-break-after:always; padding-top:6mm; }
.toc-head{ border-bottom:2pt solid var(--ink); padding-bottom:3mm; margin-bottom:8mm; }
.toc-head-en{ font-family:'Gmarket Sans',sans-serif; letter-spacing:.4em; font-size:8.5pt; color:var(--accent); }
.toc-head h2{ font-size:26pt; margin:2mm 0 0; }
.toc-list{ list-style:none; margin:0; padding:0; }
.toc-list li{ display:grid; grid-template-columns:8mm 1fr; align-items:baseline; column-gap:5mm; padding:3.1mm 0; border-bottom:.5pt dotted var(--rule-2); }
.toc-n{ font-family:'Gmarket Sans',sans-serif; font-weight:700; color:var(--accent); text-align:center; font-size:13pt; }
.toc-row2{ display:flex; justify-content:space-between; align-items:baseline; gap:5mm; min-width:0; }
.toc-t{ font-family:'Gmarket Sans',sans-serif; font-size:12.5pt; color:var(--ink); flex:none; }
.toc-s{ font-size:8.5pt; color:var(--ink-2); text-align:right; flex:1 1 auto; min-width:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.chapter{ page-break-before:always; }
.chap-open{ position:relative; padding:22mm 0 11mm; margin-bottom:8mm; overflow:hidden; border-bottom:1.2pt solid var(--rule); }
.chap-kicker{ font-family:'Gmarket Sans',sans-serif; letter-spacing:.38em; font-size:9pt; color:var(--accent); text-indent:.38em; }
.chap-title{ font-size:33pt; line-height:1.12; margin:5mm 0 0; letter-spacing:-.01em; }
.chap-sub{ font-size:11.5pt; color:var(--ink-2); margin-top:4mm; font-style:italic; font-family:'나눔명조',serif; }
.chap-ornament{ position:absolute; top:10mm; right:1mm; font-family:'Gmarket Sans',sans-serif; font-size:54pt; font-weight:700; color:%(ghost)s; line-height:1; }
.chap-body p{ margin:0 0 3.2mm; text-align:justify; } .lead{ margin-top:0; }
.dropcap{ float:left; font-family:'Gmarket Sans',sans-serif; font-weight:700; color:var(--accent); font-size:40pt; line-height:.82; padding:1mm 2.4mm 0 0; }
.chap-body h2{ font-size:16pt; margin:9mm 0 3mm; border-top:.5pt solid var(--rule); padding-top:4mm; }
.chap-body h3{ font-size:12.5pt; margin:6mm 0 2mm; color:var(--accent-2); }
strong{ font-weight:700; color:var(--ink); } em{ color:var(--ink-2); }
a{ color:var(--accent-2); text-decoration:none; }
ul,ol{ margin:2mm 0 4mm; padding-left:6mm; } li{ margin:1.2mm 0; }
hr{ border:none; text-align:center; margin:8mm 0; } hr:after{ content:"\2767"; color:var(--rule-2); font-size:14pt; }
code{ background:var(--paper-2); padding:0 1mm; border-radius:1mm; font-size:.92em; font-family:'Gmarket Sans',monospace; }
blockquote.dialogue{ margin:5mm 0; padding:5mm 6mm; background:%(card)s; border-left:2.4pt solid var(--accent); font-size:10.6pt; line-height:1.8; }
blockquote.dialogue p{ margin:0 0 2mm; } blockquote.dialogue p:last-child{ margin-bottom:0; }
blockquote.dialogue strong{ color:var(--accent-2); font-family:'Gmarket Sans',sans-serif; font-size:9.6pt; }
blockquote.dialogue em{ color:var(--ink-2); font-size:9.6pt; }
blockquote.quote{ margin:5mm 4mm; padding:1mm 0 1mm 6mm; border-left:2pt solid var(--rule-2); color:var(--ink-2); font-style:italic; }
aside.rule{ margin:5.5mm 0; padding:4.5mm 6mm; position:relative; background:%(card)s; border:.8pt solid var(--rule-2); border-radius:1.5mm; }
aside.rule .rule-tag{ position:absolute; top:-2.6mm; left:5mm; background:var(--accent); color:#fff; font-family:'Gmarket Sans',sans-serif; font-size:8pt; letter-spacing:.12em; padding:.8mm 3mm; border-radius:1mm; }
aside.rule .rule-body{ margin-top:1.5mm; font-family:'Gmarket Sans',sans-serif; font-size:10.4pt; line-height:1.7; color:var(--accent-2); }
aside.rule .rule-body p{ margin:0; }
'''

def build_html(cfg, base):
    theme = cfg.get("theme","cream-vermillion")
    pal = theme if isinstance(theme, list) else THEMES.get(theme, THEMES["cream-vermillion"])
    pw, ph = (cfg.get("page","152x226").split("x"))
    paper,paper2,ink,ink2,accent,accent2,rule,rule2 = pal
    # ghost number / card 색은 accent 기반 반투명
    css = CSS_TMPL % dict(paper=paper,paper2=paper2,ink=ink,ink2=ink2,accent=accent,
        accent2=accent2,rule=rule,rule2=rule2, pw=pw, ph=ph, coverh=str(int(ph)-40),
        ghost="rgba(0,0,0,.10)", card=paper2)
    tdir = os.path.join(base, cfg.get("translated_dir","translated"))

    chapters=[]
    for s in cfg["sections"]:
        body = drop_cap(classify_blockquotes(md_section(os.path.join(tdir, s["file"]))))
        label=str(s["label"]); is_num=label.isdigit()
        kicker = f'CHAPTER {label}' if is_num else label
        ghost = (('0'+label) if is_num and len(label)==1 else label) if is_num else ''
        chapters.append(f'''<section class="chapter"><header class="chap-open">
<div class="chap-kicker">{kicker}</div><h1 class="chap-title">{s["title"]}</h1>
<div class="chap-sub">{s.get("sub","")}</div><div class="chap-ornament">{ghost}</div>
</header><div class="chap-body">{body}</div></section>''')

    c=cfg["cover"]
    title="".join(f"{ln}<br>" for ln in c["title_lines"]).rstrip("<br>")
    cover=f'''<section class="cover"><div class="cover-frame">
<div class="cover-kicker">{c.get("kicker","")}</div>
<h1 class="cover-title">{title}</h1>
<p class="cover-sub">{c.get("subtitle","")}</p>
<div class="cover-author">{c.get("author","")}</div>
<div class="cover-foot">{c.get("footer","")}</div></div></section>'''

    rows=[]
    for s in cfg["sections"]:
        n = s["label"] if str(s["label"]).isdigit() else "—"
        rows.append(f'<li><span class="toc-n">{n}</span><span class="toc-row2">'
                    f'<span class="toc-t">{s["title"]}</span><span class="toc-s">{s.get("sub","")}</span></span></li>')
    toc=f'<section class="toc"><div class="toc-head"><span class="toc-head-en">CONTENTS</span><h2>차례</h2></div><ol class="toc-list">{"".join(rows)}</ol></section>'

    html=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body>{cover}{toc}{"".join(chapters)}</body></html>'
    htmlpath=os.path.join(base, "final", "_book.html")
    os.makedirs(os.path.dirname(htmlpath), exist_ok=True)
    open(htmlpath,"w").write(html)
    return htmlpath, hex2rgb(paper), hex2rgb(accent), hex2rgb(ink2), cfg.get("running",{})

def render_pdf(htmlpath, outpath):
    chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not os.path.exists(chrome):
        chrome = shutil.which("google-chrome") or shutil.which("chromium") or chrome
    raw = outpath + ".raw.pdf"
    subprocess.run([chrome,"--headless=new","--disable-gpu","--no-pdf-header-footer",
        f"--print-to-pdf={raw}", f"file://{os.path.abspath(htmlpath)}"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return raw

def stamp(raw, outpath, paper_rgb, accent_rgb, gray_rgb, running):
    import fitz
    d=fitz.open(raw)
    fp=None
    g=glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font7/*/AssetData/NanumMyeongjo.ttc") \
      or glob.glob("/System/Library/Fonts/Supplemental/NanumMyeongjo*.ttc")
    if g: fp=g[0]
    ko=running.get("ko",""); en=running.get("en","")
    for i,page in enumerate(d):
        page.draw_rect(page.rect, color=paper_rgb, fill=paper_rgb, overlay=False)  # 풀블리드
        if i==0: continue
        w=page.rect.width; h=page.rect.height; y=h-26
        fn="NMJ" if fp else "helv"
        if fp: page.insert_font(fontfile=fp, fontname="NMJ")
        page.insert_text((w/2-3,y), str(i), fontsize=9, fontname=fn, color=gray_rgb)
        page.insert_text((w/2-9,y), "·", fontsize=9, fontname=fn, color=accent_rgb)
        page.insert_text((w/2+9,y), "·", fontsize=9, fontname=fn, color=accent_rgb)
        if i%2==0 and ko:
            page.insert_text((w-18-len(ko)*9.5,y), ko, fontsize=7.5, fontname=fn, color=gray_rgb)
        elif en:
            page.insert_text((18,y), en, fontsize=7.5, fontname="helv", color=gray_rgb)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    d.save(outpath, deflate=True, garbage=4)
    os.remove(raw)

def main():
    if len(sys.argv)<2:
        print("usage: python build_book.py <config.json>"); sys.exit(1)
    cfg=json.load(open(sys.argv[1]))
    base=os.path.dirname(os.path.abspath(sys.argv[1]))
    out=os.path.join(base, cfg.get("output","final/Book_KO_book.pdf"))
    htmlpath, paper, accent, gray, running = build_html(cfg, base)
    raw=render_pdf(htmlpath, out)
    stamp(raw, out, paper, accent, gray, running)
    import fitz
    print(f"OK -> {out} ({fitz.open(out).page_count} pages)")

if __name__=="__main__":
    main()
