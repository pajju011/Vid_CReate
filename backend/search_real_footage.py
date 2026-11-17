import json
import urllib.parse
import urllib.request

queries = [
    "energy drink",
    "drink splash can",
    "ice water splash",
    "extreme sports stunt",
    "motocross jump",
    "skateboarding trick",
    "wingsuit flying"
]

pixabay_key = "48873723-d6c57f2025ad872f22b7a0d4c"

for q in queries:
    encoded = urllib.parse.quote(q)
    url = f"https://pixabay.com/api/videos/?key={pixabay_key}&q={encoded}&per_page=5"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            hits = data.get("hits", [])
            print(f"Query: '{q}' -> Found {len(hits)} videos")
            for h in hits[:2]:
                vids = h.get("videos", {})
                med = vids.get("large", {}).get("url") or vids.get("medium", {}).get("url")
                dur = h.get("duration")
                tags = h.get("tags")
                print(f"  - [{dur}s] Tags: {tags}")
                print(f"    URL: {med}")
    except Exception as e:
        print(f"  Error for '{q}': {e}")
