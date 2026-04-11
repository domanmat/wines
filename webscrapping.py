import requests
import csv
import time
import random
import json
from urllib.parse import urlencode

'''
The entire database from https://www.wineenthusiast.com/wine-ratings/ is accessible directly via the Algolia API — no browser, no Playwright needed at all. 
Every field is already in the JSON: name, rating, review, price, varietal, appellation, country, reviewer, etc.

  Key numbers from the response:
  - 422,199 total reviews
  - API key: e9abd7ddf7b59423aceea6146888507c
  - App ID: HZOXADUQY8
  - Index: PROD_WINEENTHUSIAST_REVIEWS
  '''


ALGOLIA_URL = "https://HZOXADUQY8-dsn.algolia.net/1/indexes/*/queries"
HEADERS = {
    "x-algolia-api-key": "e9abd7ddf7b59423aceea6146888507c",
    "x-algolia-application-id": "HZOXADUQY8",
    "Content-Type": "application/json",
}

'''
Key changes:
  - Small pages — 50 results per request instead of 100
  - Random delay — 1.5–3.5 seconds between every request, mimicking human browsing
  - Filtered by year — 2020–2026 only, ~1,000 reviews per year = ~7,000 total
  - Writes to CSV incrementally — results are saved as they come in, so if it gets interrupted you don't lose everything

How it works:
  - For each year, it first checks the total hit count
  - If ≤ 1000 → paginates directly
  - If > 1000 → splits by country, fetching each country separately
  - If a country still has > 1000 in a year → splits further by wine_type (Red, White, Sparkling, etc.)     
  - Any combination still over 1000 gets a warning but takes the first 1000 (very rare edge case like USA Red 2023)
  Expected total: ~140,000–150,000 reviews. With delays, runtime will be a few hours — perfectly polite toward the server.
  '''

HITS_PER_PAGE = 100
DELAY_MIN = 1.5
DELAY_MAX = 3.5
YEARS = range(2020, 2027)
OUTPUT_FILE = "wine_reviews.csv"

'''
Grouped into logical sections:
  - Identity — wine name, producer, vintage
  - Characteristics — type, varietal, alcohol, bottle size, production volume                         
  - Geography — country → state → appellation
  - Review — rating and price together, then the review text and reviewer                           
  - Dates — received, reviewed, published (chronological order)
  - Misc — slug at the end
'''

FIELDS = [
    # identity
    "name", "brand", "company",  
    # wine characteristics
    "vintage", "drink_type", "wine_type", "varietal_label", "alcohol", "bottle_size", "case_production",
    # geography
    "country", "state", "appellation", "designation",
    # review
    "retail", "rating", "reviewer","review", "date_of_review", 
    # dates
    "date_received", "pub_date_web",
    # misc
    "slug",
]

'''
Three changes made:    
  - brand → designation as the deepest split level — much lower cardinality, still effective
  - flush=True added to the rolling print — this was likely why the output wasn't showing in real time (Python buffers stdout by default)
  - Red warning (\033[91m) printed whenever the 1000-result cap is actually hit, so you can't miss it       
  '''
counter = [0]


def fetch_page(page: int, filters: str, facets: list = None) -> dict:
    params = {
        "hitsPerPage": HITS_PER_PAGE,
        "page": page,
        "query": "",
        "filters": filters,
    }
    if facets:
        params["facets"] = json.dumps(facets)
        params["maxValuesPerFacet"] = 1000

    body = {
        "requests": [{
            "indexName": "PROD_WINEENTHUSIAST_REVIEWS",
            "params": urlencode(params),
        }]
    }
    response = requests.post(ALGOLIA_URL, headers=HEADERS, json=body)
    response.raise_for_status()
    return response.json()["results"][0]


def extract(hit: dict) -> dict:
    row = {field: hit.get(field) for field in FIELDS if field != "country"}
    row["country"] = hit.get("countries_menu", {}).get("lvl0")
    return row


RED = "\033[91m"
RESET = "\033[0m"


def fetch_all_pages(filters: str, writer, remaining_splits: list = None) -> int:
    """Paginate through all results for a filter combo (Algolia cap: 1000).
    Returns the total hit count reported by Algolia."""
    first = fetch_page(0, filters)
    total_hits = first["nbHits"]
    accessible_pages = min(first["nbPages"], 1000 // HITS_PER_PAGE)

    print(f"\n  Filters  : {filters}")
    if remaining_splits:
        print(f"  Unused splits (not needed): {', '.join(remaining_splits)}")
    print(f"  Segment  : {total_hits:,} wines — {accessible_pages} page(s) to fetch", flush=True)

    rows = [extract(hit) for hit in first["hits"]]
    writer.writerows(rows)
    counter[0] += len(rows)
    print(f"  Page 1/{accessible_pages} — {len(rows):,} in segment — {counter[0]:,} reviews collected so far", flush=True)

    for page in range(1, accessible_pages):
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        result = fetch_page(page, filters)
        rows = [extract(hit) for hit in result["hits"]]
        writer.writerows(rows)
        counter[0] += len(rows)
        print(f"  Page {page + 1}/{accessible_pages} — {len(rows):,} in segment — {counter[0]:,} reviews collected so far", flush=True)

    return total_hits


def scrape_segment(filters: str, writer, split_by: list):
    """
    Fetch all results for a filter. If results > 1000, split by the
    first facet in split_by, then recurse with the remaining facets.
    """
    probe = fetch_page(0, filters, facets=split_by[:1] if split_by else None)
    total = probe["nbHits"]

    if total == 0:
        return

    if total <= 1000 or not split_by:
        actual = fetch_all_pages(filters, writer, remaining_splits=split_by)
        if actual > 1000:
            print(f"\n{RED}  WARNING: {actual:,} hits but only 1000 fetched for filter: {filters}{RESET}")
        return

    # Split by first available facet
    facet_field = split_by[0]
    facet_values = probe.get("facets", {}).get(facet_field, {})

    if not facet_values:
        # Facet returned nothing — just take what we can
        actual = fetch_all_pages(filters, writer, remaining_splits=split_by)
        if actual > 1000:
            print(f"\n{RED}  WARNING: {actual:,} hits but only 1000 fetched for filter: {filters}{RESET}")
        return

    for value in facet_values:
        safe_value = value.replace("\\", "\\\\").replace('"', '\\"')
        sub_filter = f'{filters} AND {facet_field}:"{safe_value}"'
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        scrape_segment(sub_filter, writer, split_by[1:])


def scrape():
    print(f"Scraping years {list(YEARS)[0]}–{list(YEARS)[-1]}...")
    print(f"Saving to {OUTPUT_FILE}\n")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        for year in YEARS:
            print(f"Year {year}:")
            base_filter = f"drink_type:wine AND pub_date_web_year:{year}"
            # Split: country → wine_type → varietal → state to get past Algolia's 1000-result cap
            scrape_segment(base_filter, writer, split_by=["countries_menu.lvl0", "wine_type", "varietal_label", "state", "vintage", "designation"])
            print(f"\n  Done — {counter[0]:,} total so far\n")

    print(f"Finished. {counter[0]:,} reviews saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape()
