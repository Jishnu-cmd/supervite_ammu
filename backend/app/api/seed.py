from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    Vendor, PurchaseOrder, PORevision, POLineItem, Invoice, InvoiceLineItem,
    ToleranceConfig, InvoiceHistory
)
from app.services.rules_engine import DeterministicRuleEngine
from app.services.audit_service import AuditService

router = APIRouter(prefix="/seed", tags=["seed"])

@router.post("")
def seed_demo_data(db: Session = Depends(get_db)):
    """
    Seeds database with PRD Section 39 Demo Scenarios:
    PO-88213 and Invoices INV-1042 (Price/Qty/Tax Mismatch), INV-1043 (Line Not on PO), INV-1044 (Clean Match).
    """
    # Clear existing tables for seed reset
    db.query(InvoiceLineItem).delete()
    db.query(Invoice).delete()
    db.query(POLineItem).delete()
    db.query(PORevision).delete()
    db.query(PurchaseOrder).delete()
    db.query(ToleranceConfig).delete()
    db.query(InvoiceHistory).delete()
    db.query(Vendor).delete()
    db.commit()

    # 1. Create Vendor
    vendor = Vendor(
        vendor_code="VEND-ACME-882",
        name="Acme Industrial Fasteners Inc.",
        contact_email="ap@acmefasteners.com",
        tax_id="US-9982314"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    # 2. Tolerance Config (Price 2%, Tax 0.01)
    tol = ToleranceConfig(
        vendor_id=vendor.id,
        price_variance_pct=2.0,
        quantity_variance_pct=0.0,
        tax_rounding_amount=0.01,
        extraction_confidence_threshold=0.80
    )
    db.add(tol)

    # 3. Create PO-88213
    po = PurchaseOrder(
        po_number="PO-88213",
        vendor_id=vendor.id,
        currency="USD",
        current_revision_number=1,
        status="OPEN"
    )
    db.add(po)
    db.commit()
    db.refresh(po)

    rev = PORevision(
        po_id=po.id,
        revision_number=1,
        status="ACTIVE",
        notes="Standard Purchase Order Authorization Revision 1"
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)

    po_line1 = POLineItem(
        revision_id=rev.id,
        line_no=1,
        sku="BOLT-M8-40",
        description="M8 x 40 Hex Bolt, Zinc Plated Grade 8.8",
        quantity_ordered=500.0,
        uom="EACH",
        unit_price=0.38,
        tax_rate=8.25,
        line_total=190.00
    )
    po_line2 = POLineItem(
        revision_id=rev.id,
        line_no=2,
        sku="NUT-M8-ZINC",
        description="M8 Hex Nut, Zinc Plated",
        quantity_ordered=1000.0,
        uom="EACH",
        unit_price=0.12,
        tax_rate=8.25,
        line_total=120.00
    )
    db.add(po_line1)
    db.add(po_line2)
    db.commit()

    # 4. Invoiced History (Partial Billing Tracking)
    # No previous billing for BOLT-M8-40, so 500 remaining.
    
    # 5. Create Demo Invoice 1: INV-1042 (PRD Section 39 Scenario)
    inv1 = Invoice(
        invoice_number="INV-1042",
        vendor_id=vendor.id,
        po_number="PO-88213",
        po_revision_used=1,
        invoice_date="2026-08-22",
        currency="USD",
        subtotal=231.00,
        tax_rate=8.25,
        tax_total=17.33, # Note: 231.00 * 8.25% should be 19.06 -> TAX_CALC_ERROR!
        invoice_total=248.33,
        document_filename="Invoice_1042_AcmeFasteners.pdf",
        extraction_status="COMPLETED",
        extraction_confidence=0.97,
        processing_status="NEW"
    )
    db.add(inv1)
    db.commit()
    db.refresh(inv1)

    inv1_l1 = InvoiceLineItem(
        invoice_id=inv1.id,
        line_no=1,
        sku="BOLT-M8-40",
        description="M8 x 40 Hex Bolt, Zinc Plated Grade 8.8",
        quantity=550.0, # 550 invoiced > 500 remaining -> QTY_MISMATCH!
        uom="EACH",
        unit_price=0.42, # $0.42 vs $0.38 PO -> 10.5% variance > 2% allowed -> PRICE_MISMATCH!
        line_total=231.00,
        tax_rate=8.25,
        tax_amount=17.33,
        confidence=0.98,
        page=1,
        bbox=[120.0, 420.0, 520.0, 450.0],
        source_text="BOLT-M8-40 M8 x 40 Hex Bolt 550 EACH $0.42 $231.00",
        match_status="UNMATCHED"
    )
    db.add(inv1_l1)
    db.commit()

    # Run Rule Engine on INV-1042
    excs1 = DeterministicRuleEngine.evaluate_invoice(db=db, invoice=inv1, po=po, tolerance_config=tol)
    for exc in excs1:
        db.add(exc)
    inv1.processing_status = "EXCEPTION" if excs1 else "MATCHED"
    db.commit()

    # 6. Create Demo Invoice 2: INV-1043 (Unauthorized Line Not on PO)
    inv2 = Invoice(
        invoice_number="INV-1043",
        vendor_id=vendor.id,
        po_number="PO-88213",
        po_revision_used=1,
        invoice_date="2026-08-21",
        currency="USD",
        subtotal=150.00,
        tax_rate=8.25,
        tax_total=12.38,
        invoice_total=162.38,
        document_filename="Invoice_1043_AcmeFasteners.pdf",
        extraction_status="COMPLETED",
        extraction_confidence=0.95,
        processing_status="NEW"
    )
    db.add(inv2)
    db.commit()
    db.refresh(inv2)

    inv2_l1 = InvoiceLineItem(
        invoice_id=inv2.id,
        line_no=1,
        sku="WASHER-M8-SPECIAL",
        description="M8 Stainless Special Sealing Washer",
        quantity=100.0,
        uom="EACH",
        unit_price=1.50,
        line_total=150.00,
        tax_rate=8.25,
        tax_amount=12.38,
        confidence=0.96,
        page=1,
        bbox=[120.0, 420.0, 520.0, 450.0],
        source_text="WASHER-M8-SPECIAL M8 Stainless Special Sealing Washer 100 EACH $1.50 $150.00"
    )
    db.add(inv2_l1)
    db.commit()

    excs2 = DeterministicRuleEngine.evaluate_invoice(db=db, invoice=inv2, po=po, tolerance_config=tol)
    for exc in excs2:
        db.add(exc)
    inv2.processing_status = "EXCEPTION" if excs2 else "MATCHED"
    db.commit()

    # 7. Create Demo Invoice 3: INV-1044 (Clean Match Invoice)
    inv3 = Invoice(
        invoice_number="INV-1044",
        vendor_id=vendor.id,
        po_number="PO-88213",
        po_revision_used=1,
        invoice_date="2026-08-19",
        currency="USD",
        subtotal=60.00,
        tax_rate=8.25,
        tax_total=4.95,
        invoice_total=64.95,
        document_filename="Invoice_1044_AcmeFasteners.pdf",
        extraction_status="COMPLETED",
        extraction_confidence=0.99,
        processing_status="NEW"
    )
    db.add(inv3)
    db.commit()
    db.refresh(inv3)

    inv3_l1 = InvoiceLineItem(
        invoice_id=inv3.id,
        line_no=1,
        sku="NUT-M8-ZINC",
        description="M8 Hex Nut, Zinc Plated",
        quantity=500.0,
        uom="EACH",
        unit_price=0.12,
        line_total=60.00,
        tax_rate=8.25,
        tax_amount=4.95,
        confidence=0.99,
        page=1,
        bbox=[120.0, 420.0, 520.0, 450.0],
        source_text="NUT-M8-ZINC M8 Hex Nut Zinc Plated 500 EACH $0.12 $60.00"
    )
    db.add(inv3_l1)
    db.commit()

    excs3 = DeterministicRuleEngine.evaluate_invoice(db=db, invoice=inv3, po=po, tolerance_config=tol)
    for exc in excs3:
        db.add(exc)
    inv3.processing_status = "MATCHED"
    db.commit()

    # Record Audit Log
    AuditService.log_event(
        db=db,
        entity_type="SYSTEM",
        entity_id="SEED",
        action="SEED_DEMO_DATA",
        details={"invoices_created": 3, "po_created": "PO-88213"}
    )

    return {"message": "Demo data successfully seeded!", "po_number": "PO-88213", "invoices": ["INV-1042", "INV-1043", "INV-1044"]}
