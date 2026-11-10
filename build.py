#!/usr/bin/env python3
"""Build the English and Latvian pages from the bilingual sources.

    python3 build.py

Edit the pages in SRC, never the generated HTML in OUT. Each source page holds
both languages as <span lang="en">…</span><span lang="lv">…</span> pairs (and
<img lang="en"> / <img lang="lv"> pairs); the head carries the Latvian title and
descriptions in data-lv attributes. This writes:

    OUT/<page>.html     English, at /<page>
    OUT/lv/<page>.html  Latvian, at /lv/<page>
    OUT/sitemap.xml     both versions linked to each other, plus SITEMAP_EXTRA

Google sees one language per address, and hreflang links tell it which pages are
translations of each other. A page with <meta property="article:published_time"> also gets
the article's author and dates as JSON-LD (what Google reads); a page with
<meta name="robots" content="noindex"> (a 404 page) gets no canonical or hreflang links and
stays out of the sitemap. No packages needed; run it before committing.

The same script is used by every IBS site; only the settings below differ.
"""
import base64
import hashlib
import html as htmllib
import json
import posixpath
import re
import sys
from pathlib import Path

# ── Settings for this site ───────────────────────────────────────────────────
SITE = 'https://gearbear.impatientbeaststudios.com'
SRC = 'src'                 # bilingual sources
OUT = '.'              # where the built pages go
STORAGE_KEY = 'lang'        # localStorage key that remembers the language
SITEMAP_EXTRA = []          # pages that are not split (an app), listed as they are
SITEMAP = None              # where sitemap.xml goes (None: OUT/sitemap.xml)
HEADERS = None              # Cloudflare _headers with the CSP (None: OUT/_headers)
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent
LANGS = ('en', 'lv')
IBS = r'https://(?:[a-z]+\.)?impatientbeaststudios\.com'
ASSET = re.compile(r'\.(?!html$)[a-z0-9]{2,5}$', re.I)   # style.css, img/x.webp … but not a page


def fail(msg):
    sys.exit('build.py: ' + msg)


def route(rel):
    """Source path → English URL path: index.html → /, guides.html → /guides."""
    p = Path(rel).with_suffix('').as_posix()
    if p == 'index':
        return '/'
    return '/' + (p[:-len('index')] if p.endswith('/index') else p)


def localise(path, lang):
    """English URL path → the same page in `lang`."""
    if lang == 'en':
        return path
    return '/lv' + path if path != '/' else '/lv/'


def with_query(url, query):
    p, sep, frag = url.partition('#')
    return p + ('&' if '?' in p else '?') + query + sep + frag


SPAN = re.compile(r'<span lang="(en|lv)">(.*?)</span>', re.S)
IMG = re.compile(r'<img lang="(en|lv)" ([^>]*)>')
# The old language script in <head>, or a marker comment where the new one goes.
HEAD_SCRIPT = re.compile(r'<script>\n[^<]*?navigator\.language[^<]*?</script>\n|<!-- build\.py: language script -->\n')
SWITCH = re.compile(r'<div class="lang" role="group" aria-label="Language / Valoda">.*?</div>', re.S)
LEFTOVER = re.compile(r'<(?!html)[a-z0-9]+ [^>]*\slang="(?:en|lv)"|data-lv=|data-title-(?:en|lv)=')


def pick_language(html, lang, name):
    def span(m):
        if '<span' in m.group(2):
            fail(f'{name}: a <span lang> contains another <span>; the build can not split that safely')
        return m.group(2) if m.group(1) == lang else ''
    html = SPAN.sub(span, html)
    return IMG.sub(lambda m: f'<img {m.group(2)}>' if m.group(1) == lang else '', html)


def redirect_script():
    # The same script on every page (so a Content-Security-Policy needs one hash).
    # A choice made earlier (or ?lang= in a link) wins. On a first visit only
    # English pages move Latvian browsers to Latvian; Latvian pages never
    # redirect by browser language, or Googlebot (English) could not read them.
    return f"""<script>
  // Language: ?lang= from a link, then the saved choice, then (first visit) the browser.
  (function () {{
    var here = document.documentElement.lang, p = location.pathname, saved = null
    var q = new URLSearchParams(location.search).get('lang')
    if (q !== 'en' && q !== 'lv') q = null
    try {{ if (q) localStorage.setItem('{STORAGE_KEY}', q); saved = localStorage.getItem('{STORAGE_KEY}') }} catch (e) {{}}
    var want = q || saved || (here === 'en' && (navigator.language || '').toLowerCase().indexOf('lv') === 0 ? 'lv' : null)
    if (want && want !== here) location.replace((want === 'lv' ? '/lv' + p : p.replace(/^\\/lv(\\/|$)/, '/')) + location.hash)
  }})()
</script>
"""


