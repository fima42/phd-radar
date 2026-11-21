# Policy subagent

You scan new policy and governance documents for the PhD radar. Read `instructions/00-rules.md`, `config/radar.yml` (sections `keywords.E_dutch`, `keywords.F_cases`, `policy`, `corpus_window_end`) and the research context in `instructions/manager.md` first.

## What counts
Documents that state, adopt, change or evaluate circular ambitions, targets, rules, instruments or results for construction, demolition, reuse or material flows, or that set the spatial and governance frame of circular area development, at these levels:
- **AREA** and **MUN**: the three cases (M4H / Merwe-Vierhavens Rotterdam, Marineterrein Amsterdam, Ringpark Zuid **Tilburg**; never the Ringpark Zuid in Antwerp) and the municipal policy of Rotterdam, Amsterdam, Tilburg on circular construction, materials, area development, omgevingsvisie or omgevingsplan.
- **REG** and **PRV**: the regions and provinces in the config.
- **NAT**: national programmes and letters (NPCE, Transitieagenda Bouw, MPG, ruimtelijke ordening, Kamerbrieven on circular construction).
- **EU**: only directly relevant acts or strategies (e.g. Construction Products Regulation, Circular Economy Act, Waste Framework Directive revisions, EU urban agenda).
Council agenda items, motions, letters, decisions, visions, programmes, monitors and reports all count. Pure procedure (agenda without content, minutes of unrelated items) does not.

## Sources and how to query (record every query you run)
1. **Open Raadsinformatie** (municipal and provincial council documents): read the API docs at `https://docs.openraadsinformatie.nl/` if the query format is unclear, then search the API (`https://api.openraadsinformatie.nl/v1/elastic/`) with curl for the three municipalities and three provinces, for documents from the last `policy.window_days` days that mention the case names or the Dutch keywords (circulair, hergebruik bouwmaterialen, grondstoffen, gebiedsontwikkeling with the case names). If the API is unreachable or the format differs, say so in the run notes and fall back to WebSearch with `site:` queries on the municipal council sites.
2. **Officiële publicaties** (gemeenteblad, provinciaal blad, Staatscourant, Kamerstukken): SRU at `https://repository.overheid.nl/sru` with `query=c.product-area==officielepublicaties AND ...` (CQL; use `dt.creator` for the issuer and `cql.textAndIndexes` or `dt.title` for terms, and `dt.date>=` for the period), `maximumRecords=50`.
3. **Tweede Kamer** open data (`https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/`): documents whose subject or title contains circulair / circulaire economie / bouw / grondstoffen in the period.
4. **EUR-Lex and EU**: WebSearch only, few queries.
5. **Case websites** in `policy.case_sites`: WebSearch `site:` queries for new documents or news that announce documents.
If a source fails, report the error once and continue with the others.

## De-duplication
- Against earlier radar weeks: `data/seen.csv` (by URL, and by title + issuer + date).
- Against the owner's vault you cannot check; the Monday jobs do that. Report plainly.

## Scoring (1 to 5, judgement)
5 a document on one of the three cases or the municipal circular-construction policy of their city; 4 regional or provincial policy that names the cases or sets their frame, or a national instrument directly about circular construction or demolition material; 3 national or EU background on circular construction or area development; 2 tangential; 1 false hit.

## Corpus candidates (until `corpus_window_end`)
Until and including that date, every document at AREA, MUN, REG or PRV level about one of the three cases, and every NAT document that applies to all three, that was **adopted or published between 2016 and 2026** and could belong to the SQ2 corpus, is also returned with `section: "corpus_candidate"`, `found_via: "radar <week> | <source> | <query>"`. Older documents found now count too: the point is to catch what the corpus may have missed. After the date, return no corpus candidates.

## Return format
Write a JSON list to `radar/items/<week>/policy.json`, one object per item:
```
{"stream": "policy", "section": "new|corpus_candidate|screened_out",
 "id": "<URL>", "url": "...", "title": "...", "issuer": "...", "level": "MUN", "case": "RTM|AMS|TLB|ALL|-",
 "date": "YYYY-MM-DD", "doc_type": "raadsvoorstel|collegebrief|motie|visie|programma|monitor|Kamerbrief|...",
 "score": 4, "bears_on": "SQ2 | Paper 1", "summary": "<one or two sentences, own words, descriptive>",
 "source": "ORI|SRU|TK|EUR-Lex|web", "query": "<the query that found it>", "found_via": "<corpus candidates only>",
 "reason": "<screened_out only>"}
```
Write the counts object to `radar/items/<week>/policy.counts.json` (add `"notes": [...]` for limitations and problems): `{"queries": n, "sources_ok": [...], "sources_failed": [...], "since": "YYYY-MM-DD"}`.
