"""Orchestrator: ties together symptom parsing, ML prediction, severity, and LLM response."""

import logging
import re

from app.services.symptom_parser import parse_symptoms
from app.services.ml_service import predict_disease
from app.services.severity_service import assess_severity
from app.services.llm_service import generate_diagnosis_response, generate_followup_response, generate_smart_followup

logger = logging.getLogger(__name__)

# Emergency keywords that trigger immediate warning
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "cannot breathe", "breathing difficulty",
    "difficulty breathing", "shortness of breath", "choking", "stroke", "paralysis",
    "severe bleeding", "heavy bleeding", "unconscious", "unresponsive", "seizure",
    "convulsion", "suicidal", "suicide", "overdose", "poisoning", "severe pain",
    "coughing blood", "vomiting blood", "blood in stool", "severe headache",
    "worst headache", "sudden numbness", "sudden weakness", "chest tightness",
    "crushing chest", "arm pain with chest", "jaw pain with chest",
]

# Follow-up questions for smart conversation
FOLLOW_UP_QUESTIONS = {
    "duration": [
        "How long have you been experiencing these symptoms?",
        "Since how many days have you had these symptoms?",
        "When did these symptoms first start?",
    ],
    "additional": [
        "Are you experiencing any other symptoms?",
        "Do you have any additional symptoms you haven't mentioned?",
        "Is there anything else bothering you?",
    ],
    "severity_check": [
        "On a scale of 1-10, how severe would you rate your symptoms?",
        "Are the symptoms getting better, worse, or staying the same?",
        "Have the symptoms changed in intensity?",
    ],
    "history": [
        "Have you experienced similar symptoms before?",
        "Do you have any pre-existing medical conditions?",
        "Are you currently taking any medications?",
    ],
}


def _detect_emergency(message: str) -> str | None:
    """Check for emergency keywords and return warning if found."""
    message_lower = message.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in message_lower:
            return (
                "⚠️ **EMERGENCY WARNING** ⚠️\n\n"
                f"You mentioned '{keyword}' which could indicate a serious medical emergency.\n\n"
                "**Please seek immediate medical attention:**\n"
                "- Call emergency services (911 in US, 999 in UK, 112 in EU)\n"
                "- Go to the nearest emergency room\n"
                "- Do NOT wait for online advice\n\n"
                "If someone is with you, let them know about your symptoms immediately."
            )
    return None


def _get_severity_suggestions(severity_level: str, symptoms: list[str]) -> dict:
    """Get suggestions based on severity level."""
    if severity_level == "mild":
        return {
            "type": "home_remedies",
            "title": "Home Care Suggestions",
            "icon": "🏠",
            "items": [
                "Rest and get plenty of sleep",
                "Stay well hydrated - drink water, herbal tea, or clear broths",
                "Use over-the-counter medications as needed for symptom relief",
                "Monitor your symptoms and note any changes",
                "Practice good hygiene to prevent spreading illness",
            ],
            "note": "These symptoms are generally manageable at home. However, if symptoms worsen or persist beyond a week, consider seeing a doctor.",
        }
    elif severity_level == "moderate":
        return {
            "type": "precautions",
            "title": "Precautions & Tips",
            "icon": "⚠️",
            "items": [
                "Schedule a doctor's appointment within the next few days",
                "Keep track of your symptoms and their progression",
                "Avoid strenuous activities until you feel better",
                "Take prescribed or OTC medications as directed",
                "Get adequate rest and maintain good nutrition",
                "Avoid contact with others if symptoms could be contagious",
            ],
            "note": "These symptoms warrant professional attention. Consider scheduling a doctor's visit soon.",
        }
    elif severity_level in ["severe", "emergency"]:
        return {
            "type": "doctor_consultation",
            "title": "Seek Medical Attention",
            "icon": "🏥",
            "items": [
                "Consult a healthcare provider as soon as possible",
                "Consider visiting an urgent care clinic or emergency room",
                "Do not delay seeking medical attention",
                "Bring a list of your symptoms and when they started",
                "Have someone accompany you if possible",
            ],
            "note": "These symptoms are serious and require professional medical evaluation. Please seek care promptly.",
        }
    return {
        "type": "general",
        "title": "General Advice",
        "icon": "💡",
        "items": [
            "Monitor your symptoms",
            "Stay hydrated and rest",
            "Consult a healthcare professional if concerned",
        ],
        "note": "Always consult a healthcare professional for proper diagnosis.",
    }


def _has_prior_diagnosis(conversation_history: list[dict] | None) -> bool:
    """Check if the conversation already contains a diagnosis."""
    if not conversation_history:
        return False
    for msg in conversation_history:
        if msg.get("role") == "assistant" and msg.get("diagnosis_data"):
            return True
    return False


