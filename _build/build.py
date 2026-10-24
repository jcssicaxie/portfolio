#!/usr/bin/env python3
"""
jcssicaxie.com — static site builder.

Every page of the portfolio is generated from `_build/content.json`, so the
masthead, colophon, project template and archive stay consistent.  The output
is plain HTML committed to the repo, which keeps GitHub Pages deployment
exactly as it was (no Actions, no Node, no dependencies at runtime).

    python3 _build/build.py            # rebuild all pages
    python3 _build/build.py --images   # also (re)generate responsive images

Image derivatives (WebP, several widths) are written to assets/img/ and listed
in _build/images.json.  Generating new ones needs Pillow (pip3 install pillow);
video posters need ffmpeg.  Without them the build still works: pages fall back
to the original files for any image that has no derivative yet.
"""
from __future__ import annotations

import datetime as _dt
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
C = json.loads((BUILD / "content.json").read_text("utf-8"))
SITE = C["site"]
MAN_PATH = BUILD / "images.json"
MAN: dict = json.loads(MAN_PATH.read_text("utf-8")) if MAN_PATH.exists() else {}
OUT_IMG = ROOT / "assets" / "img"
WIDTHS = [640, 1200, 2000]
FORCE_IMAGES = "--images" in sys.argv
TODAY = _dt.date.today()
STAMP = f"{TODAY.year}Y {TODAY.month:02d}M {TODAY.day:02d}D"

try:
    from PIL import Image, ImageOps  # type: ignore

    Image.MAX_IMAGE_PIXELS = None
    HAS_PIL = True
except Exception:  # pragma: no cover
    HAS_PIL = False

HAS_FFMPEG = shutil.which("ffmpeg") is not None
WARNED: set[str] = set()


# ─────────────────────────────────────────────────────────── helpers ──
def attr(s: str) -> str:
    """Escape a value for a double-quoted attribute (keeps existing entities)."""
    return str(s).replace('"', "&quot;").replace("<", "&lt;")


def plain(s: str) -> str:
    """Strip tags and decode entities, for <title>, meta descriptions, alt text."""
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def url(path: str, depth: str) -> str:
    return depth + quote(path)


def key_for(src: str) -> str:
    stem = src.replace("images/", "", 1).rsplit(".", 1)[0].lower()
    return re.sub(r"[^a-z0-9]+", "-", stem).strip("-")


def ensure_image(src: str) -> dict | None:
    entry = MAN.get(src)
    if entry and not FORCE_IMAGES and all(
        (OUT_IMG / f"{entry['key']}-{w}.webp").exists() for w in entry["widths"]
    ):
        return entry
    if entry and not HAS_PIL:
        return entry
    if not HAS_PIL:
        if src not in WARNED:
            WARNED.add(src)
            print(f"  ! no derivative for {src} (install Pillow to generate)")
        return None
    path = ROOT / src
    if not path.exists():
        print(f"  ! missing image {src}")
        return None
    raw = Image.open(path)
    alpha = raw.mode in ("RGBA", "LA") or (raw.mode == "P" and "transparency" in raw.info)
    orient = raw.getexif().get(0x0112, 1)
    w, h = raw.size if orient not in (5, 6, 7, 8) else raw.size[::-1]
    widths = sorted({x for x in WIDTHS if x < w} | {min(w, WIDTHS[-1])})
    key = key_for(src)
    if not FORCE_IMAGES and all((OUT_IMG / f"{key}-{tw}.webp").exists() for tw in widths):
        MAN[src] = {"key": key, "w": w, "h": h, "widths": widths, "alpha": alpha}
        save_manifest()
        return MAN[src]
    im = ImageOps.exif_transpose(raw).convert("RGBA" if alpha else "RGB")
    w, h = im.size
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    for tw in widths:
        th = round(h * tw / w)
        out = im if tw == w else im.resize((tw, th), Image.LANCZOS)
        out.save(OUT_IMG / f"{key}-{tw}.webp", "WEBP", quality=80, method=5)
    entry = {"key": key, "w": w, "h": h, "widths": widths, "alpha": alpha}
    MAN[src] = entry
    save_manifest()
    print(f"  + {src} → {len(widths)} sizes", flush=True)
    return entry


def save_manifest():
    MAN_PATH.write_text(json.dumps(MAN, indent=1, ensure_ascii=False, sort_keys=True), "utf-8")


def img(src, alt, depth, sizes="100vw", cls="", eager=False, extra=""):
    e = ensure_image(src)
    loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    if not e:
        return f'<img{c} src="{url(src, depth)}" alt="{attr(plain(alt))}" {loading} decoding="async"{extra}>'
    srcset = ", ".join(f"{depth}assets/img/{e['key']}-{w}.webp {w}w" for w in e["widths"])
    mid = e["widths"][min(1, len(e["widths"]) - 1)]
    return (
        f'<img{c} src="{depth}assets/img/{e["key"]}-{mid}.webp" srcset="{srcset}" sizes="{sizes}" '
        f'width="{e["w"]}" height="{e["h"]}" alt="{attr(plain(alt))}" {loading} decoding="async"{extra}>'
    )


def thumb(src, depth, w=640):
    e = ensure_image(src)
    if not e:
        return url(src, depth)
    best = min(e["widths"], key=lambda x: abs(x - w))
    return f"{depth}assets/img/{e['key']}-{best}.webp"


