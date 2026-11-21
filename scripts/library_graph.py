"""Citation picture of the Zotero library via OpenAlex.

Writes data/library-graph.json with
- core: works inside the library cited most often by other library items (forward-tracked weekly);
- gaps: works cited by >= MIN_GAP library items but not in the library (reviewed monthly).
Needs data/zotero-index.json (run zotero_index.py first). DOI lookups are cached in data/openalex-doi-cache.json.
Usage: python3 scripts/library_graph.py [--core N] [--gaps N]
"""
import collections, sys, urllib.parse
from common import DATA, env, get_json, load_json, norm_doi, save_json

OA = "https://api.openalex.org/works"
MIN_GAP = 3

def arg(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default

def oa(params, key):
    params = dict(params, api_key=key)
    data, _ = get_json(f"{OA}?{urllib.parse.urlencode(params)}")
    return data

def main():
    key = env("OPENALEX_API_KEY")
    n_core, n_gaps = arg("--core", 30), arg("--gaps", 30)
    idx = load_json(f"{DATA}/zotero-index.json") or sys.exit("Run zotero_index.py first.")
    cache = load_json(f"{DATA}/openalex-doi-cache.json", {}) or {}
    dois = sorted({v["doi"] for v in idx["items"].values() if v["doi"]})
    todo = [d for d in dois if d not in cache]
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        res = oa({"filter": "doi:" + "|".join(chunk), "per_page": 50,
                  "select": "id,doi,display_name,publication_year,referenced_works,cited_by_count"}, key)
        found = {norm_doi(w.get("doi")): w for w in res.get("results", [])}
        for d in chunk:
            w = found.get(d)
            cache[d] = {"id": w["id"].rsplit("/", 1)[-1], "title": w.get("display_name"), "year": w.get("publication_year"),
                        "refs": [r.rsplit("/", 1)[-1] for r in w.get("referenced_works", [])],
                        "cited_by": w.get("cited_by_count", 0)} if w else None
    save_json(f"{DATA}/openalex-doi-cache.json", cache)

    lib = {v["id"]: v for v in cache.values() if v}
    counts = collections.Counter(r for v in lib.values() for r in set(v["refs"]))
    core = [{"id": w, "title": lib[w]["title"], "year": lib[w]["year"], "cited_in_library": n, "cited_by": lib[w].get("cited_by", 0)}
            for w, n in counts.most_common() if w in lib][:n_core]
    gap_ids = [(w, n) for w, n in counts.most_common() if w not in lib and n >= MIN_GAP][:n_gaps]
    gaps = []
    for i in range(0, len(gap_ids), 50):
        part = dict(gap_ids[i:i + 50])
        res = oa({"filter": "openalex:" + "|".join(part), "per_page": 50,
                  "select": "id,doi,display_name,publication_year,cited_by_count,authorships,primary_location"}, key)
        for w in res.get("results", []):
            wid = w["id"].rsplit("/", 1)[-1]
            au = [a["author"]["display_name"] for a in (w.get("authorships") or [])[:3]]
            src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
            gaps.append({"id": wid, "doi": norm_doi(w.get("doi")), "title": w.get("display_name"), "year": w.get("publication_year"),
                         "authors": au, "venue": src, "cited_in_library": part.get(wid, 0), "cited_by": w.get("cited_by_count", 0)})
    gaps.sort(key=lambda g: -g["cited_in_library"])
    save_json(f"{DATA}/library-graph.json", {"resolved": len(lib), "library_dois": len(dois),
                                             "core": core, "gaps": gaps})
    print(f"Resolved {len(lib)}/{len(dois)} library DOIs in OpenAlex; {len(core)} core works; {len(gaps)} citation gaps (>= {MIN_GAP} library citations).")

if __name__ == "__main__":
    main()
