#!/usr/bin/env python3
"""Rebuild the remaining site pages in the redesign theme.

Reads the mirrored Next.js pages in site/, extracts their main content, cleans it to
semantic HTML and wraps it in the redesigned header/footer. Special templates cover the
FAQ, contact form, collections, dosage calculator, account and wishlist.
Output: redesign/pages/<path>/index.html (served by serve.py ahead of the mirror).
"""
import os, re, json, html, urllib.parse
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site'); RD = os.path.join(ROOT, 'redesign'); OUT = os.path.join(RD, 'pages')
HOME = open(os.path.join(RD, 'index.html')).read()
PRODUCTS_PAGE = open(os.path.join(RD, 'products', 'index.html')).read()

# ---------- shared chrome, sliced from the home page so it stays in sync ----------
HEAD = HOME[:HOME.index('</head>')]
HEAD = re.sub(r'<title>.*?</title>', '<title>{title}</title>', HEAD, flags=re.S)
HEAD = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="{description}">', HEAD)
HEAD += '<link rel="stylesheet" href="/redesign/page.css?v={v}">\n</head>'
CHROME_TOP = HOME[HOME.index('<div class="announce"'):HOME.index('<main>')]
NEWSLETTER = HOME[HOME.index('<!-- NEWSLETTER -->'):HOME.index('</main>')]
TAIL = HOME[HOME.index('<footer class="footer"'):]
TAIL = re.sub(r'<script src="/redesign/(hero-search|hero-callout|carousel)\.js[^>]*></script>\n', '', TAIL)
TAIL = TAIL.replace('</body>', '<script src="/redesign/pages.js?v={v}" defer></script>\n</body>')
V = '2'

def fix_href(h):
    if not h: return h
    h = h.replace('/index.html', '/').replace('index.html', '')
    if h.startswith('/') and h != '/' and h.endswith('/'): h = h[:-1]
    if h.startswith('/_next/image'):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(h).query); h = q.get('url', [h])[0]
    return h

KEEP = {'div','h1','h2','h3','h4','p','ul','ol','li','a','strong','b','em','i','table','thead','tbody','tr','th','td','img','blockquote','dl','dt','dd','br','hr','section','article','figure','figcaption','code','pre','sup','sub','time'}
DROP = {'script','style','svg','button','form','input','select','textarea','template','iframe','noscript','label','option'}

