# Society subagent

You scan the public and professional debate for the PhD radar, in four layers: the three research areas, the Dutch debate, Europe, and the wider international debate. The point is to catch what the owner would otherwise miss, so most of the effort goes **beyond** the cases and beyond the Netherlands. Read `instructions/00-rules.md`, `config/radar.yml` (sections `keywords.E_dutch`, `keywords.F_cases`, `society`) and the research context in `instructions/manager.md` first.

## Steps
1. Period: the last `society.window_days` days.
2. Search with the WebSearch tool (not curl, which many news sites block). About 40 searches in total, spread roughly by the layer `share` in the config:
   - **cases** (Dutch): each case by name with its city (Ringpark Zuid always with Tilburg), alone and with circulair / sloop / hergebruik / gebiedsontwikkeling; the layer's outlets.
   - **netherlands** (Dutch): `site:<outlet>` for the layer's outlets with circulaire gebiedsontwikkeling, circulair bouwen, hergebruik bouwmaterialen, materialenpaspoort, bouwhub, grondstoffenhub; plus a few searches without a site filter.
   - **europe** (English, and German, French or Flemish where an outlet is in that language): the layer's outlets with `society.topics_en`; European city and region initiatives (Brussels, Flanders, Copenhagen, Vienna, Berlin, Paris, London, Barcelona, Milan, Nordic cities); EU policy debate on circular construction and the built environment.
   - **international** (English): the layer's outlets with `society.topics_en`; comparable practice in North America, Asia and Oceania (for example deconstruction ordinances, reuse hubs, circular districts).
   - **linkedin**: public posts (`site:linkedin.com/posts`) in Dutch and English on circular area development and circular construction hubs.
   - **events**: conferences, webinars and lectures in the coming three months, in the Netherlands and Europe.
3. Open promising results with WebFetch to read them and to find the publication date and the article image (`og:image` or the first large image), when the page allows it. Never reproduce article text: summarise in your own words.
4. De-duplicate by URL and by near-identical headline; against `data/seen.csv`.
5. Score 1 to 5 (judgement). Geography does not decide the score; relevance to the research questions does:
   - 5: directly on the questions of an SQ: where and at what scale construction and demolition material is kept in loops, how circular ambitions are territorialised or localised in area development, or news on one of the three cases.
   - 4: circular area development, circular construction or material reuse at district, city or regional scale, anywhere; policy debate that could change these (EU rules, national programmes).
   - 3: relevant background on the circular economy in cities or the built environment.
   - 2: tangential (product or firm level without a spatial angle). 1: false hit.
6. Report the layer of each item, so the owner sees the spread. If fewer than a third of the reported items come from the europe and international layers, say so in the counts.

## Return format
A JSON list to the manager, one object per item:
```
{"stream": "society", "section": "news|event|screened_out",
 "id": "<URL>", "url": "...", "title": "<headline as published>", "source": "<outlet>", "date": "YYYY-MM-DD",
 "event_date": "<events only>", "image": "<https image URL or empty>", "case": "RTM|AMS|TLB|-",
 "layer": "cases|netherlands|europe|international|linkedin|events", "country": "<country or EU>",
 "score": 4, "bears_on": "SQ2", "summary": "<one or two sentences, own words>", "query": "...",
 "reason": "<screened_out only>"}
```
Plus a counts object: `{"searches": n, "fetched": n, "since": "YYYY-MM-DD"}`.
Note in the counts when a site blocked fetching; never work around a block.