def ensure_poster(src: str) -> dict | None:
    k = "video:" + src
    entry = MAN.get(k)
    if entry and (OUT_IMG / entry["poster"]).exists() and not FORCE_IMAGES:
        return entry
    if not (HAS_FFMPEG and HAS_PIL):
        return entry
    with tempfile.TemporaryDirectory() as td:
        frame = Path(td) / "f.png"
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-ss", "0.3", "-i", str(ROOT / src), "-frames:v", "1", str(frame)],
            check=False,
        )
        if not frame.exists():
            return None
        im = Image.open(frame).convert("RGB")
        w, h = im.size
        im.thumbnail((1200, 1200))
        name = key_for(src) + "-poster.webp"
        OUT_IMG.mkdir(parents=True, exist_ok=True)
        im.save(OUT_IMG / name, "WEBP", quality=78)
    entry = {"poster": name, "w": w, "h": h}
    MAN[k] = entry
    save_manifest()
    print(f"  + poster {src}")
    return entry


def video(src, alt, depth):
    p = ensure_poster(src)
    poster = f' poster="{depth}assets/img/{p["poster"]}" width="{p["w"]}" height="{p["h"]}"' if p else ""
    return (
        f'<video class="vid" muted loop playsinline preload="none" data-autoplay{poster} aria-label="{attr(alt)}">'
        f'<source src="{url(src, depth)}" type="video/mp4"></video>'
    )


# ─────────────────────────────────────────────────────────── data ──
PROJECTS = C["projects"]
for i, p in enumerate(PROJECTS, 1):
    p["n"] = f"{i:02d}"
BY_SLUG = {p["slug"]: p for p in PROJECTS}
DISC = C["disciplines"]


def index_rows():
    """Archive entries: one per project, or one per chapter for grouped features."""
    rows = []
    for p in PROJECTS:
        if p.get("chapters"):
            for j, ch in enumerate(p["chapters"]):
                first = ch["blocks"][0]["items"]
                still = next((x for x in first if isinstance(x, list)), None)
                rows.append({
                    "n": p["n"] + "abcdefgh"[j], "title": ch["index_title"], "label": p["label"],
                    "disc": p["discipline"], "year": ch.get("year", p["year"]),
                    "ctx": plain(dict(p["meta"]).get("For", "")),
                    "href": f"work/{p['slug']}.html#{ch['id']}",
                    "img": ch.get("thumb") or (still[0] if still else p["cover"][0]),
                })
        else:
            m = dict(p["meta"])
            ctx = plain(p.get("index_ctx") if "index_ctx" in p else (m.get("For") or m.get("With") or m.get("Context") or m.get("Type") or m.get("Format", "")))
            rows.append({
                "n": p["n"], "title": p["index_title"], "label": p["label"], "disc": p["discipline"],
                "year": p["year"], "ctx": ctx, "href": f"work/{p['slug']}.html", "img": p.get("thumb") or p["cover"][0],
            })
    return rows


ROWS = index_rows()

# ─────────────────────────────────────────────────────────── chrome ──
OVAL = (
    '<svg class="oval" viewBox="0 0 200 64" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
    '<path pathLength="1" d="M118 5C64 2 14 11 6 30c-7 17 36 30 96 30 58 0 94-12 92-30C192 13 150 3 92 6 66 7 44 12 31 18"/></svg>'
)

# Full-screen intro on the home page (name writes itself, then the page turns up). To switch it off:
# set INTRO_ON = False and add "false&&" before "home&&" in the head script.
INTRO_ON = True
INTRO_HTML = '<div class="intro" aria-hidden="true" data-intro><div class="intro-inner"><p class="intro-name">JessicaXie</p><p class="intro-sub">Portfolio</p></div></div>\n'
NAV = [("index.html", "Home"), ("work.html", "Work"), ("about.html", "About"), ("contact.html", "Contact")]


def head(title, desc, depth, path, og=None):
    canonical = SITE["url"] + "/" + ("" if path == "index.html" else path)
    og_img = SITE["url"] + "/" + og if og else ""
    return f"""<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{attr(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{attr(title)}">
<meta property="og:description" content="{attr(desc)}">
<meta property="og:url" content="{canonical}">
{f'<meta property="og:image" content="{og_img}">' if og_img else ''}
<meta name="color-scheme" content="light">
<script>(function(d){{d.className=d.className.replace('no-js','js');try{{var t=localStorage.getItem('jx-theme');if(t)d.setAttribute('data-theme',t)}}catch(e){{}}try{{var p=location.pathname,home=(p.slice(-1)=='/'||p.slice(-10)=='index.html');if(home)d.classList.add('head-clear');if(home&&!sessionStorage.getItem('jx-intro')&&!matchMedia('(prefers-reduced-motion: reduce)').matches)d.classList.add('show-intro')}}catch(e){{}}}})(document.documentElement)</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Ballet&amp;family=Pinyon+Script&amp;family=Jost:ital,wght@0,400;0,500;0,600;1,400;1,500&amp;display=swap">
<link rel="stylesheet" href="{depth}assets/css/jx.css">
<link rel="icon" href="{depth}assets/favicon.svg" type="image/svg+xml">
<script src="{depth}assets/js/jx.js" defer></script>
</head>"""


