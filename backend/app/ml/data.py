from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from ..dataset_registry import get_active_dataset

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_PATH = ROOT / "data" / "archive (2)" / "retail_store_inventory.csv"


def resolve_data_path(path: Optional[Path] = None) -> Path:
    if path is not None:
        return path
    active = get_active_dataset()
    normalized_path = active.get("normalizedPath") if active else None
    if normalized_path:
        candidate = Path(str(normalized_path))
        if candidate.exists():
            return candidate
    return DEFAULT_DATA_PATH


def load_groceries_sales(path: Optional[Path] = None) -> pd.DataFrame:
    data_path = resolve_data_path(path)
    df = pd.read_csv(data_path)

    if {"store_id", "product_id", "date", "units_sold", "inventory_level", "price", "discount", "competitor_price", "holiday", "seasonality", "weather"} <= set(df.columns):
        agg = df.copy()
        agg["date"] = pd.to_datetime(agg["date"])
        agg["store_id"] = agg["store_id"].astype(str)
        agg["product_id"] = agg["product_id"].astype(str)
    else:
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

    grouped = [impute_group(group) for _, group in agg.groupby(["store_id", "product_id"], sort=False)]
    agg = pd.concat(grouped, ignore_index=True) if grouped else agg.iloc[0:0].copy()
    return agg


def list_grocery_products(path: Optional[Path] = None, store_id: Optional[str] = None) -> pd.DataFrame:
    data_path = resolve_data_path(path)
    df = pd.read_csv(data_path)

    if {"store_id", "product_id", "units_sold"} <= set(df.columns):
        products = df[["store_id", "product_id", "units_sold"]].copy()
        products["store_id"] = products["store_id"].astype(str)
        products["product_id"] = products["product_id"].astype(str)
        if store_id:
            products = products[products["store_id"] == str(store_id)]
        products = (
            products.groupby(["store_id", "product_id"], as_index=False)["units_sold"]
            .sum()
            .sort_values(["store_id", "units_sold"], ascending=[True, False])
        )
    else:
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
