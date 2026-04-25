# TASKS — Wine Price Prediction Project
> Mini-sprint plan. Each sprint = one focused working session (est. 1–3h).  
> Status legend: `[ ]` to do · `[x]` done · `[~]` in progress · `[!]` blocked

---

## Sprint 0 — Environment Setup
*Goal: working local + cloud dev environment, repo ready.*

- [ ] Install Python 3.13.13 (`winget install -e --id Python.Python.3.13`)
- [ ] Install VSCode extensions: **Python**, **Jupyter**, **Databricks**
- [ ] Create Databricks workspace (Community Edition or Azure)
- [ ] Generate Databricks Personal Access Token
- [ ] Configure Databricks CLI (`databricks configure --token`)
- [ ] Connect VSCode to Databricks workspace via extension
- [ ] Initialize Git repo `wines`, push to GitHub/GitLab
- [ ] Create base folder structure:
  ```
  wines/
  ├── databricks.yml
  ├── notebooks/
  ├── src/
  └── tests/
  ```
- [ ] Create and activate Python virtual environment, add `.gitignore`

---

## Sprint 1 — Data Ingestion (Bronze Layer)
*Goal: raw data loaded into Delta Bronze table on Databricks.*

- [ ] Upload raw scraped CSV/JSON to Databricks (DBFS or Unity Catalog Volume)
- [ ] Write `notebooks/01_ingest.py`:
  - read raw file with PySpark,
  - minimal schema enforcement (column names, basic types),
  - save as Delta table: `bronze.wine_reviews`
- [ ] Verify row count and spot-check sample rows with `display()`
- [ ] Commit notebook to Git

> **Data quality issue found (2026-04-26):** Some `review` fields contain embedded newline characters, causing the CSV parser to split one logical row into multiple physical rows — the second fragment then has columns shifted, producing garbage values in `alcohol`, `vintage`, `case_production`, `retail`, `rating`. ~4,858 rows affected. Fix: strip all newline characters from the source CSV with a regex pass before creating the Delta table.

---

## Sprint 2 — EDA (Exploratory Data Analysis)
*Goal: understand the data — distributions, missing values, outliers.*

- [ ] Install EDA libraries locally: `ydata-profiling`, `dtale`, `plotly`
- [ ] Write `notebooks/02_eda.py` (exploratory, not part of final pipeline):
  - missing value heatmap per column,
  - distribution of `retail` (check skewness → confirm log-transform needed),
  - distribution of `rating`,
  - top countries, wine types, varietals by count,
  - correlation matrix of numeric features,
  - price vs rating scatter plot
- [ ] Document key findings as markdown cells in the notebook
- [ ] Commit EDA notebook to Git

---

## Sprint 3 — Data Cleaning (Silver Layer)
*Goal: clean, validated data in Delta Silver table.*

- [ ] Write `notebooks/02_clean.py` + refactor logic into `src/preprocessing.py`:
  - drop exact duplicates,
  - standardize string fields (strip whitespace, fix casing),
  - parse and validate `vintage`, `date_of_review`, `pub_date_web` as date types,
  - handle mixed number/string values in `alcohol`, `bottle_size`,
  - fix newline-in-review bug: strip embedded `\n`/`\r` from `review` field in source CSV before ingestion (causes ~4,858 rows to split into malformed fragments with shifted columns),
  - unify `wine_type` and `drink_type` labels,
  - flag rows with missing `retail` (target) — these cannot be used for training,
  - save as Delta table: `silver.wine_reviews`
- [ ] Write basic unit test in `tests/test_preprocessing.py`
- [ ] Commit to Git

---

## Sprint 4 — Feature Engineering (Gold Layer)
*Goal: model-ready feature table in Delta Gold.*

- [ ] Write `notebooks/03_features.py` + refactor into `src/feature_eng.py`:
  - impute missing values: mode for categoricals, median for numerics,
  - create new features:
    - `age_at_review` = `date_of_review` year − `vintage`,
    - `log_retail` = `log(retail)` (target variable),
  - encode categoricals:
    - One-Hot: `wine_type`, `drink_type`,
    - Target Encoding: `appellation`, `varietal_label`, `designation` (high cardinality),
    - Label Encoding: `country`, `state`, `reviewer`,
  - scale numeric features: `rating`, `alcohol`, `age_at_review`,
  - save as Delta table: `gold.wine_features`
- [ ] Verify final feature matrix shape and dtypes
- [ ] Commit to Git

---

## Sprint 5 — NLP: Heuristic Baseline
*Goal: keyword-based flavor/aroma features as a fast NLP baseline.*

- [ ] Define keyword dictionaries in `src/nlp_utils.py`:
  ```python
  FEATURE_KEYWORDS = {
      "fruitiness": ["cherry", "berry", "plum", "apple", "peach", ...],
      "tannins":    ["tannic", "tannins", "grippy", "astringent", ...],
      "acidity":    ["acid", "crisp", "bright", "zesty", "tart", ...],
      "oakiness":   ["oak", "vanilla", "cedar", "toasty", "smoky", ...],
      "sweetness":  ["sweet", "honey", "sugar", "dessert", ...],
      "body":       ["full-bodied", "light", "medium", "rich", "heavy", ...],
  }
  ```
- [ ] Apply keyword scoring to `silver.wine_reviews` → add columns `kw_fruitiness`, `kw_tannins`, etc.
- [ ] Spot-check: manually verify 10–20 reviews against their scores
- [ ] Merge keyword features into `gold.wine_features`
- [ ] Commit to Git

