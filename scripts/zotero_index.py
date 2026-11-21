"""Build data/zotero-index.json from the Zotero web API (read-only key).

Only identifiers are stored: item key, DOI, title, year, first author surname, item type.
Incremental: keeps the library version and only fetches items changed since the last run.
Usage: python3 scripts/zotero_index.py [--full]
"""
import re, sys, urllib.parse
from common import DATA, env, get_json, load_json, norm_doi, norm_name, norm_title, save_json

OUT = f"{DATA}/zotero-index.json"

def main():
    uid, key = env("ZOTERO_USER_ID"), env("ZOTERO_API_KEY")
    full = "--full" in sys.argv
    idx = {} if full else (load_json(OUT, {}) or {})
    items = idx.get("items", {})
    since = 0 if full else int(idx.get("version", 0))
    H = {"Zotero-API-Key": key, "Zotero-API-Version": "3"}
    base = f"https://api.zotero.org/users/{urllib.parse.quote(uid)}"

    # removed items since last version
    if since:
        deleted, _ = get_json(f"{base}/deleted?since={since}", H)
        for k in deleted.get("items", []): items.pop(k, None)

    start, version, fetched = 0, since, 0
    while True:
        q = urllib.parse.urlencode({"format": "json", "limit": 100, "start": start, "since": since})
        page, hdr = get_json(f"{base}/items/top?{q}", H)
        version = max(version, int(hdr.get("Last-Modified-Version", 0) or 0))
        for it in page:
            d = it.get("data", {})
            if d.get("deleted") or d.get("itemType") in ("attachment", "note", "annotation"):
                items.pop(d.get("key"), None); continue
            doi = d.get("DOI") or ""
            if not doi:   # books, chapters, reports often keep the DOI in Extra
                m = re.search(r"(?im)^\s*DOI:\s*(\S+)", d.get("extra", "") or "")
                doi = m.group(1) if m else ""
            cr = d.get("creators") or []
            first = next((c for c in cr if c.get("creatorType") in ("author", "editor")), cr[0] if cr else {})
            yr = re.search(r"\b(1[89]\d\d|20\d\d)\b", d.get("date", "") or "")
            items[d["key"]] = {"doi": norm_doi(doi), "title": d.get("title", ""), "t": norm_title(d.get("title", "")),
                               "year": int(yr.group(1)) if yr else None,
                               "first_author": norm_name(first.get("lastName") or first.get("name") or ""),
                               "type": d.get("itemType", ""), "collections": d.get("collections", [])}
        fetched += len(page)
        total = int(hdr.get("Total-Results", 0) or 0)
        start += 100
        if not page or start >= total: break

    save_json(OUT, {"version": version, "count": len(items), "items": items})
    print(f"Zotero index: {len(items)} items ({fetched} fetched since version {since}), "
          f"{sum(1 for v in items.values() if v['doi'])} with DOI.")

if __name__ == "__main__":
    main()
