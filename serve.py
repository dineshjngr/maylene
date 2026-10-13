#!/usr/bin/env python3
"""Local preview server for the mirrored maylene.uk site.
Run:  python3 serve.py   ->  http://127.0.0.1:8765/
Serves ./site, maps clean URLs (/about -> about/index.html) and resolves
Next.js /_next/image?url=...&w=... requests to the downloaded image files.
/api/* calls (the live catalogue API) are proxied to www.maylene.uk, and /store/*
calls (the Medusa store API, normally api.maylene.uk) are proxied there; GET
responses are cached in site/_api-cache so the preview keeps working offline."""
import os, re, json, mimetypes, urllib.parse, urllib.request, hashlib
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
REDESIGN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "redesign")  # new pages live here, served at /redesign/
PORT = 8765
mimetypes.add_type("image/webp", ".webp"); mimetypes.add_type("font/woff2", ".woff2")

# index the mirror map by (source url, width) for /_next/image lookups
IMG = {}
try:
    for full, local in json.load(open(os.path.join(ROOT, "_mirror-map.json"))).items():
        u = urllib.parse.urlparse(full)
        if u.path == "/_next/image":
            q = urllib.parse.parse_qs(u.query)
            IMG[(q.get("url", [""])[0], q.get("w", [""])[0])] = local
except FileNotFoundError:
    pass

LIVE = "https://www.maylene.uk"
STORE = "https://api.maylene.uk"
# The store API needs the site's publishable key; pick it up from the mirrored JS so the browser never has to send it.
PUB_KEY = ""
try:
    import glob, re
    for _f in glob.glob(os.path.join(ROOT, "_next/static/chunks/*.js")):
        _m = re.search(r"pk_[a-f0-9]{40,}", open(_f, errors="ignore").read())
        if _m: PUB_KEY = _m.group(0); break
except Exception:
    pass
CACHE = os.path.join(ROOT, "_api-cache"); os.makedirs(CACHE, exist_ok=True)

class Server(ThreadingHTTPServer):
    request_queue_size = 256   # default 5 drops parallel image requests under browser load
    daemon_threads = True
    allow_reuse_address = True