def masthead(depth, active):
    items = []
    for i, (href, label) in enumerate(NAV, 1):
        cur = ' aria-current="page"' if href == active else ""
        items.append(
            f'<li class="nav-{href.split(".")[0]}"><a href="{depth}{href}"{cur}><span class="nav-t">{label}{OVAL}</span></a></li>'
        )
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <a class="logo" href="{depth}index.html" aria-label="Jessica Xie, home"><span>Jessica Xie</span>{OVAL}</a>
  <nav class="nav" id="site-nav" aria-label="Main">
    <div class="nav-panel" id="site-nav-panel"><ol>{''.join(items)}</ol></div>
    <button class="menu-tab label" type="button" aria-expanded="false" aria-controls="site-nav-panel" data-menu-toggle><span>Menu</span></button>
  </nav>
  <button class="theme-toggle label" type="button" data-theme-toggle aria-label="Toggle dark mode">
    <span class="tt-l">Light</span><span aria-hidden="true">/</span><span class="tt-d">Dark</span>
  </button>
</header>"""


def colophon(depth, big=False):
    big_html = ""
    if big:
        big_html = f"""
  <div class="closing grid" data-ascii-trail>
    <p class="closing-hint label">Thank you for viewing my portfolio. Please take a moment to rest here and focus on your breathing as you draw around.</p>
    <h2 class="label closing-label">Contact</h2>
    <div class="closing-body">
      <p>Write to me about a project, a question, or anything in these pages.</p>
      <a class="closing-mail" href="mailto:{SITE['email']}">{SITE['email']}</a>
    </div>
  </div>"""
    cls = "colophon colophon--big" if big else "colophon"
    return f"""<footer class="{cls}">{big_html}
  <div class="colophon-row grid">
    <p class="label c-a">Footer</p>
    <p class="c-b">Jessica Xie &mdash; Portfolio {SITE['edition']}</p>
    <p class="c-c"><a href="mailto:{SITE['email']}">{SITE['email']}</a></p>
    <p class="label c-d">&copy; {TODAY.year} &middot; <a href="#top">Back to top&nbsp;&uarr;</a></p>
  </div>
</footer>"""


def page(path, title, desc, main, active, body_class="", og=None, big_colophon=False):
    depth = "../" * path.count("/")
    doc = (
        head(title, desc, depth, path, og)
        + f'\n<body id="top" class="{body_class}">\n'
        + masthead(depth, active)
        + f'\n<main id="main">\n{main}\n</main>\n'
        + colophon(depth, big_colophon)
        + '\n<div class="preview" aria-hidden="true"><img alt=""></div>\n</body>\n</html>\n'
    )
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, "utf-8")
    print(f"  · {path}")


def meta_dl(pairs, cls="receipt"):
    rows = "".join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in pairs if v)
    return f'<dl class="{cls}">{rows}</dl>'


def clip(s, n=190):
    t = plain(s)
    return html.escape(t if len(t) <= n else t[: t.rfind(" ", 0, n)] + "…")


# ─────────────────────────────────────────────────────────── home ──
def feature(f, depth=""):
    p = BY_SLUG[f["slug"]]
    href = f"work/{p['slug']}.html"
    lay = f["layout"]
    link_img = lambda inner, cls="f-media": f'<a class="{cls}" href="{href}" tabindex="-1" aria-hidden="true">{inner}</a>'
    if lay in ("e", "f"):
        sizes = "(min-width: 64rem) 30vw, 50vw" if lay == "e" else "(min-width: 64rem) 16vw, 45vw"
        figs = "".join(f'<span class="f-img f-img-{i+1}">{img(s, a, depth, sizes)}</span>' for i, (s, a) in enumerate(f["images"]))
        media = link_img(figs, "f-media f-media--set")
    else:
        sizes = {"a": "100vw", "b": "(min-width: 64rem) 66vw, 100vw", "c": "(min-width: 64rem) 66vw, 100vw", "d": "(min-width: 64rem) 30vw, 70vw", "g": "(min-width: 64rem) 66vw, 100vw"}[lay]
        media = link_img(f'<span class="f-img f-img-1">{img(f["image"], f["alt"], depth, sizes)}</span>')
        if f.get("image2"):
            media += link_img(f'<span class="f-img">{img(f["image2"], f["alt2"], depth, "(min-width: 64rem) 25vw, 50vw")}</span>', "f-media f-media--2")
    return f"""
<article class="feature feature--{lay} reveal">
  {media}
  <div class="f-text">
    <p class="f-num label" aria-hidden="true">No.&nbsp;{p['n']}</p>
    <h3 class="f-title"><a href="{href}"><span class="f-t">{p['title']}</span> <span class="f-s">{p['subtitle']}</span></a></h3>
    {meta_dl([('Discipline', p['label']), ('Year', p['year'])], 'f-meta')}
    <p class="f-deck">{clip(p['lead'])}</p>
    <a class="f-open label" href="{href}" tabindex="-1" aria-hidden="true">View more <span>&rarr;</span></a>
  </div>
