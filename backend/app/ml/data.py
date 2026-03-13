from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_PATH = ROOT / "data" / "archive (2)" / "retail_store_inventory.csv"


def load_groceries_sales(path: Optional[Path] = None) -> pd.DataFrame:
    data_path = path or DEFAULT_DATA_PATH
    df = pd.read_csv(data_path)

    df = df[df["Category"] == "Groceries"].copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Store ID"] = df["Store ID"].astype(str)
    df["Product ID"] = df["Product ID"].astype(str)

    agg = (
        df.groupby(["Store ID", "Product ID", "Date"], as_index=False)
        .agg(
            units_sold=("Units Sold", "sum"),
            inventory_level=("Inventory Level", "mean"),
            price=("Price", "mean"),
            discount=("Discount", "mean"),
            competitor_price=("Competitor Pricing", "mean"),
            holiday=("Holiday/Promotion", "max"),
            seasonality=("Seasonality", "first"),
            weather=("Weather Condition", "first"),
        )
        .sort_values(["Store ID", "Product ID", "Date"])
    )

    agg.rename(columns={"Store ID": "store_id", "Product ID": "product_id", "Date": "date"}, inplace=True)

    def impute_group(g: pd.DataFrame) -> pd.DataFrame:
        g = g.sort_values("date").copy()
        censored = (g["inventory_level"] <= 0) & (g["units_sold"] <= 0)
        if censored.any():
            series = g["units_sold"].astype(float)
            series[censored] = pd.NA
            series = series.interpolate(limit_direction="both")
            g["units_sold"] = series.fillna(0.0)
        return g

    agg = agg.groupby(["store_id", "product_id"], as_index=False).apply(impute_group)
    agg = agg.reset_index(drop=True)
    return agg


def list_grocery_products(path: Optional[Path] = None, store_id: Optional[str] = None) -> pd.DataFrame:
    data_path = path or DEFAULT_DATA_PATH
    df = pd.read_csv(data_path)
    df = df[df["Category"] == "Groceries"].copy()
    df["Store ID"] = df["Store ID"].astype(str)
    df["Product ID"] = df["Product ID"].astype(str)

    if store_id:
        df = df[df["Store ID"] == str(store_id)]

    products = (
        df.groupby(["Store ID", "Product ID"], as_index=False)["Units Sold"]
        .sum()
        .sort_values(["Store ID", "Units Sold"], ascending=[True, False])
    )
    products.rename(columns={"Store ID": "store_id", "Product ID": "product_id", "Units Sold": "units_sold"}, inplace=True)
    return products