class H(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def end_headers(self):
        # Preview only: never let the browser cache, so edits show on a plain reload.
        if not any(h[0].lower() == "cache-control" for h in getattr(self, "_headers_buffer_names", [])):
            self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def do_GET(self):
        if urllib.parse.urlparse(self.path).path in ("/cart", "/checkout"):
            return self.proxy(LIVE)
        if self.path.startswith("/api/") or self.path.startswith("/cdn-cgi/"):
            return self.proxy(LIVE)
        if self.path.startswith("/store/"):
            return self.proxy(STORE)
        return super().do_GET()
    def do_POST(self):
        if self.path.startswith("/store/") or self.path.startswith("/api/"):
            return self.proxy(STORE if self.path.startswith("/store/") else LIVE, method="POST")
        self.send_error(405)
    def do_DELETE(self):
        if self.path.startswith("/store/"):
            return self.proxy(STORE, method="DELETE")
        self.send_error(405)
    def do_OPTIONS(self):
        self.send_response(204); self.end_headers()
    def proxy(self, upstream, method="GET"):
        _path = urllib.parse.urlparse(self.path).path
        cart_request = _path == "/api/cart" or _path.startswith("/store/carts")  # basket is bound to session cookies
        cart_cookies = []
        cacheable = method == "GET" and urllib.parse.urlparse(self.path).path not in ("/cart", "/checkout") and not self.path.startswith("/store/carts")
        key = hashlib.sha1((upstream + self.path).encode()).hexdigest()
        meta, body = os.path.join(CACHE, key + ".json"), os.path.join(CACHE, key + ".bin")
        if cacheable and os.path.exists(meta):
            m = json.load(open(meta)); data = open(body, "rb").read()
        else:
            hdrs = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
            for h in ("x-publishable-api-key", "content-type", "authorization"):
                if self.headers.get(h): hdrs[h] = self.headers[h]
            if upstream == STORE and PUB_KEY and "x-publishable-api-key" not in hdrs:
                hdrs["x-publishable-api-key"] = PUB_KEY
            if cart_request:
                # The guest-cart API authenticates later requests with these cookies.
                cookies = SimpleCookie(self.headers.get("Cookie", ""))
                allowed = ("_maylene_cart_access", "_medusa_cart_id")
                cookie_header = "; ".join(f"{name}={cookies[name].coded_value}" for name in allowed if name in cookies)
                if cookie_header: hdrs["Cookie"] = cookie_header
                hdrs["Origin"] = LIVE
            n = int(self.headers.get("content-length") or 0)
            req = urllib.request.Request(upstream + self.path, data=self.rfile.read(n) if n else None, headers=hdrs, method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data, m = r.read(), {"status": r.status, "ctype": r.headers.get("Content-Type", "application/json")}
                    if cart_request: cart_cookies = r.headers.get_all("Set-Cookie", [])
            except urllib.error.HTTPError as e:
                data, m = e.read(), {"status": e.code, "ctype": e.headers.get("Content-Type", "application/json")}
                if cart_request: cart_cookies = e.headers.get_all("Set-Cookie", [])
            except Exception as e:
                self.send_error(502, f"upstream unavailable: {e}"); return
            if cacheable and m["status"] == 200:
                json.dump(m, open(meta, "w")); open(body, "wb").write(data)
        self.send_response(m["status"]); self.send_header("Content-Type", m["ctype"])
        for cookie_header in cart_cookies:
            cookies = SimpleCookie(cookie_header)
            for name, cookie in cookies.items():
                if name not in ("_maylene_cart_access", "_medusa_cart_id"): continue
                # Adapt production cookies to this HTTP-only loopback preview.
                cookie["domain"] = ""
                cookie["secure"] = ""
                self.send_header("Set-Cookie", cookie.OutputString())
        self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-store"); self.end_headers()
        self.wfile.write(data)
    def translate_path(self, path):
        u = urllib.parse.urlparse(path)
        p = urllib.parse.unquote(u.path)
        if p in ("/", "/index.html"):
            return os.path.join(REDESIGN, "index.html")
        if p in ("/products", "/products/", "/products/index.html"):
            return os.path.join(REDESIGN, "products", "index.html")
        if p == "/_next/image":
            q = urllib.parse.parse_qs(u.query)
            src, w = q.get("url", [""])[0], q.get("w", [""])[0]
            local = IMG.get((src, w))
            if not local:  # nearest width, else the original source file
                cands = sorted((int(k[1]), v) for k, v in IMG.items() if k[0] == src and k[1].isdigit())
                bigger = [v for ww, v in cands if ww >= int(w or 0)]
                local = bigger[0] if bigger else (cands[-1][1] if cands else src.lstrip("/"))
            return os.path.join(ROOT, local)
        # Redesigned product pages replace the mirrored ones; the originals stay at /original/products/<handle>.
        m = re.match(r"^/products/([a-z0-9-]+)/?(?:index\.html)?$", p)
        if m and os.path.isfile(os.path.join(REDESIGN, "products", m.group(1), "index.html")):
            return os.path.join(REDESIGN, "products", m.group(1), "index.html")
        if p.startswith("/original/"):
            p = p[len("/original"):]
        if p == "/redesign" or p.startswith("/redesign/"):
            fs = os.path.join(REDESIGN, p[len("/redesign"):].lstrip("/"))
            return os.path.join(fs, "index.html") if os.path.isdir(fs) else fs
        fs = os.path.join(ROOT, p.lstrip("/"))
        if os.path.isdir(fs) and os.path.isfile(os.path.join(fs, "index.html")):
            return os.path.join(fs, "index.html")
        if not os.path.exists(fs) and os.path.isfile(fs + ".html"):
            return fs + ".html"
        return fs
    def log_message(self, fmt, *args):
        if os.environ.get("VERBOSE") or (args and str(args[1]) not in ("200", "304")): super().log_message(fmt, *args)

if __name__ == "__main__":
    print(f"Serving {ROOT} at http://127.0.0.1:{PORT}/")
    Server(("127.0.0.1", PORT), H).serve_forever()
