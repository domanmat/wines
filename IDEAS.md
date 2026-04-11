# Project Ideas & Planned Developments

## Machine Learning: Wine Price Prediction
- Build a model predicting `retail` price from wine features
- Candidate features: `rating`, `wine_type`, `varietal_label`, `country`, `state`, `appellation`, `vintage`, `alcohol`, `designation`, `reviewer`
- Compare models: linear regression (baseline), gradient boosting (XGBoost/LightGBM), etc.
- Evaluate feature importance

## Online App: Price Explainer
- Web app built on top of the ML model
- User inputs wine features → app predicts price
- Visualises which features pushed the price up or down (e.g. SHAP values)
- Show "this wine is expensive because: Napa Valley appellation (+$20), 95 points (+$15), ..."
- Stack ideas: Streamlit (quick) or FastAPI + React (more polished)
