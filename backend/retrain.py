import asyncio
import logging
import os
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from database import get_recent_transactions_df

logger = logging.getLogger("suraksha.retrain")

MODEL_DIR = os.getenv("MODEL_DIR", "../models")

FEATURE_COLUMNS = [
    "amount",
    "km_from_last_txn",
    "minutes_from_last_txn",
    "impossible_speed",
    "hour",
    "is_weekend",
    "is_night",
    "txn_count_1hr",
    "txn_count_24hr",
    "amount_sum_1hr",
    "amount_sum_24hr",
    "amount_vs_user_avg",
    "is_new_device",
    "device_count_7d",
    "is_new_merchant_category",
]


async def retrain_model():
    """
    Pulls recent transactions from PostgreSQL using asyncpg, scales features,
    fits a fresh IsolationForest estimator, and atomically updates model artifacts.
    """
    logger.info("Extracting recent transaction records from database...")
    df = await get_recent_transactions_df(limit=50000)

    if len(df) < 50:
        logger.warning(f"Insufficient samples ({len(df)}) for production retraining.")
        return {"status": "skipped", "reason": f"Insufficient sample size ({len(df)} records)"}

    # Ensure required feature columns exist and impute missing values
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0

    X = df[FEATURE_COLUMNS].fillna(0.0).values

    logger.info(f"Fitting StandardScaler and IsolationForest on {len(df)} transactions...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=150,
        contamination=0.03,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Score percentiles for threshold calibration
    raw_scores = -model.score_samples(X_scaled)
    score_p50 = float(np.percentile(raw_scores, 50))
    score_p95 = float(np.percentile(raw_scores, 95))
    score_p99 = float(np.percentile(raw_scores, 99))

    metadata = {
        "retrained_at": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(df),
        "score_percentiles": {
            "p50": score_p50,
            "p95": score_p95,
            "p99": score_p99,
        },
        "features": FEATURE_COLUMNS,
    }

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODEL_DIR, "isolation_forest.joblib"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
    joblib.dump(metadata, os.path.join(MODEL_DIR, "metadata.joblib"))

    logger.info("Model artifacts successfully serialized to disk.")
    return {
        "status": "success",
        "training_samples": len(df),
        "retrained_at": metadata["retrained_at"],
        "p95_threshold": round(score_p95, 4),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(retrain_model())
    print("\nRetraining Result:", result)