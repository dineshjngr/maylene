import subprocess, sys, concurrent.futures, re
C = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
pages = [l.strip() for l in open(sys.argv[1]) if l.strip()]
BAD = re.compile(r"Failed to Load|Something went wrong|Minified React error|unavailable\. Please try again")
def visit(p):
    r = subprocess.run([C, "--headless=new", "--disable-gpu", "--virtual-time-budget=10000", "--enable-logging=stderr", "--v=0", "--dump-dom", "http://127.0.0.1:8765" + p],
                       capture_output=True, text=True, timeout=120)
    dom_bad = sorted(set(BAD.findall(r.stdout)))
    console = sorted(set(re.findall(r'CONSOLE:\d+\] "([^"]{0,120})', r.stderr)))
    console = [c for c in console if not re.search(r"clarity|gtm|fbevents|Third-party cookie|beacon", c)]
    return p, dom_bad, console
with concurrent.futures.ThreadPoolExecutor(4) as ex:
    for p, dom_bad, console in ex.map(visit, pages):
        print(("BAD " if dom_bad or console else "ok  ") + p, dom_bad, console[:3], flush=True)