def _get_conversation_stage(conversation_history: list[dict] | None) -> str:
    """Determine conversation stage for smart follow-ups."""
    if not conversation_history:
        return "initial"
    
    user_messages = [m for m in conversation_history if m.get("role") == "user"]
    
    if len(user_messages) <= 1:
        return "initial"
    elif len(user_messages) == 2:
        return "gathering_info"
    elif len(user_messages) <= 4:
        return "deep_dive"
    else:
        return "conclusion"


def _find_similar_past_symptoms(
    current_symptoms: list[str],
    user_symptom_history: list[dict] | None,
) -> list[dict]:
    """Find similar past symptoms from user history."""
    if not user_symptom_history or not current_symptoms:
        return []
    
    current_set = set(s.lower() for s in current_symptoms)
    similar = []
    
    for past in user_symptom_history:
        past_symptoms = set(s.lower() for s in past.get("symptoms", []))
        overlap = current_set & past_symptoms
        if overlap and len(overlap) >= 1:
            similar.append({
                "disease": past.get("disease"),
                "matching_symptoms": list(overlap),
                "date": past.get("date"),
            })
    
    return similar[:3]


async def get_diagnosis(
    user_message: str,
    conversation_history: list[dict] | None = None,
    user_symptom_history: list[dict] | None = None,
) -> dict:
    """Full diagnosis pipeline with smart follow-ups and emergency detection.

    If a diagnosis already exists in the conversation, treat new messages as
    follow-ups (routed directly to the LLM with conversation context) unless
    the user explicitly mentions new symptoms.
    """
    # Check for emergency keywords first
    emergency_warning = _detect_emergency(user_message)
    if emergency_warning:
        return {
            "message": emergency_warning,
            "diagnosis_data": None,
            "follow_up_questions": None,
        }
    
    has_diagnosis = _has_prior_diagnosis(conversation_history)
    stage = _get_conversation_stage(conversation_history)

    if has_diagnosis:
        response = await generate_followup_response(conversation_history, user_message)
        return {"message": response, "diagnosis_data": None, "follow_up_questions": None}

    # Extract symptoms
    symptoms = await parse_symptoms(user_message)

    if not symptoms:
        if conversation_history and len(conversation_history) > 0:
            response = await generate_followup_response(conversation_history, user_message)
            return {"message": response, "diagnosis_data": None, "follow_up_questions": None}
        
        # Smart initial response asking for symptoms
        return {
            "message": (
                "I'd love to help you understand what might be going on! 🩺\n\n"
                "Could you tell me more about your symptoms? For example:\n\n"
                "- What symptoms are you experiencing?\n"
                "- \"I have a headache and fever\"\n"
                "- \"I've been feeling tired with joint pain\"\n\n"
                "*I'm here to help, but remember - always consult a healthcare professional for proper diagnosis.*"
            ),
            "diagnosis_data": None,
            "follow_up_questions": [
                "What symptoms are you experiencing?",
                "When did you first notice these symptoms?",
            ],
        }

    # Check if we need more information (smart conversation flow)
    if stage == "initial" and len(symptoms) <= 2:
        # Generate smart follow-up to gather more info
        follow_up = await generate_smart_followup(symptoms, conversation_history)
        return {
            "message": follow_up["message"],
            "diagnosis_data": None,
            "follow_up_questions": follow_up.get("questions", []),
        }

    # ML prediction
    prediction = predict_disease(symptoms)

    if prediction["disease"] == "Unknown":
        return {
            "message": (
                "I found some symptoms but couldn't make a confident prediction. "
                "Could you provide more details about how you're feeling?\n\n"
                "- How long have you had these symptoms?\n"
                "- Are there any other symptoms you haven't mentioned?"
            ),
            "diagnosis_data": None,
            "follow_up_questions": FOLLOW_UP_QUESTIONS["additional"][:2],
        }

    # Severity assessment
    severity = assess_severity(symptoms)
    
    # Get severity-based suggestions
    suggestions = _get_severity_suggestions(severity["level"], symptoms)
    
    # Find similar past symptoms for personalization
    similar_past = _find_similar_past_symptoms(symptoms, user_symptom_history)

    # LLM-powered explanation with enhanced context
    llm_result = await generate_diagnosis_response(
        disease=prediction["disease"],
        confidence=prediction["confidence"],
        top_3=prediction["top_3"],
        severity=severity,
        symptoms=symptoms,
        user_message=user_message,
        similar_past=similar_past,
    )

    # Add personalization note if similar past symptoms found
    personalization_note = None
    if similar_past:
        past_diseases = [p["disease"] for p in similar_past if p["disease"]]
        if past_diseases:
            personalization_note = f"Based on your history, you've experienced similar symptoms before ({', '.join(set(past_diseases))}). This information helps provide more relevant advice."

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
        "emergency_warning": None,
        "suggestions": suggestions,
    }

    message = llm_result["message"]
    if personalization_note:
        message += f"\n\n📋 *{personalization_note}*"

    return {
        "message": message,
        "diagnosis_data": diagnosis_data,
        "follow_up_questions": FOLLOW_UP_QUESTIONS["history"][:2] if not similar_past else None,
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
