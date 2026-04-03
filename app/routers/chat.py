"""Chat endpoints: create conversation, send messages."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Conversation, Message
from app.models.schemas import ChatRequest, ChatResponse, NewConversationResponse
from app.services.diagnosis_service import get_diagnosis

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/new", response_model=NewConversationResponse)
def create_conversation(db: Session = Depends(get_db)):
    """Create a new chat conversation."""
    conv = Conversation()
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return NewConversationResponse(conversation_id=conv.id, title=conv.title)


@router.post("", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and get a diagnosis/response."""
    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
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

    # Get diagnosis / response
    result = await get_diagnosis(req.message, conversation_history=history)

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
    )
