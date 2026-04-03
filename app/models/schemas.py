from pydantic import BaseModel
from datetime import datetime


# --- Chat ---

class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class DiagnosisData(BaseModel):
    disease: str
    confidence: float
    top_3: list[dict]
    severity: str
    severity_score: float
    symptoms_identified: list[str]
    remedies: list[str] | None = None
    medications: list[str] | None = None
    specialist: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    diagnosis_data: DiagnosisData | None = None


class NewConversationResponse(BaseModel):
    conversation_id: str
    title: str


# --- Direct Diagnosis ---

class DiagnoseRequest(BaseModel):
    symptoms: list[str]


class DiagnoseResponse(BaseModel):
    disease: str
    confidence: float
    top_3: list[dict]
    severity: str
    severity_score: float
    explanation: str


# --- History ---

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    diagnosis_data: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut] = []
