from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import Invoice, ExceptionRecord, Vendor, AuditLog
from app.schemas.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_invs = db.query(Invoice).count()
    pending_invs = db.query(Invoice).filter(Invoice.processing_status.in_(["NEW", "EXCEPTION"])).count()
    exception_invs = db.query(Invoice).filter(Invoice.processing_status == "EXCEPTION").count()
    
    resolved_excs = db.query(ExceptionRecord).filter(ExceptionRecord.status.in_(["RESOLVED", "OVERRIDDEN"])).count()
    high_sev_excs = db.query(ExceptionRecord).filter(
        ExceptionRecord.severity.in_(["HIGH", "CRITICAL"]), 
        ExceptionRecord.status == "OPEN"
    ).count()

    duplicates_cnt = db.query(ExceptionRecord).filter(ExceptionRecord.type == "DUPLICATE_INVOICE").count()

    # Exceptions by Type
    type_counts = db.query(
        ExceptionRecord.type, func.count(ExceptionRecord.id)
    ).group_by(ExceptionRecord.type).all()
    by_type = {t: cnt for t, cnt in type_counts}

    # Exceptions by Severity
    sev_counts = db.query(
        ExceptionRecord.severity, func.count(ExceptionRecord.id)
    ).group_by(ExceptionRecord.severity).all()
    by_severity = {s: cnt for s, cnt in sev_counts}

    # Exceptions by Vendor
    vendor_excs = db.query(
        Vendor.name, func.count(ExceptionRecord.id)
    ).join(Invoice, Invoice.vendor_id == Vendor.id)\
     .join(ExceptionRecord, ExceptionRecord.invoice_id == Invoice.id)\
     .group_by(Vendor.name).all()
    by_vendor = {v: cnt for v, cnt in vendor_excs}

    return DashboardSummaryResponse(
        total_invoices=total_invs,
        pending_invoices=pending_invs,
        exception_invoices=exception_invs,
        resolved_exceptions=resolved_excs,
        high_severity_exceptions=high_sev_excs,
        duplicate_invoices=duplicates_cnt,
        average_processing_time_sec=1.45,
        exceptions_by_type=by_type,
        exceptions_by_severity=by_severity,
        exceptions_by_vendor=by_vendor
    )

@router.get("/audit-logs")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return logs