</article>"""


# Selected work as a numbered modular grid (6 columns). Each entry:
# image (col, colspan, row, rowspan) and text cell (col, row).
# Desktop: (image column, image column-span, text column, text position).
# Row spans come from each image's real proportions, so nothing is cropped;
# every project starts below the previous one, with one empty row in between.
SW_LAYOUT = [
    (1, 4, 6, "bottom"),
    (4, 2, 1, "top"),
    (1, 3, 5, "top"),
    (4, 3, 2, "bottom"),
    (2, 1, 4, "top"),
    (4, 2, 1, "bottom"),
    (2, 2, 5, "top"),
]
CELL_RATIO = 0.72      # desktop cell height / width
CELL_RATIO_M = 0.85    # phone


def selected_grid(feats):
    """Numbered (dotted) modular grid. Desktop/tablet: 6 columns. Phone: 4 columns,
    each image 3 columns wide, alternating left/right. Images are never cropped."""
    import math
    ratios = []
    for f in feats:
        e = ensure_image(f.get("image") or f["images"][0][0])
        ratios.append((e["h"] / e["w"]) if e else 1.0)
    # desktop placement
    d_place, cur = [], 1
    for (c, cs, tc, pos), ratio in zip(SW_LAYOUT, ratios):
        h_rows = cs * ratio / CELL_RATIO          # image height measured in rows
        rs = max(1, math.ceil(h_rows + 0.2))
        tr = cur if pos == "top" else cur + max(0, math.floor(h_rows) - 1)
        d_place.append((c, cs, cur, rs, tc, tr))
        cur += rs + 1
    rows = cur - 1
    # phone placement
    m_place, cur = [], 1
    for i, ratio in enumerate(ratios):
        span = max(2, math.ceil(3 * ratio / CELL_RATIO_M + 0.25))
        m_place.append((1 if i % 2 == 0 else 2, cur, span))
        cur += span + 3
    m_rows = cur - 1
    cells = "".join(
        f'<span class="cell-n cell-d" style="grid-area:{r}/{c}" aria-hidden="true"></span>'
        for r in range(1, rows + 1) for c in range(1, 7)
    ) + "".join(
        f'<span class="cell-n cell-m" style="grid-area:{r}/{c}" aria-hidden="true"></span>'
        for r in range(1, m_rows + 1) for c in range(1, 5)
    )
    items = []
    for f, (c, cs, r, rs, tc, tr), (mc, mr, mrs) in zip(feats, d_place, m_place):
        p = BY_SLUG[f["slug"]]
        href = f"work/{p['slug']}.html"
        src = f.get("image") or f["images"][0][0]
        alt = f.get("alt") or f["images"][0][1]
        items.append(
            f'<a class="sw-img" href="{href}" tabindex="-1" aria-hidden="true" '
            f'style="--c:{c};--cs:{cs};--r:{r};--rs:{rs};--mc:{mc};--mr:{mr};--mrs:{mrs}">'
            f'<span>{img(src, alt, "", f"(min-width: 40rem) {round(cs / 6 * 100)}vw, 75vw")}</span></a>'
            f'<div class="sw-text" style="--c:{tc};--r:{tr};--mc:{mc};--mr:{mr + mrs}">'
            f'<h3><a href="{href}">{p["title"]}</a></h3>'
            f'<p>{p["subtitle"]}</p>'
            f'<p class="sw-meta">{p["label"]} &middot; {p["year"]}</p>'
            f'<a class="sw-more" href="{href}" tabindex="-1" aria-hidden="true">View more</a></div>'
        )
    return f'<div class="sw-grid reveal">{cells}{"".join(items)}</div>'


def build_home():
    feats = C["featured"]
    featured_slugs = [f["slug"] for f in feats]
    coverlines = "".join(
        f'<li><a href="work/{s}.html"><span class="cl-n">{BY_SLUG[s]["n"]}</span>'
        f'<span class="cl-t">{BY_SLUG[s]["title"]}</span><span class="cl-s">{BY_SLUG[s]["subtitle"]}</span></a></li>'
        for s in featured_slugs[:5]
    )
    hl = " ".join(SITE["headline"])
    rest = [r for r in ROWS if r["href"].split("/")[1].split(".")[0].split("#")[0] not in featured_slugs]
    also = "".join(
        f'<li class="also-row" data-preview="{thumb(r["img"], "")}"><a href="{r["href"]}"><span class="ar-n">{r["n"]}</span>'
        f'<span class="ar-t">{r["title"]}</span><span class="ar-d">{r["label"]}</span><span class="ar-y">{r["year"]}</span></a></li>'
        for r in rest
    )
    facts = meta_dl([
        ("Study", "Communication &amp; Multimedia Design"),
        ("School", "Hogeschool van Amsterdam"),
        ("Based", SITE["location"]),
        ("Practice", "UX/UI, visual &amp; editorial design, photography"),
    ], "receipt note-facts")
    main = f"""
{INTRO_HTML if INTRO_ON else ''}<section class="cover hero4" aria-labelledby="cover-title">
  <div class="cover-bg" aria-hidden="true" style="background-image:url('{thumb(SITE['hero_image'], '', 2000)}')"></div>
  <div class="h4-top label">
    <span>Communication &amp; Multimedia Design</span>
    <span>Hogeschool van Amsterdam</span>
    <span>{SITE['location']}</span>
  </div>
  <div class="h4-center">
    <h1 class="h4-name" id="cover-title" aria-label="Jessica Xie"><span aria-hidden="true">JessicaXie</span></h1>
    <p class="h4-script" aria-hidden="true">portfolio</p>
  </div>
  <div class="h4-bottom">
    <p class="h4-deck">{SITE['deck']}</p>
    <a class="h4-scroll label" href="#sel-title">Selected work <span aria-hidden="true">&darr;</span></a>
    <p class="h4-statement label">Between the<br>image and the<br>interface.</p>
  </div>
</section>

