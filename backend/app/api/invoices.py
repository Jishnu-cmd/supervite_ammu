import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.models import (
    Invoice, InvoiceLineItem, PurchaseOrder, ExceptionRecord, Vendor, ToleranceConfig
)
from app.schemas.schemas import InvoiceResponse
from app.services.document_service import DocumentService
from app.services.extraction_service import ExtractionService
from app.services.rules_engine import DeterministicRuleEngine
from app.services.audit_service import AuditService

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.post("/upload", response_model=InvoiceResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    po_number: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload invoice PDF/Image, perform extraction, match lines against PO,
    execute deterministic rule engine, store structured exceptions.
    """
    if not file.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, PNG, or JPEG.")

    # Save original file
    file_bytes = await file.read()
    fingerprint = DocumentService.calculate_file_hash(file_bytes)
    
    file_location = os.path.join(settings.UPLOAD_DIR, f"{fingerprint}_{file.filename}")
    with open(file_location, "wb") as f:
        f.write(file_bytes)

    # Step 1: Perform Document Extraction
    extracted_data, confidence = ExtractionService.extract_invoice_data(file_location, file.filename)

    # Determine PO Number
    target_po_no = po_number or extracted_data.po_number or "PO-88213"

    # Find Vendor or Create Default
    vendor = db.query(Vendor).filter(Vendor.name.ilike(f"%{extracted_data.vendor_name}%")).first()
    if not vendor:
        vendor = db.query(Vendor).first()
    if not vendor:
        vendor = Vendor(vendor_code="VEND-001", name=extracted_data.vendor_name or "Acme Supplies Inc.")
        db.add(vendor)
        db.commit()
        db.refresh(vendor)

    # Find PO
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == target_po_no).first()

    # Step 2: Save Invoice & Line Items
    db_invoice = Invoice(
        invoice_number=extracted_data.invoice_number,
        vendor_id=vendor.id if vendor else None,
        po_number=target_po_no,
        po_revision_used=po.current_revision_number if po else 1,
        invoice_date=extracted_data.invoice_date,
        currency=extracted_data.currency,
        subtotal=extracted_data.subtotal,
        tax_rate=extracted_data.tax_rate,
        tax_total=extracted_data.tax_total,
        invoice_total=extracted_data.invoice_total,
        document_filename=file.filename,
        document_path=file_location,
        file_type=file.content_type,
        fingerprint=fingerprint,
        extraction_status="COMPLETED" if confidence >= 0.80 else "UNCERTAIN",
        extraction_confidence=confidence,
        processing_status="NEW"
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    for item in extracted_data.line_items:
        db_line = InvoiceLineItem(
            invoice_id=db_invoice.id,
            line_no=item.line_no,
            sku=item.sku,
            description=item.description,
            quantity=item.quantity,
            uom=item.uom,
            unit_price=item.unit_price,
            line_total=item.line_total,
            tax_rate=item.tax_rate,
            tax_amount=item.tax_amount,
            confidence=item.confidence,
            page=item.page,
            bbox=item.bbox,
            source_text=item.source_text,
            match_status="UNMATCHED"
        )
        db.add(db_line)

    db.commit()
    db.refresh(db_invoice)

    # Step 3: Execute Deterministic Reconciliation Rules Engine
    tolerance_cfg = db.query(ToleranceConfig).filter(
        (ToleranceConfig.vendor_id == vendor.id) | (ToleranceConfig.company_id == "DEFAULT_COMPANY")
    ).first()

    exceptions = DeterministicRuleEngine.evaluate_invoice(
        db=db, 
        invoice=db_invoice, 
        po=po, 
        tolerance_config=tolerance_cfg
    )

    # Save Exception objects to Exception Store
    for exc in exceptions:
        db.add(exc)

    db_invoice.processing_status = "EXCEPTION" if len(exceptions) > 0 else "MATCHED"
    db.commit()
    db.refresh(db_invoice)

    # Audit Trail Log
    AuditService.log_event(
        db=db,
        entity_type="INVOICE",
        entity_id=db_invoice.id,
        action="UPLOAD_AND_RECONCILE",
        details={
            "invoice_number": db_invoice.invoice_number,
            "po_number": target_po_no,
            "exceptions_count": len(exceptions),
            "status": db_invoice.processing_status
        }
    )

    return db_invoice

@router.get("", response_model=List[InvoiceResponse])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    return invoices

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/{invoice_id}/reconcile", response_model=InvoiceResponse)
def reconcile_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == invoice.po_number).first()
    
    # Delete old exceptions
    db.query(ExceptionRecord).filter(ExceptionRecord.invoice_id == invoice.id).delete()

    tolerance_cfg = db.query(ToleranceConfig).first()
    exceptions = DeterministicRuleEngine.evaluate_invoice(db=db, invoice=invoice, po=po, tolerance_config=tolerance_cfg)

    for exc in exceptions:
        db.add(exc)

    invoice.processing_status = "EXCEPTION" if len(exceptions) > 0 else "MATCHED"
    db.commit()
    db.refresh(invoice)

    AuditService.log_event(
        db=db,
        entity_type="INVOICE",
        entity_id=invoice.id,
        action="RECONCILE",
        details={"exceptions_count": len(exceptions)}
    )

    return invoice
