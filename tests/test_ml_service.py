"""Tests for ML prediction service."""

from app.services.ml_service import predict_disease, get_known_symptoms


def test_predict_with_known_symptoms():
    result = predict_disease(["headache", "high_fever"])
    assert result["disease"] != "Unknown"
    assert result["confidence"] > 0
    assert len(result["top_3"]) > 0
    assert len(result["matched_symptoms"]) > 0


def test_predict_with_unknown_symptoms():
    result = predict_disease(["completely_made_up_symptom"])
    assert result["disease"] == "Unknown"
    assert result["confidence"] == 0.0
    assert result["matched_symptoms"] == []


def test_predict_normalizes_symptoms():
    result = predict_disease(["high fever", "Headache"])
    assert result["disease"] != "Unknown"


def test_get_known_symptoms():
    symptoms = get_known_symptoms()
    assert len(symptoms) > 50
    assert "headache" in symptoms


def test_predict_returns_top_3():
    result = predict_disease(["headache", "high_fever", "fatigue"])
    for item in result["top_3"]:
        assert "disease" in item
        assert "confidence" in item
        assert item["confidence"] > 0.01
