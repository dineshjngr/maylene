#!/usr/bin/env python3
"""Build the redesigned product pages.
Run:  python3 tools/extract_products.py && python3 tools/build_product_pages.py
Reads redesign/product-data.json and writes redesign/products/<handle>/index.html for every product.
The announcement bar, header, newsletter, benefits strip, footer and cart popup are copied from
redesign/index.html so every page stays in sync with the home page. Also refreshes
redesign/cart-products.json so the cart popup and product cards know every product's variant."""
import html, json, os, re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RED = os.path.join(ROOT, "redesign")
SITE = os.path.join(ROOT, "site")
DATA = json.load(open(os.path.join(RED, "product-data.json"), encoding="utf-8"))
HOME = open(os.path.join(RED, "index.html"), encoding="utf-8").read()
CSS_VERSION = "20261013-pdp-2"
JS_VERSION = "20261013-pdp-2"

e = lambda v: html.escape(str(v), quote=True)


def between(start, end, s=HOME, include_end=True):
    i = s.index(start)
    j = s.index(end, i)
    return s[i:j + (len(end) if include_end else 0)]


SHELL_TOP = between('<div class="announce"', "</header>")
BENEFITS = between('<section class="features benefits-strip"', "</section>")
NEWSLETTER = between('<section class="section nl nl--band"', "</section>")
FOOTER = between('<footer class="footer"', '<p class="sr-only" id="cart-feedback"', include_end=False)
FOOTER += '<p class="sr-only" id="cart-feedback" role="status" aria-live="polite"></p>'
STYLES_LINK = re.search(r'<link rel="stylesheet" href="/redesign/styles\.css[^"]*">', HOME).group(0)
HEADER_LINK = re.search(r'<link rel="stylesheet" href="/redesign/header\.css[^"]*">', HOME).group(0)
SCRIPTS = {name: re.search(rf'<script src="/redesign/{name}\.js[^"]*" defer></script>', HOME).group(0)
           for name in ("products", "header", "support", "newsletter")}

ICON = {
    "arrow": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    "external": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>',
    "cart": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3h2l3 12h10l3-8H6M9 20h.01M18 20h.01"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/></svg>',
    "pen": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 4 6 6M16.5 6.5 7 16l-3 4 4-3 9.5-9.5M10 13l1 1"/></svg>',
    "box": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/></svg>',
    "flask": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3"/><path d="M7.5 15h9"/></svg>',
    "doc": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 8 4v5c0 4-3 7-8 9-5-2-8-5-8-9V7z"/><path d="m8.5 12 2.5 2.5 4.5-5"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h11v9H3zM14 10h4l3 3v3h-7z"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17.5" cy="17.5" r="1.8"/></svg>',
    "snow": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2v20M4.9 6.5l14.2 11M19.1 6.5 4.9 17.5M9.5 3.5 12 6l2.5-2.5M9.5 20.5 12 18l2.5 2.5"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
    "lock": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>',
    "calc": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01M8 18h4"/></svg>',
    "plus": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    "check": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4.5 4.5L19 7"/></svg>',
    "info": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>',
}
STAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8z"/></svg>'


PEN_ICON = next("/_images/" + f for f in sorted(os.listdir(os.path.join(SITE, "_images"))) if f.startswith("generic-navy-pen-w96-"))


def nb(text):
    """Keep compound names such as BPC-157 or TB-500 together when a title wraps."""
    return re.sub(r"(?<=\w)-(?=\w)", "\u2011", e(text))


def money(v):
    return f"£{v:,.2f}"


def stars(rating, cls="stars"):
    rating = float(rating or 0)
    out = []
    for i in range(5):
        fill = max(0.0, min(1.0, rating - i))
        out.append(f'<span class="star" style="--fill:{fill * 100:.0f}%">{STAR}</span>')
    return f'<span class="{cls}" role="img" aria-label="{rating:.1f} out of 5 stars">{"".join(out)}</span>'


def noun(p, n=1):
    word = "bundle" if p["isBundle"] else "pen"
    return word if n == 1 else word + "s"


def short_label(p):
    if p["isBundle"]:
        return f'Product bundle · {p["details"][1]["strong"] if len(p["details"]) > 1 else "paired compounds"}'
    return f'{p["variant"]} labelled content · prefilled pen'


