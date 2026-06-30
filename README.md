# Vintelligence — Wine Price & Rating Prediction

A end-to-end data and machine-learning project that scrapes professional wine
reviews, cleans them into an analytics-ready dataset, engineers structured and
text-derived features, and trains gradient-boosted models to predict two
targets from a wine's attributes and its tasting note:

- **`retail`** — the bottle's price in USD (a producer-facing question: *what should this wine cost?*)
- **`rating`** — the reviewer's 80–100 quality score (a consumer-facing question: *is this wine any good?*)

The project is built and validated locally with pandas; a small Streamlit app
demonstrates the trained models interactively.

---

## Architecture overview

The data flows through a **medallion architecture** (Bronze → Silver → Gold),
each stage persisted as Parquet so every step is reproducible and cheap to
re-run:

- **Bronze** — the raw scrape, loaded verbatim as typed-as-string Parquet.
- **Silver** — one cleaned, validated, de-duplicated row per review, with
  correct dtypes and a stable `wine_id` key. This is the single source of truth
  for everything downstream.
- **Gold** — model-ready feature tables derived from Silver. Each feature family
  (structured, keywords, embeddings, …) is its own Parquet file, all joined on
  `wine_id` in the modelling notebooks. Only deterministic, leakage-free
  transforms are persisted here; target encoding and scaling are deliberately
  left to model-training time and fit on the training split only.

Work is organised as Jupyter notebooks split by role — `pipeline/` (the
Bronze → Silver → Gold ETL), `exploration/` (off-pipeline EDA), and `models/`
(the predictive modelling) — plus a standalone `webscraping/` scraper and a
`ui/` Streamlit demo.

### Repository layout

```
wines/
├── webscraping/                          # Algolia API scraper (data acquisition)
│   ├── webscrapping.py
│   └── algolia-query-example.json
├── .data/                                # raw + Bronze + Silver (gitignored)
│   ├── wine_reviews-2026-04-11-23-44.csv     # raw scrape (135,211 rows)
│   ├── wine_reviews_bronze.parquet           # Bronze  (135,211 × 22)
│   ├── wine_reviews_silver.parquet           # Silver  (135,192 × 24, + wine_id)
│   └── wine_reviews_silver_profile.html      # ydata-profiling report
├── features/                             # Gold feature tables (joined on wine_id)
│   ├── features_basic.parquet                # encoded structured features (135,192 × 15)
│   ├── features_keywords.parquet             # 8-axis aroma keyword scores
│   ├── features_keywords_robust.parquet      # ~49 fine-grained concept axes
│   ├── features_embeddings.parquet           # MiniLM-L6-v2, 384-dim
│   ├── features_embeddings_PCA.parquet       # 20 principal components
│   └── features_embeddings_anchored.parquet  # 22 concept cosine-similarities
├── notebooks/
│   ├── pipeline/                         # Bronze → Silver → Gold
│   │   ├── 01_ingest.ipynb                   # CSV → Bronze
│   │   ├── 02_cleaning.ipynb                 # Bronze → Silver (+ wine_id)
│   │   ├── 03_feature_engineering.ipynb      # Silver → features_basic
│   │   ├── 04_nlp_keywords.ipynb             # 8-axis keyword densities
│   │   ├── 05_nlp_keywords_robust.ipynb      # ~49 concept densities
│   │   ├── 06_nlp_embeddings.ipynb           # sentence embeddings
│   │   ├── 07_PCA_reduction.ipynb            # embeddings → 20 PCs
│   │   └── 08_anchor_embeddings.ipynb        # embeddings → anchor features
│   ├── exploration/                      # off-pipeline EDA (loads Silver)
│   │   ├── 01_eda_basic.ipynb                # distributions, missingness, correlations
│   │   └── 02_eda_adv.ipynb                  # segment statistics
│   └── models/
│       ├── 01_models_retail.ipynb            # target = retail (price)
│       └── 02_models_rating.ipynb            # target = rating (score)
├── ui/                                   # local Streamlit demo
│   ├── app.py                                # two-mode UI (price / rating)
│   ├── train.py                              # trains + pickles demo models
│   ├── predict.py                            # inference helpers (no Streamlit)
│   ├── keywords.py                           # keyword scorer for the description
│   └── artifacts/                            # pickled models + metadata (generated)
├── requirements.txt
└── README.md
```

