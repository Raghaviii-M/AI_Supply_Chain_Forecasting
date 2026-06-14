from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io
import joblib
import os
import shutil
import pandas as pd
from fastapi.staticfiles import StaticFiles

from decision_engine import generate_decision
from product_ranking import (
    top_products,
    get_product_list,
    get_inventory_data,
    get_demand_trend,
    get_category_distribution,
    get_recent_activities,
)
from train_model import train_model
from reports import REPORTS, df_to_excel_bytes, df_to_pdf_bytes

app = FastAPI(
    title="AI Supply Chain Forecasting API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.onrender.com",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "demand_model.pkl")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
SALES_DATA_PATH = os.path.join(DATASET_DIR, "sales_data.csv")

os.makedirs(DATASET_DIR, exist_ok=True)


model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"Warning: failed to load existing model: {e}")
        model = None

PROJECT_ROOT = os.path.dirname(BASE_DIR)
STATIC_DIR = os.path.join(PROJECT_ROOT, "frontend")



@app.get("/api")
def home():
    return {"status": "API Running"}


@app.get("/dashboard-metrics")
def dashboard_metrics():
    product_list = get_product_list(SALES_DATA_PATH)

    return {
        "total_products": len(product_list) if product_list else 0,
        "available_stock": 12540,
        "total_orders": 1230,
        "predicted_demand": 8950,
        "demand_trend": get_demand_trend(SALES_DATA_PATH),
        "categories": get_category_distribution(SALES_DATA_PATH),
        "recent_activities": get_recent_activities(SALES_DATA_PATH, MODEL_PATH),
    }


@app.get("/forecast")
def forecast(
    month: int = Query(..., ge=1, le=12, description="Month number (1 = Jan … 12 = Dec)")
):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not trained yet. Please upload a dataset first.",
        )

    try:
        prediction = model.predict([[month]])
        predicted_demand = round(float(prediction[0]), 2)
        decision = generate_decision(predicted_demand)

        return {
            "month": month,
            "predicted_demand": predicted_demand,
            "decision": decision,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")


@app.get("/top-products")
def get_top_products(
    n: int = Query(3, ge=1, le=20, description="How many top products to return")
):
    try:
        results = top_products(SALES_DATA_PATH, n=n)
        return {"top_products": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking error: {str(e)}")


@app.get("/api/products")
def get_products():
    """Used by predict.html to populate the product dropdown."""
    try:
        return {"products": get_product_list(SALES_DATA_PATH)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product list error: {str(e)}")


@app.get("/api/inventory")
def get_inventory():
    """Used by inventory.html for the optimisation table + risk score."""
    try:
        return {"inventory": get_inventory_data(SALES_DATA_PATH)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory error: {str(e)}")


@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    global model

    try:
        # Validate file type
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files allowed")

        # Save file
        with open(SALES_DATA_PATH, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate CSV BEFORE training
        df = pd.read_csv(SALES_DATA_PATH)

        if df.empty:
            raise HTTPException(status_code=400, detail="Uploaded CSV is empty")

        # Retrain model
        score = train_model(SALES_DATA_PATH, MODEL_PATH)

        # Reload model safely
        model = joblib.load(MODEL_PATH)

        return {
            "success": True,
            "message": "Dataset uploaded and model retrained",
            "r2_score": round(score, 4),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(orient="records"),
        }

    except HTTPException:
        # Don't let our own 400s get swallowed and re-wrapped as 500s
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Reports & Analytics: real Excel/PDF generation from uploaded data ───────
@app.get("/api/reports/{report_key}/{file_format}")
def download_report(report_key: str, file_format: str):
    if report_key not in REPORTS:
        raise HTTPException(status_code=404, detail=f"Unknown report type: {report_key}")

    if file_format not in ("excel", "pdf"):
        raise HTTPException(status_code=404, detail=f"Unknown format: {file_format}")

    report = REPORTS[report_key]
    title = report["title"]
    description = report["description"]

    try:
        df = report["builder"](SALES_DATA_PATH)

        if file_format == "excel":
            data = df_to_excel_bytes(df, sheet_name=title)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
        else:
            data = df_to_pdf_bytes(title, description, df)
            media_type = "application/pdf"
            ext = "pdf"

        filename = f"{title.replace(' ', '_')}.{ext}"
        return StreamingResponse(
            io.BytesIO(data),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")


if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")