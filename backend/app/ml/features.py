from __future__ import annotations

import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["dow"] = out["date"].dt.dayofweek
    out["month"] = out["date"].dt.month
    out["day"] = out["date"].dt.day
    return out


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    group_cols = ["store_id", "product_id"]
    out["lag_1"] = out.groupby(group_cols)["units_sold"].shift(1)
    out["lag_7"] = out.groupby(group_cols)["units_sold"].shift(7)
    out["lag_14"] = out.groupby(group_cols)["units_sold"].shift(14)
    out["roll_7"] = out.groupby(group_cols)["units_sold"].transform(
        lambda s: s.shift(1).rolling(7).mean()
    )
    return out


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = add_time_features(df)
    out = add_lag_features(out)

    out = pd.get_dummies(
        out,
        columns=["seasonality", "weather", "store_id", "product_id"],
        prefix=["season", "weather", "store", "product"],
        dtype=float,
    )
    out = out.dropna().reset_index(drop=True)
    return out
