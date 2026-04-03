"""Direct diagnosis endpoint: takes symptom list, returns diagnosis."""

from fastapi import APIRouter

from app.models.schemas import DiagnoseRequest, DiagnoseResponse
from app.services.diagnosis_service import get_direct_diagnosis

router = APIRouter(prefix="/api", tags=["diagnosis"])


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    """Diagnose from a direct list of symptoms (no chat context)."""
    result = await get_direct_diagnosis(req.symptoms)
    return DiagnoseResponse(**result)
