# Maylene site export

Static mirror of https://www.maylene.uk (exported 13 Oct 2026) as the reference for the redesign.

## Preview

```bash
python3 serve.py
```

Then open http://127.0.0.1:8765/

## Layout

- `site/` — the exported site. 77 pages, each saved as `<path>/index.html`
  (e.g. `site/about/index.html`, `site/products/apex-bpc-157-10mg-pen/index.html`).
- `site/_next/static/` — the site's CSS, JS chunks and fonts.
- `site/_images/` — optimised image variants; `site/products/`, `site/images/`, `site/branding/` — original images.
- `site/_mirror-map.json` — original URL -> local file map.
- `site/_api-cache/` — cached responses from the live catalogue/store APIs (filled as pages are visited).
- `serve.py` — preview server. Maps clean URLs, resolves Next.js `/_next/image` requests to local files,
  and proxies `/api/*` and `/store/*` to the live APIs with on-disk caching.
- `tools/mirror.py` — the crawler used for the export (`python3 tools/mirror.py site tools/sitemap-urls.txt`,
  add `--pages-only` to refresh just the HTML). `tools/sweep.py` renders every page headlessly and reports JS errors.

## Notes

- The site is a Next.js app backed by a Medusa store API. Pages are server-rendered HTML, so content, styles and
  images are all local. Live pricing/stock refresh and cart calls go through the proxy in `serve.py`.
- Cart/checkout, account and wishlist are not functional offline.

## Redesign

New pages live in `redesign/` and are served by `serve.py` at http://127.0.0.1:8765/redesign/ next to the
original mirror. The root homepage also serves the current redesign. They are plain HTML + CSS (no build step) and reuse
the exported images from `site/`.

- `redesign/index.html` — new home page (v2: clean, Inter-based layout)
- `redesign/styles.css` — design tokens, typography and components
- `redesign/v1/` — the first editorial-serif pass, kept for comparison at /redesign/v1/

### Product pages

All 19 product pages are redesigned in the same style and served at their normal URLs,
e.g. http://127.0.0.1:8765/products/apex-retatrutide-20mg-pen. The mirrored originals stay available
under `/original/`, e.g. http://127.0.0.1:8765/original/products/apex-retatrutide-20mg-pen.

- `tools/extract_products.py` — reads the mirrored product pages and writes `redesign/product-data.json`
  (prices, variants, strengths, gallery images, lab reports, accordions, reviews, related products).
- `tools/build_product_pages.py` — writes `redesign/products/<handle>/index.html` from that data. The
  announcement bar, header, benefits strip, newsletter and footer are copied from `redesign/index.html`,
  so rebuild after changing them. It also refreshes `redesign/cart-products.json`.
- `redesign/product.css` / `redesign/product.js` — page styles and behaviour (gallery, strength and
  quantity selection, add to cart via the shared basket in `products.js`, sticky buy bar).

```bash
python3 tools/extract_products.py && python3 tools/build_product_pages.py
```

Typography: Inter (all text), loaded from Google Fonts. References used for v2: a Framer "Orbix" store
template (type, structure, CTAs) and the Medilazar pharmacy theme (promo tiles, popular categories,
health-advice cards).
