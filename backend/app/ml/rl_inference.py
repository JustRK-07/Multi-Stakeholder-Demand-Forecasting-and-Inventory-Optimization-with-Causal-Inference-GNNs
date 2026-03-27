from __future__ import annotations

from typing import Dict, List, Optional

from .rl_analysis import recommendation_rows


def recommend_orders(store_id: Optional[str] = None, limit: int = 4, use_rl: bool = True) -> List[Dict[str, object]]:
    rows = recommendation_rows(store_id=store_id, limit=limit)
    recs: List[Dict[str, object]] = []
    for row in rows:
        qty = row["rl_order_qty"] if use_rl else row["baseline_order_qty"]
        action_label = "Adaptive Policy" if use_rl else "Baseline Policy"
        recs.append(
            {
                "sku": row["sku"],
                "action": f"{action_label}: order {int(row[str('rl_order_qty' if use_rl else 'baseline_order_qty')])} units",
                "confidence": int(row["confidence"]),
                "expectedSaving": f"${float(row['expected_saving_value']):.2f}",
                "urgency": row["urgency"],
                "storeId": row["store_id"],
                "recommendedQty": int(qty),
                "baselineQty": int(row["baseline_order_qty"]),
                "rlQty": int(row["rl_order_qty"]),
            }
        )
    return recs
