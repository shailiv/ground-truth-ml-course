"""Print the live address from the record Wrangler wrote during the deploy (falls back to the last known one)."""
import json, pathlib

url = ""
f = pathlib.Path("../.secrets/deploy.ndjson")
for line in (f.read_text(encoding="utf-8").splitlines() if f.exists() else []):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    for t in d.get("targets") or []:
        if isinstance(t, str) and "workers.dev" in t:
            url = t.split()[0].rstrip("/")
old = pathlib.Path("../.secrets/url.txt")
url = url or (old.read_text(encoding="utf-8").strip() if old.exists() else "")
if url and not url.startswith("http"):
    url = "https://" + url
print(url)
