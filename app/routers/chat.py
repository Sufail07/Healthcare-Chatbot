"""Chat endpoints: create conversation, send messages."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Conversation, Message, User
from app.models.schemas import ChatRequest, ChatResponse, NewConversationResponse
from app.services.diagnosis_service import get_diagnosis
from app.services.auth_service import require_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/new", response_model=NewConversationResponse)
def create_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Create a new chat conversation for authenticated user."""
    conv = Conversation(user_id=current_user.id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return NewConversationResponse(conversation_id=conv.id, title=conv.title)


@router.post("", response_model=ChatResponse)
async def send_message(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Send a message and get a diagnosis/response."""
    conv = db.query(Conversation).filter(
        Conversation.id == req.conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.commit()

    # Build conversation history for context
    messages = db.query(Message).filter(
        Message.conversation_id == conv.id
    ).order_by(Message.created_at).all()

    history = [
        {"role": m.role, "content": m.content, "diagnosis_data": m.diagnosis_data}
        for m in messages
    ]

    # Get user's past symptom history for personalization
    user_symptom_history = _get_user_symptom_history(db, current_user.id, exclude_conv=conv.id)

    # Get diagnosis / response
    result = await get_diagnosis(
        req.message,
        conversation_history=history,
        user_symptom_history=user_symptom_history,
    )

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=result["message"],
        diagnosis_data=result.get("diagnosis_data"),
    )
    db.add(assistant_msg)

    # Update conversation title from first diagnosis
    if conv.title == "New Conversation" and result.get("diagnosis_data"):
        disease = result["diagnosis_data"]["disease"]
        conv.title = f"{disease} Assessment"

    db.commit()

    return ChatResponse(
        conversation_id=conv.id,
        message=result["message"],
        diagnosis_data=result.get("diagnosis_data"),
        follow_up_questions=result.get("follow_up_questions"),
    )


def _get_user_symptom_history(db: Session, user_id: str, exclude_conv: str) -> list[dict]:
    """Get past diagnoses for personalization."""
    past_convs = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.id != exclude_conv,
    ).order_by(Conversation.updated_at.desc()).limit(10).all()
    
    history = []
    for conv in past_convs:
        for msg in conv.messages:
            if msg.diagnosis_data:
                history.append({
                    "disease": msg.diagnosis_data.get("disease"),
                    "symptoms": msg.diagnosis_data.get("symptoms_identified", []),
                    "severity": msg.diagnosis_data.get("severity"),
                    "date": conv.created_at.isoformat() if conv.created_at else None,
                })
    return history