<section class="selected" aria-labelledby="sel-title">
  <header class="section-head grid">
    <h2 class="section-title" id="sel-title"><span class="script">Selected</span><span class="caps">Work</span></h2>
    <p class="label sh-a">{len(feats)} projects</p>
    <p class="label sh-b"><a href="work.html">All {len(ROWS)} entries &rarr;</a></p>
  </header>
  {selected_grid(feats)}
</section>

<section class="note grid reveal" aria-labelledby="note-title">
  <p class="label note-label" id="note-title">A note from Jessica</p>
  <figure class="note-portrait">{img(SITE['about_portrait'], SITE['about_portrait_alt'], '', '(min-width: 64rem) 22vw, 60vw')}</figure>
  <blockquote class="note-text"><p>{SITE['about_short']}</p></blockquote>
  <div class="note-side">
    {facts}
    <p><a class="click" href="about.html">CLICK to read more about Jessica</a></p>
  </div>
</section>

<section class="also grid reveal" aria-labelledby="also-title">
  <h2 class="also-title" id="also-title"><span class="script">More</span><span class="caps">work</span></h2>
  <ol class="also-list">{also}</ol>
  <p class="also-more"><a class="click" href="work.html">CLICK to open the full index</a></p>
</section>"""
    page("index.html", "Jessica Xie — Portfolio",
         plain(SITE["deck"]), main, "index.html", "home", og=None, big_colophon=True)


# ─────────────────────────────────────────────────────────── work ──
def build_work():
    counts = {k: sum(1 for r in ROWS if r["disc"] == k) for k in DISC}
    filters = f'<button type="button" aria-pressed="true" data-filter="all">All<sup>{len(ROWS)}</sup>{OVAL}</button>' + "".join(
        f'<button type="button" aria-pressed="false" data-filter="{k}">{v}<sup>{counts[k]}</sup>{OVAL}</button>' for k, v in DISC.items()
    )
    groups: dict[str, list] = {}
    for r in ROWS:
        y = plain(r["year"])[:4]
        groups.setdefault(y, []).append(r)
    blocks = []
    for y, rows in groups.items():
        lis = "".join(
            f'<li class="ix-row" data-discipline="{r["disc"]}" data-preview="{thumb(r["img"], "")}">'
            f'<a href="{r["href"]}"><span class="ix-n">{r["n"]}</span><span class="ix-t">{r["title"]}</span>'
            f'<span class="ix-d">{r["label"]}</span><span class="ix-c">{r["ctx"]}</span><span class="ix-y">{r["year"]}</span>'
            f'<img class="ix-thumb" src="{thumb(r["img"], "", 640)}" alt="" loading="lazy" decoding="async"></a></li>'
            for r in rows
        )
        blocks.append(f'<li class="ix-group"><h2 class="ix-year">{y}</h2><ol class="ix-rows">{lis}</ol></li>')
    main = f"""
<section class="page-head grid">
  <p class="label ph-a">Index of work</p>
  <p class="label ph-b">{len(ROWS)} entries &middot; 2022&ndash;{SITE['edition']}</p>
  <h1 class="page-title">Index<span class="script">of work</span></h1>
  <p class="page-intro">Every project, newest first. Filter by discipline, or hover a title for a glimpse.</p>
</section>
<section class="index grid" aria-label="All projects">
  <div class="filters" role="group" aria-label="Filter by discipline">{filters}</div>
  <p class="label ix-count" aria-live="polite" data-count>{len(ROWS)} entries</p>
  <div class="ix-head label" aria-hidden="true"><span>No.</span><span>Title</span><span>Discipline</span><span>Context</span><span>Year</span></div>
  <ol class="ix-list">{''.join(blocks)}</ol>
