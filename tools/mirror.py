import re, os, sys, hashlib, urllib.request, urllib.parse, concurrent.futures, html, json
from urllib.parse import urljoin, urlparse, urlunparse

BASE = "https://www.maylene.uk"
HOSTS = {"www.maylene.uk", "maylene.uk"}
OUT = sys.argv[1]
SEEDS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read(), r.headers.get("Content-Type", "")

def norm(url):
    u = urlparse(url)
    if u.netloc == "maylene.uk":
        u = u._replace(netloc="www.maylene.uk")
    return urlunparse(u._replace(fragment=""))

def is_internal(url):
    u = urlparse(url)
    return u.scheme in ("http", "https") and u.netloc in HOSTS

def local_path(url, ctype=""):
    """Map a URL to a local file path (relative to OUT)."""
    u = urlparse(url)
    path = urllib.parse.unquote(u.path)
    if path in ("", "/"):
        path = "/index.html"
    is_page = not re.search(r"\.[a-zA-Z0-9]{1,5}$", path) or path.endswith(".html")
    if path.startswith("/_next/image"):
        q = urllib.parse.parse_qs(u.query)
        src = q.get("url", [""])[0]
        w = q.get("w", ["0"])[0]
        name = os.path.basename(urlparse(src).path) or "img"
        h = hashlib.md5(url.encode()).hexdigest()[:8]
        stem, ext = os.path.splitext(name)
        ext = ext if ext else ".webp"
        return f"_images/{stem}-w{w}-{h}{ext}"
    if is_page:
        if path.endswith(".html"):
            return path.lstrip("/")
        return path.strip("/") + "/index.html"
    if u.query and not path.startswith("/_next/static/"):
        # keep query-variant assets distinct
        h = hashlib.md5(u.query.encode()).hexdigest()[:8]
        stem, ext = os.path.splitext(path)
        return f"{stem}-{h}{ext}".lstrip("/")
    return path.lstrip("/")

PAGES_ONLY = "--pages-only" in sys.argv
seen = set(); queue = list(dict.fromkeys(norm(s) for s in SEEDS)); results = {}
HTML_ATTR = re.compile(r'''(?:href|src|srcset|content|poster|data-src)\s*=\s*["']([^"']+)["']''', re.I)
CSS_URL = re.compile(r'''url\(\s*["']?([^"')]+)["']?\s*\)''')

def discover(url, body, ctype):
    found = set()
    if "text/html" in ctype:
        text = body.decode("utf-8", "ignore")
        for m in HTML_ATTR.finditer(text):
            val = html.unescape(m.group(1))
            if m.group(0).lower().startswith("content") and not val.startswith(("/", "http")):
                continue
            if "srcset" in m.group(0).lower()[:7]:
                for part in val.split(","):
                    cand = part.strip().split(" ")[0]
                    if cand: found.add(cand)
            else:
                found.add(val)
        # Next.js data / preload hints inside scripts
        for m in re.finditer(r'["\'](/_next/[^"\'\\\s]+)["\']', text):
            found.add(m.group(1))
        for m in re.finditer(r'["\'](/(?:images|img|assets|fonts|videos|media)/[^"\'\\\s]+)["\']', text):
            found.add(m.group(1))
    elif "text/css" in ctype or url.endswith(".css"):
        text = body.decode("utf-8", "ignore")
        for m in CSS_URL.finditer(text):
            found.add(m.group(1))
    elif "javascript" in ctype or url.endswith(".js"):
        text = body.decode("utf-8", "ignore")
        for m in re.finditer(r'["\'](/_next/static/[^"\'\\\s]+)["\']', text):
            found.add(m.group(1))
        for m in re.finditer(r'["\'](/(?:images|img|assets|fonts|videos|media)/[^"\'\\\s]+\.(?:png|jpe?g|webp|svg|gif|mp4|webm|woff2?|ttf|avif))["\']', text):
            found.add(m.group(1))
    out = set()
    for f in found:
        f = html.unescape(f).replace("\\u0026", "&")
        if " " in f: continue
        if f.startswith(("data:", "mailto:", "tel:", "javascript:", "#", "blob:")): continue
        if f.startswith("//"): f = "https:" + f
        full = norm(urljoin(url, f))
        if is_internal(full) and not full.startswith(BASE + "/cdn-cgi/") and "/api/" not in full:
            out.add(full)
    return out

