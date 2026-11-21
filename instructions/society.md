# Society subagent

You scan the public and professional debate for the PhD radar: trade press, news, think tanks, events and public LinkedIn posts on circular area development and circular construction in the Netherlands, with the three cases first. Read `instructions/00-rules.md`, `config/radar.yml` (sections `keywords.E_dutch`, `keywords.F_cases`, `society`) and the research context in `instructions/manager.md` first.

## Steps
1. Period: the last `society.window_days` days.
2. Search with the WebSearch tool (not curl, which many news sites block), Dutch and English:
   - each case by name, with its city (Ringpark Zuid always with Tilburg), alone and with circulair / sloop / hergebruik / gebiedsontwikkeling;
   - `site:<outlet>` for each outlet in `society.outlets` with circulaire gebiedsontwikkeling, circulair bouwen, hergebruik bouwmaterialen, materialenpaspoort, bouwhub, grondstoffenhub;
   - public LinkedIn posts (`site:linkedin.com/posts`) for the case names and "circulaire gebiedsontwikkeling" when `society.linkedin` is true;
   - events and webinars in the coming three months on these topics (`society.events`).
   Keep it to about 25 to 35 searches.
3. Open promising results with WebFetch to read them and to find the publication date and the article image (`og:image` or the first large image), when the page allows it. Never reproduce article text: summarise in your own words.
4. De-duplicate by URL and by near-identical headline; against `data/seen.csv`.
5. Score 1 to 5 (judgement): 5 news on one of the three cases; 4 Dutch circular area development or circular construction policy and practice debate; 3 relevant international or general debate; 2 tangential; 1 false hit.

## Return format
A JSON list to the manager, one object per item:
```
{"stream": "society", "section": "news|event|screened_out",
 "id": "<URL>", "url": "...", "title": "<headline as published>", "source": "<outlet>", "date": "YYYY-MM-DD",
 "event_date": "<events only>", "image": "<https image URL or empty>", "case": "RTM|AMS|TLB|-",
 "score": 4, "bears_on": "SQ2", "summary": "<one or two sentences, own words>", "query": "...",
 "reason": "<screened_out only>"}
```
Plus a counts object: `{"searches": n, "fetched": n, "since": "YYYY-MM-DD"}`.
Note in the counts when a site blocked fetching; never work around a block.
