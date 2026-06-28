from fastapi import FastAPI
import pandas as pd
import joblib
from pydantic import BaseModel
import numpy as np

app = FastAPI(title="DBKlik Price Optimization API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# LOAD DATA
# =========================

df = pd.read_excel("data/dataset_feature_engineering.xlsx")

# =========================
# LOAD MODEL
# =========================

model = joblib.load("models/rf_demand_model_v2.pkl")

# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "DBKlik API Ready"
    }

@app.get("/dashboard")
def dashboard():

    total_produk = int(
        df["Nama_DB"].nunique()
    )

    total_omset = float(
        df["Omset_DB"].sum()
    )

    total_profit = float(
        (
            df["Margin_Rp"]
            *
            df["Qty_DB"]
        ).sum()
    )

    total_kompetitor = int(
        df["Jumlah_Kompetitor"].sum()
    )

    return {

        "total_produk":
            total_produk,

        "total_omset":
            total_omset,

        "total_profit":
            total_profit,

        "total_kompetitor":
            total_kompetitor

    }


@app.get("/products")
def get_products():

    products = (
        df["Nama_DB"]
        .dropna()
        .unique()
        .tolist()
    )

    products = sorted(products)

    return products

# =========================
# PRODUCT DETAIL
# =========================

@app.get("/product/{product_name}")
def get_product(product_name: str):

    produk = df[
        df["Nama_DB"] == product_name
    ]

    if len(produk) == 0:

        return {
            "error": "Produk tidak ditemukan"
        }

    row = produk.iloc[0]

    return {

        "Nama_Produk":
            row["Nama_DB"],

        "Brand":
            row["Brand_DB"],

        "Harga":
            float(row["Harga_DB"]),

        "HPP":
            float(row["HPP (Latest)"]),

        "Qty":
            float(row["Qty_DB"]),

        "Margin":
            float(row["Margin_Pct"]),

        "Kompetitor":
            int(row["Jumlah_Kompetitor"])

    }

# =========================
# REQUEST BODY
# =========================

class SimulateRequest(BaseModel):
    product_name: str
    new_price: float

class OptimizeRequest(BaseModel):
    product_name: str
# =========================
# FEATURE COLUMNS
# =========================

FEATURE_COLUMNS = [
    "Harga_DB",
    "HPP (Latest)",
    "Margin_Rp",
    "Margin_Pct",
    "Min_Harga_Komp",
    "Avg_Harga_Komp",
    "Max_Harga_Komp",
    "Avg_Qty_Komp",
    "Max_Qty_Komp",
    "Jumlah_Kompetitor",
    "Avg_Similarity",
    "Price_Gap_Min",
    "Price_Gap_Avg",
    "Price_Ratio",
    "Price_Change",
    "Price_Change_Pct",
    "Harga_Lag1",
    "Avg_Harga_Komp_Lag1",
    "Rolling_Harga_3",
    "Month",
    "Day",
    "Weekday"
]

# =========================
# SIMULATE PRICE
# =========================

@app.post("/simulate")
def simulate_price(req: SimulateRequest):

    produk = df[df["Nama_DB"] == req.product_name]

    if len(produk) == 0:
        return {"error": "Produk tidak ditemukan"}

    row = produk.iloc[0].copy()

    old_price = float(row["Harga_DB"])
    new_price = req.new_price
    hpp = float(row["HPP (Latest)"])

    if new_price <= 0:
        return {
            "error": "Harga harus lebih dari 0"
        }

    row["Harga_DB"] = new_price
    row["Margin_Rp"] = new_price - hpp
    row["Margin_Pct"] = ((new_price - hpp) / new_price) * 100

    row["Price_Gap_Min"] = new_price - row["Min_Harga_Komp"]
    row["Price_Gap_Avg"] = new_price - row["Avg_Harga_Komp"]
    row["Price_Ratio"] = new_price / row["Avg_Harga_Komp"]

    row["Price_Change"] = new_price - row["Harga_Lag1"]
    if row["Harga_Lag1"] == 0:
        row["Price_Change_Pct"] = 0

    else:

        row["Price_Change_Pct"] = (
            row["Price_Change"]
            / row["Harga_Lag1"]
        )

    row["Rolling_Harga_3"] = (row["Rolling_Harga_3"]- old_price/3+ new_price/3)

    X_pred = row[FEATURE_COLUMNS].to_frame().T

    pred_log = model.predict(X_pred)[0]
    pred_qty = np.expm1(pred_log)

    revenue = new_price * pred_qty
    profit = (new_price - hpp) * pred_qty

    return {
        "product_name": req.product_name,
        "old_price": round(old_price, 2),
        "new_price": round(new_price, 2),
        "predicted_qty": round(pred_qty, 2),
        "predicted_revenue": round(revenue, 2),
        "predicted_profit": round(profit, 2),
        "predicted_margin_pct": round(row["Margin_Pct"], 2)
    }

@app.post("/optimize")
def optimize_price(req: OptimizeRequest):

    produk = df[df["Nama_DB"] == req.product_name]

    if len(produk) == 0:
        return {"error": "Produk tidak ditemukan"}

    row = produk.iloc[0].copy()

    old_price = float(row["Harga_DB"])
    hpp = float(row["HPP (Latest)"])

    best_price = old_price
    curve = []
    best_profit = -999999999
    best_qty = 0

    for factor in np.arange(0.8, 1.21, 0.02):

        test_price = old_price * factor

        temp = row.copy()

        temp = temp.fillna(0)

        temp["Harga_DB"] = test_price

        temp["Margin_Rp"] = test_price - hpp

        if test_price == 0:

            temp["Margin_Pct"] = 0

        else:

            temp["Margin_Pct"] = (
                (test_price - hpp)
                / test_price
            ) * 100

        temp["Price_Gap_Min"] = (test_price- temp["Min_Harga_Komp"])
        temp["Price_Gap_Avg"] = (test_price- temp["Avg_Harga_Komp"])

        if temp["Avg_Harga_Komp"] == 0:

            temp["Price_Ratio"] = 0

        else:

            temp["Price_Ratio"] = (test_price/ temp["Avg_Harga_Komp"])

        harga_lag = temp["Harga_Lag1"]

        temp["Price_Change"] = (test_price- harga_lag)

        if harga_lag == 0:

            temp["Price_Change_Pct"] = 0

        else:

            temp["Price_Change_Pct"] = (temp["Price_Change"]/ harga_lag)

        temp["Rolling_Harga_3"] = (temp["Rolling_Harga_3"]- old_price / 3+ test_price / 3)

        X_pred = temp[FEATURE_COLUMNS].to_frame().T
        X_pred = X_pred.replace(
            [np.inf, -np.inf],
            0
        )
        X_pred = X_pred.fillna(0)
        pred_log = model.predict(
            X_pred
        )[0]

        pred_qty = np.expm1(pred_log)
        profit = ((test_price - hpp)* pred_qty)
        curve.append({

            "price":
                float(test_price),

            "profit":
                float(profit)

        })

        if profit > best_profit:
            best_profit = profit
            best_price = test_price
            best_qty = pred_qty
        current_profit = (
        (old_price - hpp)
        * row["Qty_DB"]
    )

    return {

        "product_name": req.product_name,

        "current_price": round(old_price,2),

        "optimal_price": round(best_price,2),

        "predicted_qty": round(best_qty,2),

        "current_profit": round(current_profit,2),

        "optimal_profit": round(best_profit,2),

        "profit_improvement": round(
            best_profit-current_profit,
            2
        ),

        "curve": curve

    }