def picture(img, alt, sizes, cls="", loading="lazy", priority=False):
    attrs = f' fetchpriority="high"' if priority else ""
    return (f'<img{f" class={chr(34)}{cls}{chr(34)}" if cls else ""} src="{e(img["src"])}" srcset="{e(img["srcset"])}" '
            f'sizes="{e(sizes)}" alt="{e(alt)}" width="1080" height="1080" loading="{loading}" decoding="async"{attrs}>')


def discount(p):
    if p["compareAt"] and p["compareAt"] > p["price"]:
        return round((p["compareAt"] - p["price"]) / p["compareAt"] * 100)
    return 0


# ---------- page sections ----------

def gallery(p):
    imgs = p["gallery"]
    seal = ""
    if p["purity"]:
        seal = (f'<a class="pdp-seal" href="#lab-reports" aria-label="{e(p["purity"])}% reported purity for the tested sample. View the lab report">'
                f'<span class="pdp-seal__mark" aria-hidden="true">{ICON["shield"]}</span>'
                f'<span><strong>{e(p["purity"])}% purity</strong><small>Independent test · tested sample</small></span></a>')
    stage_alts = [p["imageAlt"]] + [f'{p["title"]} — view {i + 2}' for i in range(len(imgs) - 1)]
    slides = "".join(
        f'<figure class="pdp-gallery__slide" id="pdp-slide-{i}" data-index="{i}"{"" if i == 0 else " aria-hidden=" + chr(34) + "true" + chr(34)}>'
        f'{picture(img, stage_alts[i], "(max-width: 900px) 100vw, 640px", loading="eager" if i == 0 else "lazy", priority=i == 0)}</figure>'
        for i, img in enumerate(imgs))
    thumbs = "".join(
        f'<button class="pdp-gallery__thumb" type="button" data-index="{i}" aria-controls="pdp-slide-{i}" aria-pressed="{"true" if i == 0 else "false"}" aria-label="Show image {i + 1} of {len(imgs)}">'
        f'<img src="{e(img["thumb"])}" alt="" width="256" height="256" loading="lazy" decoding="async"></button>'
        for i, img in enumerate(imgs))
    dots = "".join(f'<span class="pdp-gallery__dot{" is-active" if i == 0 else ""}" data-index="{i}"></span>' for i in range(len(imgs)))
    badge = f'<span class="badge pdp-gallery__badge">{e(p["badge"].title())}</span>' if p["badge"] else ""
    return f'''
    <div class="pdp-gallery" data-gallery>
      <div class="pdp-gallery__stage">
        {badge}
        <button class="pdp-gallery__wish" type="button" data-wishlist data-product="{e(p["handle"])}" data-name="{e(p["title"])}" aria-label="Save {e(p["title"])} to wishlist" aria-pressed="false">{ICON["heart"]}</button>
        <div class="pdp-gallery__track" tabindex="0" aria-label="{e(p["title"])} images" data-track>{slides}</div>
        {seal}
        <div class="pdp-gallery__dots" aria-hidden="true">{dots}</div>
      </div>
      <div class="pdp-gallery__thumbs" role="group" aria-label="Choose an image">{thumbs}</div>
    </div>'''


def facts(p):
    items = []
    if p["isBundle"]:
        items.append((ICON["box"], "Product bundle", "Format"))
        count = p["details"][1]["strong"] if len(p["details"]) > 1 else "2 products"
        items.append((ICON["pen"], count, "In each bundle"))
    else:
        items.append((ICON["pen"], "Prefilled pen", "Format"))
        items.append((ICON["flask"], p["variant"], "Labelled content"))
    if p["purity"]:
        items.append((ICON["shield"], f'{p["purity"]}%', "Reported purity", "#lab-reports"))
    elif p["reports"]:
        items.append((ICON["doc"], f'{len(p["reports"])} lab report{"s" if len(p["reports"]) > 1 else ""}', "Independent tests", "#lab-reports"))
    else:
        items.append((ICON["doc"], "Records", "Certificates library", "/certificates"))
    out = []
    for item in items:
        icon, strong, small = item[:3]
        tag, attr = ("a", f' href="{item[3]}"') if len(item) > 3 else ("div", "")
        out.append(f'<li><{tag} class="pdp-fact"{attr}><span class="pdp-fact__icon">{icon}</span><span><strong>{e(strong)}</strong><small>{e(small)}</small></span></{tag}></li>')
    return f'<ul class="pdp-facts" aria-label="Product details">{"".join(out)}</ul>'


