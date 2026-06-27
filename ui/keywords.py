"""Keyword aroma/structure scorer — lifted verbatim from
`notebooks/pipeline/05_nlp_keywords_robust.ipynb` so the demo turns a typed
description into the same `kw_<concept>` density features the rating model was
trained on. Single source of truth for the demo's text features.
"""
import re

FEATURE_KEYWORDS = {
    # --- taste / structure ---
    "dry":        ["dry", "bone dry", "bone-dry", "dryness"],
    "acidic":     ["acid", "acidity", "acidic"],
    "tart":       ["tart", "tangy", "sour", "zesty", "zest"],
    "sweet":      ["sweet", "sweetness", "sugary", "sugar", "honeyed"],
    "caramel":    ["caramel", "butterscotch", "toffee"],
    "alcohol":    ["alcohol", "alcoholic", "boozy", "hot", "warming"],
    "strong":     ["strong", "powerful", "robust", "intense", "muscular"],
    "balanced":   ["balanced", "harmony", "harmonious"],
    # --- citrus / orchard ---
    "citrus":     ["citrus", "lemon", "lime", "grapefruit", "orange", "tangerine"],
    "apple":      ["apple", "apples"],
    "pear":       ["pear", "pears"],
    # --- red / black fruit ---
    "strawberry": ["strawberry", "strawberries"],
    "raspberry":  ["raspberry", "raspberries"],
    "cherry":     ["cherry", "cherries"],
    "red":        ["red fruit", "red fruits", "red berry", "red berries", "redcurrant", "red currant"],
    "black":      ["black fruit", "black fruits", "black currant", "blackcurrant", "cassis"],
    "blackberry": ["blackberry", "blackberries"],
    # --- tropical / stone ---
    "tropical":   ["tropical", "mango", "guava", "passion fruit", "passionfruit", "papaya"],
    "banana":     ["banana", "bananas"],
    "pineapple":  ["pineapple", "pineapples"],
    "lichi":      ["lichi", "lychee", "litchi"],
    "stone":      ["stone fruit", "stone fruits", "stonefruit", "apricot", "nectarine"],
    "peach":      ["peach", "peaches"],
    # --- earth / soil ---
    "soil":       ["soil", "potting soil", "topsoil"],
    "mineral":    ["mineral", "minerality", "wet stone", "flint", "chalk"],
    # --- oak / barrel ---
    "oak":        ["oak", "oaky", "oaked", "barrel", "barrique"],
    "coconut":    ["coconut"],
    "vanilla":    ["vanilla"],
    "smoke":      ["smoke", "smoky", "smoked", "smokiness"],
    # --- tannin / body ---
    "tannic":     ["tannic", "tannin", "tannins", "grippy", "grip"],
    "light":      ["light", "light-bodied", "delicate"],
    "heavy":      ["heavy", "full-bodied", "weighty", "dense"],
    "body":       ["body", "bodied", "mouthfeel", "texture", "medium-bodied"],
    # --- floral / herbal / green ---
    "flowers":    ["flower", "flowers", "blossom", "rose", "violet", "jasmine"],
    "floral":     ["floral"],
    "grass":      ["grass", "grassy"],
    "herbs":      ["herb", "herbs", "herbal", "thyme", "sage", "rosemary", "mint"],
    "spicy":      ["spicy", "spice", "spices"],
    "vegetables": ["vegetal", "vegetable", "vegetables"],
    "pepper":     ["pepper", "peppery", "peppercorn"],
    "bell":       ["bell pepper", "bell peppers", "capsicum"],
    "earth":      ["earth", "earthy", "mineral", "minerality", "wet stone"],
    "leather":    ["leather", "leathery"],
    "tea":        ["tea", "black tea", "green tea", "tea leaf"],
    # --- producer / style cues ---
    "family":     ["family", "family-owned", "family-run"],
    "artisan":    ["artisan", "artisanal", "handcrafted", "hand-crafted"],
    "biodynamic": ["bio", "biodynamic", "biodynamics"],
    "ecologic":   ["ecologic", "ecology", "ecological", "sustainable", "sustainably"],
    "natural":    ["natural", "organic", "naturally"],
    "summer":     ["summer", "summery"],
    "serious":    ["serious", "seriously"],
    "elegant":    ["elegant", "elegance"],
    "refreshing": ["refreshing", "refreshment"],
}


def _build_patterns(keyword_dict):
    patterns = {}
    for feature, words in keyword_dict.items():
        alt = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
        patterns[feature] = re.compile(rf"\b(?:{alt})\b", re.IGNORECASE)
    return patterns


WORD_RE = re.compile(r"\b\w+\b")
PATTERNS = _build_patterns(FEATURE_KEYWORDS)

# canonical density-feature order (matches features_keywords_robust.parquet)
KW_DENSITY_COLS = [f"kw_{c}" for c in FEATURE_KEYWORDS]


def score_text(text):
    """Return {kw_<concept>: hits-per-100-words} for one description string."""
    text = text or ""
    n_words = max(len(WORD_RE.findall(text)), 1)
    out = {}
    for feature, pat in PATTERNS.items():
        hits = len(pat.findall(text))
        out[f"kw_{feature}"] = round(100 * hits / n_words, 3)
    return out
