from __future__ import annotations

import os
from typing import Dict, Optional


def mlflow_enabled() -> bool:
    return os.getenv("MLFLOW_TRACKING_URI") is not None


def log_run(
    run_name: str,
    params: Dict[str, object],
    metrics: Dict[str, float],
    artifact_path: Optional[str] = None,
) -> None:
    if not mlflow_enabled():
        return

    try:
        import mlflow

        mlflow.set_experiment("retailcast-forecast")
        with mlflow.start_run(run_name=run_name):
            for k, v in params.items():
                mlflow.log_param(k, v)
            for k, v in metrics.items():
                mlflow.log_metric(k, v)
            if artifact_path:
                mlflow.log_artifact(artifact_path)
    except Exception:
        # Avoid breaking training if MLflow is unavailable.
        return