def strengths(p):
    if not p["options"]:
        return ""
    links = []
    for o in p["options"]:
        current = o["handle"] == p["handle"]
        links.append(
            f'<a class="pdp-strength" href="/products/{e(o["handle"])}"{" aria-current=" + chr(34) + "page" + chr(34) if current else ""}>'
            f'<strong>{e(o["variant"])}</strong><small>{money(o["price"])}</small></a>')
    return f'''
      <div class="pdp-option">
        <div class="pdp-option__head"><h2 class="pdp-option__title" id="strength-label">Labelled content</h2><span class="pdp-option__value">{e(p["variant"])} selected</span></div>
        <nav class="pdp-strengths" aria-labelledby="strength-label">{"".join(links)}</nav>
      </div>'''


def quantities(p):
    rows = []
    for n in (1, 2, 4):
        total = p["price"] * n
        was = p["compareAt"] * n if p["compareAt"] else None
        marks = "".join(f'<img src="{PEN_ICON}" alt="" width="32" height="32" loading="lazy" decoding="async">' for _ in range(n))
        tag = '<span class="pdp-qty__tag">Recommended</span>' if n == 2 else ""
        rows.append(f'''
          <label class="pdp-qty">
            <input type="radio" name="quantity" value="{n}" data-total="{total:.2f}" data-was="{(was or 0):.2f}"{" checked" if n == 1 else ""}>
            <span class="pdp-qty__card">{tag}
              <span class="pdp-qty__marks" aria-hidden="true">{marks}</span>
              <span class="pdp-qty__name"><strong>{n} {noun(p, n)}</strong><small>{money(p["price"])} each</small></span>
              <span class="pdp-qty__price">{f"<s>{money(was)}</s>" if was else ""}<strong>{money(total)}</strong></span>
            </span>
          </label>''')
    return f'''
      <fieldset class="pdp-option pdp-option--qty">
        <legend class="pdp-option__title">Choose your quantity</legend>
        <div class="pdp-qtys">{"".join(rows)}</div>
      </fieldset>'''


def buybox(p):
    rating = ""
    if p["reviewCount"]:
        rating = (f'<a class="pdp-rating" href="#reviews">{stars(p["rating"])}<span><strong>{float(p["rating"]):.1f}</strong> · {p["reviewCount"]} reviews</span></a>')
    social = f'<span class="pdp-social">{ICON["check"]}{p["purchased"]}+ others purchased</span>' if p["purchased"] else ""
    off = discount(p)
    price = (f'<div class="pdp-price" aria-live="polite">'
             f'<strong data-price>{money(p["price"])}</strong>'
             + (f'<s data-was aria-label="Regular price">{money(p["compareAt"])}</s><span class="pdp-price__save">Save {off}%</span>' if off else "")
             + '</div>')
    in_stock = (p.get("inventory") or 0) > 0
    stock = (f'<p class="pdp-stock{"" if in_stock else " pdp-stock--out"}"><span aria-hidden="true"></span>'
             f'{"In stock · same-day dispatch before 4pm" if in_stock else "Currently unavailable"}</p>')
    brand = f' · {e(p["brand"])}' if p.get("brand") else ""
    return f'''
    <div class="pdp-buy">
      <p class="label pdp-buy__eyebrow">{e(p["category"])}{brand}</p>
      <h1 class="pdp-buy__title">{nb(p["title"])}</h1>
      <div class="pdp-buy__meta">{rating}{social}</div>
      {price}
      {stock}
      <p class="pdp-buy__desc">{e(p["description"])}</p>
      {facts(p)}
      {strengths(p)}
      {quantities(p)}
      <div class="pdp-cta" id="order-module">
        <button class="btn btn--primary pdp-cta__add" type="button" data-add data-product="{e(p["handle"])}" data-name="{e(p["title"])}"{"" if in_stock else " disabled"}>
          {ICON["cart"]}<span data-add-label>{"Add to cart" if in_stock else "Unavailable"}</span><span class="pdp-cta__sep" aria-hidden="true"></span><span class="pdp-cta__total" data-total>{money(p["price"])}</span>
        </button>
        <button class="pdp-cta__wish" type="button" data-wishlist data-product="{e(p["handle"])}" data-name="{e(p["title"])}" aria-label="Save {e(p["title"])} to wishlist" aria-pressed="false">{ICON["heart"]}</button>
      </div>
      <p class="pdp-cta__status" data-cart-status role="status" aria-live="polite"></p>
      <div class="pdp-pay">
        <ul class="pdp-pay__brands" aria-label="Accepted payment methods"><li>VISA</li><li>Mastercard</li><li>AMEX</li><li>Apple Pay</li><li>Google Pay</li><li>Klarna</li></ul>
        <span class="pdp-pay__secure">{ICON["lock"]}Secure checkout</span>
      </div>
      <section class="pdp-delivery" aria-labelledby="delivery-heading">
        <h2 id="delivery-heading">{ICON["truck"]}Free UK delivery</h2>
        <dl>
          <div><dt>Dispatch days</dt><dd>Monday–Friday</dd></div>
          <div><dt>UK delivery</dt><dd>1–2 business days</dd></div>
          <div><dt>International</dt><dd>£35 flat rate</dd></div>
        </dl>
        <p>Same-day dispatch for payments confirmed before <strong>4pm UK time</strong>. Delivery estimate is after dispatch.</p>
        <p class="pdp-delivery__foot">{ICON["snow"]}Temperature-controlled packaging</p>
      </section>
      <div class="pdp-tools">
        <a href="/dosage-calculator">{ICON["calc"]}Dosage calculator{ICON["arrow"]}</a>
        <a href="{"#lab-reports" if p["reports"] else "/certificates"}">{ICON["doc"]}{"View lab reports" if p["reports"] else "Certificates & records"}{ICON["arrow"]}</a>
      </div>
      <p class="pdp-ruo">{ICON["info"]}<span><strong>For laboratory research only.</strong> Not for human or veterinary use.</span></p>
    </div>'''


