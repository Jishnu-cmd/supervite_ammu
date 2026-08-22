export type BBox = [number, number, number, number];

export interface InvoiceLineItem {
  id: string;
  line_no: number;
  sku: string | null;
  description: string;
  quantity: number;
  uom: string;
  unit_price: number;
  line_total: number;
  tax_rate: number;
  tax_amount: number;
  confidence: number;
  page: number;
  bbox: BBox | null;
  source_text: string | null;
  match_status: string;
  match_confidence: number;
  matched_po_line_id: string | null;
}

export interface ExceptionRecord {
  id: string;
  exception_code: string;
  invoice_id: string;
  line_no: number | null;
  sku: string | null;
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  invoice_value: number | null;
  po_value: number | null;
  delta_abs: number | null;
  delta_pct: number | null;
  tolerance_allowed: number | null;
  rule_triggered: string;
  invoice_source_field: string | null;
  po_source_field: string | null;
  bbox: BBox | null;
  page: number;
  status: 'OPEN' | 'UNDER_REVIEW' | 'RESOLVED' | 'OVERRIDDEN' | 'REJECTED';
  override_reason: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  vendor_id: string | null;
  vendor_name?: string;
  po_number: string | null;
  po_revision_used: number | null;
  invoice_date: string | null;
  due_date: string | null;
  currency: string;
  subtotal: number;
  tax_rate: number;
  tax_total: number;
  invoice_total: number;
  document_filename: string | null;
  document_path: string | null;
  file_type: string | null;
  extraction_status: string;
  extraction_confidence: number;
  processing_status: 'NEW' | 'MATCHED' | 'EXCEPTION' | 'APPROVED' | 'REJECTED';
  created_at: string;
  updated_at: string;
  line_items: InvoiceLineItem[];
  exceptions: ExceptionRecord[];
}

export interface POLineItem {
  id: string;
  line_no: number;
  sku: string;
  description: string;
  quantity_ordered: number;
  quantity_invoiced?: number;
  quantity_remaining?: number;
  uom: string;
  unit_price: number;
  tax_rate: number;
  line_total: number;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  vendor_name: string;
  currency: string;
  current_revision: number;
  status: string;
  line_items: POLineItem[];
}

export interface ChatMessage {
  id: string;
  sender: 'USER' | 'ASSISTANT';
  message: string;
  sources?: string[];
  timestamp: string;
}

export interface DashboardSummary {
  total_invoices: number;
  pending_invoices: number;
  exception_invoices: number;
  resolved_exceptions: number;
  high_severity_exceptions: number;
  duplicate_invoices: number;
  average_processing_time_sec: number;
  exceptions_by_type: Record<string, number>;
  exceptions_by_severity: Record<string, number>;
  exceptions_by_vendor: Record<string, number>;
}

export interface AuditLog {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  user_id: string;
  details: any;
  timestamp: string;
}
