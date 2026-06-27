```
wines/
├── .data/                                      # raw + Bronze + Silver (gitignored)
│   ├── wine_reviews-2026-04-11-23-44.csv
│   ├── wine_reviews_bronze.parquet
│   └── wine_reviews_silver.parquet             # 135,192 × 24 (+ wine_id key)
│   └── wine_reviews_gold_features.parquet      # final merged feature table (to be added)
├── features/                                   
│   ├── features_basic.parquet                  # Gold feature tables (joined on wine_id)
│   ├── features_keywords.parquet               # encoded/engineered features
│   ├── features_keywords_robust.parquet        
│   ├── features_embeddings.parquet             
│   ├── features_embeddings_PCA.parquet
│   └── features_embeddings_anchored.parquet
├── notebooks/
│   ├── pipeline/                           # Bronze → Silver → Gold
│   │   ├── 01_ingest.ipynb                 # CSV → Bronze
│   │   ├── 02_cleaning.ipynb               # Bronze → Silver (+ wine_id)
│   │   ├── 03_feature_engineering.ipynb    # Silver + features → Gold
│   │   ├── 04_nlp_keywords.ipynb           # 8-axis kw_* aroma scores
│   │   ├── 05_nlp_keywords_robust.ipynb    # ~49 concept axes
│   │   ├── 06_nlp_embeddings.ipynb         # MiniLM 384-dim
│   │   ├── 07_PCA_reduction.ipynb          # PCA dimensionality reduction
│   │   └── 08_anchor_embeddings.ipynb
│   ├── exploration/                # off-pipeline EDA (loads Silver)
│   │   ├── 01_eda_basic.ipynb      # distributions, missing, correlations, profiling
│   │   └── 02_eda_adv.ipynb        # segment stats by country/variety/type/age/keywords
│   └── models/
│       ├── 01_models_retail.ipynb  # target retail models 
│       └── 02_models_rating.ipynb  # target rating models
├── webscraping/  
├── TASKS.md
├── IDEAS.md
└── requirements.txt
```
