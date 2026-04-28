# Project: Wine Enthusiast Scraper

## Data source
Wine Enthusiast reviews are available directly via the **Algolia API** — no Playwright or BeautifulSoup needed.
- URL: `https://HZOXADUQY8-dsn.algolia.net/1/indexes/*/queries`
- App ID: `HZOXADUQY8`
- API key: `e9abd7ddf7b59423aceea6146888507c`
- Index: `PROD_WINEENTHUSIAST_REVIEWS`
- Total reviews in DB: ~422,000
- Target: 2020–2026, expected ~140,000–150,000 reviews

## Scraper: `webscrapping.py`
- Fetches wine reviews 2020–2026 via Algolia API using `requests`
- Algolia caps results at 1000 per query — overcome by recursive splitting:
  `year → country → wine_type → varietal_label → state → vintage → designation`
- Small facet values (< 200 wines, BATCH_THRESHOLD) are batched into OR filters to avoid hundreds of tiny API calls
- Large facet values (>= 200) get individual recursive calls
- Random delay 1.5–3.5s between requests to avoid IP blocking
- 100 hits per page, maxValuesPerFacet=1000
- Output: timestamped CSV `wine_reviews-YYYY-MM-DD-HH-MM.csv`
- Warns in red when 1000-result cap is hit
- Progress output: prints filters, segment size, page/total counter per segment

## CSV fields (in order)
- Identity: name, brand, company, vintage, designation
- Characteristics: drink_type, wine_type, varietal_label, alcohol, bottle_size, case_production
- Geography: country, state, appellation
- Review: retail, rating, reviewer, review, date_of_review
- Dates: date_received, pub_date_web
- Misc: slug

## Exploration: `wine_explore.ipynb` and `explore.py`
- Uses `pandas` + `ydata_profiling` for EDA
- `ProfileReport(df, title="Wine Reviews EDA", explorative=True)`
- Known issue: `ModuleNotFoundError: No module named 'pkg_resources'`
  - setuptools==82.0.1 is installed but pkg_resources not visible
  - Fix: fully restart VS Code with no Python processes running
  - Always run scripts via `.venv` Python, not system Python

## Environment
- VS Code on Windows 11
- `.venv` virtual environment at `.venv\Scripts\python.exe`
- Registered as Jupyter kernel "Python (wines-venv)"
- Always activate venv before running scripts: `.venv\Scripts\Activate.ps1`
- Dependencies in `requirements.txt`

## requirements.txt
- pandas (no version pinned yet)
- requests==2.33.1
- ydata-profiling==4.18.1
- ipykernel==7.2.0
- setuptools==82.0.1

## Current status (as of 2026-04-12)
- Scraper is currently running — mid-way through year 2022
- CSV output being written incrementally
- No red warnings observed so far (1000-cap not hit)
- Poland (4 wines in 2022) confirmed present in Algolia facets — will be scraped

## Preferences
- Verbose progress output: segment filters, page counts, running total
- Red ANSI warnings for any data loss situations
- Incremental CSV writes (don't buffer in memory)
- Timestamped output filenames
- Direct API over browser automation wherever possible
- Step-by-step guidance preferred