def accordions(p):
    out = []
    for i, a in enumerate(p["accordions"]):
        body = a["html"]
        body = body.replace('<a href="/terms">Read the returns policy</a>', '<a class="pdp-acc__link" href="/terms#returns-and-refunds">Read the returns policy</a>')
        out.append(f'''
        <details class="pdp-acc"{" open" if i == 0 else ""}>
          <summary><span>{e(a["title"])}</span><i aria-hidden="true">{ICON["plus"]}</i></summary>
          <div class="pdp-acc__body">{body}</div>
        </details>''')
    return "".join(out)


def reports(p):
    if p["reports"]:
        rows = []
        for r in p["reports"]:
            seal = (f'<span class="coa__seal"><strong>{e(r["purity"])}%</strong><small>purity</small></span>' if r["purity"]
                    else f'<span class="coa__seal coa__seal--icon">{ICON["doc"]}</span>')
            rows.append(f'''
          <li><a class="coa__item" href="{e(r["href"])}" target="_blank" rel="noopener noreferrer">
            {seal}
            <span class="coa__copy"><strong>{e(r["title"])}</strong><small>{e(r["subtitle"])}</small></span>
            <span class="coa__open">Read report{ICON["external"]}<span class="sr-only"> (opens in a new tab)</span></span>
          </a></li>''')
        n = len(p["reports"])
        return f'''
      <aside class="coa" id="lab-reports" aria-labelledby="coa-heading" tabindex="-1">
        <div class="coa__head"><div><p class="label">Lab reports</p><h2 id="coa-heading">Independent Janoshik tests</h2></div><span class="coa__count">{n} report{"s" if n > 1 else ""}</span></div>
        <p class="coa__sub">Matched to this exact product and strength.</p>
        <ul class="coa__list">{"".join(rows)}</ul>
        <p class="coa__note">{ICON["info"]}Reports cover the tested sample. Match the batch details to your product.</p>
        <a class="coa__all" href="/certificates">All lab reports{ICON["arrow"]}</a>
      </aside>'''
    return f'''
      <aside class="coa coa--empty" id="lab-reports" aria-labelledby="coa-heading">
        <div class="coa__head"><div><p class="label">Documentation</p><h2 id="coa-heading">Certificates &amp; records</h2></div></div>
        <p class="coa__sub">Certificates and batch records for the catalogue are collected in one place, so you can review the documentation before you order.</p>
        <a class="btn btn--ghost coa__btn" href="/certificates">Browse certificates{ICON["arrow"]}</a>
        <p class="coa__note">{ICON["info"]}Questions about a batch? Email <a href="mailto:contact@maylene.uk">contact@maylene.uk</a>.</p>
      </aside>'''


