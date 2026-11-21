"""Weekly academic scan: keyword queries and forward citations of core works, via OpenAlex.

Writes data/candidates/<ISO week>.json: raw hits with the queries that matched, deduplicated against
the Zotero index (exact and probable matches) and against data/seen.csv. No judgement happens here:
relevance scoring is done afterwards by the academia agent, following instructions/academia.md.
Usage: python3 scripts/openalex_scan.py [--monthly]   (monthly adds the methods and AI-coding groups)
"""
import datetime, sys, urllib.parse
from common import (DATA, config, env, get_json, iso_week, load_json, norm_doi, norm_name, norm_title,
                    read_csv, save_json, title_similarity)

OA = "https://api.openalex.org/works"
SELECT = ("id,doi,display_name,publication_year,publication_date,type,authorships,primary_location,"
          "open_access,best_oa_location,cited_by_count,abstract_inverted_index,referenced_works,language")

def q_or(terms):
    out = []
    for t in terms:
        t = str(t).strip()
        out.append(t if t.startswith('"') or " " not in t else f'"{t}"')
    return "(" + " OR ".join(out) + ")"

def abstract(inv):
    if not inv: return ""
    pos = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in pos)

def build_queries(cfg, monthly):
    k = cfg["keywords"]
    A, B, D = k["A_core_concepts"], k["B_domain"], k["D_governance"]
    C, H, I = k["C_instruments"]["terms"], k["H_methods"]["terms"], k["I_ai_coding"]["terms"]
    qs = []
    for i in range(0, len(A), 6):   # chunks keep the boolean expression short
        qs.append(("A×B", f"{q_or(A[i:i + 6])} AND {q_or(B)}"))
    for t in C:
        qs.append(("C", t if t.startswith('"') else f'"{t}"'))
    qs.append(("D", f'{q_or(D)} AND "circular economy" AND (urban OR area OR city)'))
    qs.append(("H×B", f"{q_or(H)} AND {q_or(B)} AND (urban OR area OR city OR regional)"))
    if monthly:
        for i in range(0, len(H), 7):
            qs.append(("H methods", q_or(H[i:i + 7])))
        for t in I:
            qs.append(("I AI coding", t))
    return qs

def oa(params, key, pages=2):
    out, cursor = [], "*"
    for _ in range(pages):
        p = dict(params, api_key=key, per_page=50, cursor=cursor, select=SELECT)
        data, _ = get_json(f"{OA}?{urllib.parse.urlencode(p)}")
        out += data.get("results", [])
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor: break
    return out

def main():
    key, cfg = env("OPENALEX_API_KEY"), config()
    monthly = "--monthly" in sys.argv
    since = (datetime.date.today() - datetime.timedelta(days=int(cfg.get("window_days", 60)))).isoformat()
    base = f"from_publication_date:{since},is_paratext:false,type:article|review|book-chapter|book|preprint|report"
    hits = {}

    def add(w, label):
        wid = w["id"].rsplit("/", 1)[-1]
        h = hits.get(wid)
        if not h:
            loc = (w.get("primary_location") or {})
            oa_loc = (w.get("best_oa_location") or {})
            h = hits[wid] = {
                "id": wid, "doi": norm_doi(w.get("doi")), "title": w.get("display_name") or "",
                "year": w.get("publication_year"), "date": w.get("publication_date"), "type": w.get("type"),
                "authors": [a["author"]["display_name"] for a in (w.get("authorships") or [])[:6]],
                "venue": (loc.get("source") or {}).get("display_name"),
                "is_oa": (w.get("open_access") or {}).get("is_oa", False),
                "oa_url": oa_loc.get("pdf_url") or oa_loc.get("landing_page_url"),
                "cited_by": w.get("cited_by_count", 0), "language": w.get("language"),
                "abstract": abstract(w.get("abstract_inverted_index"))[:2000],
                "refs": [r.rsplit("/", 1)[-1] for r in w.get("referenced_works", [])],
                "matched": [], "cites_core": []}
        if label not in h["matched"]: h["matched"].append(label)

    n_q = 0
    for label, q in build_queries(cfg, monthly):
        for w in oa({"filter": f"{base},title_and_abstract.search:{q}"}, key):
            add(w, label)
        n_q += 1

    graph = load_json(f"{DATA}/library-graph.json", {}) or {}
    core = {c["id"]: c for c in graph.get("core", [])}
    if core:
        ids = list(core)
        for i in range(0, len(ids), 25):
            for w in oa({"filter": f"{base},cites:" + "|".join(ids[i:i + 25])}, key, pages=3):
                add(w, "G forward citation")
            n_q += 1
    for h in hits.values():
        h["cites_core"] = [core[r]["title"] for r in h["refs"] if r in core]
        h.pop("refs", None)

    # de-duplicate against the Zotero library and earlier radar weeks
    idx = (load_json(f"{DATA}/zotero-index.json", {}) or {}).get("items", {})
    by_doi = {v["doi"]: (k, v) for k, v in idx.items() if v["doi"]}
    seen = {r["id"]: r for r in read_csv(f"{DATA}/seen.csv")}
    for h in hits.values():
        h["library"], h["library_match"] = "new", None
        if h["doi"] and h["doi"] in by_doi:
            h["library"], h["library_match"] = "in_library", by_doi[h["doi"]][1]["title"]
        else:
            t, fa = norm_title(h["title"]), norm_name(h["authors"][0] if h["authors"] else "")
            for k, v in idx.items():
                if not v["t"]: continue
                yr_ok = not (v["year"] and h["year"]) or abs(v["year"] - h["year"]) <= 1
                if t == v["t"] and yr_ok and (not fa or not v["first_author"] or fa == v["first_author"]):
                    h["library"], h["library_match"] = "in_library", v["title"]; break
                if yr_ok and fa and fa == v["first_author"] and title_similarity(h["title"], v["title"]) >= 0.6:
                    h["library"], h["library_match"] = "probable", v["title"]
        key_ = h["doi"] or h["id"]
        h["seen"] = seen.get(key_, {}).get("status") if key_ in seen else None

    week = iso_week()
    out = sorted(hits.values(), key=lambda h: (h["library"] != "new", -len(h["matched"]), -(h["cited_by"] or 0)))
    save_json(f"{DATA}/candidates/{week}.json", {"week": week, "since": since, "monthly": monthly,
                                                   "queries": n_q, "count": len(out), "items": out})
    new = [h for h in out if h["library"] == "new" and not h["seen"]]
    print(f"{week}: {n_q} queries, {len(out)} hits since {since}; {len(new)} new and unseen, "
          f"{sum(h['library'] == 'in_library' for h in out)} already in Zotero, "
          f"{sum(h['library'] == 'probable' for h in out)} probable matches, {sum(bool(h['seen']) for h in out)} seen before.")

if __name__ == "__main__":
    main()
