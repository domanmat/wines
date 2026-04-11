# import sys                
# print(sys.executable)
# import importlib.util                                   
# print(importlib.util.find_spec("pkg_resources"))         


# import pandas as pd
# df=pd.read_csv("wine_reviews-2026-04-11-23-44 copy.csv")

# # from ydata_profiling import ProfileReport
# # profile = ProfileReport(df, title="Wine Reviews EDA", explorative=True)
# # profile.to_notebook_iframe() 

import requests, json
from urllib.parse import urlencode

'''params = urlencode({
    "hitsPerPage": 1,
    "page": 0,
    "query": "adoria chardonnay poland",
    "filters": "drink_type:wine",
})

body = {"requests": [{"indexName": "PROD_WINEENTHUSIAST_REVIEWS", "params": params}]}
r = requests.post(
    "https://HZOXADUQY8-dsn.algolia.net/1/indexes/*/queries",
    headers={"x-algolia-api-key": "e9abd7ddf7b59423aceea6146888507c",
             "x-algolia-application-id": "HZOXADUQY8",
             "Content-Type": "application/json"},
    json=body
)
hit = r.json()["results"][0]["hits"][0]
print("pub_date_web_year:", hit.get("pub_date_web_year"))
print("pub_date_web:", hit.get("pub_date_web"))
print("vintage:", hit.get("vintage"))

print("countries_menu:", hit.get("countries_menu"))              
print("country lvl0:", hit.get("countries_menu", {}).get("lvl0"))
'''

params = urlencode({
    "hitsPerPage": 1,
    "page": 0,
    "query": "",
    "filters": "drink_type:wine AND pub_date_web_year:2022",
    "facets": json.dumps(["countries_menu.lvl0"]),
    "maxValuesPerFacet": 1000,
})
body = {"requests": [{"indexName": "PROD_WINEENTHUSIAST_REVIEWS", "params": params}]}
r = requests.post(
    "https://HZOXADUQY8-dsn.algolia.net/1/indexes/*/queries",
    headers={"x-algolia-api-key": "e9abd7ddf7b59423aceea6146888507c",
             "x-algolia-application-id": "HZOXADUQY8",
             "Content-Type": "application/json"},
    json=body
)
facets = r.json()["results"][0]["facets"]["countries_menu.lvl0"]
print("Poland" in facets, facets.get("Poland"))
print(f"Total countries in facet: {len(facets)}")