"""BMI calculation and history endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import BMIRecord, User
from app.models.schemas import BMICalculateRequest, BMIResult, BMIRecordOut, BMIHistoryResponse
from app.services.bmi_service import calculate_bmi, compare_bmi_records
from app.services.auth_service import require_current_user

router = APIRouter(prefix="/api/bmi", tags=["bmi"])


@router.post("/calculate", response_model=BMIResult)
def calculate_bmi_endpoint(
    req: BMICalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Calculate BMI and save to history."""
    result = calculate_bmi(req.height, req.weight)
    
    record = BMIRecord(
        user_id=current_user.id,
        height=req.height,
        weight=req.weight,
        bmi=result["bmi"],
        category=result["category"],
    )
    db.add(record)
    db.commit()
    
    return BMIResult(**result)


@router.get("/history", response_model=BMIHistoryResponse)
def get_bmi_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Get BMI history with comparison to previous record."""
    records = db.query(BMIRecord).filter(
        BMIRecord.user_id == current_user.id
    ).order_by(BMIRecord.created_at.desc()).limit(20).all()
    
    comparison = None
    if len(records) >= 2:
        current = {"bmi": records[0].bmi, "category": records[0].category}
        previous = {"bmi": records[1].bmi, "category": records[1].category}
        comparison = compare_bmi_records(current, previous)
    
    return BMIHistoryResponse(
        records=[BMIRecordOut.model_validate(r) for r in records],
        comparison=comparison,
    )


@router.get("/latest", response_model=BMIRecordOut | None)
def get_latest_bmi(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Get the most recent BMI record."""
    record = db.query(BMIRecord).filter(
        BMIRecord.user_id == current_user.id
    ).order_by(BMIRecord.created_at.desc()).first()
    
    if not record:
        return None
    
    return BMIRecordOut.model_validate(record)


@router.delete("/{record_id}")
def delete_bmi_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user),
):
    """Delete a BMI record."""
    record = db.query(BMIRecord).filter(
        BMIRecord.id == record_id,
        BMIRecord.user_id == current_user.id,
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="BMI record not found")
    
    db.delete(record)
    db.commit()
    return {"status": "deleted"}
