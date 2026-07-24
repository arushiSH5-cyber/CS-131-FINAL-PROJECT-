# Backup Dataset — Option B: GDELT 2.0

Fallback if GH Archive is rejected in proposal feedback or turns out unworkable.
The four-phase structure and repo layout stay identical; only the dataset,
schema, and the exact CLI/Spark columns change.

## Dataset
**GDELT 2.0** (https://www.gdeltproject.org/data.html) — a very large global
news/event database built from worldwide news media. Two feeds:
- **Events** table — one row per detected event (actors, action, location,
  Goldstein scale, average tone). Tab-separated (`.CSV` that is actually TSV),
  ~60 columns, updated every 15 minutes since 2015.
- **GKG** (Global Knowledge Graph) — themes, people, orgs, locations, and
  tone/sentiment per article.

Files: `http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMMSS.export.CSV.zip`
(Events) and `...gkg.csv.zip` (GKG). The master file list is at
`http://data.gdeltproject.org/gdeltv2/masterfilelist.txt`.

## Question
> How has global news sentiment around AI regulation / cybersecurity /
> semiconductor supply chains changed across countries from 2015 to 2026?

Secondary: which countries dominate AI-regulation coverage; how cybersecurity
news volume spikes after major breaches; which tech themes carry the most
negative/positive media tone.

## Size floor
GDELT 2.0 easily exceeds **5 GB / 50 M rows** across a multi-year span (15-minute
files since Feb 2015). Prove exact sizes in Phase 1, same as GH Archive.

## Phase mapping (what changes)
| Phase | GDELT specifics |
|-------|-----------------|
| 1 Profile | TSV, so `cut -f`, `awk -F'\t'`, `grep -c`, `sort \| uniq -c` on country / theme / tone columns. Watch the header/no-header + tab delimiter. |
| 2 Breaking | Same idea — Excel row cap, pandas OOM on the concatenated CSVs. |
| 3 Scaling | `spark.read.option("sep","\t").schema(...).csv("gs://...")`; groupBy country/month, window for month-over-month, Spark SQL on tone. |
| 4 Analysis | Time-series of average tone by theme/country; annotate real-world tech events. |

## Key columns (GDELT 2.0 Events, 0-indexed selection)
- `SQLDATE` / `DATEADDED` — date
- `Actor1CountryCode`, `Actor2CountryCode`, `ActionGeo_CountryCode` — geography
- `EventCode`, `GoldsteinScale` — event type / intensity
- `AvgTone` — sentiment (negative = more negative coverage)
- `SOURCEURL` — article link (theme filtering by keyword)

## Why kept as backup, not primary
GH Archive is chosen first: cleaner one-object-per-line JSON, simpler schema,
and a tighter "AI vs general" narrative. GDELT is the stronger *sentiment* story
but heavier to clean (wide TSV, no header, coded columns). Switch only if needed.
