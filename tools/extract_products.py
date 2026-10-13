#!/usr/bin/env python3
"""Extract structured product data from the mirrored product pages.
Run:  python3 tools/extract_products.py  ->  writes redesign/product-data.json
Sources per page: the Next.js flight payload (store product, variants, sibling strengths),
the Product JSON-LD (rating, reviews, brand) and the server-rendered HTML (copy, accordions,
lab reports, related products)."""
import glob, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "redesign", "product-data.json")
LIVE = "https://www.maylene.uk"


def flight(s):
    out = ""
    for c in re.findall(r"self\.__next_f\.push\((\[.*?\])\)</script>", s, re.S):
        try:
            a = json.loads(c)
            if len(a) > 1 and isinstance(a[1], str):
                out += a[1]
        except ValueError:
            pass
    return out


def text(fragment):
    t = re.sub(r"<!-- -->", "", fragment)
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def local(url):
    return url.replace(LIVE, "") if url else url


def clean_links(fragment):
    """Make mirrored links match the preview server's clean URLs and drop Cloudflare email obfuscation."""
    fragment = re.sub(r"<!-- -->", "", fragment)
    fragment = re.sub(r'href="(/[^"#]*?)/index\.html', r'href="\1', fragment)
    fragment = re.sub(r'href="/index\.html', 'href="/', fragment)
    fragment = re.sub(r'<a [^>]*href="/cdn-cgi/l/email-protection[^"]*"[^>]*>.*?</a>',
                      '<a href="mailto:contact@maylene.uk">contact@maylene.uk</a>', fragment, flags=re.S)
    fragment = re.sub(r"<svg.*?</svg>", "", fragment, flags=re.S)
    fragment = re.sub(r' (class|style|id|data-[a-z-]+)="[^"]*"', "", fragment)
    return fragment


IMAGES = {}
for _f in os.listdir(os.path.join(SITE, "_images")):
    _m = re.match(r"(.+)-w(\d+)-[0-9a-f]+\.(\w+)$", _f)
    if _m:
        IMAGES.setdefault(_m.group(1), {})[int(_m.group(2))] = "/_images/" + _f


def srcset(base):
    """All locally exported widths of one image, for a responsive srcset."""
    widths = {w: u for w, u in IMAGES.get(base, {}).items() if w <= 1920}
    return {"name": base, "src": widths.get(1080) or widths[max(widths)],
            "thumb": widths.get(256) or widths[min(widths)],
            "srcset": ", ".join(f"{u} {w}w" for w, u in sorted(widths.items()) if w >= 256)}


def variant_summary(p):
    v = p["variants"][0]
    cp = v.get("calculated_price") or {}
    return {
        "handle": p["handle"],
        "title": p["title"],
        "variantId": v["id"],
        "variant": v["title"],
        "sku": v.get("sku"),
        "price": cp.get("calculated_amount"),
        "inventory": v.get("inventory_quantity"),
        "thumbnail": local(p.get("thumbnail")),
    }


