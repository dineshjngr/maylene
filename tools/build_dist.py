#!/usr/bin/env python3
"""Assemble dist/: a fully static copy of the redesigned site for Cloudflare Pages.

Pages, CSS, JS and images are laid out at their public URLs, so no server is needed.
Run after any redesign change:  python3 tools/build_dist.py
"""
import os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE, RD, DIST = (os.path.join(ROOT, p) for p in ('site', 'redesign', 'dist'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)

shutil.rmtree(DIST, ignore_errors=True); os.makedirs(DIST)
# 1. static assets from the mirror (images, branding, icons); no mirrored HTML or Next.js runtime
SKIP_DIRS = {'_api-cache', '_next', 'opengraph-image'}
for root, dirs, files in os.walk(SITE):
    rel = os.path.relpath(root, SITE)
    if rel.split(os.sep)[0] in SKIP_DIRS: continue
    for f in files:
        if f == 'index.html' or f.endswith('.json') and rel == '.': continue
        copy(os.path.join(root, f), os.path.join(DIST, rel, f))
copy(os.path.join(SITE, 'opengraph-image', 'index.html'), os.path.join(DIST, 'opengraph-image.png'))
# 2. redesign assets served under /redesign/
for root, dirs, files in os.walk(RD):
    rel = os.path.relpath(root, RD)
    top = rel.split(os.sep)[0]
    if top in ('pages', 'products', 'v1', '_preview'): continue
    for f in files:
        if f.startswith('_') or f.endswith(('.py', '.md')) or f == '.DS_Store': continue
        if rel == '.' and f.endswith('.html'): continue
        copy(os.path.join(root, f), os.path.join(DIST, 'redesign', rel, f))
# 3. pages at their public URLs
copy(os.path.join(RD, 'index.html'), os.path.join(DIST, 'index.html'))
for root, dirs, files in os.walk(os.path.join(RD, 'products')):
    if 'index.html' in files:
        copy(os.path.join(root, 'index.html'), os.path.join(DIST, 'products', os.path.relpath(root, os.path.join(RD, 'products')), 'index.html'))
for root, dirs, files in os.walk(os.path.join(RD, 'pages')):
    if 'index.html' in files:
        copy(os.path.join(root, 'index.html'), os.path.join(DIST, os.path.relpath(root, os.path.join(RD, 'pages')), 'index.html'))
# footer link fix for pages built before the source footer changed
for r, _, fs in os.walk(DIST):
    for f in fs:
        if f.endswith('.html'):
            fp = os.path.join(r, f); t = open(fp).read()
            if 'href="/learn/peptides/"' in t: open(fp, 'w').write(t.replace('href="/learn/peptides/"', 'href="/learn"'))
# 4. 404 page in the same theme
import build_pages as bp
body = bp.page_head('Page not found', 'This page could not be found.', ['The link may be out of date, or the page has moved.'], [{'href': '/products', 'text': 'Browse all products'}, {'href': '/learn', 'text': 'Research library'}, {'href': '/contact', 'text': 'Contact our team'}], [('Not found', '/404')])
body += '<section class="wrap page-body"><a class="btn btn--primary" href="/">Back to the home page <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></section>'
open(os.path.join(DIST, '404.html'), 'w').write(bp.wrap('Page not found | Maylene', 'Page not found.', body, newsletter=False))
# 5. Cloudflare headers
open(os.path.join(DIST, '_headers'), 'w').write('''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin

/redesign/*
  Cache-Control: public, max-age=3600

/_images/*
  Cache-Control: public, max-age=2592000

/products/pens/*
  Cache-Control: public, max-age=2592000

# Keep preview deployments out of search results.
https://:project.pages.dev/*
  X-Robots-Tag: noindex
''')
n = sum(len(f) for _, _, f in os.walk(DIST)); size = sum(os.path.getsize(os.path.join(r, x)) for r, _, f in os.walk(DIST) for x in f)
print(f'dist/: {n} files, {size/1e6:.1f} MB')