---

## Tools & technologies

| Area | Tooling |
|---|---|
| Language / environment | Python 3, virtual environment (`.venv`), VS Code + Jupyter |
| Data wrangling | pandas 3.0, Parquet (via pyarrow) |
| Acquisition | `requests` against the site's Algolia Search API |
| EDA & profiling | ydata-profiling, plotly, matplotlib, itables |
| Encoding | scikit-learn 1.8 `TargetEncoder`, ordinal label maps |
| Modelling | XGBoost 3.2 (gradient-boosted trees), 5-fold cross-validation |
| NLP | sentence-transformers (`all-MiniLM-L6-v2`, CPU torch), regex keyword scoring |
| Interpretation | XGBoost gain importance, exact tree SHAP (`pred_contribs`) |
| Demo app | Streamlit, joblib for artifact persistence |
| Versioning | Git |

Visualizations are produced in the notebooks (plotly/matplotlib); no external BI
tool is used. The demo runs locally only — there is no cloud deployment.

---

## Data acquisition — `webscraping/`

`webscrapping.py` collects professional reviews from Wine Enthusiast directly
through the **Algolia Search API** that powers the site's review index — no
browser automation, no HTML parsing. Working against the JSON API with
`requests` is far faster and more reliable than scraping rendered pages.

Algolia caps any single query at 1,000 results, so the scraper **recursively
splits** the query space along a facet hierarchy
(`year → country → wine_type → varietal_label → state → vintage → designation`)
until every segment fits under the cap. To keep the number of requests sane,
small facet values (below a threshold) are **batched** into OR-filtered queries
rather than fetched individually. Requests are spaced with a random 1.5–3.5 s
delay, results are written incrementally to a timestamped CSV, and the run warns
loudly whenever a segment still hits the 1,000-result cap.

The result is **135,211 reviews** spanning vintages 2020–2026 (out of ~422,000
in the full index), with identity, characteristic, geography, review and date
fields per record.

---

## Pipeline — `notebooks/pipeline/`

### 01 · Ingest (Bronze)
Reads the raw scrape CSV and writes it unchanged as
`wine_reviews_bronze.parquet` (135,211 × 22, all columns as strings). This
isolates the immutable raw layer from any cleaning logic.

### 02 · Cleaning (Silver)
Casts every column to its proper type while tracking failures in `_cast` /
`_error` helper columns, then applies per-column cleaning:

- **alcohol** — fixes mis-scaled unit values;
- **bottle_size** — parses mixed formats (e.g. `750ml`, `0.75L`) to millilitres;
- **vintage** — range-validates and adds an `is_nv` (non-vintage) flag;
- **retail / case_production** — zeros → null; implausible production volumes
  (> 1,000,000 cases) treated as parse errors → null;
- **rating** — rows below 80 are dropped (different scoring scale);
- **country** — `United States` merged into `USA`;
- **designation** — missing → `"none"` (absence is informative — undesignated
  wines are materially cheaper, so missingness is encoded as a real category).

Exact-row duplicates and repeated `(slug, date_of_review)` pairs are removed,
and a stable **`wine_id`** primary key is added (the raw `slug` is not unique).
Output: **`wine_reviews_silver.parquet`, 135,192 × 24** — the clean source of
truth for all downstream work.

### 03 · Feature engineering (Gold — `features_basic`)
Builds the structured model matrix: a leakage-free **ordinal label map** for the
categoricals (NaN kept as its own code), `log_retail` (the price target is
strongly right-skewed), `age_at_review` (review year − vintage; null for NV
wines), and pass-through numerics. Saved as `features_basic.parquet`
(135,192 × 15), keyed by `wine_id`. Target encoding and scaling are intentionally
**not** done here — they are fit on the training split inside the model notebooks
to avoid leakage.

