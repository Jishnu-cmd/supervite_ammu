import type { Invoice, PurchaseOrder, ChatMessage, DashboardSummary, ExceptionRecord, AuditLog } from '../types';

const API_BASE = 'http://127.0.0.1:8080/api/v1';

export const fetchInvoices = async (): Promise<Invoice[]> => {
  const res = await fetch(`${API_BASE}/invoices`);
  if (!res.ok) throw new Error('Failed to fetch invoices');
  return res.json();
};

export const fetchInvoiceById = async (id: string): Promise<Invoice> => {
  const res = await fetch(`${API_BASE}/invoices/${id}`);
  if (!res.ok) throw new Error('Failed to fetch invoice details');
  return res.json();
};

export const uploadInvoice = async (file: File, poNumber?: string): Promise<Invoice> => {
  const formData = new FormData();
  formData.append('file', file);
  if (poNumber) formData.append('po_number', poNumber);

  const res = await fetch(`${API_BASE}/invoices/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
};

export const fetchPurchaseOrders = async (): Promise<PurchaseOrder[]> => {
  const res = await fetch(`${API_BASE}/purchase-orders`);
  if (!res.ok) throw new Error('Failed to fetch purchase orders');
  return res.json();
};

export const overrideException = async (
  exceptionId: string, 
  action: 'RESOLVE' | 'OVERRIDE' | 'REJECT', 
  reason: string,
  userName: string = 'AP Reviewer'
): Promise<ExceptionRecord> => {
  const res = await fetch(`${API_BASE}/exceptions/${exceptionId}/override`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, reason, user_name: userName }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Action failed');
  }
  return res.json();
};

export const approveInvoice = async (invoiceId: string, reason: string): Promise<any> => {
  const res = await fetch(`${API_BASE}/exceptions/invoice/${invoiceId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'APPROVE', reason, user_name: 'AP Reviewer' }),
  });
  if (!res.ok) throw new Error('Failed to approve invoice');
  return res.json();
};

export const sendChatMessage = async (invoiceId: string, message: string): Promise<ChatMessage> => {
  const res = await fetch(`${API_BASE}/chat/invoice/${invoiceId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error('Failed to send chat message');
  return res.json();
};

export const fetchChatHistory = async (invoiceId: string): Promise<ChatMessage[]> => {
  const res = await fetch(`${API_BASE}/chat/invoice/${invoiceId}/history`);
  if (!res.ok) return [];
  return res.json();
};

export const fetchDashboardSummary = async (): Promise<DashboardSummary> => {
  const res = await fetch(`${API_BASE}/dashboard/summary`);
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
};

export const fetchAuditLogs = async (): Promise<AuditLog[]> => {
  const res = await fetch(`${API_BASE}/dashboard/audit-logs`);
  if (!res.ok) return [];
  return res.json();
};

export const seedDemoData = async (): Promise<any> => {
  const res = await fetch(`${API_BASE}/seed`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to seed demo data');
  return res.json();
};
