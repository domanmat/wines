# Project Ideas & Planned Developments

## Databricks Architecture

The project is built on Databricks as the primary data and ML platform, with VSCode as the local development environment.

**Development workflow:**
- Code is written and version-controlled locally in VSCode (GitHub/GitLab),
- Databricks Extension for VSCode enables remote execution on Databricks clusters,
- Project is packaged as a **Databricks Asset Bundle (DAB)** — the full pipeline (notebooks, job config, cluster config) lives in Git and deploys with a single command (`databricks bundle deploy`).

**Delta Lake layered storage (Medallion Architecture):**
- `Bronze` — raw scraped data, stored as-is (CSV/JSON), no transformations,
- `Silver` — cleaned, validated, deduplicated data with unified data types,
- `Gold` — model-ready feature tables (encoded, scaled, with NLP embeddings).

**Databricks Workflows (pipeline orchestration):**

The pipeline is defined as a DAG of jobs. Tasks 3 and 4 run in parallel as they are independent:

```
[1. Ingest → Bronze]
        ↓
[2. Clean → Silver]
        ↓
  ┌─────┴──────┐
[3. Feature  [4. NLP
  Eng. →       Embeddings →    ← GPU cluster
  Gold]         Gold]
  └─────┬──────┘
        ↓
[5. Train Models]   → MLflow experiment tracking
        ↓
[6. Evaluate & Register]  → MLflow Model Registry
        ↓
[7. BI Export / Dashboard refresh]
```

**Project structure (local repository):**
```
wines/
├── databricks.yml              # bundle config: clusters, jobs, environments
├── notebooks/
│   ├── 01_ingest.py
│   ├── 02_clean.py
│   ├── 03_features.py
│   ├── 04_embeddings.py
│   ├── 05_train.py
│   └── 06_evaluate.py
├── src/
│   ├── preprocessing.py        # shared logic as reusable modules
│   ├── feature_eng.py
│   └── nlp_utils.py
└── tests/
    └── test_preprocessing.py
```

**Tool responsibilities:**

| Task | Tool |
|---|---|
| Code writing & editing | VSCode |
| Version control | VSCode + GitHub/GitLab |
| Remote code execution (Spark) | Databricks cluster (via VSCode extension) |
| Pipeline orchestration | Databricks Workflows |
| ML experiment tracking | MLflow (built into Databricks) |
| Delta table browsing | Databricks UI (Catalog) |
| App deployment (optional) | Azure cloud |

---

## Data Exploration and Analysis

- Create **data preprocessing pipeline**:
    - data extraction, data cleaning (data formats, errors),
    - handling mixed number/string values,
    - merging labels where applicable.
- Create **feature engineering pipeline**:
    - data encoding for ML model,
    - data scaling and standardization,
    - missing values handling with chosen method (e.g. mode for string or mean for numeric; or dropping),
    - new feature creation, if applicable.
- Candidate features from the dataset: `rating` *(expected to be one of the strongest predictors of price)*, `wine_type`, `varietal_label`, `country`, `state`, `appellation`, `vintage`, `alcohol`, `designation`, `reviewer`
- Target variable is `retail` — a bottle's price in store.
- Extra task for feature engineering — analyze review body with NLP and pre-trained models:
    - Analyze review bodies to extract interpretable flavor/aroma features (e.g. fruitiness, tannins, acidity, oakiness) as additional numeric features for the ML model,
    - Create a baseline heuristic model: define keywords and calculate their weight (frequency) in the text,
    - Create sentence embeddings for the review bodies using a pre-trained **SentenceTransformer** model, then calculate feature embeddings using a regressor for each target flavor/aroma feature based on sentence embeddings. Alternatively, use direct cosine similarity against feature anchor embeddings (no labeled data required).

---

## Machine Learning: Wine Price Prediction

- Build a model predicting `retail` price from wine features. Candidate models:
    - Linear regression (OLS = baseline, likely on log-transformed target due to right-skewed price distribution),
    - More advanced linear models (Lasso, Ridge, Elastic-Net),
    - SVM regression (SVR),
    - Gradient boosting (XGBoost / LightGBM).
- Model validation strategy: train/test split (e.g. 80/20) with k-fold cross-validation to ensure generalization.
- All experiments tracked automatically in **MLflow** (parameters, metrics, artifacts); best model registered in MLflow Model Registry.
- Compare model performance vs baseline model.
- Evaluate feature importance — use SHAP values both for model interpretation and as a standalone analysis of which features drive wine prices.

---

## Container/Online App

- Additional task - if time allows. General ideas:
    - Container app built on top of the ML model served from MLflow Model Registry,
    - App predicts price of an unknown wine based on user-provided feature inputs,
    - Visualize which features pushed the price up or down (SHAP values),
    - Stack ideas: Streamlit (quick) or FastAPI + React (more polished),
    - If time allows, deploy in Azure cloud (Azure Container Apps or Azure App Service).

---

## Visualizations & Reporting + Concluding Presentation

- Apply a BI application to create interactive visualizations (Tableau or Power BI), sourced from Delta Gold tables:
    - Word frequency analysis of the reviews (e.g. word cloud) — analyze frequency and presence of descriptors in high-rating reviews,
    - Statistics on wine count vs rating, and price vs rating,
    - Map of countries of interest with average statistics,
    - Treemap chart with count of wines by country/region.
- Describe example scenarios (e.g. best cheap wine with predicted price),
- Search for trend changes between years,
- Keep in mind what the model does not assess: the bottle (shape, weight, color) and the label (text, graphics, logo).
- Summarize findings and draw final conclusions.