### 04–05 · Keyword features (heuristic NLP)
A fast, fully interpretable text baseline. Each review is scored against curated
descriptor dictionaries, producing per-axis raw counts (`kw_<axis>_count`) and
length-normalised densities (`kw_<axis>`, hits per 100 words):

- **04** — 8 broad axes (fruity, tannic, acidic, oaky, sweet, body, earthy, floral) → `features_keywords.parquet`;
- **05** — a granular variant with ~49 fine-grained concepts (individual fruits, oak/barrel markers, structure, producer/style cues) → `features_keywords_robust.parquet`.

Each concept is a single case-insensitive, word-boundaried regex (so
`full-bodied` stays intact and `oak` doesn't match `croak`).

### 06 · Sentence embeddings
Encodes every review into a 384-dimensional semantic vector with a pre-trained
**SentenceTransformer (`all-MiniLM-L6-v2`)**, stored as float32 columns
`emb_000…emb_383` in `features_embeddings.parquet`. This is the expensive,
**compute-once** artifact; everything downstream reads the cache instead of
re-encoding.

### 07 · PCA reduction
Compresses the 384 raw dimensions to **20 principal components**
(`features_embeddings_PCA.parquet`). PCA is unsupervised — it never sees the
target — so fitting on all rows is leakage-free and safe to cache as a Gold
module.

### 08 · Anchor projection
The interpretable counterpart to raw embeddings: each of 22 named wine concepts
is described by several anchor sentences, encoded with the same model and
averaged into a unit **concept centroid**; every review's cached embedding is
then cosine-projected onto those centroids to give 22 `anchor_*` features
(`features_embeddings_anchored.parquet`) — the semantic analogue of the lexical
keyword scores.

---

## Exploration — `notebooks/exploration/`

- **01 · Basic EDA** — missing-value heatmap, distributions of `retail`
  (confirming the log transform) and `rating`, top categorical values, numeric
  correlations, a price-vs-rating scatter, and a full ydata-profiling report.
- **02 · Advanced EDA** — segment statistics: mean/median price and rating broken
  down by country, variety, wine type, bottle age, and keyword presence.

Key takeaways that shaped modelling: price is heavily right-skewed (train on
`log_retail`); `rating` is narrow and publication-biased (80–100, centred ~90);
the `rating`↔`retail` link is the dominant numeric signal; and most predictive
power lives in the high-cardinality categoricals and the review text.

---

## Modelling — `notebooks/models/`

Both notebooks share one recipe and differ only in target. The flow is
**baseline → target encoding → tuning → final cross-validation**, each run with
and without the strongest opposite-target predictor, so the contribution of each
choice is isolated.

**Methods finally applied:**

- **Estimator** — XGBoost gradient-boosted trees.
- **Split** — 70 / 15 / 15 train / validation / test. The test set is touched
  only for final metrics; the validation set drives early stopping. The split is
  shared across feature blocks so differences come from the features, not the rows.
- **Encoding** — high-cardinality categoricals (`appellation`, `varietal_label`,
  `country`, …) are **target-encoded** with `sklearn.TargetEncoder`, **fit on the
  training split only**. This replaced arbitrary ordinal integers and was the
  single biggest accuracy lift.
- **Tuning** — hand-tuned XGBoost hyperparameters, early-stopped on the
  validation set.
- **Validation** — 5-fold cross-validation for a variance estimate, with the
  target encoder re-fit inside every fold (no leakage).
- **Feature A/B** — every run compares `basic` against `basic + keywords`,
  `basic + emb-PCA`, and `basic + anchors`.
- **Interpretation** — XGBoost gain importance plus exact tree SHAP (signed,
  in dollars for price and in rating points for the score).

### Results

Both targets are compared the same two ways: an **A/B of feature blocks** at the
baseline model (which dataset wins), and the **stage-by-stage development** of the
chosen block (baseline → target encoding → tuning → 5-fold CV).

**Price model (`01_models_retail`).** Feature-block A/B at baseline (default XGB,
ordinal encoding, `rating` included) — no text block beats plain `basic`, so
`basic` is carried forward:

| feature block | test R² |
|---|---|
| **basic** | **0.653** |
| basic + keywords | 0.633 |
| basic + emb-PCA | 0.631 |
| basic + anchors | 0.632 |
| basic + full embeddings | 0.599 |

Development of `basic`, with and without `rating` (a reviewer score is usually
unavailable when pricing, so the *without-`rating`* column is the realistic case):

| stage | with `rating` | without `rating` |
|---|---|---|
| Baseline (default XGB, ordinal encoding) | 0.653 | 0.598 |
| + Target encoding | 0.683 | — |
| + Target encoding + hyperparameter tuning | 0.703 | 0.661 |
| 5-fold CV (final, with `rating`) | **0.709 ± 0.005** | — |

Final: R² 0.703 with `rating` (RMSE 9.63, MAE 6.94) and **0.661 without it**. Top
SHAP drivers (signed dollars): `appellation` (+$5.4), `rating` (+$3.7) and
`company` (+$3.5) push price up; higher `case_production` pushes it down (−$2.6).

**Rating model (`02_models_rating`).** Rows restricted to the 2nd–90th retail
percentile (~$11–$80). Feature-block A/B at baseline (default XGB, ordinal
encoding, `retail` included) — keywords clearly help, so `basic + keywords` is
carried forward (full embeddings edge it here but are 396-dim and noisy, so they
are dropped):

| feature block | test R² |
|---|---|
| basic | 0.452 |
| **basic + keywords** | **0.545** |
| basic + emb-PCA | 0.478 |
| basic + anchors | 0.459 |
| basic + full embeddings | 0.564 |

Development of `basic + keywords`, with and without `retail` (how much the score
leans on price):

| stage | with `retail` | without `retail` |
|---|---|---|
| Baseline (default XGB, ordinal encoding) | 0.545 | 0.481 |
| + Target encoding | 0.577 | — |
| + Target encoding + hyperparameter tuning | 0.603 | 0.569 |
| 5-fold CV (final, with `retail`) | **0.606 ± 0.005** | — |

Final: R² 0.603 (RMSE 1.56, MAE 1.22). The keyword block carries ~68% of gain
importance (spread thinly across many descriptors), while the largest single SHAP
movers stay structured (`retail` +0.78, `company` +0.42, `appellation` +0.24 points).

**Headline finding:** review text helps predict **`rating` but not `retail`** — a
clean asymmetry. Prose tracks the score (same author writes note and score);
price tracks region, producer and tier. Cheap lexical keywords beat both
embedding-based blocks for rating, and no text block helps price.

---

## Demo — `ui/`

A self-contained Streamlit app that runs the trained models interactively, in
two modes:

- **Predict Price** — *how much should this wine cost?* (rating is not an input);
- **Predict Rating** — *is this wine good?* (price **is** an input).

`train.py` trains the two demo models from Silver and the robust keyword
features, using the same tuned configuration and target encoding as the model
notebooks but **refit on the full dataset** and reading raw form strings instead
of pre-encoded columns; the fitted models, encoders, feature order and form
metadata are pickled to `ui/artifacts/`. `predict.py` holds Streamlit-free
inference helpers (so they stay unit-testable), `keywords.py` scores the
free-text description into keyword densities, and `app.py` renders the shared
form and results.

```bash
# 1. install dependencies
pip install -r requirements.txt

# 2. train the demo models (writes ui/artifacts/)
python ui/train.py

# 3. launch the app
streamlit run ui/app.py
```

---

## Getting started

The pipeline runs top to bottom from the raw CSV:

1. Create and activate the virtual environment, then `pip install -r requirements.txt`.
2. (Optional) re-scrape with `python webscraping/webscrapping.py`, or use the CSV already in `.data/`.
3. Run the `notebooks/pipeline/` notebooks in order (01 → 08) to rebuild Bronze, Silver and the Gold feature tables.
4. Explore with `notebooks/exploration/`, then train and evaluate in `notebooks/models/`.
5. Try the interactive demo in `ui/`.

> Note: the embedding step (06) takes a few minutes on CPU but is cached; the
> downstream PCA, anchor and modelling steps are fast.
