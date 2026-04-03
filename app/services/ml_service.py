"""Service layer for ML model loading and prediction."""

from app.ml.predictor import DiseasePredictor
from app.config import get_settings

_predictor: DiseasePredictor | None = None


def get_predictor() -> DiseasePredictor:
    global _predictor
    if _predictor is None:
        settings = get_settings()
        _predictor = DiseasePredictor(
            model_path=settings.ml_model_path,
            feature_columns_path=settings.feature_columns_path,
        )
    return _predictor


def predict_disease(symptoms: list[str]) -> dict:
    """Predict disease from symptom list. Returns prediction dict."""
    predictor = get_predictor()
    return predictor.predict(symptoms)


def get_known_symptoms() -> list[str]:
    """Return list of all symptoms the model knows about."""
    return get_predictor().known_symptoms
