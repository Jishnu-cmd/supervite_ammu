import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

def generate_id():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_id)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False, default="AP_REVIEWER") # AP_REVIEWER, AP_MANAGER, ADMIN
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String, primary_key=True, default=generate_id)
    vendor_code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    contact_email = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")
    tolerances = relationship("ToleranceConfig", back_populates="vendor")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String, primary_key=True, default=generate_id)
    po_number = Column(String, unique=True, nullable=False, index=True)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    currency = Column(String, default="USD")
    current_revision_number = Column(Integer, default=1)
    status = Column(String, default="OPEN") # OPEN, CLOSED, CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="purchase_orders")
    revisions = relationship("PORevision", back_populates="purchase_order", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="purchase_order")

class PORevision(Base):
    __tablename__ = "po_revisions"

    id = Column(String, primary_key=True, default=generate_id)
    po_id = Column(String, ForeignKey("purchase_orders.id"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    effective_date = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)
    status = Column(String, default="ACTIVE")

    purchase_order = relationship("PurchaseOrder", back_populates="revisions")
    line_items = relationship("POLineItem", back_populates="revision", cascade="all, delete-orphan")

class POLineItem(Base):
    __tablename__ = "po_line_items"

    id = Column(String, primary_key=True, default=generate_id)
    revision_id = Column(String, ForeignKey("po_revisions.id"), nullable=False)
    line_no = Column(Integer, nullable=False)
    sku = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    quantity_ordered = Column(Float, nullable=False)
    uom = Column(String, nullable=False, default="EACH")
    unit_price = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0)
    line_total = Column(Float, nullable=False)

    revision = relationship("PORevision", back_populates="line_items")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=generate_id)
    invoice_number = Column(String, nullable=False, index=True)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    po_number = Column(String, ForeignKey("purchase_orders.po_number"), nullable=True, index=True)
    po_revision_used = Column(Integer, nullable=True)
    invoice_date = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    currency = Column(String, default="USD")
    
    subtotal = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    tax_total = Column(Float, default=0.0)
    invoice_total = Column(Float, default=0.0)

    # Document details
    document_filename = Column(String, nullable=True)
    document_path = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    fingerprint = Column(String, nullable=True, index=True)

    # Status tracking
    extraction_status = Column(String, default="COMPLETED") # COMPLETED, FAILED, UNCERTAIN
    extraction_confidence = Column(Float, default=1.0)
    processing_status = Column(String, default="NEW") # NEW, MATCHED, EXCEPTION, APPROVED, REJECTED
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="invoices")
    purchase_order = relationship("PurchaseOrder", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    exceptions = relationship("ExceptionRecord", back_populates="invoice", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="invoice", cascade="all, delete-orphan")
    review_actions = relationship("ReviewAction", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(String, primary_key=True, default=generate_id)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    line_no = Column(Integer, nullable=False)
    sku = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    uom = Column(String, nullable=False, default="EACH")
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)

    # Extraction source tracking
    confidence = Column(Float, default=0.95)
    page = Column(Integer, default=1)
    bbox = Column(JSON, nullable=True) # [x0, y0, x1, y1]
    source_text = Column(String, nullable=True)

    # Matching result
    matched_po_line_id = Column(String, nullable=True)
    match_status = Column(String, default="UNMATCHED") # MATCHED, PARTIAL_MATCH, UNMATCHED, LOW_CONFIDENCE_MATCH
    match_confidence = Column(Float, default=0.0)

    invoice = relationship("Invoice", back_populates="line_items")

class ExceptionRecord(Base):
    __tablename__ = "exceptions"

    id = Column(String, primary_key=True, default=generate_id)
    exception_code = Column(String, nullable=False, index=True) # e.g. EXC-INV1042-L1-PRICE
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False, index=True)
    line_no = Column(Integer, nullable=True)
    sku = Column(String, nullable=True)
    type = Column(String, nullable=False, index=True) # PRICE_MISMATCH, QTY_MISMATCH, TAX_RATE_MISMATCH, TAX_CALC_ERROR, LINE_NOT_ON_PO, OVER_PO_TOTAL, DUPLICATE_INVOICE, EXTRACTION_UNCERTAIN, UNIT_MISMATCH
    severity = Column(String, nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL

    invoice_value = Column(Float, nullable=True)
    po_value = Column(Float, nullable=True)
    delta_abs = Column(Float, nullable=True)
    delta_pct = Column(Float, nullable=True)
    tolerance_allowed = Column(Float, nullable=True)

    rule_triggered = Column(Text, nullable=False)
    invoice_source_field = Column(String, nullable=True)
    po_source_field = Column(String, nullable=True)
    bbox = Column(JSON, nullable=True)
    page = Column(Integer, default=1)

    status = Column(String, default="OPEN", index=True) # OPEN, UNDER_REVIEW, RESOLVED, OVERRIDDEN, REJECTED
    override_reason = Column(Text, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invoice = relationship("Invoice", back_populates="exceptions")

class ToleranceConfig(Base):
    __tablename__ = "tolerance_configs"

    id = Column(String, primary_key=True, default=generate_id)
    company_id = Column(String, default="DEFAULT_COMPANY")
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    po_id = Column(String, ForeignKey("purchase_orders.id"), nullable=True)

    price_variance_pct = Column(Float, default=2.0) # 2%
    quantity_variance_pct = Column(Float, default=0.0) # 0%
    tax_rounding_amount = Column(Float, default=0.01) # $0.01
    currency_variance = Column(Float, default=0.0)
    extraction_confidence_threshold = Column(Float, default=0.80)

    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="tolerances")

class InvoiceHistory(Base):
    __tablename__ = "invoice_history"

    id = Column(String, primary_key=True, default=generate_id)
    po_number = Column(String, nullable=False, index=True)
    sku = Column(String, nullable=False, index=True)
    invoice_number = Column(String, nullable=False)
    invoiced_quantity = Column(Float, nullable=False)
    invoiced_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(String, primary_key=True, default=generate_id)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    exception_id = Column(String, nullable=True)
    action_type = Column(String, nullable=False) # RESOLVE, OVERRIDE, APPROVE, REJECT, ESCALATE
    user_id = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    invoice = relationship("Invoice", back_populates="review_actions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_id)
    entity_type = Column(String, nullable=False) # INVOICE, EXCEPTION, PO, CHAT
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False) # UPLOAD, EXTRACT, MATCH, RECONCILE, OVERRIDE, CHAT
    user_id = Column(String, default="SYSTEM")
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=generate_id)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invoice = relationship("Invoice", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_id)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    sender = Column(String, nullable=False) # USER, ASSISTANT
    message = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True) # list of source field JSON pointers
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
