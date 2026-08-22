from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.models import PurchaseOrder, PORevision, POLineItem, Vendor, InvoiceHistory

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

class POLineItemCreate(BaseModel):
    line_no: int
    sku: str
    description: str
    quantity_ordered: float
    uom: str = "EACH"
    unit_price: float
    tax_rate: float = 0.0

class POCreateRequest(BaseModel):
    po_number: str
    vendor_name: str
    currency: str = "USD"
    line_items: List[POLineItemCreate]

@router.get("")
def list_purchase_orders(db: Session = Depends(get_db)):
    pos = db.query(PurchaseOrder).all()
    res = []
    for po in pos:
        vendor = db.query(Vendor).filter(Vendor.id == po.vendor_id).first()
        active_rev = db.query(PORevision).filter(
            PORevision.po_id == po.id, 
            PORevision.revision_number == po.current_revision_number
        ).first()
        lines = active_rev.line_items if active_rev else []
        
        # Calculate remaining quantity for partial invoicing history
        line_items_data = []
        for line in lines:
            prev_history = db.query(InvoiceHistory).filter(
                InvoiceHistory.po_number == po.po_number,
                InvoiceHistory.sku == line.sku
            ).all()
            cum_invoiced = sum(h.invoiced_quantity for h in prev_history)
            line_items_data.append({
                "id": line.id,
                "line_no": line.line_no,
                "sku": line.sku,
                "description": line.description,
                "quantity_ordered": line.quantity_ordered,
                "quantity_invoiced": cum_invoiced,
                "quantity_remaining": max(0.0, line.quantity_ordered - cum_invoiced),
                "uom": line.uom,
                "unit_price": line.unit_price,
                "tax_rate": line.tax_rate,
                "line_total": line.line_total
            })

        res.append({
            "id": po.id,
            "po_number": po.po_number,
            "vendor_name": vendor.name if vendor else "Unknown",
            "currency": po.currency,
            "current_revision": po.current_revision_number,
            "status": po.status,
            "line_items": line_items_data
        })
    return res

@router.get("/{po_number}")
def get_purchase_order(po_number: str, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    vendor = db.query(Vendor).filter(Vendor.id == po.vendor_id).first()
    revisions = []

    for rev in po.revisions:
        revisions.append({
            "revision_number": rev.revision_number,
            "effective_date": rev.effective_date,
            "status": rev.status,
            "notes": rev.notes,
            "line_items": [
                {
                    "line_no": line.line_no,
                    "sku": line.sku,
                    "description": line.description,
                    "quantity_ordered": line.quantity_ordered,
                    "uom": line.uom,
                    "unit_price": line.unit_price,
                    "tax_rate": line.tax_rate,
                    "line_total": line.line_total
                } for line in rev.line_items
            ]
        })

    return {
        "id": po.id,
        "po_number": po.po_number,
        "vendor_name": vendor.name if vendor else "Unknown",
        "currency": po.currency,
        "current_revision": po.current_revision_number,
        "status": po.status,
        "revisions": revisions
    }

@router.post("")
def create_purchase_order(req: POCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == req.po_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="PO number already exists")

    vendor = db.query(Vendor).filter(Vendor.name.ilike(f"%{req.vendor_name}%")).first()
    if not vendor:
        vendor = Vendor(vendor_code=f"VEND-{req.po_number[:5]}", name=req.vendor_name)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)

    po = PurchaseOrder(
        po_number=req.po_number,
        vendor_id=vendor.id,
        currency=req.currency,
        current_revision_number=1,
        status="OPEN"
    )
    db.add(po)
    db.commit()
    db.refresh(po)

    rev = PORevision(po_id=po.id, revision_number=1, status="ACTIVE", notes="Initial PO Creation")
    db.add(rev)
    db.commit()
    db.refresh(rev)

    for item in req.line_items:
        line_tot = round(item.quantity_ordered * item.unit_price, 2)
        po_line = POLineItem(
            revision_id=rev.id,
            line_no=item.line_no,
            sku=item.sku,
            description=item.description,
            quantity_ordered=item.quantity_ordered,
            uom=item.uom,
            unit_price=item.unit_price,
            tax_rate=item.tax_rate,
            line_total=line_tot
        )
        db.add(po_line)

    db.commit()
    return {"message": "PO created successfully", "po_number": po.po_number}
