import os
import pandas as pd
import time

# DATA LOADING
def _load_normalized(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df


# COLUMN DETECTION HELPERS
def detect_product_column(df: pd.DataFrame) -> str | None:
    candidates = [
        "product_name", "product", "item", "item_name",
        "category", "product_category", "name", "sku",
    ]
    for c in candidates:
        if c in df.columns:
            return c

    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().sum() > len(df) * 0.5:
                continue
        except Exception:
            pass
        return col

    return None


def detect_quantity_column(df: pd.DataFrame, date_col: str | None = None) -> str | None:
    candidates = [
        "quantity", "qty", "units", "units_sold",
        "sales", "demand", "amount", "volume",
    ]
    for c in candidates:
        if c in df.columns:
            return c

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != date_col]

    return numeric_cols[0] if numeric_cols else None


def detect_date_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if "date" in col or "time" in col:
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > 0:
                    return col
            except Exception:
                continue
    return None


# CORE ANALYTICS
def top_products(csv_path: str, n: int = 3) -> list[dict]:
    if not os.path.exists(csv_path):
        return []

    try:
        df = _load_normalized(csv_path)

        date_col = detect_date_column(df)
        product_col = detect_product_column(df)
        qty_col = detect_quantity_column(df, date_col)

        if not product_col or not qty_col:
            return []

        top = (
            df.groupby(product_col)[qty_col]
            .sum()
            .sort_values(ascending=False)
            .head(n)
            .reset_index()
        )

        return top.rename(
            columns={product_col: "product_name", qty_col: "total_quantity"}
        ).to_dict(orient="records")

    except Exception:
        return []


def get_product_list(csv_path: str) -> list[str]:
    if not os.path.exists(csv_path):
        return []

    try:
        df = _load_normalized(csv_path)
        product_col = detect_product_column(df)
        if not product_col:
            return []
        return sorted(df[product_col].dropna().astype(str).unique().tolist())
    except Exception:
        return []


def get_inventory_data(csv_path: str) -> list[dict]:
    if not os.path.exists(csv_path):
        return []

    try:
        df = _load_normalized(csv_path)

        date_col = detect_date_column(df)
        product_col = detect_product_column(df)
        qty_col = detect_quantity_column(df, date_col)

        if not product_col or not qty_col:
            return []

        grouped = (
            df.groupby(product_col)[qty_col]
            .sum()
            .reset_index()
            .rename(columns={product_col: "product_name", qty_col: "predicted_demand"})
        )

        items = []
        for _, row in grouped.iterrows():
            demand = float(row["predicted_demand"])
            current_stock = round(demand * 0.7)
            recommended_stock = round(demand * 1.15)
            status = "Reorder" if current_stock < demand else "Sufficient"

            items.append({
                "product_name": str(row["product_name"]),
                "current_stock": current_stock,
                "predicted_demand": round(demand),
                "recommended_stock": recommended_stock,
                "status": status,
            })

        return items

    except Exception:
        return []


# TREND ANALYTICS
def get_demand_trend(csv_path: str, months: int = 6) -> list[dict]:
    """Monthly demand totals for last N months."""
    if not os.path.exists(csv_path):
        return []

    try:
        df = _load_normalized(csv_path)
        date_col = detect_date_column(df)
        qty_col = detect_quantity_column(df, date_col)

        if not date_col or not qty_col:
            return []

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])

        df["period"] = df[date_col].dt.to_period("M")
        grouped = df.groupby("period")[qty_col].sum().sort_index()
        last = grouped.tail(months)

        return [
            {"month": period.strftime("%b"), "demand": round(float(val))}
            for period, val in last.items()
        ]

    except Exception:
        return []


def get_category_distribution(csv_path: str, top_n: int = 3) -> list[dict]:
    """Percentage share per product/category."""
    if not os.path.exists(csv_path):
        return []

    try:
        df = _load_normalized(csv_path)
        date_col = detect_date_column(df)
        product_col = detect_product_column(df)
        qty_col = detect_quantity_column(df, date_col)

        if not product_col or not qty_col:
            return []

        totals = df.groupby(product_col)[qty_col].sum().sort_values(ascending=False)
        total_sum = totals.sum()

        if total_sum == 0:
            return []

        top = totals.head(top_n)

        result = [
            {"name": str(name), "value": round(float(val) / total_sum * 100)}
            for name, val in top.items()
        ]

        other_sum = totals.iloc[top_n:].sum()
        if other_sum > 0:
            result.append({
                "name": "Other",
                "value": round(float(other_sum) / total_sum * 100)
            })

        return result

    except Exception:
        return []



# TIME HELPERS
def _time_ago(timestamp: float) -> str:
    diff = time.time() - timestamp

    if diff < 60:
        return "just now"
    if diff < 3600:
        mins = int(diff // 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    if diff < 86400:
        hrs = int(diff // 3600)
        return f"{hrs} hour{'s' if hrs != 1 else ''} ago"

    days = int(diff // 86400)
    return f"{days} day{'s' if days != 1 else ''} ago"


def get_recent_activities(csv_path: str, model_path: str) -> list[dict]:
    """Simple activity feed based on file timestamps."""
    activities = []

    if os.path.exists(csv_path):
        activities.append({
            "action": "Dataset uploaded",
            "time": _time_ago(os.path.getmtime(csv_path)),
        })

    if os.path.exists(model_path):
        activities.append({
            "action": "AI model retrained",
            "time": _time_ago(os.path.getmtime(model_path)),
        })

    activities.append({
        "action": "Dashboard refreshed",
        "time": "just now"
    })

    return activities