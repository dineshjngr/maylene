# Deploying the Maylene redesign to Cloudflare Pages

The redesign is a **static design showcase**. Every page is plain HTML/CSS/JS; there is no server code.
Cart, checkout, newsletter and contact submissions are not connected in this build.

## One-time setup (Cloudflare dashboard)

1. Push this repository to GitHub (`origin` is `github.com/dineshjngr/maylene`).
2. Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git** → pick the repo.
3. Build settings:

   | Setting | Value |
   |---|---|
   | Framework preset | None |
   | Build command | `python3 tools/build_dist.py` |
   | Build output directory | `dist` |
   | Root directory | *(leave empty)* |

4. Save and deploy. Every push to `main` redeploys; other branches get preview URLs.

## Updating the site

- Edit files in `redesign/` (home page, styles, scripts) and rebuild the generated pages:
  ```
  python3 tools/build_pages.py            # content pages (about, learn, guides, faq …)
  python3 tools/build_product_pages.py    # product detail pages
  python3 tools/build_dist.py             # assemble dist/ locally to check
  ```
- Commit and push; Cloudflare runs `tools/build_dist.py` itself.

## Notes

- `dist/_headers` sets caching and adds `noindex` on `*.pages.dev` preview URLs.
- `dist/404.html` is the themed not-found page.
- Local preview with the live-store proxy is still `python3 serve.py` → http://127.0.0.1:8765/.