</section>"""
    page("work.html", "Work — Index | Jessica Xie",
         "Index of every project by Jessica Xie: UX/UI, graphic and editorial design, and photography, 2022–2026.",
         main, "work.html", "work")


# ─────────────────────────────────────────────────────────── project ──
FIG = {"n": 0}
CURRENT: dict = {}


def fig(item, depth, sizes, cls="b-fig"):
    if isinstance(item, dict):
        return f'<figure class="{cls}">{video(item["video"], item.get("alt", ""), depth)}</figure>'
    src, alt, cap = (item + ["", ""])[:3]
    FIG["n"] += 1
    capt = f'<figcaption><span class="fig-n">Fig. {FIG["n"]:02d}</span> {cap}</figcaption>' if cap else ""
    return f'<figure class="{cls}">{img(src, alt, depth, sizes)}{capt}</figure>'


def block(b, depth):
    t = b["type"]
    items = b.get("items", [])
    if t == "heading":
        return f'<header class="b-heading grid reveal"><h2 class="label">{b["label"]}</h2><p>{b["text"]}</p></header>'
    if t == "full":
        return f'<div class="b b-full reveal">{fig(items[0], depth, "100vw")}</div>'
    if t == "wide":
        return f'<div class="b b-wide grid reveal">{fig(items[0], depth, "(min-width: 64rem) 85vw, 100vw")}</div>'
    if t == "offset":
        return f'<div class="b b-offset b-offset--{b.get("side", "right")} grid reveal">{fig(items[0], depth, "(min-width: 64rem) 62vw, 100vw")}</div>'
    if t == "pair":
        r = b.get("ratio", "6-6")
        st = " b-stagger" if b.get("stagger") else ""
        a, c = (int(x) for x in r.split("-"))
        return (f'<div class="b b-pair b-pair--{r}{st} grid reveal">'
                f'{fig(items[0], depth, f"(min-width: 64rem) {round(a/12*100)}vw, 100vw")}'
                f'{fig(items[1], depth, f"(min-width: 64rem) {round(c/12*100)}vw, 100vw")}</div>')
    if t == "match":
        # n images side by side at one shared height: widths follow each image's aspect ratio, so no gaps
        # optional "scale": relative widths (e.g. so text inside two boards renders at the same size)
        figs = []
        sc = b.get("scale")
        for k, i in enumerate(items):
            e = ensure_image(i[0]) if not isinstance(i, dict) else None
            ar = round(e["w"] / e["h"], 3) if e else 1
            st = f"--ar:{ar}"
            if sc:
                st = f"--ar:{sc[k]};--pct:{round(sc[k] / max(sc) * 100, 2)}%"
            figs.append(fig(i, depth, f"(min-width: 64rem) {round(100 / len(items))}vw, 100vw", cls=f"b-fig\" style=\"{st}"))
        return f'<div class="b b-match grid reveal"><div class="m-row">{"".join(figs)}</div></div>'
    if t == "trio":
        return f'<div class="b b-trio grid reveal">{"".join(fig(i, depth, "(min-width: 40rem) 33vw, 100vw") for i in items)}</div>'
    if t == "row":
        n = len(items)
        return f'<div class="b b-row grid reveal" style="--n:{n}">{"".join(fig(i, depth, f"(min-width: 64rem) {round(100/n)}vw, 50vw") for i in items)}</div>'
    if t == "sheet":
        return f'<div class="b b-sheet grid reveal">{"".join(fig(i, depth, "(min-width: 64rem) 18vw, 33vw") for i in items)}</div>'
    if t == "scroll":
        frames = []
        for src, alt, cap in items:
            FIG["n"] += 1
            frames.append(
                f'<figure class="b-scroll-fig"><div class="b-scroll-frame" tabindex="0" role="region" aria-label="{attr(plain(cap))}, scrollable">'
                f'{img(src, alt, depth, "(min-width: 64rem) 30vw, 85vw")}</div>'
                f'<figcaption><span class="fig-n">Fig. {FIG["n"]:02d}</span> {cap} <span class="hint">&darr; scroll</span></figcaption></figure>'
            )
        return f'<div class="b b-scroll grid reveal" style="--n:{len(items)}">{"".join(frames)}</div>'
    if t == "credits":
        groups = []
        for title, rows in CURRENT["p"].get("credits", []):
            dl = "".join(f'<div><dt>{k}</dt><dd>{v if isinstance(v, str) else ", ".join(v)}</dd></div>' for k, v in rows)
            groups.append(f'<div class="cr-group"><h3 class="label">{title}</h3><dl class="receipt">{dl}</dl></div>')
        return f'<section class="b b-credits grid reveal" aria-label="Credits"><h2 class="cr-title"><span class="script">Credits</span></h2>{"".join(groups)}</section>'
    if t == "pages":
        pages = []
        for i in range(1, b["count"] + 1):
            src = b["src"].replace("{n}", f"{i:04d}")
            alt_i = f'{b["alt"]} {i}'
            pages.append(f'<li class="pg">{img(src, alt_i, depth, "(min-width: 64rem) 30vw, 75vw")}<span class="label">{i:02d}</span></li>')
        return f"""<div class="b b-pages reveal" data-pages>
  <ol class="pg-track" tabindex="0" aria-label="Magazine pages, scroll horizontally">{''.join(pages)}</ol>
  <div class="pg-controls grid"><button type="button" class="label" data-pg-prev>&larr; Previous</button><span class="label" data-pg-count>01 / {b['count']:02d}</span><button type="button" class="label" data-pg-next>Next &rarr;</button></div>
</div>"""
    raise ValueError(t)


def docs_html(p, depth):
    if not p.get("docs"):
        return ""
    lis = "".join(
        f'<li><a class="click" href="{url(d, depth)}" target="_blank" rel="noopener">CLICK to {label}</a> <span class="label">{lang} &middot; PDF</span></li>'
        if lang != "PDF" else
        f'<li><a class="click" href="{url(d, depth)}" target="_blank" rel="noopener">CLICK to {label}</a> <span class="label">PDF</span></li>'
        for d, label, lang in p["docs"]
    )
    return f'<div class="p-docs"><p class="label">Further reading</p><ul>{lis}</ul></div>'


def build_project(i, p):
    FIG["n"] = 0
    CURRENT["p"] = p
    depth = "../"
    disc = DISC[p["discipline"]]
    cover_style = p.get("cover_style", "wide")
    sizes = {"wide": "100vw", "contained": "(min-width: 64rem) 60vw, 100vw", "portrait": "(min-width: 64rem) 45vw, 100vw"}[cover_style]
    cover = img(p["cover"][0], p["cover"][1], depth, sizes, eager=True)
    body = "".join(f"<p>{x}</p>" for x in p.get("body", []))
    receipt = meta_dl([("No.", p["n"]), ("Year", p["year"]), ("Discipline", p["label"])] + [tuple(m) for m in p["meta"]])
    chapters = ""
    toc = ""
    if p.get("chapters"):
        letters = "abcdefgh"
        toc = '<nav class="p-toc" aria-label="In this project"><p class="label">In this project</p><ol>' + "".join(
            f'<li><a href="#{ch["id"]}"><span>{letters[j]}.</span> {ch["title"]}</a></li>' for j, ch in enumerate(p["chapters"])
        ) + "</ol></nav>"
        for j, ch in enumerate(p["chapters"]):
            m = [("Year", ch["year"])] if ch.get("year") else []
            chapters += f"""
