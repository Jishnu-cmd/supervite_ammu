import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import ExceptionRecord, Invoice
from app.schemas.schemas import ExceptionResponse, OverrideRequest
from app.services.audit_service import AuditService

router = APIRouter(prefix="/exceptions", tags=["exceptions"])

@router.get("/invoice/{invoice_id}", response_model=List[ExceptionResponse])
def get_invoice_exceptions(invoice_id: str, db: Session = Depends(get_db)):
    exceptions = db.query(ExceptionRecord).filter(ExceptionRecord.invoice_id == invoice_id).all()
    return exceptions

@router.post("/{exception_id}/override", response_model=ExceptionResponse)
def override_exception(
    exception_id: str, 
    req: OverrideRequest, 
    db: Session = Depends(get_db)
):
    """
    Reviewer override for an exception. Mandatory reason is recorded in audit log.
    Does NOT delete the original exception or rule execution record.
    """
    if not req.reason or len(req.reason.strip()) == 0:
        raise HTTPException(status_code=400, detail="Mandatory override reason is required")

    exc = db.query(ExceptionRecord).filter(ExceptionRecord.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception record not found")

    exc.status = "OVERRIDDEN" if req.action == "OVERRIDE" else "RESOLVED"
    exc.override_reason = req.reason
    exc.resolved_by = req.user_name
    exc.resolved_at = datetime.datetime.utcnow()

    # Log to Review Actions and Audit Trail
    AuditService.log_review_action(
        db=db,
        invoice_id=exc.invoice_id,
        exception_id=exc.id,
        action_type=req.action,
        user_name=req.user_name,
        reason=req.reason
    )

    # Check if all exceptions for invoice are resolved/overridden
    remaining_open = db.query(ExceptionRecord).filter(
        ExceptionRecord.invoice_id == exc.invoice_id,
        ExceptionRecord.status == "OPEN"
    ).count()

    invoice = db.query(Invoice).filter(Invoice.id == exc.invoice_id).first()
    if invoice and remaining_open == 0:
        invoice.processing_status = "APPROVED"

    db.commit()
    db.refresh(exc)
    return exc

@router.post("/invoice/{invoice_id}/approve")
def approve_invoice(invoice_id: str, req: OverrideRequest, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.processing_status = "APPROVED"
    
    # Resolve all open exceptions
    open_excs = db.query(ExceptionRecord).filter(
        ExceptionRecord.invoice_id == invoice_id,
        ExceptionRecord.status == "OPEN"
    ).all()

    for exc in open_excs:
        exc.status = "OVERRIDDEN"
        exc.override_reason = req.reason
        exc.resolved_by = req.user_name
        exc.resolved_at = datetime.datetime.utcnow()

    AuditService.log_review_action(
        db=db,
        invoice_id=invoice_id,
        action_type="APPROVE_INVOICE",
        user_name=req.user_name,
        reason=req.reason
    )

    db.commit()
    return {"message": f"Invoice {invoice.invoice_number} approved successfully"}