class Clean(HTMLParser):
    """Keeps semantic structure, drops presentation. Handles the mirrored page-heading block."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []; self.skip = 0; self.stack = []
        self.eyebrow = ''; self.h1 = ''; self.intro = []; self.related = []
        self.mode = None; self.cap = None; self.depth_mark = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = a.get('class', '') or ''
        if self.skip: self.skip += 1; return
        if tag in DROP or (tag == 'nav' and a.get('aria-label') == 'Breadcrumb') or 'breadcrumb' in cls:
            self.skip = 1; return
        # page heading block (about/terms/contact style)
        if 'apex-page-eyebrow' in cls or 'apex-learning-eyebrow' in cls or 'apex-info-eyebrow' in cls:
            self.cap = ('eyebrow', []); self.cap_depth = len(self.stack)
        if 'apex-page-introduction' in cls or 'apex-learning-intro' in cls:
            self.cap = ('intro', []); self.cap_depth = len(self.stack)
        if tag == 'nav' and a.get('aria-label') == 'Related pages':
            self.cap = ('related', []); self.cap_depth = len(self.stack)
        if tag == 'h1' and not self.h1:
            self.cap = ('h1', []); self.cap_depth = len(self.stack)
        self.stack.append(tag)
        if self.cap:
            kind, buf = self.cap
            if kind == 'related' and tag == 'a': buf.append({'href': fix_href(a.get('href')), 'text': ''})
            elif kind == 'intro' and tag == 'p': buf.append('')
            return
        if tag in KEEP:
            if tag == 'a':
                href = fix_href(a.get('href'))
                extra = ' target="_blank" rel="noopener noreferrer"' if href and href.startswith('http') else ''
                self.out.append(f'<a href="{html.escape(href or "#")}"{extra}>')
            elif tag == 'img':
                src = fix_href(a.get('src', '')); self.out.append(f'<img src="{html.escape(src)}" alt="{html.escape(a.get("alt","") or "")}" loading="lazy" decoding="async">')
            elif tag in ('br', 'hr'): self.out.append(f'<{tag}>')
            else:
                idattr = f' id="{html.escape(a["id"])}"' if a.get('id') and not a['id'].startswith('_R_') else ''
                self.out.append(f'<{tag}{idattr}>')
    def handle_endtag(self, tag):
        if self.skip: self.skip -= 1; return
        if self.stack and self.stack[-1] == tag: self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag: self.stack.pop()
            if self.stack: self.stack.pop()
        if self.cap:
            kind, buf = self.cap
            if len(self.stack) <= self.cap_depth:
                if kind == 'eyebrow': self.eyebrow = re.sub(r'\s+', ' ', ''.join(buf)).strip()
                elif kind == 'h1': self.h1 = re.sub(r'\s+', ' ', ''.join(buf)).strip()
                elif kind == 'intro': self.intro = [b.strip() for b in buf if b.strip()]
                elif kind == 'related': self.related = [r for r in buf if r['text'].strip()]
                self.cap = None
            return
        if tag in KEEP and tag not in ('br', 'hr', 'img'): self.out.append(f'</{tag}>')
        elif tag == 'span': self.out.append(' ')
    def handle_data(self, d):
        if self.skip: return
        if self.cap:
            kind, buf = self.cap
            if kind in ('eyebrow', 'h1'): buf.append(d)
            elif kind == 'intro' and buf: buf[-1] += d
            elif kind == 'related' and buf: buf[-1]['text'] += d
            return
        self.out.append(d)
    def handle_entityref(self, n): self.handle_data(f'&{n};')
    def handle_charref(self, n): self.handle_data(f'&#{n};')
    def handle_comment(self, d): pass

def clean_main(path):
    s = open(os.path.join(SITE, path, 'index.html')).read()
    m = re.search(r'<main[^>]*>(.*?)</main>', s, re.S)
    body = m.group(1) if m else ''
    body = re.sub(r'<script type="application/ld\+json">.*?</script>', '', body, flags=re.S)
    c = Clean(); c.feed(body)
    out = ''.join(c.out)
    out = re.sub(r'<(p|li|h[2-4]|strong|em|span)>\s*</\1>', '', out)
    out = re.sub(r'\s+', ' ', out)
    out = re.sub(r'<(ul|ol)>\s*</\1>', '', out)
    for _ in range(4): out = re.sub(r'<div>\s*</div>', '', out)
    out = re.sub(r'<a href="[^"]*"[^>]*>\s*Back to [^<]*</a>', '', out)
    out = re.sub(r'(<p>\s*){2,}', '<p>', out); out = re.sub(r'(\s*</p>){2,}', '</p>', out)
    # cut in-page chrome that duplicates the site shell
    for marker in ['More to discover', 'Get exclusive deals', 'Research updates</h', 'Loved by our customers']:
        i = out.find(marker)
        if i > 0:
            j = out.rfind('<h2', 0, i); j = out.rfind('<section', 0, j if j > 0 else i)
            out = out[:j if j > 0 else i]
    hub = re.search(r'<h[23]>\s*Catalogue\s*</h[23]>.*?<h[23]>\s*Company\s*</h[23]>', out, re.S)
    if hub: out = out[:out.rfind('<section', 0, hub.start()) if out.rfind('<section', 0, hub.start()) > 0 else hub.start()]
    # link cards: <a><h3>…</h3><p>…</p></a>
    out = re.sub(r'<a href="([^"]+)"([^>]*)>((?:\s*<div>)*)\s*<h3>', r'<a href="\1"\2 class="linkcard">\3<h3>', out)
    out = re.sub(r'((?:<a href="[^"]+"[^>]*class="linkcard">.*?</a>\s*){2,})', r'<div class="linkcards">\1</div>', out, flags=re.S)
    def _cf(m):
        enc = m.group(1); k = int(enc[:2], 16)
        email = ''.join(chr(int(enc[i:i+2], 16) ^ k) for i in range(2, len(enc), 2))
        return f'<a href="mailto:{email}">{email}</a>'
    out = re.sub(r'<a href="/cdn-cgi/l/email-protection#([0-9a-f]+)"[^>]*>.*?</a>', _cf, out)
    out = re.sub(r'\[email(?:&#160;|\s)protected\]', 'contact@maylene.uk', out)
    out = out.replace('<a href="#">', '<a>').replace('<section>', '<section class="prose__section">')
    title = html.unescape(re.sub(r'<[^>]+>', '', (re.search(r'<title>(.*?)</title>', s, re.S) or [None, ''])[1] if re.search(r'<title>', s) else ''))
    desc = re.search(r'<meta name="description" content="([^"]*)"', s)
    return {'html': out, 'eyebrow': html.unescape(c.eyebrow), 'h1': html.unescape(c.h1), 'intro': [html.unescape(i) for i in c.intro], 'related': c.related, 'title': title or c.h1, 'description': html.unescape(desc.group(1)) if desc else ''}

def crumbs(parts):
    items = ['<a href="/">Home</a>']
    for label, href in parts[:-1]: items.append(f'<a href="{href}">{html.escape(label)}</a>')
    items.append(f'<span aria-current="page">{html.escape(parts[-1][0])}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span aria-hidden="true">/</span>'.join(items) + '</nav>'

def page_head(eyebrow, h1, intro, related, trail):
    rel = ''
    if related:
        rel = '<nav class="page-head__related" aria-label="Related pages">' + ''.join(f'<a href="{html.escape(r["href"] or "#")}">{html.escape(r["text"].strip())}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg></a>' for r in related) + '</nav>'
    intro_html = ''.join(f'<p>{html.escape(i)}</p>' for i in intro[:2])
    return f'''<section class="page-head"><div class="wrap">{crumbs(trail)}<div class="page-head__in"><div class="page-head__copy">{f'<p class="label">{html.escape(eyebrow)}</p>' if eyebrow else ''}<h1 class="h1">{html.escape(h1)}</h1><div class="page-head__intro">{intro_html}</div></div>{rel}</div></div></section>'''

def wrap(title, description, body, newsletter=True, extra_head=''):
    return (HEAD.replace('{title}', html.escape(title)).replace('{description}', html.escape(description)).replace('{v}', V).replace('</head>', extra_head + '</head>')
            + '\n<body>\n\n' + CHROME_TOP + '<main>\n' + body + ('\n' + NEWSLETTER if newsletter else '') + '</main>\n\n' + TAIL.replace('{v}', V))

def write(path, content):
    d = os.path.join(OUT, path); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w').write(content)

# ---------- generic content pages ----------
TRAILS = {
  'about': [('About Maylene', '/about')], 'affiliate': [('Partners', '/wholesale'), ('Affiliate program', '/affiliate')], 'bulk-offers': [('Partners', '/wholesale'), ('Bulk offers', '/bulk-offers')],
  'certificates': [('Certificates & records', '/certificates')], 'contact': [('Contact', '/contact')], 'editorial-policy': [('Editorial policy', '/editorial-policy')],
  'faq': [('FAQ', '/faq')], 'getting-started': [('Getting started', '/getting-started')], 'privacy': [('Privacy policy', '/privacy')], 'terms': [('Terms of service', '/terms')],
  'research-pack': [('Research pack', '/research-pack')], 'wholesale': [('Partners', '/wholesale'), ('Wholesale', '/wholesale')], 'learn': [('Learn', '/learn')], 'learn/all': [('Learn', '/learn'), ('All profiles', '/learn/all')],
}
def trail_for(path, h1):
    if path in TRAILS: return TRAILS[path]
    if path.startswith('guides/'): return [('Learn', '/learn'), (h1, '/' + path)]
    if path.startswith('learn/peptides/'): return [('Learn', '/learn'), ('Peptide guides', '/learn'), (h1, '/' + path)]
    if path.startswith('learn/compare/'): return [('Learn', '/learn'), ('Compare', '/learn'), (h1, '/' + path)]
    if path.startswith('learn/'): return [('Learn', '/learn'), (h1, '/' + path)]
    return [(h1, '/' + path)]

def build_content(path, variant='prose'):
    d = clean_main(path)
    h1 = d['h1'] or path.split('/')[-1].replace('-', ' ').title()
    body = page_head(d['eyebrow'], h1, d['intro'], d['related'], trail_for(path, h1))
    body += f'<section class="wrap page-body page-body--{variant}"><div class="prose">{d["html"]}</div></section>'
    write(path, wrap(d['title'] or f'{h1} | Maylene', d['description'], body))
    return h1

# ---------- FAQ ----------
def build_faq():
    s = open(os.path.join(SITE, 'faq', 'index.html')).read(); b = re.search(r'<main[^>]*>(.*?)</main>', s, re.S).group(1)
    items = re.findall(r'<button aria-expanded="false"[^>]*><span[^>]*>(.*?)</span>.*?<div id="[^"]+" hidden=""[^>]*>(.*?)</div></div>', b, re.S)
    d = clean_main('faq')
    CLS = re.compile(r' class="[^"]*"')
    def _cfe(m):
        enc = m.group(1); k = int(enc[:2], 16)
        e = ''.join(chr(int(enc[i:i+2], 16) ^ k) for i in range(2, len(enc), 2))
        return f'<a href="mailto:{e}">{e}</a>'
    items = [(q, re.sub(r'<a href="/cdn-cgi/l/email-protection"[^>]*data-cfemail="([0-9a-f]+)"[^>]*>.*?</a>', _cfe, ans)) for q, ans in items]
    faq = ''.join('<details class="faq"><summary>' + q.strip() + '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary><div class="faq__a">' + CLS.sub('', ans) + '</div></details>' for q, ans in items)
    body = page_head('Support', 'Frequently asked questions', ['Answers about products, ordering, shipping, quality and returns. Still stuck? Email contact@maylene.uk.'], [{'href': '/contact', 'text': 'Contact our team'}, {'href': '/getting-started', 'text': 'How ordering works'}, {'href': '/certificates', 'text': 'Batch documentation'}], TRAILS['faq'])
    body += f'''<section class="wrap page-body"><div class="faq-tools"><label class="plp__search faq-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input type="search" id="faq-q" placeholder="Search questions" aria-label="Search questions"></label><p class="plp__count" id="faq-count">{len(items)} questions</p></div><div class="faq-list" id="faq-list">{faq}</div><p class="plp__empty" id="faq-empty" hidden><strong>No matching questions.</strong></p></section>'''
    write('faq', wrap('Frequently asked questions | Maylene', d['description'], body))

# ---------- contact ----------
def build_contact():
    d = clean_main('contact')
    body = page_head('Support & enquiries', 'Contact us', ["Have questions about our products or need research support? We're here to help.", 'Include your order number if applicable, the compounds you are asking about, and any timeline requirements.'], d['related'], TRAILS['contact'])
    body += '''<section class="wrap page-body"><div class="contact">
  <div class="contact__info">
    <div class="info-card"><h2>Get in touch</h2><p>We support product questions, order updates, documentation requests and wholesale enquiries.</p>
      <dl class="info-list"><div><dt>Email</dt><dd><a href="mailto:contact@maylene.uk">contact@maylene.uk</a></dd></div><div><dt>WhatsApp</dt><dd><a href="https://wa.me/447353268148" target="_blank" rel="noopener noreferrer">Message us</a></dd></div><div><dt>Response time</dt><dd>Within 24 hours on business days</dd></div><div><dt>Business details</dt><dd>Maylene, United Kingdom</dd></div></dl></div>
    <div class="info-card info-card--soft"><h3>Before you submit</h3><ul><li>Add your order number if you are asking about an active shipment.</li><li>Use the subject field to route your request to the right team faster.</li><li>For wholesale requests, include expected unit volume and location.</li></ul><p><a class="more" href="/faq">Quick answers in the FAQ <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></p></div>
  </div>
  <form class="contact__form" id="contact-form" novalidate>
    <h2>Send us a message</h2><p class="contact__hint">Share as much relevant detail as possible so we can respond precisely on the first reply.</p>
    <div class="field"><label for="c-name">Name <span>*</span></label><input id="c-name" name="name" type="text" required minlength="2" maxlength="100" autocomplete="name" placeholder="Your name"></div>
    <div class="field"><label for="c-email">Email <span>*</span></label><input id="c-email" name="email" type="email" required maxlength="254" autocomplete="email" placeholder="your.email@example.com"></div>
    <div class="field"><label for="c-subject">Subject <span>*</span></label><select id="c-subject" name="subject" required><option value="">Select a subject</option><option value="product">Product inquiry</option><option value="order">Order status</option><option value="support">Technical support</option><option value="bulk">Bulk order request</option><option value="quality">Quality concern</option><option value="other">Other</option></select></div>
    <div class="field"><label for="c-message">Message <span>*</span></label><textarea id="c-message" name="message" rows="6" required minlength="10" maxlength="1000" placeholder="Please provide details about your inquiry…"></textarea><small><span id="c-counter">0</span>/1,000 · 10–1,000 characters</small></div>
    <p class="contact__status" id="contact-status" role="status" aria-live="polite"></p>
    <div class="contact__actions"><button class="btn btn--primary" type="submit">Send message <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button><small>* Required fields. Please do not include sensitive personal or health information.</small></div>
  </form>
</div></section>'''
    write('contact', wrap('Contact us | Maylene', d['description'], body))

# ---------- collections ----------
def build_collection(slug, category, h1, intro):
    s = PRODUCTS_PAGE
    s = re.sub(r'<title>.*?</title>', f'<title>{html.escape(h1)} | Maylene</title>', s, flags=re.S)
    s = s.replace('<span aria-current="page">All products</span>', f'<a href="/products">All products</a><span aria-hidden="true">/</span><span aria-current="page">{html.escape(h1)}</span>')
    s = s.replace('<h1 class="h1">Research peptides &amp; pens.</h1>', f'<h1 class="h1">{html.escape(h1)}</h1>')
    s = re.sub(r'<p class="plp-head__p">.*?</p>', f'<p class="plp-head__p">{html.escape(intro)}</p>', s, flags=re.S)
    s = s.replace('<div class="plp-grid" id="plp-grid">', f'<div class="plp-grid" id="plp-grid" data-default-category="{category}">')
    write('collections/' + slug, s)

# ---------- dosage calculator ----------
def build_calculator():
    s = open(os.path.join(SITE, 'dosage-calculator', 'index.html')).read()
    raw = html.unescape(s).replace('\\"', '"')
    objs = re.findall(r'\{"handle":"apex-[^"]+","label":"[^"]+","familyId":"[^"]+","familyLabel":"[^"]+","strengthMg":[\d.]+,"kind":"[a-z]+","conversion":(?:null|\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})(?:,"note":"[^"]*")?,"image":"[^"]+"\}', raw)
    products = []
    seen = set()
    for o in objs:
        try: p = json.loads(o)
        except Exception: continue
        if p['handle'] in seen: continue
        seen.add(p['handle']); products.append(p)
    d = clean_main('dosage-calculator')
    opts = ''.join(f'<option value="{p["handle"]}">{html.escape(p["label"])}</option>' for p in products)
    body = page_head('The Maylene toolkit', 'Dosage calculator.', ['Your product. Your strength. A clear conversion between milligrams and pen clicks, in either direction.'], [{'href': '/products', 'text': 'The collection'}, {'href': '/certificates', 'text': 'Lab reports'}], [('Dosage calculator', '/dosage-calculator')])
    body += f'''<section class="wrap page-body"><div class="calc" id="calc" data-products='{html.escape(json.dumps(products), quote=True)}'>
  <div class="calc__panel">
    <p class="label">01 · Choose your product</p>
    <label class="field"><span>Product</span><select id="calc-product">{opts}</select></label>
    <p class="calc__meta" id="calc-meta"></p>
    <p class="label" style="margin-top:22px">02 · Enter your value</p>
    <div class="calc__inputs"><label class="field"><span>Amount in milligrams</span><input id="calc-mg" type="number" inputmode="decimal" min="0" step="0.1" placeholder="0.0"><small>mg</small></label><label class="field"><span>Number of clicks</span><input id="calc-clicks" type="number" inputmode="numeric" min="0" step="1" placeholder="0"><small>clicks</small></label></div>
    <div class="calc__points" id="calc-points"></div>
    <button type="button" class="btn btn--outline" id="calc-clear">Clear values</button>
  </div>
  <div class="calc__result">
    <p class="label">03 · Your conversion</p>
    <div class="calc__out" id="calc-out"><strong>Ready when you are.</strong><p>Enter milligrams or clicks to see the matching amount here.</p></div>
    <p class="calc__note" id="calc-note">Based on the published values for matching pens. Check your pen’s instructions. This tool does not choose a dose.</p>
    <a class="more" id="calc-link" href="/products">View product <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
  </div>
</div>
<div class="prose prose--narrow" style="margin-top:48px"><h2>Know what the numbers mean.</h2><p>This is a conversion reference. It does not select an amount or recommend a protocol. Reference values are the published conversion points for matching pens and are not recommended amounts. Products are for laboratory research only.</p></div></section>'''
    write('dosage-calculator', wrap('Dosage calculator | Maylene', d['description'], body))
    return len(products)

# ---------- account & wishlist ----------
def build_account():
    body = page_head('Account', 'Your account', ['Sign in to view orders, saved details and documentation requests.'], [], [('Account', '/account')])
    body += '''<section class="wrap page-body"><div class="account">
  <div class="info-card account__card"><h2>Sign in</h2><p>Accounts are managed on the live store. You will be taken to the secure Maylene sign-in page.</p><div class="account__actions"><a class="btn btn--primary" href="https://www.maylene.uk/login">Sign in <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a><a class="btn btn--outline" href="https://www.maylene.uk/signup">Create an account</a></div></div>
  <div class="info-card info-card--soft"><h3>What you can do</h3><ul><li>Track orders and view dispatch details.</li><li>Save your wishlist across devices.</li><li>Request certificates and batch records.</li></ul><p><a class="more" href="/wishlist">View your wishlist <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></p></div>
</div></section>'''
    write('account', wrap('Your account | Maylene', 'Sign in to your Maylene account.', body))

def build_wishlist():
    body = page_head('Saved items', 'My wishlist', ['Products you saved with the heart icon. Saved items are kept in this browser.'], [{'href': '/products', 'text': 'Browse all products'}], [('Wishlist', '/wishlist')])
    body += '''<section class="wrap page-body"><p class="plp__count" id="wl-count"></p><div class="plp-grid" id="wl-grid"></div><div class="plp__empty" id="wl-empty" hidden><strong>Your wishlist is empty.</strong><p>Tap the heart on any product to save it here.</p><a class="btn btn--primary" href="/products">Browse products <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a></div><p class="sr-only" id="wishlist-status" role="status" aria-live="polite"></p></section>'''
    write('wishlist', wrap('My wishlist | Maylene', 'Your saved Maylene products.', body, extra_head='<link rel="stylesheet" href="/redesign/catalog.css?v=2">'))

if __name__ == '__main__':
    built = []
    generic = ['about','affiliate','bulk-offers','certificates','editorial-policy','getting-started','privacy','terms','research-pack','wholesale','learn','learn/all']
    for root, dirs, files in os.walk(os.path.join(SITE, 'learn')):
        if 'index.html' in files:
            rel = os.path.relpath(root, SITE)
            if rel not in generic: generic.append(rel)
    for root, dirs, files in os.walk(os.path.join(SITE, 'guides')):
        if 'index.html' in files: generic.append(os.path.relpath(root, SITE))
    for p in generic: built.append((p, build_content(p)))
    build_faq(); build_contact(); build_account(); build_wishlist()
    n = build_calculator()
    build_collection('research-pens', 'Research Pens', 'Research peptide pens.', 'Sixteen prefilled research pens with labelled content, pricing and documentation shown before you order.')
    build_collection('product-bundles', 'Product Bundles', 'Research peptide bundles.', 'Paired compounds in one considered bundle, with the same documentation and tracked UK dispatch.')
    print(f'{len(built)} content pages, calculator products: {n}')
    for p, h in built: print(f'  {p:40} {h}')
