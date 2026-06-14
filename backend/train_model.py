import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import joblib


def detect_date_column(df):
    for col in df.columns:
        if "date" in col or "time" in col:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                if df[col].notna().sum() > 0:
                    return col
            except Exception:
                continue
    return None


def detect_target_column(df, date_col):
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
    numeric_cols = [c for c in numeric_cols if c != date_col]

    if len(numeric_cols) == 0:
        return None

    return numeric_cols[0]


def train_model(csv_path, model_path="demand_model.pkl"):
    """
    FIX 1: model_path is now a parameter (absolute path passed from app.py)
           instead of a hardcoded relative "demand_model.pkl".

    FIX 2: trained only on "month" (single feature), to match the
           /forecast endpoint which only supplies model.predict([[month]]).
           Training on month/day/weekday but predicting with only month
           caused a feature-count mismatch error before.
    """
    df = pd.read_csv(csv_path)

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    date_col = detect_date_column(df)
    target_col = detect_target_column(df, date_col)

    if not date_col or not target_col:
        raise ValueError(f"Could not detect columns. Found: {list(df.columns)}")

    df = df.dropna(subset=[date_col, target_col])

    if len(df) < 5:
        raise ValueError("Dataset must contain at least 5 valid rows")

    df["month"] = df[date_col].dt.month

    X = df[["month"]]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    score = r2_score(y_test, y_pred)

    joblib.dump(model, model_path)

    return score