"""Inference helpers shared by the Streamlit app (no Streamlit import here, so it
stays unit-testable). Builds one feature row from the form and runs the model.
"""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from keywords import score_text

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"


def artifacts_exist():
    return all((ARTIFACTS / f).exists()
               for f in ("price_model.joblib", "rating_model.joblib", "meta.joblib"))


def load_all():
    price = joblib.load(ARTIFACTS / "price_model.joblib")
    rating = joblib.load(ARTIFACTS / "rating_model.joblib")
    meta = joblib.load(ARTIFACTS / "meta.joblib")
    return price, rating, meta


def build_row(form, meta, with_retail):
    """form: dict of raw UI values. Returns a dict of model features."""
    nv = bool(form["is_nv"])
    row = {
        "country": form["country"],
        "wine_type": form["wine_type"],
        "varietal_label": form["varietal_label"],
        "appellation": form["appellation"],
        "alcohol": float(form["abv_pct"]) / 100.0,            # UI shows %, model uses fraction
        "age_at_review": np.nan if nv else meta["current_year"] - int(form["year"]),
        "is_nv": 1 if nv else 0,
    }
    row.update(score_text(form.get("description", "")))         # kw_<concept> densities
    if with_retail:
        row["retail"] = float(form["retail"])                  # price is a feature for rating
    return row


def predict(bundle, meta, form, with_retail):
    row = build_row(form, meta, with_retail)
    X = pd.DataFrame([row])
    X[meta["cat"]] = bundle["encoder"].transform(X[meta["cat"]])
    X = X[bundle["feature_order"]]
    return float(bundle["model"].predict(X)[0])


def rating_verdict(score):
    """Wine Enthusiast-style band for a 80-100 score."""
    s = round(score)
    if s >= 98: return "Classic", "🏆"
    if s >= 94: return "Superb", "🌟"
    if s >= 90: return "Excellent", "✅"
    if s >= 87: return "Very Good", "👍"
    if s >= 83: return "Good", "🙂"
    return "Acceptable", "😐"
