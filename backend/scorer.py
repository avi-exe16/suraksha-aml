import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import shap
from config import (
    FRAUD_THRESHOLD_BLOCK,
    FRAUD_THRESHOLD_REVIEW,
    MODEL_PATH,
    SCALER_PATH,
    FEATURE_COLUMNS_PATH,
)

logger = logging.getLogger("suraksha.scorer")

# Consistent min/max empirical bounds for Isolation Forest decision_function
ISO_MIN_SCORE: float = -0.5
ISO_MAX_SCORE: float = 0.5


class FraudScoringEngine:
    def __init__(self):
        self.iso_forest = None
        self.scaler = None
        self.feature_columns: List[str] = []
        self.explainer: Optional[shap.TreeExplainer] = None
        self._is_loaded: bool = False

    def load_artifacts(
        self,
        model_path: str = MODEL_PATH,
        scaler_path: str = SCALER_PATH,
        features_path: str = FEATURE_COLUMNS_PATH,
    ) -> None:
        """Loads artifacts into memory and initializes fast SHAP TreeExplainer."""
        import joblib
        import os

        if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
            raise FileNotFoundError(
                "Model artifacts missing. Artifacts must be downloaded during CI/CD or container build."
            )

        logger.info("Loading ML artifacts into memory...")
        self.iso_forest = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.feature_columns = list(joblib.load(features_path))

        # Pre-initialize TreeExplainer for fast per-instance local attribution
        # Isolation Forest is tree-based; TreeExplainer computes exact local SHAP values in ~1-3ms
        self.explainer = shap.TreeExplainer(self.iso_forest)
        self._is_loaded = True
        logger.info("Artifacts and SHAP TreeExplainer successfully initialized.")

    def _normalize_score(self, raw_scores: np.ndarray) -> np.ndarray:
        """Consistently maps Isolation Forest score to [0, 1] anomaly score across all pathways."""
        clipped = np.clip(raw_scores, ISO_MIN_SCORE, ISO_MAX_SCORE)
        normalized = (clipped - ISO_MIN_SCORE) / (ISO_MAX_SCORE - ISO_MIN_SCORE)
        return 1.0 - normalized

    def score_transaction(self, txn: Dict[str, Any], explain: bool = True) -> Dict[str, Any]:
        """
        Scores a single transaction. Pure NumPy execution path for sub-5ms latency.
        """
        if not self._is_loaded:
            raise RuntimeError("Scoring engine called before artifacts were loaded.")

        # Extract features without Pandas DataFrame overhead
        try:
            vector = np.array([[float(txn.get(col, 0.0)) for col in self.feature_columns]], dtype=np.float32)
        except (ValueError, TypeError) as err:
            raise ValueError(f"Malformed input features: {err}") from err

        # Scale and score
        scaled = self.scaler.transform(vector)
        raw_score = float(self.iso_forest.decision_function(scaled)[0])
        anomaly_score = round(float(self._normalize_score(np.array([raw_score]))[0]), 4)

        if anomaly_score >= FRAUD_THRESHOLD_BLOCK:
            action, risk_level = "blocked", "high"
        elif anomaly_score >= FRAUD_THRESHOLD_REVIEW:
            action, risk_level = "step_up_auth", "medium"
        else:
            action, risk_level = "approved", "low"

        # Local instance-level SHAP explanation
        explanation_parts = []
        if explain:
            # TreeExplainer calculates true local contribution for this specific transaction
            shap_values = self.explainer.shap_values(scaled)[0]
            # Higher negative impact on decision function = higher anomaly contribution
            top_indices = np.argsort(shap_values)[:5]

            for idx in top_indices:
                feature_name = self.feature_columns[idx]
                explanation_parts.append({
                    "feature": feature_name,
                    "value": float(vector[0][idx]),
                    "importance": round(float(abs(shap_values[idx])), 4),
                })

        return {
            "anomaly_score": anomaly_score,
            "risk_level": risk_level,
            "action": action,
            "explanation": explanation_parts,
        }

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """High-throughput vectorized batch scoring."""
        if not self._is_loaded:
            raise RuntimeError("Scoring engine called before artifacts were loaded.")

        X = df[self.feature_columns].fillna(0.0).to_numpy(dtype=np.float32)
        X_scaled = self.scaler.transform(X)

        raw_scores = self.iso_forest.decision_function(X_scaled)
        anomaly_scores = self._normalize_score(raw_scores)

        df_out = df.copy()
        df_out["anomaly_score"] = np.round(anomaly_scores, 4)
        df_out["predicted_fraud"] = (self.iso_forest.predict(X_scaled) == -1).astype(int)
        return df_out


# Singleton instance managed by FastAPI lifespan
engine = FraudScoringEngine()