<section class="chapter" id="{ch['id']}" aria-labelledby="{ch['id']}-t">
  <header class="ch-head grid reveal">
    <p class="ch-letter" aria-hidden="true">{letters[j]}</p>
    <h2 class="ch-title" id="{ch['id']}-t">{ch['title']}</h2>
    <p class="ch-text">{ch['text']}</p>
    {meta_dl(m + [tuple(x) for x in ch.get('meta', [])], 'receipt ch-meta')}
  </header>
  {''.join(block(b, depth) for b in ch['blocks'])}
</section>"""
    blocks = "".join(block(b, depth) for b in p.get("blocks", []))
    prev_p = PROJECTS[i - 1]
    next_p = PROJECTS[(i + 1) % len(PROJECTS)]
    main = f"""
<article class="project project--{cover_style}">
  <header class="p-head grid">
    <nav class="crumbs label" aria-label="Breadcrumb"><a href="../work.html">Work</a> <span aria-hidden="true">/</span> No.&nbsp;{p['n']} <span aria-hidden="true">/</span> {disc}</nav>
    <p class="p-num label" aria-hidden="true">No.&nbsp;{p['n']}</p>
    <h1 class="p-title"><span class="p-t">{p['title']}</span> <span class="p-s">{p['subtitle']}</span></h1>
    {receipt}
  </header>
  <figure class="p-cover">{cover}</figure>
  <section class="p-intro grid" aria-label="Introduction">
    <p class="lead">{p['lead']}</p>
    <div class="p-body">{body}{docs_html(p, depth)}</div>
    {toc}
  </section>
  {blocks}
  {chapters}
  <nav class="p-next grid" aria-label="More projects">
    <a class="pn pn-prev" href="{prev_p['slug']}.html"><span class="label">&larr; Previous &middot; No.&nbsp;{prev_p['n']}</span><span class="pn-t">{prev_p['title']}</span>
      <span class="pn-img">{img(prev_p['cover'][0], '', depth, '(min-width: 64rem) 20vw, 40vw')}</span></a>
    <a class="pn pn-all label" href="../work.html">All work</a>
    <a class="pn pn-next" href="{next_p['slug']}.html"><span class="label">Next &middot; No.&nbsp;{next_p['n']} &rarr;</span><span class="pn-t">{next_p['title']}</span>
      <span class="pn-img">{img(next_p['cover'][0], '', depth, '(min-width: 64rem) 20vw, 40vw')}</span></a>
  </nav>
</article>"""
    title = f"{plain(p['title'])} — {plain(p['subtitle'])} | Jessica Xie"
    og = "assets/img/" + MAN[p["cover"][0]]["key"] + "-1200.webp" if p["cover"][0] in MAN and 1200 in MAN[p["cover"][0]]["widths"] else None
    page(f"work/{p['slug']}.html", title, plain(p["lead"])[:300], main, "work.html", "project-page", og=og)


# ─────────────────────────────────────────────────────────── about ──
def build_about():
    sheet = "".join(
        f'<li class="cs-item">{img(s, a, "", "(min-width: 64rem) 16vw, 45vw")}<span class="label">{i:02d}</span></li>'
        for i, (s, a) in enumerate(SITE["about_sheet"], 1)
    )
    paras = "".join(f"<p>{x}</p>" for x in SITE["about_long"][1:])
    discs = "".join(
        f'<li><a href="work.html#{k}"><span>{v}</span><sup>{sum(1 for r in ROWS if r["disc"] == k)}</sup></a></li>' for k, v in DISC.items()
    )
    tools = SITE.get("tools") or sorted({t.strip() for p in PROJECTS for k, v in p["meta"] if k == "Tools" for t in plain(v).split(",")})
    facts = meta_dl([
        ("Name", "Jessica Xie"),
        ("Study", "Communication &amp; Multimedia Design (CMD)"),
        ("School", "Hogeschool van Amsterdam (HvA)"),
        ("Based", SITE["location"]),
        ("Practice", "UX/UI, visual design, editorial, graphic design, photography"),
        ("Tools", ", ".join(tools)),
        ("Contact", f'<a href="mailto:{SITE["email"]}">{SITE["email"]}</a>'),
    ])
    main = f"""
<section class="about-head grid">
  <p class="label ph-a">About</p>
  <p class="label ph-b">In her own words</p>
  <h1 class="about-title">Shaped by <em>curiosity</em>, informed by culture.</h1>
  <figure class="about-portrait">{img(SITE['about_portrait'], SITE['about_portrait_alt'], '', '(min-width: 64rem) 40vw, 100vw', eager=True)}</figure>
  <div class="about-text">
    <p class="lead">{SITE['about_long'][0]}</p>
    {paras}
  </div>
  <p class="about-quote" aria-hidden="true">{SITE['pull_quote']}</p>
  <div class="about-facts">{facts}</div>
</section>
<section class="disciplines grid reveal" aria-labelledby="disc-t">
  <h2 class="label" id="disc-t">Disciplines</h2>
  <ol class="disc-list">{discs}</ol>
</section>
<section class="contact-sheet grid reveal" aria-labelledby="cs-t">
  <h2 class="cs-title" id="cs-t"><span class="script">Contact</span><span class="caps">sheet</span></h2>
  <p class="cs-note">From my own camera roll: outfits, textures, places and small details that quietly find their way into what I make.</p>
  <ol class="cs-grid">{sheet}</ol>
