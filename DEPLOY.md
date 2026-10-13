# Deploying the Maylene redesign to Cloudflare

The redesign is a **static design showcase** served as a Cloudflare Worker with static assets.
There is no server code. Cart, checkout, newsletter and contact submissions are not connected.

## How the deploy works

Cloudflare runs `npx wrangler deploy`. `wrangler.toml` tells Wrangler to:
1. run `python3 tools/build_dist.py`, which assembles every page and asset into `dist/`;
2. upload `dist/` as static assets, using `dist/404.html` for unknown URLs.

## Cloudflare settings (Workers & Pages → your Worker → Settings → Build)

| Setting | Value |
|---|---|
| Git repository | `dineshjngr/maylene`, branch `main` |
| Build command | *(leave empty)* |
| Deploy command | `npx wrangler deploy` |
| Root directory | `/` |

The Worker name in Cloudflare must match `name` in `wrangler.toml` (`maylene`). If your Worker has a different name, change `name` to match.

## Updating the site

```
python3 tools/build_pages.py            # regenerate content pages after changing redesign/index.html
python3 tools/build_product_pages.py    # regenerate product detail pages
npx wrangler deploy --dry-run           # optional: check the build locally
```
Commit and push to `main`; Cloudflare rebuilds and deploys.

Local preview with the live-store proxy is still `python3 serve.py` → http://127.0.0.1:8765/.
