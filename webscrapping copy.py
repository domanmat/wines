      1  import requests                                                                                                       2 -import json
      2  import csv                                                                                                      
      3  import time
      4 +import random
      5
      6  ALGOLIA_URL = "https://HZOXADUQY8-dsn.algolia.net/1/indexes/*/queries"
      7  HEADERS = {
     ...
      10      "Content-Type": "application/json",
      11  }
      12
      13 -HITS_PER_PAGE = 100  # max practical page size                                                                 
      13 +HITS_PER_PAGE = 50       # small pages to stay under the radar                                                 
      14 +DELAY_MIN = 1.5          # seconds between requests                                                            
      15 +DELAY_MAX = 3.5                                                                                                
      16 +YEARS = range(2020, 2027)  # 2020–2026 inclusive                                                               
      17  OUTPUT_FILE = "wine_reviews.csv"
      18
      19  FIELDS = [
      20      "name", "brand", "vintage", "varietal_label", "wine_type",
      21      "appellation", "designation", "rating", "review", "reviewer",
      19 -    "retail", "state", "slug", "pub_date_web", "alcohol",                                                      
      22 +    "retail", "state", "slug", "pub_date_web", "alcohol", "country",                                           
      23  ]
      24
      25
      23 -def fetch_page(page: int) -> dict:                                                                             
      26 +def fetch_page(page: int, year: int) -> dict:                                                                  
      27      body = {
      28          "requests": [{
      29              "indexName": "PROD_WINEENTHUSIAST_REVIEWS",
      27 -            "params": f"hitsPerPage={HITS_PER_PAGE}&page={page}&query=&filters=drink_type%3Awine"              
      30 +            "params": (                                                                                        
      31 +                f"hitsPerPage={HITS_PER_PAGE}&page={page}&query="                                              
      32 +                f"&filters=drink_type%3Awine%20AND%20pub_date_web_year%3A{year}"                               
      33 +            )                                                                                                  
      34          }]
      35      }
      36      response = requests.post(ALGOLIA_URL, headers=HEADERS, json=body)
     ...
      39
      40
      41  def extract(hit: dict) -> dict:
      36 -    row = {field: hit.get(field) for field in FIELDS}                                                          
      37 -    # flatten country from nested countries_menu                                                               
      42 +    row = {field: hit.get(field) for field in FIELDS if field != "country"}                                    
      43      row["country"] = hit.get("countries_menu", {}).get("lvl0")
      44      return row
      45
      46
      42 -def scrape(max_pages: int = None):                                                                             
      43 -    # fetch first page to get total page count                                                                 
      44 -    first = fetch_page(0)                                                                                      
      45 -    total_pages = first["nbPages"]                                                                             
      46 -    total_hits = first["nbHits"]                                                                               
      47 +def scrape():                                                                                                  
      48 +    all_rows = []                                                                                              
      49
      48 -    # Algolia caps accessible results at offset 1000                                                           
      49 -    accessible_pages = min(total_pages, 1000 // HITS_PER_PAGE)                                                 
      50 -    if max_pages:                                                                                              
      51 -        accessible_pages = min(accessible_pages, max_pages)                                                    
      50 +    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:                                            
      51 +        writer = csv.DictWriter(f, fieldnames=FIELDS)                                                          
      52 +        writer.writeheader()                                                                                   
      53
      53 -    print(f"Total reviews in DB: {total_hits:,}")                                                              
      54 -    print(f"Accessible via pagination: {accessible_pages * HITS_PER_PAGE:,} ({accessible_pages} pages)")       
      55 -    print(f"Saving to {OUTPUT_FILE}...")                                                                       
      54 +        for year in YEARS:                                                                                     
      55 +            print(f"\nYear {year}:")                                                                           
      56 +            first = fetch_page(0, year)                                                                        
      57 +            total_pages = first["nbPages"]                                                                     
      58 +            total_hits = first["nbHits"]                                                                       
      59
      57 -    all_rows = [extract(hit) for hit in first["hits"]]                                                         
      60 +            # Algolia caps at offset 1000                                                                      
      61 +            accessible_pages = min(total_pages, 1000 // HITS_PER_PAGE)                                         
      62 +            print(f"  {total_hits:,} reviews available, fetching {accessible_pages * HITS_PER_PAGE} ({ac       
         +cessible_pages} pages)")                                                                                       
      63
      59 -    for page in range(1, accessible_pages):                                                                    
      60 -        result = fetch_page(page)                                                                              
      61 -        all_rows.extend(extract(hit) for hit in result["hits"])                                                
      62 -        print(f"  Page {page + 1}/{accessible_pages} — {len(all_rows):,} reviews collected", end="\r")         
      63 -        time.sleep(0.1)  # be polite                                                                           
      64 +            rows = [extract(hit) for hit in first["hits"]]                                                     
      65 +            writer.writerows(rows)                                                                             
      66 +            all_rows.extend(rows)                                                                              
      67
      65 -    print(f"\nDone. Collected {len(all_rows):,} reviews.")                                                     
      68 +            for page in range(1, accessible_pages):                                                            
      69 +                delay = random.uniform(DELAY_MIN, DELAY_MAX)                                                   
      70 +                time.sleep(delay)                                                                              
      71
      67 -    fieldnames = FIELDS + ["country"]                                                                          
      68 -    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:                                            
      69 -        writer = csv.DictWriter(f, fieldnames=fieldnames)                                                      
      70 -        writer.writeheader()                                                                                   
      71 -        writer.writerows(all_rows)                                                                             
      72 +                result = fetch_page(page, year)                                                                
      73 +                rows = [extract(hit) for hit in result["hits"]]                                                
      74 +                writer.writerows(rows)                                                                         
      75 +                all_rows.extend(rows)                                                                          
      76
      73 -    print(f"Saved to {OUTPUT_FILE}")                                                                           
      77 +                print(f"  Page {page + 1}/{accessible_pages} — {len(all_rows):,} total collected", end="       
         +\r")                                                                                                           
      78
      79 +            print(f"  Year {year} done — {len(all_rows):,} total so far")                                      
      80
      81 +    print(f"\nFinished. {len(all_rows):,} reviews saved to {OUTPUT_FILE}")                                     
      82 +                                                                                                               
      83 +                                                                                                               
      84  if __name__ == "__main__":
      85      scrape()