</section>"""
    page("about.html", "About | Jessica Xie",
         "Jessica Xie studies Communication & Multimedia Design at the Hogeschool van Amsterdam, working across UX/UI, visual and editorial design, and photography.",
         main, "about.html", "about")


def build_contact():
    main = f"""
<section class="contact grid">
  <p class="label ph-a">Contact</p>
  <p class="label ph-b">{SITE['location']}</p>
  <h1 class="contact-title"><span>Write</span> <span class="ct-2">to <em>me</em>.</span></h1>
  <div class="contact-body">
    <p class="lead">For projects, questions, or a conversation about anything on this site, email is the best way to reach me.</p>
    <a class="contact-mail" href="mailto:{SITE['email']}">{SITE['email']}</a>
    <p><button class="click copy-btn" type="button" data-copy="{SITE['email']}">CLICK to copy the address</button> <span class="label" data-copy-status aria-live="polite"></span></p>
  </div>
  <div class="contact-card" aria-hidden="true">
    <p class="label">Correspondence card</p>
    <p class="cc-name">Jessica Xie</p>
    <p class="cc-script">with love</p>
    <dl class="receipt"><div><dt>Study</dt><dd>CMD, HvA</dd></div><div><dt>Based</dt><dd>{SITE['location']}</dd></div><div><dt>Date</dt><dd>{STAMP}</dd></div></dl>
  </div>
</section>"""
    page("contact.html", "Contact | Jessica Xie", f"Get in touch with Jessica Xie: {SITE['email']}.", main, "contact.html", "contact-page")


# ─────────────────────────────────────────────────────────── extras ──
REDIRECTS = {
    "projects/webdesign.html": ("work.html#ui", {"gisou": "gisou-digital", "thugclub": "thug-club", "boekenzoeker": "boekenzoeker",
                                                 "public-city-jazz": "public-city-jazz", "starsync": "starsync", "the-new-order": "the-new-order"}),
    "projects/uxdesign.html": ("work.html#ux", {"heartspace": "heartspace", "herinnering-aan-tafel": "herinnering-aan-tafel"}),
    "projects/graphicdesign.html": ("work.html#graphic", {
        "gisou-retail": "gisou-retail", "lowside-afropiano": "lowside#afropiano", "lowside-return": "lowside#return-of-10s",
        "lowside-sip-swap": "lowside#sip-n-swap", "lowside-halloween": "lowside#halloween"}),
    "projects/magazinedesign.html": ("work/kitty-couture.html", {}),
    "projects/photography.html": ("work.html#photography", {"tokyo-kyoto": "tokyo-kyoto", "paris-fashion-week": "paris-fashion-week"}),
    "projects/photography-paris.html": ("work/paris-fashion-week.html", {}),
    "projects/photography-tokyo-kyoto.html": ("work/tokyo-kyoto.html", {}),
    "works.html": ("work.html", {}),
    "cv.html": ("work.html", {}),
}


def build_redirects():
    for path, (fallback, mapping) in REDIRECTS.items():
        depth = "../" * path.count("/")
        m = {k: f"work/{v.split('#')[0]}.html" + (f"#{v.split('#')[1]}" if "#" in v else "") for k, v in mapping.items()}
        doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Moved | Jessica Xie</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{SITE['url']}/{fallback.split('#')[0]}">
<meta http-equiv="refresh" content="0; url={depth}{fallback}">
<script>(function(){{var m={json.dumps(m)},h=location.hash.slice(1);location.replace("{depth}"+(m[h]||"{fallback}"));}})()</script>
</head><body><p>This page has moved to <a href="{depth}{fallback}">{fallback}</a>.</p></body></html>
"""
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc, "utf-8")
    print(f"  · {len(REDIRECTS)} redirects for old URLs")


def build_404():
    main = f"""
<section class="erratum grid">
  <p class="label ph-a">404</p>
  <h1 class="erratum-title">This page could not be <em>found</em>.</h1>
  <p class="lead erratum-body">The address may have changed in the redesign. Everything is still listed in the index.</p>
  <p class="erratum-links"><a class="click" href="/work.html">CLICK to open the index</a><br><a class="click" href="/">CLICK to return to the cover</a></p>
</section>"""
    # 404 is served from any depth by GitHub Pages, so use root-absolute asset paths
    doc = (head("Not found | Jessica Xie", "Page not found.", "/", "404.html")
           + '\n<body id="top" class="erratum-page">\n' + masthead("/", "") + f'\n<main id="main">{main}</main>\n' + colophon("/") + "\n</body>\n</html>\n")
    (ROOT / "404.html").write_text(doc, "utf-8")
    print("  · 404.html")


def build_sitemap():
    urls = ["", "work.html", "about.html", "contact.html"] + [f"work/{p['slug']}.html" for p in PROJECTS]
    body = "".join(f"<url><loc>{SITE['url']}/{u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n', "utf-8")
    print("  · sitemap.xml")


def main():
    print(f"Building jcssicaxie.com  (Pillow: {HAS_PIL}, ffmpeg: {HAS_FFMPEG})")
    build_home()
    build_work()
    for i, p in enumerate(PROJECTS):
        build_project(i, p)
    build_about()
    build_contact()
    build_redirects()
    build_404()
    build_sitemap()
    save_manifest()
    print("Done.")


if __name__ == "__main__":
    main()