def work(url):
    try:
        body, ctype = fetch(url)
        return url, body, ctype, None
    except Exception as e:
        return url, None, "", str(e)

with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    if PAGES_ONLY:
        old = json.load(open(os.path.join(OUT, "_mirror-map.json")))
        pages = [u for u, lp in old.items() if lp.endswith(".html")]
        for url, body, ctype, err in ex.map(work, pages):
            if err: print("FAIL", url, err)
            else: results[url] = (body, ctype)
        print(f"re-fetched {len(results)} pages", flush=True)
        queue = []
    while queue:
        batch = [u for u in queue if u not in seen]
        for u in batch: seen.add(u)
        queue = []
        for url, body, ctype, err in ex.map(work, batch):
            if err:
                print("FAIL", url, err); continue
            results[url] = (body, ctype)
            for n in discover(url, body, ctype):
                if n not in seen: queue.append(n)
        print(f"fetched {len(results)}, queued {len(set(queue))}", flush=True)

# Build URL -> local path map, then rewrite and write
pathmap = {u: local_path(u, c) for u, (b, c) in results.items()}
if PAGES_ONLY:
    pathmap = {**old, **pathmap}

SCRIPT_RE = re.compile(r'<script\b[^>]*>.*?</script>', re.S)

def rewrite_text(text, url):
    """Rewrite URLs, but leave <script> blocks holding the Next.js flight payload
    (self.__next_f.push) untouched: its rows are byte-length prefixed."""
    parts, last = [], 0
    for m in SCRIPT_RE.finditer(text):
        parts.append(_rewrite(text[last:m.start()], url))
        parts.append(m.group(0) if "__next_f" in m.group(0) else _rewrite(m.group(0), url))
        last = m.end()
    parts.append(_rewrite(text[last:], url))
    return "".join(parts)

def _rewrite(text, url):
    def repl_url(raw):
        val = html.unescape(raw)
        if val.startswith(("data:", "mailto:", "tel:", "javascript:", "#", "blob:")): return raw
        full = norm(urljoin(url, val if not val.startswith("//") else "https:" + val))
        if full in pathmap:
            return "/" + pathmap[full]
        return raw
    def attr_sub(m):
        whole = m.group(0); val = m.group(1)
        if whole.lower().startswith("srcset"):
            parts = []
            for part in val.split(","):
                bits = part.strip().split(" ", 1)
                bits[0] = repl_url(bits[0])
                parts.append(" ".join(bits))
            new = ", ".join(parts)
        else:
            new = repl_url(val)
        return whole.replace(val, new) if new != val else whole
    text = HTML_ATTR.sub(attr_sub, text)
    text = CSS_URL.sub(lambda m: m.group(0).replace(m.group(1), repl_url(m.group(1))), text)
    # bare absolute-site and /_next/image references in scripts/JSON
    text = text.replace(BASE, "")
    def nextimg(m):
        full = norm(urljoin(url, html.unescape(m.group(1).replace("\\u0026", "&").replace("\\/", "/"))))
        return '"/' + pathmap[full] + '"' if full in pathmap else m.group(0)
    text = re.sub(r'"(/_next/image\?[^"]+)"', nextimg, text)
    return text

for url, (body, ctype) in results.items():
    p = os.path.join(OUT, pathmap[url])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if "text/html" in ctype or "text/css" in ctype or "javascript" in ctype:
        text = body.decode("utf-8", "ignore")
        text = rewrite_text(text, url)
        with open(p, "w", encoding="utf-8") as f: f.write(text)
    else:
        with open(p, "wb") as f: f.write(body)
json.dump(pathmap, open(os.path.join(OUT, "_mirror-map.json"), "w"), indent=1)
print("DONE pages:", sum(1 for u,(b,c) in results.items() if "text/html" in c), "assets:", len(results))
