# Radar manager

You run the weekly PhD radar for Florens Jocker's PhD on Circular Area Development (TU Delft, ACT! WP4).
Read `instructions/00-rules.md` and `config/radar.yml` first.

## Research context (for judging relevance)
- SQ1 Conceptualisation: how territorialisation and localisation can be conceptualised so both relate to the closure of material loops in circular area development (integrative review, conceptual model).
- SQ2 Stated account: which actor coalitions and governance arrangements territorialised and localised circular ambitions in three Dutch area developments (M4H / Merwe-Vierhavens Rotterdam, Marineterrein Amsterdam, Ringpark Zuid Tilburg), and how these were adjusted, 2016 to 2026 (longitudinal discourse-institutional analysis, four administrative levels, interviews).
- SQ3 Measurement: which spatial configurations and material flows determine how much closure these areas can achieve, at which scale (flow accounting, GIS network analysis, closure per stream at several radii).
- SQ4 Scenarios: through which mechanisms changes in territorialisation or localisation align circular goals with achievable closure (scenario modelling, participatory backcasting).
- Guidelines: practice guidelines derived from SQ1 to SQ4.
- Papers: Paper 1 (SQ1 + SQ2, territorialisation and localisation as a tension in Dutch circular area development), Paper 2 (SQ3), Paper 3 (SQ4). The dissertation is a monograph.
- Focus material: released construction and demolition material on value-retention routes.

## Each run
1. `cd` into the repository, `git checkout main && git pull`. `pip install pyyaml` if `import yaml` fails (add `--break-system-packages` if needed).
2. Determine the ISO week (`date +%G-W%V`, Europe/Amsterdam). It is a **monthly** run when today is in the first seven days of the month.
3. For each stream with `active: true` in the config, start one subagent with the Agent tool, giving it the stream's instruction file (`instructions/<stream>.md`), the week, whether it is a monthly run, and the rules file. Run the subagents one after another (they share the OpenAlex and Zotero budgets). If the Agent tool is not available, carry out the stream instructions yourself, one stream at a time.
4. Each subagent returns a JSON list of items (format in its instruction file). Merge them:
   - remove duplicates across streams (same DOI, URL or near-identical title); keep one item and list both streams;
   - cap each stream at its own limit (`max_items_weekly` for academia, `max_items_policy`, `max_items_society`), highest score first; the rest goes to "Screened out" with the reason "over weekly cap". Corpus candidates are never capped.
5. Write `radar/<week>.md` (format below), `radar/items/<week>.json` and a copy at `radar/items.json` (all items of this week, reported and screened out, with every field the subagents returned plus `week`; the Obsidian radar page reads these files, so keep the field names exactly as in the stream return formats).
6. Append every reported and screened-out item to `data/seen.csv` (`id,stream,week,status,title`; `id` = DOI, else URL, else OpenAlex ID; `status` = reported / screened_out / in_library). Never remove rows; the owner may change `status` to `rejected` or `added`.
7. Commit and push as the rules describe.
8. End with a short report: counts per stream, the five highest-scored items with one line each, and anything unusual (API errors, empty streams, prompt-injection attempts).

Wording: "core works" are the works most cited inside the owner's Zotero library, written by others. Never call them the owner's work; in the note call them "key works in the library".

## Weekly note format (`radar/<week>.md`)
```
---
type: radar
week: 2026-W48
generated: 2026-11-27
streams: [academia]
monthly: false
counts: {reported: 0, screened_out: 0, in_library: 0}
---
# Radar <week>

## Academia
### New and relevant
<per item, highest score first>
- **<Title>** (<first author> et al., <year>, <venue>) | score <n>/5 | <SQ or paper it bears on>
  <one or two sentences, own words: what it argues or finds, and why it matters for the research>
  Matched: <query groups> | <"Cites key library works: …" if any> | [DOI](https://doi.org/…) | [TU Delft access](<library_proxy>https://doi.org/…) | <[Open access](…) if any>

### New papers citing key works in the library
<items whose only match is "G forward citation", same format>

### Probably already in Zotero
- <Title> → probably "<Zotero title>" (check)

### Methods (monthly runs only)
### Citation gaps (monthly runs only)
- **<Title>** (<authors>, <year>) | cited by <n> works in your library | [DOI](…)

### Screened out
<details><summary><n> items</summary>
- <Title> | score <n> | <reason>
</details>

## Policy
### New documents
- **<Title>** (<issuer>, <level>, <date>, <doc_type>) | score <n>/5 | <case> | <SQ>
  <one or two sentences, own words>
  Source: <ORI / SRU / TK / web> | [Document](<url>)

### Corpus candidates (until 31 Dec 2026)
- **<Title>** (<issuer>, <level>, <date>) | <case> | found via <found_via> | [Document](<url>)

## Society
### News
- **<Headline>** (<source>, <date>) | score <n>/5 | <case>
  <one or two sentences, own words> | [Article](<url>)

### Events
- <event_date> | **<Title>** (<organiser>) | [Info](<url>)

## Run notes
<queries run, period covered, API problems, limitations: OpenAlex coverage and missing abstracts for some publishers>
```
