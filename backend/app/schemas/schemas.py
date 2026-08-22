from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

# Bounding Box Coordinate Model [x0, y0, x1, y1]
BBox = List[float]

class FieldMetadata(BaseModel):
    value: Any
    confidence: float = 1.0
    page: int = 1
    bbox: Optional[BBox] = None
    source_text: Optional[str] = None

# Line item schema for Invoice Extraction
class ExtractedInvoiceLineItem(BaseModel):
    line_no: int
    sku: Optional[str] = None
    description: str
    quantity: float
    uom: str = "EACH"
    unit_price: float
    line_total: float
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    confidence: float = 0.95
    page: int = 1
    bbox: Optional[BBox] = None
    source_text: Optional[str] = None

# Canonical Invoice Schema
class ExtractedInvoice(BaseModel):
    invoice_number: str
    vendor_name: str
    invoice_date: str
    po_number: Optional[str] = None
    currency: str = "USD"
    subtotal: float
    tax_rate: float = 0.0
    tax_total: float = 0.0
    invoice_total: float
    line_items: List[ExtractedInvoiceLineItem] = []
    extraction_confidence: float = 0.95

# Line item schema for PO
class POLineItemSchema(BaseModel):
    id: Optional[str] = None
    line_no: int
    sku: str
    description: str
    quantity_ordered: float
    uom: str = "EACH"
    unit_price: float
    tax_rate: float = 0.0
    line_total: float

class POSchema(BaseModel):
    id: Optional[str] = None
    po_number: str
    vendor_name: str
    currency: str = "USD"
    current_revision_number: int = 1
    status: str = "OPEN"
    line_items: List[POLineItemSchema] = []

class InvoiceLineItemResponse(BaseModel):
    id: str
    line_no: int
    sku: Optional[str]
    description: str
    quantity: float
    uom: str
    unit_price: float
    line_total: float
    tax_rate: float
    tax_amount: float
    confidence: float
    page: int
    bbox: Optional[BBox]
    source_text: Optional[str]
    match_status: str
    match_confidence: float
    matched_po_line_id: Optional[str]

    class Config:
        from_attributes = True

class ExceptionResponse(BaseModel):
    id: str
    exception_code: str
    invoice_id: str
    line_no: Optional[int]
    sku: Optional[str]
    type: str
    severity: str
    invoice_value: Optional[float]
    po_value: Optional[float]
    delta_abs: Optional[float]
    delta_pct: Optional[float]
    tolerance_allowed: Optional[float]
    rule_triggered: str
    invoice_source_field: Optional[str]
    po_source_field: Optional[str]
    bbox: Optional[BBox]
    page: int
    status: str
    override_reason: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    vendor_id: Optional[str]
    vendor_name: Optional[str] = None
    po_number: Optional[str]
    po_revision_used: Optional[int]
    invoice_date: Optional[str]
    due_date: Optional[str]
    currency: str
    subtotal: float
    tax_rate: float
    tax_total: float
    invoice_total: float
    document_filename: Optional[str]
    document_path: Optional[str]
    file_type: Optional[str]
    extraction_status: str
    extraction_confidence: float
    processing_status: str
    created_at: datetime
    updated_at: datetime
    line_items: List[InvoiceLineItemResponse] = []
    exceptions: List[ExceptionResponse] = []

    class Config:
        from_attributes = True

class ChatMessageRequest(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    id: str
    sender: str
    message: str
    sources: Optional[List[str]] = []
    timestamp: datetime

    class Config:
        from_attributes = True

class OverrideRequest(BaseModel):
    action: str # RESOLVE, OVERRIDE, REJECT
    reason: str
    user_name: str = "AP Reviewer"

class ToleranceConfigRequest(BaseModel):
    price_variance_pct: float = 2.0
    quantity_variance_pct: float = 0.0
    tax_rounding_amount: float = 0.01
    extraction_confidence_threshold: float = 0.80

class DashboardSummaryResponse(BaseModel):
    total_invoices: int
    pending_invoices: int
    exception_invoices: int
    resolved_exceptions: int
    high_severity_exceptions: int
    duplicate_invoices: int
    average_processing_time_sec: float
    exceptions_by_type: Dict[str, int]
    exceptions_by_severity: Dict[str, int]
    exceptions_by_vendor: Dict[str, int]
