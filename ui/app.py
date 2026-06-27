"""Wine demo UI — run with:  .venv\\Scripts\\streamlit run ui\\app.py

Two modes:
  * Predict Price  — "How much should this wine cost?"  (no rating input)
  * Predict Rating — "Is this wine good?"               (price IS an input)

Train the models first:  .venv\\Scripts\\python.exe ui\\train.py
"""
import streamlit as st

from predict import artifacts_exist, load_all, predict, rating_verdict

st.set_page_config(page_title="Wine Demo", page_icon="🍷", layout="centered")

EXAMPLE_DESC = (
    "Aromas of black cherry, plum and a touch of vanilla and oak. Full-bodied "
    "with firm tannins, bright acidity and a long, elegant, spicy finish."
)


@st.cache_resource
def get_models():
    return load_all()


def field_row(meta, mode):
    """Render the shared form; return the collected values dict."""
    d = meta["defaults"]
    o = meta["options"]
    r = meta["ranges"]

    c1, c2 = st.columns(2)
    with c1:
        wine_type = st.selectbox("Type of wine", o["wine_type"],
                                 index=o["wine_type"].index(d["wine_type"]))
        country = st.selectbox("Country", o["country"],
                               index=o["country"].index(d["country"]))
        varietal_label = st.selectbox("Grape variety", o["varietal_label"],
                                      index=o["varietal_label"].index(d["varietal_label"]))
    with c2:
        appellation = st.selectbox("Appellation", o["appellation"],
                                   index=o["appellation"].index(d["appellation"]))
        abv_pct = st.number_input("Alcohol by volume (%)", min_value=r["abv_min"],
                                  max_value=r["abv_max"], value=float(d["abv_pct"]), step=0.1)
        is_nv = st.checkbox("Non-vintage (NV)", value=False)
        year = st.number_input(f"Vintage year (current year is {meta['current_year']})",
                               min_value=r["year_min"], max_value=r["year_max"],
                               value=int(d["year"]), step=1, disabled=is_nv)

    form = {
        "wine_type": wine_type, "country": country, "varietal_label": varietal_label,
        "appellation": appellation, "abv_pct": abv_pct, "is_nv": is_nv, "year": year,
    }

    # Price is an input only when predicting rating (we know what it sold for).
    if mode == "rating":
        form["retail"] = st.number_input("Price — retail ($)", min_value=r["retail_min"],
                                         max_value=r["retail_max"], value=float(d["retail"]), step=1.0)

    form["description"] = st.text_area("Description (like a review)", value=EXAMPLE_DESC, height=120)
    return form


def landing():
    st.title("🍷 Wine demo")
    st.write("What would you like to predict?")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("💰 Predict Price")
        st.caption("How much should this wine cost?")
        if st.button("Choose Price", use_container_width=True):
            st.session_state.mode = "price"
            st.rerun()
    with c2:
        st.subheader("⭐ Predict Rating")
        st.caption("Is this wine good?")
        if st.button("Choose Rating", use_container_width=True):
            st.session_state.mode = "rating"
            st.rerun()


def mode_page(mode):
    price_b, rating_b, meta = get_models()

    if st.button("← Back"):
        st.session_state.mode = None
        st.rerun()

    if mode == "price":
        st.title("💰 Predict Price")
        st.caption("How much should this wine cost? (rating is **not** used)")
    else:
        st.title("⭐ Predict Rating")
        st.caption("Is this wine good? (its price **is** used)")

    form = field_row(meta, mode)

    if st.button("Predict", type="primary", use_container_width=True):
        if mode == "price":
            value = predict(price_b, meta, form, with_retail=False)
            st.success(f"### Estimated fair price: **${value:,.0f}**")
            st.caption("Predicted from type, region, variety, age, ABV and the description.")
        else:
            value = predict(rating_b, meta, form, with_retail=True)
            value = max(80.0, min(100.0, value))
            label, icon = rating_verdict(value)
            st.success(f"### Predicted rating: **{value:.1f} / 100**  {icon} {label}")
            st.caption("Predicted from the same features plus the wine's price.")


def main():
    if not artifacts_exist():
        st.error("Models not trained yet. Run:  `.venv\\Scripts\\python.exe ui\\train.py`")
        st.stop()

    st.session_state.setdefault("mode", None)
    if st.session_state.mode is None:
        landing()
    else:
        mode_page(st.session_state.mode)


if __name__ == "__main__":
    main()
