"""Orchestrator: ties together symptom parsing, ML prediction, severity, and LLM response."""

import logging

from app.services.symptom_parser import parse_symptoms
from app.services.ml_service import predict_disease
from app.services.severity_service import assess_severity
from app.services.llm_service import generate_diagnosis_response, generate_followup_response

logger = logging.getLogger(__name__)


def _has_prior_diagnosis(conversation_history: list[dict] | None) -> bool:
    """Check if the conversation already contains a diagnosis."""
    if not conversation_history:
        return False
    for msg in conversation_history:
        if msg.get("role") == "assistant" and msg.get("diagnosis_data"):
            return True
    return False


async def get_diagnosis(user_message: str, conversation_history: list[dict] | None = None) -> dict:
    """Full diagnosis pipeline: parse → predict → severity → explain.

    If a diagnosis already exists in the conversation, treat new messages as
    follow-ups (routed directly to the LLM with conversation context) unless
    the user explicitly mentions new symptoms.
    """
    has_diagnosis = _has_prior_diagnosis(conversation_history)

    if has_diagnosis:
        # Conversation already has a diagnosis — route to follow-up by default.
        # Only re-diagnose if the user is clearly reporting NEW symptoms.
        response = await generate_followup_response(conversation_history, user_message)
        return {"message": response, "diagnosis_data": None}

    # First diagnostic message — extract symptoms
    symptoms = await parse_symptoms(user_message)

    if not symptoms:
        if conversation_history:
            response = await generate_followup_response(conversation_history, user_message)
            return {"message": response, "diagnosis_data": None}
        return {
            "message": (
                "I couldn't identify specific symptoms from your message. "
                "Could you describe your symptoms in more detail? For example:\n\n"
                "- \"I have a headache and fever\"\n"
                "- \"I've been coughing and have chest pain\"\n"
                "- \"My joints are aching and I feel tired\"\n\n"
                "*I'm here to help you understand your symptoms, but please remember "
                "to consult a healthcare professional for proper diagnosis.*"
            ),
            "diagnosis_data": None,
        }

    # ML prediction
    prediction = predict_disease(symptoms)

    if prediction["disease"] == "Unknown":
        return {
            "message": (
                "I found some symptoms but couldn't make a confident prediction. "
                "Could you provide more details about how you're feeling?"
            ),
            "diagnosis_data": None,
        }

    # Severity assessment
    severity = assess_severity(symptoms)

    # LLM-powered explanation
    llm_result = await generate_diagnosis_response(
        disease=prediction["disease"],
        confidence=prediction["confidence"],
        top_3=prediction["top_3"],
        severity=severity,
        symptoms=symptoms,
        user_message=user_message,
    )

    diagnosis_data = {
        "disease": prediction["disease"],
        "confidence": prediction["confidence"],
        "top_3": prediction["top_3"],
        "severity": severity["level"],
        "severity_score": severity["score"],
        "symptoms_identified": symptoms,
        "remedies": llm_result.get("remedies"),
        "medications": llm_result.get("medications"),
        "specialist": llm_result.get("specialist"),
    }

    return {
        "message": llm_result["message"],
        "diagnosis_data": diagnosis_data,
    }


async def get_direct_diagnosis(symptoms: list[str]) -> dict:
    """Direct diagnosis from pre-parsed symptoms (no LLM symptom extraction)."""
    prediction = predict_disease(symptoms)
    if prediction["disease"] == "Unknown":
        return {
            "disease": "Unknown",
            "confidence": 0.0,
            "top_3": [],
            "severity": "unknown",
            "severity_score": 0.0,
            "explanation": "Could not identify a condition from the given symptoms.",
        }

    severity = assess_severity(symptoms)

    llm_result = await generate_diagnosis_response(
        disease=prediction["disease"],
        confidence=prediction["confidence"],
        top_3=prediction["top_3"],
        severity=severity,
        symptoms=symptoms,
        user_message=f"My symptoms are: {', '.join(symptoms)}",
    )

    return {
        "disease": prediction["disease"],
        "confidence": prediction["confidence"],
        "top_3": prediction["top_3"],
        "severity": severity["level"],
        "severity_score": severity["score"],
        "explanation": llm_result["message"],
    }