def script_hash():
    """CSP hash of the inline redirect script (what goes in script-src)."""
    body = redirect_script()[len('<script>'):-len('</script>\n')]
    return "'sha256-" + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode() + "'"


def meta_content(html, attr, name):
    m = re.search(rf'<meta {attr}="{re.escape(name)}" content="([^"]*)"', html)
    return htmllib.unescape(m.group(1)) if m else None


def article_data(html, url, lang):
    """JSON-LD for an article page (one with article:published_time), or '' for any other page."""
    published = meta_content(html, 'property', 'article:published_time')
    if not published:
        return ''
    title = htmllib.unescape(re.search(r'<title>(.*?)</title>', html, re.S).group(1))
    site = meta_content(html, 'property', 'og:site_name') or 'ImpatientBeastStudios'
    author = meta_content(html, 'property', 'article:author')
    data = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': title.rsplit(' · ', 1)[0],
        'description': meta_content(html, 'name', 'description'),
        'datePublished': published,
        'dateModified': meta_content(html, 'property', 'article:modified_time') or published,
        'inLanguage': lang,
        'url': url,
        'mainEntityOfPage': url,
        'image': meta_content(html, 'property', 'og:image'),
        'author': {'@type': 'Person', 'name': author, 'url': 'https://impatientbeaststudios.com' + localise('/about', lang)}
                  if author else {'@type': 'Organization', 'name': site},
        'publisher': {'@type': 'Organization', 'name': 'ImpatientBeastStudios', 'url': 'https://impatientbeaststudios.com/'},
    }
    data = {k: v for k, v in data.items() if v}
    body = json.dumps(data, ensure_ascii=False, indent=2).replace('</', '<\\/')
    return f'<script type="application/ld+json">\n{body}\n</script>\n'


