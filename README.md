# Wine demo UI

A small local Streamlit app with two modes:

- **💰 Predict Price** — *How much should this wine cost?* (rating is **not** an input)
- **⭐ Predict Rating** — *Is this wine good?* (the wine's **price is** an input)

Both modes share the same form: type of wine, country, appellation, grape variety,
alcohol by volume, vintage year (with a **Non-vintage** option — age is computed
against the current year, **2026**), and a free-text **description** (scored into the
same keyword features the rating model uses). Each field is pre-filled with the most
frequent / median value and is easy to change.

## Run it

From the project root, with the project venv:

```powershell
# 1) one-time: install Streamlit
.venv\Scripts\python.exe -m pip install -r ui\requirements.txt

# 2) one-time: train the two models -> ui\artifacts\  (~1-2 min)
.venv\Scripts\python.exe ui\train.py

# 3) launch the UI (opens http://localhost:8501)
.venv\Scripts\streamlit run ui\app.py
```

## How it works

- `train.py` trains two XGBoost models from `.data/wine_reviews_silver.parquet`
  (+ `features/features_keywords_robust.parquet`) using only the features the UI can
  provide. Categoricals are target-encoded; the description is scored into
  `kw_<concept>` densities. `retail` (Price) is the **target** for the price model and
  a **feature** for the rating model. Artifacts are pickled to `ui/artifacts/`.
- `app.py` loads the artifacts, renders the mode picker + form, and predicts.
- `keywords.py` is the description scorer (lifted from
  `notebooks/pipeline/05_nlp_keywords_robust.ipynb`).
- `predict.py` builds the feature row and runs the model (no Streamlit dependency).

> Demo simplification: the UI models use only UI-available features (so they omit
> `bottle_size`, `case_production`, `state`, `company` that the notebook models use),
> and `age` is measured against 2026 rather than the original review date.
