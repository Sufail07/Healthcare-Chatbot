"""Makes disease predictions from a list of symptoms using the trained model."""

import json
import numpy as np
import joblib
from pathlib import Path


class DiseasePredictor:
    def __init__(self, model_path: str, feature_columns_path: str):
        self._model = joblib.load(model_path)
        with open(feature_columns_path) as f:
            self._feature_columns = json.load(f)
        self._feature_set = set(self._feature_columns)

    def predict(self, symptoms: list[str], top_n: int = 3) -> dict:
        """Predict diseases from a list of symptom strings.

        Returns dict with: disease, confidence, top_3 list, matched_symptoms.
        """
        # Normalize symptoms
        normalized = [s.strip().replace(" ", "_").lower() for s in symptoms]
        matched = [s for s in normalized if s in self._feature_set]

        if not matched:
            return {
                "disease": "Unknown",
                "confidence": 0.0,
                "top_3": [],
                "matched_symptoms": [],
            }

        # Build feature vector
        vector = np.zeros(len(self._feature_columns))
        for s in matched:
            idx = self._feature_columns.index(s)
            vector[idx] = 1

        vector = vector.reshape(1, -1)
        probas = self._model.predict_proba(vector)[0]
        classes = self._model.classes_

        top_indices = np.argsort(probas)[::-1][:top_n]
        top_3 = [
            {"disease": classes[i], "confidence": round(float(probas[i]), 4)}
            for i in top_indices
            if probas[i] > 0.01
        ]

        best_idx = top_indices[0]
        return {
            "disease": classes[best_idx],
            "confidence": round(float(probas[best_idx]), 4),
            "top_3": top_3,
            "matched_symptoms": matched,
        }

    @property
    def known_symptoms(self) -> list[str]:
        return list(self._feature_columns)
