---
name: Wines project context
description: Architecture, data source, scraper status, and open issues for the Wine Enthusiast scraper
type: project
originSessionId: 4c9d9065-af85-4cb9-9746-d9481ea820c9
---
## Data source
Wine Enthusiast reviews are available directly via the **Algolia API** — no Playwright or BeautifulSoup needed.
- URL: `https://HZOXADUQY8-dsn.algolia.net/1/indexes/*/queries`
- App ID: `HZOXADUQY8`
- API key: `e9abd7ddf7b59423aceea6146888507c`
- Index: `PROD_WINEENTHUSIAST_REVIEWS`
- Total reviews in DB: ~422,000

## Scraper: `webscrapping.py`
- Fetches wine reviews 2020–2026 via Algolia API using `requests`
- Algolia caps results at 1000 per query — overcome by recursive splitting:
  `year → country → wine_type → varietal_label → state → vintage → designation`
- Small facet values (< 200 wines) are **batched into OR filters** to avoid hundreds of tiny API calls
- Random delay 1.5–3.5s between requests to avoid IP blocking
- 100 hits per page
- Output: timestamped CSV `wine_reviews-YYYY-MM-DD-HH-MM.csv`
- Warns in red when 1000-result cap is hit

## CSV fields (in order)
identity: name, brand, company, vintage, designation
characteristics: drink_type, wine_type, varietal_label, alcohol, bottle_size, case_production
geography: country, state, appellation
review: retail, rating, reviewer, review, date_of_review
dates: date_received, pub_date_web
misc: slug

## Exploration notebook: `wine_explore.ipynb`
- Uses `pandas` + `ydata_profiling` for EDA
- `ProfileReport(df, title="Wine Reviews EDA", explorative=True)`
- **Open issue**: `ModuleNotFoundError: No module named 'pkg_resources'` despite setuptools==82.0.1 being installed
  - Root cause likely stale VS Code / kernel process — fix: fully restart VS Code with no Python processes running

## Requirements (`requirements.txt`)
- requests==2.33.1
- ydata-profiling==4.18.1
- ipykernel==7.2.0
- setuptools==82.0.1
