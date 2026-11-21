# phd-radar

Weekly radar for the PhD *Circular Area Development* (Florens Jocker, TU Delft, ACT! WP4): new science, policy and society items on the research topic, checked against the Zotero library so only missing work is reported.

- `config/radar.yml` | keywords (groups A to I), journals, cases, thresholds, the SQ2 corpus window (until 31 Dec 2026). Edit freely.
- `instructions/` | the manager and one file per stream (academia active; policy and society to follow). `00-rules.md` applies to all.
- `scripts/` | deterministic fetching: `zotero_index.py` (library identifiers via the Zotero web API), `library_graph.py` (core works and citation gaps via OpenAlex), `openalex_scan.py` (weekly keyword and forward-citation scan with duplicate check).
- `data/` | working data: `zotero-index.json`, `library-graph.json`, `candidates/<week>.json`, `seen.csv` (everything reported before; set `status` to `rejected` or `added` to steer later runs).
- `radar/<week>.md` | the weekly note, shown in Obsidian through the submodule at `10 PhD/Radar`.

Keys live only in the `phd-radar` cloud environment: `ZOTERO_USER_ID`, `ZOTERO_API_KEY` (read-only), `OPENALEX_API_KEY`.
The radar proposes; it never writes to Zotero, the vault, the SQ2 corpus or the document register.
