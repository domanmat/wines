# notebooks

Jupyter notebooks for the Wine Price Prediction project, organized by role in the
Bronze → Silver → Gold medallion pipeline. All notebooks run in the project `.venv`
(Jupyter kernel "Python (wines-venv)").

## Layout

- `pipeline/` — the data pipeline: ingest → clean (Silver) → feature engineering / NLP (Gold). Run these in numeric order.
- `exploration/` — off-pipeline EDA (loads Silver, produces no pipeline artifacts).
- `models/` — modelling notebooks (baseline vs. feature-augmented comparisons).

The Algolia scraper lives outside this folder, at the project root in `webscraping/`.

## `pipeline/` — Bronze → Silver → Gold

| Notebook | Input → Output |
|---|---|
| `01_ingest.ipynb` | source CSV → `.data/wine_reviews_bronze.parquet` |
| `02_cleaning.ipynb` | Bronze → `.data/wine_reviews_silver.parquet` (135,192 × 24, + stable `wine_id` key) |
| `03_feature_engineering.ipynb` | Silver → `features/features_basic.parquet` (leakage-safe encodings, `log_retail`, `age_at_review`) |
| `04_nlp_keywords.ipynb` | Silver → `features/features_keywords.parquet` (8-axis aroma scores) |
| `05_nlp_keywords_robust.ipynb` | Silver → `features/features_keywords_robust.parquet` (~49 concept axes) |
| `06_nlp_embeddings.ipynb` | Silver → `features/features_embeddings.parquet` (MiniLM-L6-v2, 384-dim) |
| `07_PCA_reduction.ipynb` | embeddings → `features/features_embeddings_PCA.parquet` (`pca_00..pca_19`) |
| `08_anchor_embeddings.ipynb` | embeddings → `features/features_embeddings_anchored.parquet` (22 `anchor_*` cosine cols) |

All Gold `features_*` tables are keyed on `wine_id` and joined in the model notebooks.
A final merged Gold table, `features/wine_reviews_gold_features.parquet`, will collect
the selected feature blocks into one model-ready file (to be added).

## `exploration/` — EDA

- `01_eda_basic.ipynb` — distributions, missing-value heatmap, top categoricals, correlations, price-vs-rating, ydata-profiling (pandas-3.0 workaround).
- `02_eda_adv.ipynb` — segment statistics (mean/median price & rating) by country / variety / wine_type / `age_at_review` / robust-keyword presence.

## `models/`

- `01_models_retail.ipynb` — target `retail`. Default-XGB baseline + tuned pipeline (70/15/15 train/val/test, early-stopped XGBoost, `TargetEncoder` on categoricals). Tuned **R² ≈ 0.700** (CV 0.706 ± 0.005). Compares base / +kw / +emb-PCA / +anchors.
- `02_models_rating.ipynb` — sibling, target `rating` (retail→feature). Still on the older default-XGB / 80/20 setup (upgrade pending).

## Data locations

- `.data/` — raw + Bronze + Silver (gitignored).
- `features/` — Gold feature tables.

See the project-root `CLAUDE.md`, `TASKS.md`, and `IDEAS.md` for full status and roadmap.
