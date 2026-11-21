"""Compose a radar week from the stream files, update seen.csv and the cumulative database.

Each stream (academia, policy, society) writes its judged items to radar/items/<week>/<stream>.json
(a JSON list) and optionally radar/items/<week>/<stream>.counts.json. This script is deterministic (no judgement):
- merges the stream files of the week, removes duplicates across streams, applies the per-stream caps;
- writes radar/items/<week>.json, radar/items.json (latest) and the weekly note radar/<week>.md;
- appends new rows to data/seen.csv;
- appends every item (also screened out) to the database data/archive/items.jsonl and recomputes data/archive/stats.json.
It can run after each stream: a later run of the same week simply recomposes with the streams present by then.
Usage: python3 scripts/compose.py [<ISO week>]
"""
import collections, datetime, glob, hashlib, json, os, re, sys
from common import DATA, ROOT, config, iso_week, load_json, norm_doi, norm_title, read_csv, save_json, write_csv

RADAR = os.path.join(ROOT, "radar")
ARCH = os.path.join(DATA, "archive")
STREAMS = ["academia", "policy", "society"]
CAPS = {"academia": "max_items_weekly", "policy": "max_items_policy", "society": "max_items_society"}
REPORTED = {"new", "forward", "methods", "corpus_candidate", "news", "event", "gap", "context"}

def key_of(it):
    return norm_doi(it.get("doi")) or (it.get("url") or "").strip().lower().rstrip("/") or it.get("id") or norm_title(it.get("title"))

def load_week(week):
    items, counts = [], {}
    for st in STREAMS:
        f = os.path.join(RADAR, "items", week, f"{st}.json")
        data = load_json(f)
        if data is None: continue
        arr = data if isinstance(data, list) else data.get("items", [])
        for it in arr:
            it.setdefault("stream", st); it["week"] = week; items.append(it)
        counts[st] = load_json(os.path.join(RADAR, "items", week, f"{st}.counts.json"), {}) or (data.get("counts", {}) if isinstance(data, dict) else {})
    return items, counts

def merge(items, cfg):
    # duplicates across streams: keep the highest score, remember all streams
    best = {}
    for it in items:
        k = key_of(it)
        t = norm_title(it.get("title"))
        hit = best.get(k) or next((v for v in best.values() if t and norm_title(v.get("title")) == t), None)
        if hit is None: best[k] = it; continue
        hit.setdefault("streams", [hit["stream"]])
        if it["stream"] not in hit["streams"]: hit["streams"].append(it["stream"])
        if (it.get("score") or 0) > (hit.get("score") or 0) and it.get("section") != "screened_out":
            it["streams"] = hit["streams"]; best[key_of(hit)] = it
    out = list(best.values())
    # per-stream caps (corpus candidates and gaps are never capped)
    for st, ck in CAPS.items():
        cap = int(cfg.get(ck, 25) or 25)
        rep = sorted([i for i in out if i["stream"] == st and i.get("section") in ("new", "forward", "news")],
                     key=lambda i: -(i.get("score") or 0))
        for i in rep[cap:]:
            i["section"], i["reason"] = "screened_out", "over weekly cap"
    return out

