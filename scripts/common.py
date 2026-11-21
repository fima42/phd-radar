"""Shared helpers for the PhD radar scripts. Standard library plus PyYAML only.

Keys come from the environment (ZOTERO_USER_ID, ZOTERO_API_KEY, OPENALEX_API_KEY) and are never written to disk or printed.
"""
import csv, datetime, json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = "phd-radar/1.0 (TU Delft PhD research; mailto via OpenAlex key)"

def env(name, required=True):
    v = os.environ.get(name, "").strip()
    if required and not v:
        sys.exit(f"Missing environment variable {name}. Add it to the phd-radar cloud environment.")
    return v

def config():
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML missing: run `pip install pyyaml` (add --break-system-packages if needed).")
    with open(os.path.join(ROOT, "config", "radar.yml")) as f:
        return yaml.safe_load(f)

def get_json(url, headers=None, tries=4):
    """GET a JSON URL with simple backoff. Returns (data, response headers)."""
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
                return json.loads(r.read().decode("utf-8")), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(int(e.headers.get("Retry-After") or 2 ** (i + 1)))
                continue
            # never echo the URL: it can contain the API key
            raise SystemExit(f"HTTP {e.code} from {urllib.parse.urlsplit(url).netloc}{urllib.parse.urlsplit(url).path}")
        except urllib.error.URLError as e:
            if i < tries - 1:
                time.sleep(2 ** (i + 1)); continue
            raise SystemExit(f"Network error reaching {urllib.parse.urlsplit(url).netloc}: {e.reason}. "
                             "Check the phd-radar environment's allowed domains.")

STOP = set("a an the of and or in on for to with from by at as is are be its their this that into towards toward via".split())

def norm_doi(d):
    if not d: return ""
    d = str(d).strip().lower()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.strip().rstrip(".")

def norm_title(t):
    if not t: return ""
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"<[^>]+>", " ", t)          # html tags in some titles
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return " ".join(w for w in t.split() if w not in STOP)

def norm_name(n):
    n = unicodedata.normalize("NFKD", str(n or "")).encode("ascii", "ignore").decode().lower()
    n = re.sub(r"[^a-z ]+", " ", n).split()
    return n[-1] if n else ""

def title_similarity(a, b):
    """Jaccard similarity of normalised title words (0 to 1)."""
    A, B = set(norm_title(a).split()), set(norm_title(b).split())
    return len(A & B) / len(A | B) if A and B else 0.0

def iso_week(d=None):
    d = d or datetime.date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"

def read_csv(path):
    if not os.path.exists(path): return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError): return default