def reviews(p):
    if not p["reviewCount"] or not p["reviews"]:
        return ""
    cards = []
    for r in p["reviews"]:
        initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", r["author"])[:2]).upper()
        when = date.fromisoformat(r["date"]).strftime("%-d %b %Y") if r.get("date") else ""
        title = f'<h3>{e(r["title"])}</h3>' if r.get("title") else ""
        cards.append(f'''
        <article class="review">
          <div class="review__top">{stars(r["rating"], "stars stars--sm")}<time datetime="{e(r.get("date", ""))}">{e(when)}</time></div>
          {title}<p>{e(r["body"])}</p>
          <footer><span class="review__avatar" aria-hidden="true">{e(initials)}</span><span><strong>{e(r["author"])}</strong><small>{ICON["check"]}Verified purchase</small></span></footer>
        </article>''')
    return f'''
<section class="wrap section pdp-reviews" id="reviews" aria-labelledby="reviews-heading" tabindex="-1">
  <div class="head"><div><p class="label">Reviews</p><h2 class="h2" id="reviews-heading">Loved by our customers</h2></div></div>
  <div class="pdp-reviews__grid">
    <div class="pdp-reviews__summary">
      <strong class="pdp-reviews__score">{float(p["rating"]):.1f}<span>/5</span></strong>
      {stars(p["rating"], "stars stars--lg")}
      <p>Based on {p["reviewCount"]} reviews for {e(p["title"])}.</p>
      <p class="pdp-reviews__shown">Showing {len(p["reviews"])} of {p["reviewCount"]} reviews</p>
    </div>
    <div class="pdp-reviews__list" role="region" aria-label="Customer reviews" tabindex="0">{"".join(cards)}</div>
  </div>
</section>'''


def card(h):
    r = DATA[h]
    img = r["gallery"][0]
    off = discount(r)
    price = (f'<s>{money(r["compareAt"])}</s><span class="card__discount">Save {off}%</span>' if off else "") + f'<strong>{money(r["price"])}</strong>'
    return f'''
    <article class="card">
      <div class="card__img">
        <a class="card__image-link" href="/products/{e(h)}" aria-label="View {e(r["title"])}">{picture(img, r["title"], "(max-width: 560px) 82vw, (max-width: 1024px) 45vw, 340px")}</a>
        <button class="card__wishlist" type="button" data-product="{e(h)}" data-name="{e(r["title"])}" aria-label="Save {e(r["title"])} to wishlist" aria-pressed="false">{ICON["heart"]}</button>
      </div>
      <div class="card__body">
        <h3 class="card__name"><a href="/products/{e(h)}">{nb(r["title"])}</a></h3>
        <p class="card__description">{e(short_label(r))}</p>
        <div class="card__purchase"><span class="card__price">{price}</span><button class="card__add" type="button" data-product="{e(h)}" data-name="{e(r["title"])}" data-price="{r["price"]:.2f}" aria-label="Add {e(r["title"])} to cart">{ICON["cart"]}<span>Add to cart</span></button></div>
      </div>
    </article>'''


def related(p):
    handles = [h for h in p["related"] if h in DATA and h != p["handle"]]
    # Fill to four cards from the same category so every page shows a full row.
    for h, r in DATA.items():
        if len(handles) >= 4:
            break
        if h not in handles and h != p["handle"] and r["category"] == p["category"]:
            handles.append(h)
    for h in DATA:
        if len(handles) >= 4:
            break
        if h not in handles and h != p["handle"]:
            handles.append(h)
    return f'''
<section class="wrap section featured-products pdp-related" aria-labelledby="related-heading" data-support-anchor>
  <div class="head"><div><p class="label">You may also like</p><h2 class="h2" id="related-heading">More from the collection</h2></div><a class="more" href="/products">View all products{ICON["arrow"]}</a></div>
  <div class="grid" aria-label="Recommended products">{"".join(card(h) for h in handles[:4])}</div>
  <p class="sr-only" id="wishlist-status" role="status" aria-live="polite"></p>
</section>'''


def collection_band():
    pens = sum(1 for r in DATA.values() if not r["isBundle"])
    bundles = sum(1 for r in DATA.values() if r["isBundle"])
    return f'''
<section class="wrap pdp-band" aria-labelledby="band-heading">
  <div class="pdp-band__in">
    <div class="pdp-band__copy"><p class="label label--light">Meet the collection</p><h2 id="band-heading">More to discover. <span>All in one place.</span></h2></div>
    <a class="pdp-band__link" href="/collections/research-pens"><strong>{pens}</strong><span>Research pens</span>{ICON["arrow"]}</a>
    <a class="pdp-band__link" href="/collections/product-bundles"><strong>{bundles}</strong><span>Product bundles</span>{ICON["arrow"]}</a>
    <a class="pdp-band__link pdp-band__link--cta" href="/products"><strong>Shop</strong><span>Explore the full range</span>{ICON["arrow"]}</a>
  </div>
</section>'''


