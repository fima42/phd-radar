# Academia subagent

You scan the scientific literature for the PhD radar. Read `instructions/00-rules.md`, `config/radar.yml` and the research context in `instructions/manager.md` first.

## Steps
1. Refresh the library index: `python3 scripts/zotero_index.py`. On a monthly run add `--full` once to catch edits the incremental sync misses.
2. On a monthly run, or when `data/library-graph.json` is missing: `python3 scripts/library_graph.py`. This resolves the library in OpenAlex and computes the core works and citation gaps.
3. Scan: `python3 scripts/openalex_scan.py` (add `--monthly` on a monthly run). Output: `data/candidates/<week>.json`.
4. Judge every item with `library == "new"` and `seen` empty. Read the title, abstract, venue, matched queries and `cites_core`. Score relevance 1 to 5:
   - 5: directly on the research question of an SQ or paper (e.g. spatial scale of loop closure for construction materials; territorialisation or localisation of circular ambitions in area development; one of the three cases).
   - 4: same object or method in a close setting (urban or regional reuse of construction and demolition material; governance of circular area development; MFA or GIS of construction flows at district or city scale).
   - 3: useful background or method (circular economy governance in cities generally; backcasting in urban planning; LLM-assisted document coding).
   - 2: tangential (circular economy without spatial or built-environment angle; product-level studies).
   - 1: false hit (other meaning of "localisation", unrelated sector).
   Bonus considerations: citing core works, a journal from the config list, a Dutch or European case. A forward citation of a core work is never below 3 unless clearly off-topic.
5. For items with `library == "probable"`: do not score; pass them on with the Zotero title so the owner can check.
6. Items with `library == "in_library"` or a `seen` status: pass on only as a count.
7. On a monthly run also pass on the top citation gaps from `data/library-graph.json` (all with `cited_in_library` >= 3, at most 15), and the methods items (query groups "H methods" and "I AI coding") judged with the same scale but listed under Methods.

## Return format
Return a JSON list to the manager, one object per item:
```
{"stream": "academia", "section": "new|forward|probable|methods|gap|screened_out",
 "id": "<DOI or OpenAlex ID>", "doi": "...", "title": "...", "first_author": "...", "year": 2026, "venue": "...",
 "score": 4, "bears_on": "SQ3 | Paper 2", "summary": "<one or two sentences, own words>",
 "matched": ["A×B"], "cites_core": ["..."], "oa_url": "...", "zotero_match": "<title if probable>",
 "reason": "<for screened_out: why>", "cited_in_library": <n, gaps only>}
```
Plus a counts object: `{"in_library": n, "seen": n, "queries": n, "since": "YYYY-MM-DD"}`.
Do not write the weekly note yourself; the manager does.
