"""Self-host the three typefaces (latin subsets, variable woff2) so the site makes no third-party requests."""
import pathlib
import re
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
FAMS = {
    "Bricolage Grotesque": "family=Bricolage+Grotesque:opsz,wght@12..96,400..800",
    "Inter": "family=Inter:wght@400..700",
    "JetBrains Mono": "family=JetBrains+Mono:wght@400..600",
}
out = pathlib.Path("site/public/fonts")
out.mkdir(parents=True, exist_ok=True)
css_out = []
for fam, q in FAMS.items():
    req = urllib.request.Request(f"https://fonts.googleapis.com/css2?{q}&display=swap", headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
    blocks = re.findall(r"/\* ([\w-]+) \*/\s*(@font-face\s*{[^}]+})", css)
    keep = [b for name, b in blocks if name in ("latin", "latin-ext")]
    for name, b in [(n, b) for n, b in blocks if n in ("latin", "latin-ext")]:
        url = re.search(r"url\((https://[^)]+\.woff2)\)", b).group(1)
        fn = f"{fam.lower().replace(' ', '-')}-{name}.woff2"
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
        (out / fn).write_bytes(data)
        css_out.append(b.replace(url, f"../fonts/{fn}"))
        print(f"{fn}: {len(data):,} bytes")
pathlib.Path("site/public/css").mkdir(parents=True, exist_ok=True)
pathlib.Path("site/public/css/fonts.css").write_text("\n".join(css_out) + "\n", encoding="utf-8")
print("wrote site/public/css/fonts.css")