def sticky_bar(p):
    return f'''
<div class="pdp-bar" data-bar hidden>
  <div class="pdp-bar__in">
    <img src="{e(p["gallery"][0]["thumb"])}" alt="" width="48" height="48">
    <div class="pdp-bar__copy"><strong>{e(p["title"])}</strong><span><span data-bar-qty>1 {noun(p)}</span> · <span data-bar-total>{money(p["price"])}</span></span></div>
    <button class="btn btn--primary pdp-bar__add" type="button" data-bar-add{"" if (p.get("inventory") or 0) > 0 else " disabled"}>{ICON["cart"]}<span>Add to cart</span></button>
  </div>
</div>'''


def json_ld(handle):
    src = open(os.path.join(SITE, "products", handle, "index.html"), encoding="utf-8").read()
    blocks = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try:
            d = json.loads(block)
        except ValueError:
            continue
        if d.get("@type") in ("Product", "BreadcrumbList"):
            blocks.append(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False, separators=(",", ":"))}</script>')
    return "\n".join(blocks)


def page(p):
    cat_href = "/collections/product-bundles" if p["isBundle"] else "/collections/research-pens"
    meta = f'{p["title"]}: {p["description"]}'[:155].rsplit(" ", 1)[0] + "…" if len(p["description"]) > 120 else p["description"]
    data = {"handle": p["handle"], "name": p["title"], "price": p["price"], "compareAt": p["compareAt"],
            "variantId": p["variantId"], "unit": noun(p), "units": noun(p, 2)}
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(p["title"])} | Research Peptides | Maylene</title>
<meta name="description" content="{e(meta)}">
<link rel="icon" href="/favicon.ico">
<meta property="og:title" content="{e(p["title"])} | Maylene">
<meta property="og:image" content="{e(p["image"])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
{STYLES_LINK}
{HEADER_LINK}
<link rel="stylesheet" href="/redesign/product.css?v={CSS_VERSION}">
{json_ld(p["handle"])}
</head>
<body class="pdp-page">

{SHELL_TOP}

<main>

<nav class="wrap pdp-crumbs" aria-label="Breadcrumb">
  <ol><li><a href="/">Home</a></li><li><a href="/products">Shop</a></li><li><a href="{cat_href}">{e(p["category"])}</a></li><li><span aria-current="page">{e(p["title"])}</span></li></ol>
</nav>

<section class="wrap pdp" aria-label="{e(p["title"])}" data-product-page='{e(json.dumps(data))}'>
  {gallery(p)}
  {buybox(p)}
</section>

{BENEFITS}

<section class="wrap section pdp-info" aria-labelledby="info-heading">
  <div class="head"><div><p class="label">Product information</p><h2 class="h2" id="info-heading">Care, delivery and documentation</h2></div></div>
  <div class="pdp-info__grid">
    <div class="pdp-info__acc">{accordions(p)}</div>
    {reports(p)}
  </div>
</section>

{reviews(p)}

{related(p)}

{collection_band()}

{NEWSLETTER}

</main>

{FOOTER}
{sticky_bar(p)}
{SCRIPTS["products"]}
{SCRIPTS["header"]}
{SCRIPTS["support"]}
{SCRIPTS["newsletter"]}
<script src="/redesign/product.js?v={JS_VERSION}" defer></script>
</body>
</html>
'''


def cart_catalogue():
    path = os.path.join(RED, "cart-products.json")
    current = json.load(open(path, encoding="utf-8"))
    current["products"] = [{
        "handle": h, "name": r["title"], "variantId": r["variantId"], "variant": r["variant"],
        "image": r["gallery"][0]["thumb"], "url": f"/products/{h}",
    } for h, r in DATA.items()]
    json.dump(current, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(path, "a").write("\n")


if __name__ == "__main__":
    for handle, p in DATA.items():
        out = os.path.join(RED, "products", handle)
        os.makedirs(out, exist_ok=True)
        open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page(p))
    cart_catalogue()
    print(f"{len(DATA)} product pages -> redesign/products/")