def extract(path):
    s = open(path, encoding="utf-8").read()
    handle = path.split(os.sep)[-2]
    rsc = flight(s)
    i = rsc.index('{"product":{"id":"prod_')
    props, _ = json.JSONDecoder().raw_decode(rsc, i)
    prod = props["product"]
    base = variant_summary(prod)

    ld = {}
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            d = json.loads(block)
        except ValueError:
            continue
        if d.get("@type") == "Product":
            ld = d
    body = s[s.index('id="order-module"'):]

    price_block = re.search(r'<div[^>]*aria-live="polite"[^>]*>(.*?)</div>', body, re.S).group(1)
    compare = re.search(r"<del[^>]*>£([\d,.]+)", price_block)
    badge = re.search(r'<span[^>]*aria-label="([^"]*)"[^>]*>([A-Z ]+)</span>', price_block)

    desc_html = re.search(r'<p[^>]*>([^<]{40,}?)</p><ul[^>]*aria-label="Product details"', body, re.S)
    details = []
    ul = re.search(r'<ul[^>]*aria-label="Product details"[^>]*>(.*?)</ul>', body, re.S)
    if ul:
        for li in re.findall(r"<li[^>]*>(.*?)</li>", ul.group(1), re.S):
            strong = re.search(r"<strong[^>]*>(.*?)</strong>", li, re.S)
            if strong:
                details.append({"strong": text(strong.group(1)), "rest": text(li.replace(strong.group(0), ""))})

    # Gallery: every distinct image shown in the order module's gallery, with all local width variants.
    gallery, seen = [], set()
    head = body.split('aria-label="Product details"')[0]
    alts = re.findall(r'<img alt="([^"]*)"', head)
    for src in re.findall(r'src="/_images/([^"]+)"', head):
        m = re.match(r"(.+)-w\d+-[0-9a-f]+\.(\w+)$", src)
        if not m or m.group(1) in seen or "generic-navy-pen" in src:
            continue
        seen.add(m.group(1))
        gallery.append(srcset(m.group(1)))
    main_alt = alts[0] if alts else prod["title"]
    reports = []
    for href, label, inner in re.findall(r'<a [^>]*?href="(https://(?:verify\.|www\.)?janoshik\.com[^"]+)"[^>]*aria-label="([^"]*)"[^>]*>(.*?)</a>', body, re.S):
        purity = re.search(r"([\d.]+)%(?:<!-- -->)? Reported purity", inner)
        title = re.search(r"<strong[^>]*>(.*?)</strong>", inner, re.S)
        small = re.search(r"<small[^>]*>(.*?)</small>", inner, re.S)
        reports.append({"href": href, "purity": purity and purity.group(1),
                        "title": text(title.group(1)) if title else "Lab report",
                        "subtitle": text(small.group(1)) if small else ""})
    purity = next((r["purity"] for r in reports if r["purity"]), None)
    if not purity:
        m = re.search(r"; ([\d.]+)% reported purity", body)
        purity = m and m.group(1)

    accordions = []
    for summary, inner in re.findall(r"<details[^>]*><summary[^>]*>(.*?)</summary><div[^>]*>(.*?)</div></details>", body, re.S):
        accordions.append({"title": text(summary), "html": clean_links(inner)})

    related = []
    rel = re.search(r'aria-label="Recommended products"[^>]*>(.*?)</section>', body, re.S)
    if rel:
        for art in re.findall(r"<article[^>]*>(.*?)</article>", rel.group(1), re.S):
            h = re.search(r'href="/products/([^/"]+)', art)
            name = re.search(r"<h3[^>]*>(.*?)</h3>", art, re.S)
            if h and name:
                related.append(h.group(1))

    purchased = re.search(r"<strong>(\d+)(?:<!-- -->)?\+</strong> others purchased", s)
    agg = ld.get("aggregateRating") or {}
    reviews = [{"author": r["author"]["name"], "title": r.get("name"), "body": r.get("reviewBody"),
                "date": r.get("datePublished"), "rating": r["reviewRating"]["ratingValue"]}
               for r in ld.get("review", [])]

    options = []
    for o in props.get("contentOptions") or []:
        if isinstance(o, dict) and o.get("handle"):
            options.append(variant_summary(o))
        elif isinstance(o, str):
            options.append(base)  # "$..." back-reference to the current product
    if not any(o["handle"] == handle for o in options) and options:
        options.append(base)
    options.sort(key=lambda o: float(re.sub(r"[^\d.]", "", o["variant"]) or 0))

    cats = [c["name"] for c in prod.get("categories") or []]
    return {
        **base,
        "id": prod["id"],
        "category": cats[0] if cats else "Research Pens",
        "brand": (ld.get("brand") or {}).get("name"),
        "shortDescription": prod.get("description"),
        "description": text(desc_html.group(1)) if desc_html else "",
        "details": details,
        "compareAt": float(compare.group(1).replace(",", "")) if compare else None,
        "badge": badge.group(2).strip() if badge else None,
        "gallery": gallery,
        "image": local(prod.get("thumbnail")),
        "imageAlt": main_alt,
        "purity": purity,
        "reports": reports,
        "options": options if len(options) > 1 else [],
        "accordions": accordions,
        "related": related,
        "purchased": int(purchased.group(1)) if purchased else None,
        "rating": agg.get("ratingValue"),
        "reviewCount": agg.get("reviewCount"),
        "reviews": reviews,
        "isBundle": "bundle" in handle,
    }


if __name__ == "__main__":
    data = {}
    for f in sorted(glob.glob(os.path.join(SITE, "products", "*", "index.html"))):
        if "order-module" in open(f, encoding="utf-8").read():
            p = extract(f)
            data[p["handle"]] = p
    json.dump(data, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{len(data)} products -> {os.path.relpath(OUT, ROOT)}")
