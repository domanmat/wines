"""Train the two demo models (price + rating) from Silver and save artifacts.

Run once:  .venv\\Scripts\\python.exe ui\\train.py

The demo uses only the features the UI can ask for (a deliberate simplification
of the full notebook models):
  categoricals (target-encoded): country, wine_type, varietal_label, appellation
  numerics: alcohol (fraction), age_at_review = CURRENT_YEAR - vintage, is_nv
  text: kw_<concept> densities from the description
  + retail (PRICE) is a FEATURE for the rating model, the TARGET for the price model.

Models, encoders, the feature order, and form defaults/options are pickled to
ui/artifacts/ for app.py to load.
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import TargetEncoder
import xgboost as xgb

from keywords import KW_DENSITY_COLS, score_text  # noqa: F401  (score_text re-exported for app)

ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / ".data" / "wine_reviews_silver.parquet"
KW_PARQUET = ROOT / "features" / "features_keywords_robust.parquet"
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

CURRENT_YEAR = 2026
CAT = ["country", "wine_type", "varietal_label", "appellation"]
NUM = ["alcohol", "age_at_review", "is_nv"]

# Identical to `cv_params` in notebooks/models/01_models_retail & 02_models_rating
# (the tuned final config). The demo = those models' recipe — target encoding +
# this estimator — refit on the FULL dataset (no 70/15/15 split, no early stopping),
# reading raw UI strings instead of the notebooks' ordinal-encoded columns.
XGB_PARAMS = dict(
    n_estimators=900, learning_rate=0.03, max_depth=8, subsample=0.8,
    colsample_bytree=0.8, min_child_weight=5, reg_lambda=2.0,
    eval_metric="rmse", random_state=42, n_jobs=-1,
)


def load_data():
    df = pd.read_parquet(SILVER)
    # text features: join precomputed robust keyword densities (same scorer as the demo)
    kw = pd.read_parquet(KW_PARQUET)[["wine_id"] + KW_DENSITY_COLS]
    df = df.merge(kw, on="wine_id", how="left")
    # age relative to "today" (2026), matching what the UI computes from the year field
    df["age_at_review"] = CURRENT_YEAR - df["vintage"]
    # Require a known price: retail is the PRICE model's target AND the RATING model's
    # feature, and the app always supplies a price. Drop the ~8k null-retail rows so
    # both models train on the same population. (No percentile band, unlike the
    # notebooks — the full price range is kept.)
    df = df[df["retail"].notna()].copy()
    for c in CAT:
        df[c] = df[c].fillna("none").astype(str)
    return df


def train_one(df, target, extra_features):
    """Fit TargetEncoder (on `target`) + tuned XGB; return (model, encoder, feature_order)."""
    feature_order = CAT + NUM + KW_DENSITY_COLS + extra_features
    work = df.dropna(subset=[target]).copy()
    print(f"  -> target={target}: {len(work):,} rows x {len(feature_order)} features")

    enc = TargetEncoder(target_type="continuous", random_state=42)
    X = work[feature_order].copy()
    X[CAT] = enc.fit_transform(work[CAT], work[target])

    model = xgb.XGBRegressor(**XGB_PARAMS).fit(X, work[target])
    return model, enc, feature_order


def main():
    print(f"Loading {SILVER} ...")
    df = load_data()
    print(f"  {len(df):,} rows (full dataset, no price trim)")

    print("Training PRICE model (target = retail, no rating) ...")
    price = train_one(df, target="retail", extra_features=[])  # retail is the target -> not a feature

    print("Training RATING model (target = rating, retail IS a feature) ...")
    rating = train_one(df, target="rating", extra_features=["retail"])

    # form defaults (mode / median) and dropdown options
    def opts(col):
        return sorted(df[col].astype(str).unique().tolist())

    meta = {
        "current_year": CURRENT_YEAR,
        "cat": CAT, "num": NUM, "kw": KW_DENSITY_COLS,
        "options": {c: opts(c) for c in CAT},
        "defaults": {
            "country": df["country"].mode()[0],
            "wine_type": df["wine_type"].mode()[0],
            "varietal_label": df["varietal_label"].mode()[0],
            "appellation": df["appellation"].mode()[0],
            "abv_pct": round(float(df["alcohol"].median()) * 100, 1),
            "year": int(df["vintage"].mode()[0]),
            "retail": round(float(df["retail"].median()), 0),
        },
        "ranges": {
            "abv_min": 5.0, "abv_max": 25.0,
            "year_min": 1950, "year_max": CURRENT_YEAR,
            "retail_min": 1.0, "retail_max": 500.0,
        },
    }

    joblib.dump({"model": price[0], "encoder": price[1], "feature_order": price[2]},
                ARTIFACTS / "price_model.joblib")
    joblib.dump({"model": rating[0], "encoder": rating[1], "feature_order": rating[2]},
                ARTIFACTS / "rating_model.joblib")
    joblib.dump(meta, ARTIFACTS / "meta.joblib")
    print(f"Saved artifacts -> {ARTIFACTS}")
    print(f"  price features:  {len(price[2])}  |  rating features: {len(rating[2])}")


if __name__ == "__main__":
    main()
