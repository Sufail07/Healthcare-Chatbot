"""Calculates severity scores from symptoms using the severity weights dataset."""

import csv
from pathlib import Path
from functools import lru_cache


@lru_cache
def _load_severity_weights() -> dict[str, int]:
    """Load symptom severity weights from CSV."""
    weights = {}
    path = Path("data/raw/Symptom-severity.csv")
    if not path.exists():
        return weights
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symptom = row["Symptom"].strip().replace(" ", "_").lower()
            weight = int(row["weight"])
            weights[symptom] = weight
    return weights


def assess_severity(symptoms: list[str]) -> dict:
    """Assess severity from a list of symptoms.

    Returns: {level, score, recommendation, max_weight}
    """
    weights = _load_severity_weights()
    if not symptoms:
        return {
            "level": "unknown",
            "score": 0.0,
            "recommendation": "Please describe your symptoms for an assessment.",
            "max_weight": 0,
        }

    normalized = [s.strip().replace(" ", "_").lower() for s in symptoms]
    matched_weights = [weights.get(s, 2) for s in normalized]

    max_weight = max(matched_weights)
    avg_weight = sum(matched_weights) / len(matched_weights)
    # Severity score: blend of average and max (0-1 scale, max weight 7)
    score = round((0.4 * avg_weight + 0.6 * max_weight) / 7, 2)

    if score >= 0.75:
        level = "emergency"
        recommendation = "Seek immediate emergency medical attention."
    elif score >= 0.55:
        level = "severe"
        recommendation = "Please consult a doctor as soon as possible."
    elif score >= 0.35:
        level = "moderate"
        recommendation = "Consider scheduling a doctor's appointment soon."
    else:
        level = "mild"
        recommendation = "Monitor your symptoms. Rest and home care may be sufficient."

    return {
        "level": level,
        "score": score,
        "recommendation": recommendation,
        "max_weight": max_weight,
    }