def note(week, items, counts, cfg):
    proxy = cfg.get("library_proxy", "")
    sec = lambda st, s: sorted([i for i in items if i["stream"] == st and i.get("section") == s], key=lambda i: -(i.get("score") or 0))
    L = [f"---\ntype: radar\nweek: {week}\ngenerated: {datetime.date.today().isoformat()}\nstreams: [{', '.join(sorted({i['stream'] for i in items}))}]",
         f"counts: {{reported: {sum(i.get('section') in REPORTED for i in items)}, screened_out: {sum(i.get('section') == 'screened_out' for i in items)}}}\n---",
         f"# Radar {week}", "", "Scores, \"bears on\" tags and summaries are the radar's judgements, not findings of the sources.", ""]
    def links(i):
        out = []
        if i.get("doi"): out += [f"[DOI](https://doi.org/{i['doi']})"] + ([f"[TU Delft access]({proxy}https://doi.org/{i['doi']})"] if proxy else [])
        elif i.get("url"): out.append(f"[Open]({i['url']})")
        if i.get("oa_url"): out.append(f"[Open access]({i['oa_url']})")
        return " | ".join(out)
    def paper(i):
        head = f"- **{i.get('title','')}** ({i.get('first_author','?')} et al., {i.get('year','')}, {i.get('venue') or ''}) | score {i.get('score','?')}/5 | {i.get('bears_on','')}"
        tail = [f"Matched: {', '.join(i.get('matched') or [])}"] if i.get("matched") else []
        if i.get("cites_core"): tail.append("Cites key library works: " + "; ".join(i["cites_core"][:3]))
        return [head, f"  {i.get('summary','')}", "  " + " | ".join(tail + [links(i)])]
    L += ["## Academia", "### New and relevant"] + [x for i in sec("academia", "new") for x in paper(i)] + [""]
    L += ["### New papers citing key works in the library"] + [x for i in sec("academia", "forward") for x in paper(i)] + [""]
    if sec("academia", "methods"): L += ["### Methods"] + [x for i in sec("academia", "methods") for x in paper(i)] + [""]
    if sec("academia", "gap"): L += ["### Citation gaps"] + [f"- **{i.get('title')}** ({i.get('first_author','')}, {i.get('year','')}) | cited by {i.get('cited_in_library','?')} works in the library | {links(i)}" for i in sec("academia", "gap")] + [""]
    if sec("academia", "probable"): L += ["### Probably already in Zotero"] + [f"- {i.get('title')} → probably \"{i.get('zotero_match','')}\" (check)" for i in sec("academia", "probable")] + [""]
    L += ["## Policy", "### New documents"] + [x for i in sec("policy", "new") for x in [
        f"- **{i.get('title','')}** ({i.get('issuer','')}, {i.get('level','')}, {i.get('date','')}, {i.get('doc_type','')}) | score {i.get('score','?')}/5 | {i.get('case','')} | {i.get('bears_on','')}",
        f"  {i.get('summary','')}", f"  Source: {i.get('source','')} | {links(i)}"]] + [""]
    if sec("policy", "corpus_candidate"):
        L += [f"### Corpus candidates (until {cfg.get('corpus_window_end','')})"] + [f"- **{i.get('title','')}** ({i.get('issuer','')}, {i.get('level','')}, {i.get('date','')}) | {i.get('case','')} | found via {i.get('found_via','')} | {links(i)}" for i in sec("policy", "corpus_candidate")] + [""]
    eu = load_json(os.path.join(DATA, "eu-dossiers.json"), {}) or {}
    if eu:
        L += ["### EU dossiers", "| Dossier | Stage | Last step | Next step |", "|---|---|---|---|"]
        L += [f"| {d.get('name', k)} | {d.get('stage', '')} ({d.get('stage_date', '')}) | {d.get('last_event', '')} ({d.get('last_event_date', '')}) | {d.get('next_step', '')} |" for k, d in eu.items()] + [""]
    L += ["## Society", "### News"] + [x for i in sec("society", "news") for x in [
        f"- **{i.get('title','')}** ({i.get('source','')}, {i.get('country','')}, {i.get('date','')}) | score {i.get('score','?')}/5 | {i.get('layer','')}",
        f"  {i.get('summary','')} | {links(i)}"]] + [""]
    ctx = sec("society", "context")
    if ctx:
        dn = {d["id"]: d["name"] for d in (cfg.get("context") or {}).get("drivers", [])}
        L += ["## Context | the wider picture"]
        for did in dict.fromkeys(i.get("driver", "") for i in ctx):
            L += [f"### {dn.get(did, did or 'Other')}"] + [x for i in ctx if i.get("driver", "") == did for x in [
                f"- {'**[signal]** ' if i.get('signal') else ''}**{i.get('title','')}** ({i.get('source','')}, {i.get('date','')}) | {links(i)}",
                f"  {i.get('summary','')} {('Why it may matter: ' + i['why']) if i.get('why') else ''}"]] + [""]
    if sec("society", "event"): L += ["### Events"] + [f"- {i.get('event_date','')} | **{i.get('title','')}** ({i.get('source','')}) | {links(i)}" for i in sorted(sec('society', 'event'), key=lambda i: str(i.get('event_date')))] + [""]
    ev = load_json(os.path.join(DATA, "events.json"), []) or []
    if ev:
        today = datetime.date.today().isoformat()
        up = sorted([e for e in ev if (e.get("end") or e.get("start") or "9999") >= today], key=lambda e: e.get("start") or "9999")
        dl = sorted([e for e in up if e.get("deadline") and e["deadline"] >= today], key=lambda e: e["deadline"])
        L += ["## Events and conferences"]
        if dl: L += ["### Coming deadlines"] + [f"- **{e['deadline']}** {e.get('deadline_what','')} | {e.get('title','')} ({e.get('place','')}) | [Site]({e.get('url','')})" for e in dl[:8]] + [""]
        L += ["### Dutch events"] + [f"- {e.get('start','')} | **{e.get('title','')}** ({e.get('organiser','')}, {e.get('place','')}) | [Info]({e.get('url','')})" for e in up if e.get("kind") == "nl_event"] + [""]
        L += ["### Conferences"] + [f"- {e.get('start','')} to {e.get('end','')} | **{e.get('title','')}** ({e.get('place','')}){' | deadline ' + e['deadline'] if e.get('deadline') else ''}{'' if e.get('verified', True) else ' | not verified'} | [Site]({e.get('url','')})" for e in up if e.get("kind") == "conference"] + [""]
    so = [i for i in items if i.get("section") == "screened_out"]
    L += ["## Screened out", f"<details><summary>{len(so)} items</summary>", ""] + [f"- [{i['stream']}] {i.get('title','')} | score {i.get('score','?')} | {i.get('reason','')}" for i in so] + ["", "</details>", ""]
    L += ["## Run notes"]
    for st, c in counts.items():
        c = dict(c or {}); notes = c.pop("notes", [])
        L.append(f"- **{st}**: " + ", ".join(f"{k} {v}" for k, v in c.items()))
        L += [f"  - {n}" for n in notes]
    return "\n".join(L) + "\n"