---

## Sprint 6 — NLP: Sentence Embeddings + Feature Projection
*Goal: SentenceTransformer-based flavor features as improved NLP features.*

- [ ] Write `notebooks/04_embeddings.py`:
  - load `SentenceTransformer('all-MiniLM-L6-v2')`,
  - encode `review` column in batches (batch_size=64),
  - save embeddings as Delta table: `gold.review_embeddings` (shape: 130k × 384)
- [ ] Implement anchor embedding projection in `src/nlp_utils.py`:
  - define anchor sentences per flavor feature,
  - compute cosine similarity between each review embedding and each anchor,
  - result: columns `emb_fruitiness`, `emb_tannins`, etc. (values 0–1)
- [ ] Compare keyword scores vs embedding scores on sample — sanity check
- [ ] Merge embedding features into `gold.wine_features`
- [ ] Commit to Git

---

## Sprint 7 — ML: Baseline Model
*Goal: first working model with MLflow tracking.*

- [ ] Write `notebooks/05_train.py`:
  - load `gold.wine_features`,
  - train/test split 80/20 (stratified by `country` or `wine_type`),
  - train OLS linear regression on `log_retail`,
  - log to MLflow: params, RMSE, MAE, R² on test set,
  - save model artifact to MLflow
- [ ] Check MLflow UI in Databricks — verify experiment is visible
- [ ] Commit to Git

---

## Sprint 8 — ML: Model Comparison
*Goal: train all candidate models, compare against baseline.*

- [ ] Extend `notebooks/05_train.py` with remaining models in a loop:
  - Lasso, Ridge, Elastic-Net,
  - SVR,
  - XGBoost, LightGBM
- [ ] For each model: log hyperparameters + metrics to MLflow
- [ ] Add k-fold cross-validation (k=5) for each model
- [ ] Write `notebooks/06_evaluate.py`:
  - compare all runs in MLflow,
  - select best model by RMSE,
  - register best model in MLflow Model Registry as `wines-price-predictor`
- [ ] Commit to Git

---

## Sprint 9 — ML: Feature Importance & SHAP
*Goal: understand what drives wine prices.*

- [ ] Add SHAP analysis to `notebooks/06_evaluate.py`:
  - compute SHAP values for best model on test set,
  - plot: summary plot, beeswarm plot, top-10 features bar chart,
  - identify top positive and negative price drivers
- [ ] Export SHAP summary as image/table for final report
- [ ] Commit to Git

---

## Sprint 10 — Databricks Workflows Setup
*Goal: full pipeline runs as an automated DAG, not manual notebooks.*

- [ ] Write `databricks.yml` — define Asset Bundle with:
  - cluster configs (standard + GPU cluster for embeddings),
  - job definition with 7 tasks (matching the DAG in IDEAS.md),
  - task dependencies (tasks 3 & 4 parallel)
- [ ] Test: `databricks bundle validate`
- [ ] Deploy: `databricks bundle deploy`
- [ ] Run full pipeline end-to-end: `databricks bundle run wines_pipeline`
- [ ] Verify all Delta tables created, MLflow experiment populated
- [ ] Commit `databricks.yml` to Git

---

## Sprint 11 — Visualizations & BI Dashboard
*Goal: interactive dashboard in Tableau or Power BI sourced from Delta Gold.*

- [ ] Connect Tableau / Power BI to Databricks (via JDBC/ODBC or native connector)
- [ ] Build dashboard views:
  - [ ] Treemap: wine count by country/region
  - [ ] Map: average `rating` and `retail` by country
  - [ ] Scatter: `price` vs `rating` (colored by `wine_type`)
  - [ ] Bar: top 20 varietals by average price
  - [ ] Word cloud: most frequent words in high-rating reviews (rating ≥ 95)
  - [ ] Line chart: average price and rating trends by vintage year
- [ ] Export dashboard as PDF/screenshots for report
- [ ] Commit any export scripts to Git

---

## Sprint 12 — Report & Conclusions
*Goal: written report covering all 5 required sections.*

- [ ] Section 1: Business problem — wine pricing, market context, project goals
- [ ] Section 2: Methodology, expected outcomes, risk analysis
- [ ] Section 3: Data source (Wine Enthusiast scraping), structure, legal/quality notes
- [ ] Section 4: Step-by-step solution description (reference sprints 1–10)
- [ ] Section 5: Results discussion — what worked, what didn't, future directions
- [ ] Add visualizations and SHAP plots to report
- [ ] Proofread and finalize

---

## Sprint 13 — App (Optional, if time allows)
*Goal: working web app serving model predictions with SHAP explanations.*

- [ ] Choose stack: Streamlit (faster) or FastAPI + React (more polished)
- [ ] Load model from MLflow Model Registry via API
- [ ] Build input form for wine features
- [ ] Display predicted price + SHAP waterfall chart
- [ ] Containerize with Docker
- [ ] (Optional) Deploy to Azure Container Apps

---

## Backlog / Nice-to-have
- [ ] Hyperparameter tuning for XGBoost/LightGBM (Optuna or Hyperopt)
- [ ] Wine recommendation system (best value for price in a category)
- [ ] Automated pipeline schedule in Databricks Workflows (e.g. monthly refresh)
- [ ] Unit tests for `src/feature_eng.py` and `src/nlp_utils.py`
