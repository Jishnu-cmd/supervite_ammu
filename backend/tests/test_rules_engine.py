import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.models import (
    Vendor, PurchaseOrder, PORevision, POLineItem, Invoice, InvoiceLineItem, ToleranceConfig
)
from app.services.rules_engine import DeterministicRuleEngine
from app.services.normalization_service import NormalizationService
from app.services.matching_service import LineItemMatchingEngine

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_normalization_uom():
    assert NormalizationService.normalize_uom("Box of 12") == "BOX_12"
    assert NormalizationService.normalize_uom("ea") == "EACH"
    assert NormalizationService.are_uoms_compatible("ea", "EACH") is True

def test_matching_engine():
    inv_line = InvoiceLineItem(
        id="inv_l1", line_no=1, sku="BOLT-M8-40", description="M8 Bolt Zinc", quantity=500, unit_price=0.42, uom="EACH"
    )
    po_line = POLineItem(
        id="po_l1", revision_id="r1", line_no=1, sku="BOLT-M8-40", description="M8 Bolt Zinc", quantity_ordered=500, unit_price=0.38, uom="EACH", line_total=190.0
    )
    results = LineItemMatchingEngine.match_line_items([inv_line], [po_line])
    assert len(results) == 1
    assert results[0]["status"] == "MATCHED"
    assert results[0]["po_line_id"] == "po_l1"

def test_demo_price_qty_tax_exceptions(db_session):
    # Setup Vendor & PO
    vendor = Vendor(vendor_code="V1", name="Acme Test")
    db_session.add(vendor)
    db_session.commit()

    po = PurchaseOrder(po_number="PO-88213", vendor_id=vendor.id, currency="USD")
    db_session.add(po)
    db_session.commit()

    rev = PORevision(po_id=po.id, revision_number=1, status="ACTIVE")
    db_session.add(rev)
    db_session.commit()

    po_line = POLineItem(
        revision_id=rev.id, line_no=1, sku="BOLT-M8-40", description="M8 Bolt", quantity_ordered=500.0, uom="EACH", unit_price=0.38, tax_rate=8.25, line_total=190.0
    )
    db_session.add(po_line)
    db_session.commit()

    # Create Invoice 1042 ($0.42 vs $0.38 price, 550 qty vs 500 ordered, bad tax calc)
    inv = Invoice(
        invoice_number="INV-1042", vendor_id=vendor.id, po_number="PO-88213", currency="USD",
        subtotal=231.00, tax_rate=8.25, tax_total=17.33, invoice_total=248.33
    )
    db_session.add(inv)
    db_session.commit()

    inv_line = InvoiceLineItem(
        invoice_id=inv.id, line_no=1, sku="BOLT-M8-40", description="M8 Bolt", quantity=550.0, uom="EACH", unit_price=0.42, line_total=231.00, tax_rate=8.25, tax_amount=17.33
    )
    db_session.add(inv_line)
    db_session.commit()

    tolerance = ToleranceConfig(price_variance_pct=2.0, tax_rounding_amount=0.01)
    exceptions = DeterministicRuleEngine.evaluate_invoice(db_session, inv, po, tolerance)

    exc_types = [e.type for e in exceptions]
    assert "PRICE_MISMATCH" in exc_types
    assert "QTY_MISMATCH" in exc_types
    assert "TAX_CALC_ERROR" in exc_types

    price_exc = next(e for e in exceptions if e.type == "PRICE_MISMATCH")
    assert price_exc.invoice_value == 0.42
    assert price_exc.po_value == 0.38
    assert price_exc.delta_pct == 10.53 or round(price_exc.delta_pct, 1) == 10.5