def update_seen(items):
    path = os.path.join(DATA, "seen.csv")
    rows = read_csv(path); have = {r["id"] for r in rows}
    for i in items:
        k = key_of(i)
        if k and k not in have:
            rows.append({"id": k, "stream": i["stream"], "week": i["week"],
                         "status": "screened_out" if i.get("section") == "screened_out" else "reported", "title": (i.get("title") or "")[:200]})
            have.add(k)
    write_csv(path, rows, ["id", "stream", "week", "status", "title"])

FIELDS = ["stream", "section", "driver", "signal", "layer", "country", "level", "case", "bears_on", "score", "title", "venue", "source", "issuer",
          "doc_type", "date", "year", "matched", "doi", "url", "first_author", "cited_in_library"]

def update_archive(week, items, cfg):
    os.makedirs(ARCH, exist_ok=True)
    path = os.path.join(ARCH, "items.jsonl")
    seen = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try: r = json.loads(line); seen.add((r["key"], r["week"]))
                except ValueError: pass
    cfg_hash = hashlib.sha1(open(os.path.join(ROOT, "config", "radar.yml"), "rb").read()).hexdigest()[:10]
    with open(path, "a", encoding="utf-8") as f:
        for i in items:
            k = key_of(i)
            if (k, week) in seen: continue
            r = {"key": k, "week": week, "config": cfg_hash}
            r.update({x: i.get(x) for x in FIELDS if i.get(x) not in (None, "", [])})
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats(cfg)

def stats(cfg):
    rows = []
    with open(os.path.join(ARCH, "items.jsonl"), encoding="utf-8") as f:
        for line in f:
            try: rows.append(json.loads(line))
            except ValueError: pass
    terms = cfg.get("trend_terms") or []
    pats = [(t, re.compile(r"\b" + re.escape(t.lower()).replace(r"\ ", r"[\s-]") + r"\w*", re.I)) for t in terms]
    weeks = sorted({r["week"] for r in rows})
    S = {"generated": datetime.date.today().isoformat(), "weeks": weeks, "items": len(rows),
         "configs": {}, "by_stream": {}, "reported_by_stream": {}, "bears_on": {}, "layer": {}, "country": {},
         "level": {}, "case": {}, "matched": {}, "terms": {}}
    add = lambda d, a, w, n=1: d.setdefault(a, {}).__setitem__(w, d.setdefault(a, {}).get(w, 0) + n)
    for r in rows:
        w = r["week"]; rep = r.get("section") != "screened_out"
        S["configs"][w] = r.get("config")
        add(S["by_stream"], r["stream"], w)
        if rep: add(S["reported_by_stream"], r["stream"], w)
        if not (rep or (r.get("score") or 0) >= 3): continue   # trends: reported items plus relevant ones over the cap
        for sq in re.findall(r"SQ\s?[1-4]|Guidelines", str(r.get("bears_on") or "")): add(S["bears_on"], sq.replace(" ", ""), w)
        for f in ("layer", "country", "level", "case"):
            if r.get(f): add(S[f], str(r[f]), w)
        for m in r.get("matched") or []: add(S["matched"], m, w)
        text = " ".join(str(r.get(x) or "") for x in ("title",))
        for t, p in pats:
            if p.search(text): add(S["terms"], t, w)
    save_json(os.path.join(ARCH, "stats.json"), S)

def main():
    week = sys.argv[1] if len(sys.argv) > 1 else iso_week()
    cfg = config()
    raw, counts = load_week(week)
    if not raw: sys.exit(f"No stream files in radar/items/{week}/ yet.")
    items = merge(raw, cfg)
    save_json(os.path.join(RADAR, "items", f"{week}.json"), items)
    save_json(os.path.join(RADAR, "items.json"), items)
    with open(os.path.join(RADAR, f"{week}.md"), "w", encoding="utf-8") as f: f.write(note(week, items, counts, cfg))
    save_json(os.path.join(DATA, "config.json"), json.loads(json.dumps(cfg, default=str)))   # a JSON copy of the config for the Obsidian page
    update_seen(items)
    update_archive(week, items, cfg)
    by = collections.Counter((i["stream"], i.get("section")) for i in items)
    print(f"{week}: " + ", ".join(f"{s}/{x} {n}" for (s, x), n in sorted(by.items())))

if __name__ == "__main__":
    main()