def build_page(src_file, src_root, out_root, pages):
    rel = src_file.relative_to(src_root)
    name = rel.as_posix()
    source = src_file.read_text(encoding='utf-8')
    en_path = route(rel)
    noindex = re.search(r'<meta name="robots" content="[^"]*noindex', source) is not None
    page_dir = en_path if en_path.endswith('/') else posixpath.dirname(en_path)

    for lang in LANGS:
        here = localise(en_path, lang)
        html = source

        html, n = re.subn(r'<html lang="(?:en|lv)"', f'<html lang="{lang}"', html, count=1)
        if not n:
            fail(f'{name}: no <html lang="…">')
        html = pick_language(html, lang, name)

        # Head text: English stays in the content, Latvian comes from data-lv.
        def title(m):
            return f'<title>{m.group(1) if lang == "lv" else m.group(2)}</title>'
        html, n = re.subn(r'<title data-lv="([^"]*)">(.*?)</title>', title, html)
        if n != 1:
            fail(f'{name}: <title> needs a data-lv="…" with the Latvian title')

        def meta(m):
            attrs = m.group(1)
            if lang == 'lv':
                attrs = re.sub(r'content="[^"]*"', lambda _: f'content="{m.group(2)}"', attrs)
            return f'<meta{attrs}{m.group(3)}>'
        html = re.sub(r'<meta( [^>]*?) data-lv="([^"]*)"( ?/?)>', meta, html)

        # Links and assets.
        def link(m):
            attr, target = m.group(1), m.group(2)
            if not target or target.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                return m.group(0)
            if target == SITE or target.startswith((SITE + '/', SITE + '#', SITE + '?')):
                target = target[len(SITE):]
                target = target if target.startswith('/') else '/' + target
            elif target.startswith(('http:', 'https:')):
                if lang == 'lv' and re.match(IBS, target) and 'lang=' not in target:
                    target = re.sub('^(' + IBS + ')(?=$|[?#])', r'\1/', target)
                    target = with_query(target, 'lang=lv')   # the other IBS site opens in Latvian
                return f'{attr}="{target}"'
            path, rest = re.match(r'([^#?]*)(.*)', target).groups()
            if not path.startswith('/'):
                trail = '/' if path.endswith('/') or path in ('', '.') else ''
                path = posixpath.normpath(posixpath.join(page_dir, path or '.'))
                path = (path.rstrip('/') + trail) or '/'
            if ASSET.search(path):
                return f'{attr}="{path}{rest}"'          # absolute, so /lv/ pages find it
            if path.endswith('.html'):
                path = route(path.lstrip('/'))
            if path in pages:
                return f'{attr}="{localise(path, lang)}{rest}"'
            if lang == 'lv' and attr == 'href' and 'lang=' not in rest:
                return f'{attr}="{with_query(path + rest, "lang=lv")}"'   # an app page: open in Latvian
            return f'{attr}="{path}{rest}"'
        html = re.sub(r'\b(href|src)="([^"]*)"', link, html)

        # Own address, translations, locale.
        url = SITE + here
        if noindex:
            html = re.sub(r'<link rel="canonical" href="[^"]*" ?/?>\n?', '', html)   # a 404 page has no address of its own
        html, n = re.subn(r'<link rel="canonical" href="[^"]*"( ?/?)>', lambda m:
                          f'<link rel="canonical" href="{url}"{m.group(1)}>\n'
                          f'<link rel="alternate" hreflang="en" href="{SITE + en_path}"{m.group(1)}>\n'
                          f'<link rel="alternate" hreflang="lv" href="{SITE + localise(en_path, "lv")}"{m.group(1)}>\n'
                          f'<link rel="alternate" hreflang="x-default" href="{SITE + en_path}"{m.group(1)}>', html, count=1)
        if not n and not noindex:
            fail(f'{name}: no <link rel="canonical">')
        html = re.sub(r'<meta property="og:url" content="[^"]*"( ?/?)>', lambda m:
                          f'<meta property="og:url" content="{url}"{m.group(1)}>\n'
                          f'<meta property="og:locale" content="{"en_GB" if lang == "en" else "lv_LV"}"{m.group(1)}>\n'
                          f'<meta property="og:locale:alternate" content="{"lv_LV" if lang == "en" else "en_GB"}"{m.group(1)}>', html, count=1)  # only if the page has og:url

        head_end = html.index('</head>')
        head, n = HEAD_SCRIPT.subn(lambda _: redirect_script(), html[:head_end], count=1)
        if not n:
            fail(f'{name}: language script not found in <head>')
        html = head + article_data(html, url, lang) + html[head_end:]

        # EN / LV switch: links to the two versions.
        def switch(m):
            indent = re.search(r'\n([ \t]*)<button', m.group(0))
            ind = indent.group(1) if indent else ''
            def a(l):
                cur = ' aria-current="true"' if l == lang else ''
                return f'{ind}<a href="{localise(en_path, l)}" hreflang="{l}" data-lang="{l}"{cur}>{l.upper()}</a>'
            close = ind[:-2] if len(ind) >= 2 else ''
            return f'<nav class="lang" aria-label="Language / Valoda">\n{a("en")}\n{a("lv")}\n{close}</nav>'
        html, n = SWITCH.subn(switch, html, count=1)
        if not n:
            fail(f'{name}: EN/LV switch not found')

        m = LEFTOVER.search(html)
        if m:
            fail(f'{name} ({lang}): "{m.group(0)}" left over; check the markup')

        out = out_root / ('lv' if lang == 'lv' else '') / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding='utf-8')
    return None if noindex else en_path


def main():
    src_root, out_root = ROOT / SRC, ROOT / OUT
    sources = sorted(src_root.rglob('*.html'))
    if not sources:
        fail(f'no pages in {SRC}/')
    pages = {route(f.relative_to(src_root)) for f in sources}
    results = [build_page(f, src_root, out_root, pages) for f in sources]
    built = [p for p in results if p]                     # noindex pages stay out of the sitemap

    rows = [f'  <url><loc>{SITE + p}</loc></url>' for p in SITEMAP_EXTRA]
    for p in sorted(built, key=lambda p: (p != '/', p)):
        alts = ''.join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE + localise(p, l)}"/>' for l in LANGS)
        rows += [f'  <url>\n    <loc>{SITE + localise(p, l)}</loc>{alts}\n  </url>' for l in LANGS]
    (ROOT / SITEMAP if SITEMAP else out_root / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + '\n'.join(rows) + '\n</urlset>\n', encoding='utf-8')
    print(f'built {len(results)} pages × {len(LANGS)} languages + sitemap.xml')

    # A Content-Security-Policy without 'unsafe-inline' must list this script's hash.
    headers = ROOT / HEADERS if HEADERS else out_root / '_headers'
    m = re.search(r'script-src[^;\n]*', headers.read_text(encoding='utf-8')) if headers.exists() else None
    if m and "'unsafe-inline'" not in m.group(0) and script_hash() not in m.group(0):
        fail(f"add {script_hash()} to script-src in {headers.relative_to(ROOT)}, or the browser blocks the language script")


if __name__ == '__main__':
    main()
