from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# --- Auth / User ---

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


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
    emergency_warning: str | None = None
    suggestions: dict | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    diagnosis_data: DiagnosisData | None = None
    follow_up_questions: list[str] | None = None


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


# --- BMI ---

class BMICalculateRequest(BaseModel):
    height: float = Field(..., gt=0, description="Height in cm")
    weight: float = Field(..., gt=0, description="Weight in kg")


class BMIResult(BaseModel):
    bmi: float
    category: str
    message: str
    suggestions: list[str]
    color: str


class BMIRecordOut(BaseModel):
    id: int
    height: float
    weight: float
    bmi: float
    category: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BMIHistoryResponse(BaseModel):
    records: list[BMIRecordOut]
    comparison: dict | None = None


# --- Disease ---

class DiseaseOut(BaseModel):
    id: int
    name: str
    symptoms: list[str]
    severity: str
    description: str | None
    home_remedies: list[str] | None
    precautions: list[str] | None
    doctor_advice: str | None
    specialist: str | None

    model_config = {"from_attributes": True}
