"""LLM API integration for natural language responses via OpenRouter."""

import asyncio
import re
import logging
import httpx
from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=httpx.Timeout(120.0, connect=15.0),
            default_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Healthcare Chatbot",
            },
        )
    return _client


async def _call_with_retry(client, **kwargs) -> object:
    """Call the API, cycling through fallback models on rate-limit/timeout."""
    settings = get_settings()
    models = settings.all_models
    last_error = None

    for model in models:
        kwargs["model"] = model
        try:
            response = await client.chat.completions.create(**kwargs)
            return response
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            is_retryable = "429" in str(e) or "rate" in err_str or "timeout" in err_str
            if is_retryable:
                logger.warning(f"Model {model} rate-limited/timed out, trying next fallback: {e}")
                await asyncio.sleep(1)
                continue
            raise

    # All models exhausted — retry primary once more after a longer wait
    logger.warning("All models rate-limited, waiting 5s and retrying primary...")
    await asyncio.sleep(5)
    kwargs["model"] = models[0]
    return await client.chat.completions.create(**kwargs)


def _strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> reasoning blocks from model output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


async def generate_smart_followup(
    symptoms: list[str],
    conversation_history: list[dict] | None,
) -> dict:
    """Generate smart follow-up questions to gather more information."""
    symptom_str = ", ".join(s.replace("_", " ") for s in symptoms)
    
    system_prompt = (
        "You are a friendly healthcare assistant having a conversation to understand "
        "a patient's symptoms better. Ask follow-up questions naturally to gather more "
        "information before making any conclusions.\n\n"
        "Be warm, empathetic, and conversational. Ask ONE main question with optional "
        "clarifying sub-questions."
    )
    
    user_prompt = (
        f"The user has mentioned these symptoms: {symptom_str}\n\n"
        "Ask a friendly follow-up question to learn more. Consider asking about:\n"
        "- Duration (how long they've had symptoms)\n"
        "- Severity (mild, moderate, severe)\n"
        "- Other symptoms they might have\n"
        "- Any triggers or patterns they've noticed\n\n"
        "Keep your response brief and conversational. Also provide 2 suggested follow-up "
        "questions at the END in this format:\n"
        "QUESTIONS: question1 | question2"
    )
    
    try:
        settings = get_settings()
        client = _get_client()
        response = await _call_with_retry(
            client,
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        content = response.choices[0].message.content
        content = _strip_think_blocks(content)
        
        # Parse questions
        questions = []
        lines = content.strip().split("\n")
        message_lines = []
        for line in lines:
            if line.upper().startswith("QUESTIONS:"):
                questions = [q.strip() for q in line.split(":", 1)[1].split("|") if q.strip()]
            else:
                message_lines.append(line)
        
        return {
            "message": "\n".join(message_lines).strip(),
            "questions": questions[:3] if questions else [
                "How long have you been experiencing these symptoms?",
                "Are there any other symptoms you've noticed?",
            ],
        }
    except Exception as e:
        logger.error(f"Smart followup error: {e}")
        return {
            "message": (
                f"I see you're experiencing {symptom_str}. To better understand your situation:\n\n"
                "- How long have you been experiencing these symptoms?\n"
                "- Are there any other symptoms you've noticed?\n"
                "- Have the symptoms been getting better, worse, or staying the same?"
            ),
            "questions": [
                "How long have you had these symptoms?",
                "Any other symptoms?",
            ],
        }


async def generate_diagnosis_response(
    disease: str,
    confidence: float,
    top_3: list[dict],
    severity: dict,
    symptoms: list[str],
    user_message: str,
    similar_past: list[dict] | None = None,
) -> dict:
    """Generate a rich diagnosis response using the LLM.

    Returns: {message, remedies, medications, specialist}
    """
    system_prompt = (
        "You are a helpful healthcare assistant chatbot. You provide informational "
        "health guidance based on symptom analysis. You are NOT a doctor. Always include "
        "a disclaimer that this is not medical advice and users should consult a healthcare "
        "professional.\n\n"
        "Respond in a warm, empathetic tone. Structure your response with:\n"
        "1. Acknowledge the user's symptoms\n"
        "2. Explain the likely condition briefly\n"
        "3. Suggest home remedies (3-4 bullet points)\n"
        "4. Suggest OTC medications if appropriate (2-3)\n"
        "5. Recommend what type of specialist to see\n"
        "6. Note severity and urgency\n\n"
        "Keep response concise (under 300 words). Use markdown formatting."
    )

    top_3_str = ", ".join(
        f"{d['disease']} ({d['confidence']:.0%})" for d in top_3
    )
    
    past_context = ""
    if similar_past:
        past_diseases = [p["disease"] for p in similar_past if p.get("disease")]
        if past_diseases:
            past_context = f"\nNote: The user has previously experienced similar symptoms related to: {', '.join(set(past_diseases))}. Consider this history in your response.\n"

    user_prompt = (
        f"The user said: \"{user_message}\"\n\n"
        f"Identified symptoms: {', '.join(symptoms)}\n"
        f"Most likely condition: {disease} (confidence: {confidence:.0%})\n"
        f"Other possibilities: {top_3_str}\n"
        f"Severity: {severity['level']} (score: {severity['score']})\n"
        f"Severity recommendation: {severity['recommendation']}\n"
        f"{past_context}\n"
        "Please provide a helpful response. Also return structured data in this exact format "
        "at the END of your response on separate lines:\n"
        "REMEDIES: remedy1 | remedy2 | remedy3\n"
        "MEDICATIONS: med1 | med2 | med3\n"
        "SPECIALIST: specialist type"
    )

    try:
        settings = get_settings()
        client = _get_client()
        response = await _call_with_retry(
            client,
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        content = response.choices[0].message.content
        content = _strip_think_blocks(content)
        return _parse_llm_response(content)

    except Exception as e:
        logger.error(f"LLM API error: {e}")
        return _fallback_response(disease, confidence, severity, symptoms)


async def generate_followup_response(
    conversation_messages: list[dict],
    user_message: str,
) -> str:
    """Generate a follow-up response for ongoing conversation."""
    system_prompt = (
        "You are a helpful healthcare assistant chatbot. Continue the conversation "
        "helpfully. If the user asks about specialists, medications, or follow-up care, "
        "provide relevant guidance. Always remind them to consult a real doctor. "
        "Keep responses concise and use markdown."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_messages[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        settings = get_settings()
        client = _get_client()
        response = await _call_with_retry(
            client,
            model=settings.deepseek_model,
            messages=messages,
            temperature=0.7,
            max_tokens=400,
        )
        content = response.choices[0].message.content
        return _strip_think_blocks(content)
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        return (
            "I'm having trouble connecting right now. Please try again in a moment. "
            "If you're experiencing a medical emergency, please call emergency services."
        )


def _parse_llm_response(content: str) -> dict:
    """Parse structured data from LLM response."""
    lines = content.strip().split("\n")
    remedies = None
    medications = None
    specialist = None
    message_lines = []

    for line in lines:
        upper = line.strip().upper()
        if upper.startswith("REMEDIES:"):
            remedies = [r.strip() for r in line.split(":", 1)[1].split("|") if r.strip()]
        elif upper.startswith("MEDICATIONS:"):
            medications = [m.strip() for m in line.split(":", 1)[1].split("|") if m.strip()]
        elif upper.startswith("SPECIALIST:"):
            specialist = line.split(":", 1)[1].strip()
        else:
            message_lines.append(line)

    return {
        "message": "\n".join(message_lines).strip(),
        "remedies": remedies,
        "medications": medications,
        "specialist": specialist,
    }


def _fallback_response(disease: str, confidence: float, severity: dict,
                        symptoms: list[str]) -> dict:
    """Template-based fallback when LLM API is unavailable."""
    symptom_str = ", ".join(s.replace("_", " ") for s in symptoms)
    message = (
        f"Based on your symptoms ({symptom_str}), the analysis suggests "
        f"**{disease}** with {confidence:.0%} confidence.\n\n"
        f"**Severity**: {severity['level'].title()} — {severity['recommendation']}\n\n"
        "**General recommendations:**\n"
        "- Rest and stay hydrated\n"
        "- Monitor your symptoms closely\n"
        "- Consult a healthcare professional for proper diagnosis\n\n"
        "*Disclaimer: This is not medical advice. Please consult a qualified "
        "healthcare professional for proper diagnosis and treatment.*"
    )
    return {
        "message": message,
        "remedies": ["Rest", "Stay hydrated", "Monitor symptoms"],
        "medications": None,
        "specialist": "General Practitioner",
    }
