# import joblib

# model = joblib.load("models/rf_demand_model_v2.pkl")

# print(model.feature_names_in_)

import pandas as pd
df = pd.read_excel("D:\dbklik-price-optimization\data\dataset_feature_engineering.xlsx")
print(df[[
    "Harga_DB",
    "HPP (Latest)",
    "Margin_Rp",
    "Qty_DB",
    "Omset_DB"
]].head(10))