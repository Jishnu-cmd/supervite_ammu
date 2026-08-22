import { useState, useEffect, useRef } from 'react';
import type { FC, FormEvent } from 'react';
import { 
  ArrowLeft, AlertTriangle, CheckCircle, ShieldAlert, FileText, Send, 
  Sparkles, CheckCircle2
} from 'lucide-react';
import type { Invoice, ExceptionRecord, ChatMessage, BBox } from '../types';
import { fetchInvoiceById, sendChatMessage, fetchChatHistory, overrideException, approveInvoice } from '../services/api';

interface ReviewWorkspaceProps {
  invoiceId: string;
  onBack: () => void;
}

export const InvoiceReviewWorkspace: FC<ReviewWorkspaceProps> = ({ invoiceId, onBack }) => {
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [highlightedBBox, setHighlightedBBox] = useState<BBox | null>(null);
  const [selectedException, setSelectedException] = useState<ExceptionRecord | null>(null);

  // Override Modal State
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [overrideAction, setOverrideAction] = useState<'OVERRIDE' | 'RESOLVE'>('OVERRIDE');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideSubmitting, setOverrideSubmitting] = useState(false);

  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadInvoiceDetails();
  }, [invoiceId]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadInvoiceDetails = async () => {
    try {
      const invData = await fetchInvoiceById(invoiceId);
      setInvoice(invData);
      if (invData.exceptions.length > 0) {
        setSelectedException(invData.exceptions[0]);
        if (invData.exceptions[0].bbox) {
          setHighlightedBBox(invData.exceptions[0].bbox);
        }
      }

      const history = await fetchChatHistory(invoiceId);
      setMessages(history);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendMessage = async (msgText?: string) => {
    const textToSend = msgText || chatInput;
    if (!textToSend.trim() || chatLoading) return;

    try {
      setChatLoading(true);
      setChatInput('');
      
      const tempUserMsg: ChatMessage = {
        id: Date.now().toString(),
        sender: 'USER',
        message: textToSend,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, tempUserMsg]);

      const asstResponse = await sendChatMessage(invoiceId, textToSend);
      setMessages(prev => [...prev, asstResponse]);
    } catch (err) {
      console.error(err);
    } finally {
      setChatLoading(false);
    }
  };

  const handleOverrideSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedException || !overrideReason.trim()) return;

    try {
      setOverrideSubmitting(true);
      await overrideException(selectedException.id, overrideAction, overrideReason);
      setShowOverrideModal(false);
      setOverrideReason('');
      await loadInvoiceDetails();
    } catch (err) {
      console.error(err);
    } finally {
      setOverrideSubmitting(false);
    }
  };

  const handleApproveAll = async () => {
    const reason = prompt("Enter mandatory approval reason note:");
    if (!reason) return;

    try {
      await approveInvoice(invoiceId, reason);
      await loadInvoiceDetails();
    } catch (err) {
      console.error(err);
    }
  };

  if (!invoice) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-800"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Workspace Top Header Bar */}
      <div className="bg-white px-6 py-4 rounded-2xl border border-stone-200 flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="p-2 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl transition-colors border border-stone-300"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-3">
              <h2 className="text-xl font-extrabold text-stone-900">Invoice #{invoice.invoice_number}</h2>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                invoice.processing_status === 'EXCEPTION' 
                  ? 'bg-rose-100 text-rose-800 border border-rose-200' 
                  : invoice.processing_status === 'APPROVED'
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  : 'bg-amber-100 text-amber-800 border border-amber-200'
              }`}>
                {invoice.processing_status}
              </span>
            </div>
            <p className="text-xs text-stone-500 mt-0.5">PO Linked: <strong className="text-amber-900 font-bold">{invoice.po_number}</strong> | Date: {invoice.invoice_date}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleApproveAll}
            className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-700/20 transition-all"
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Approve Invoice</span>
          </button>
        </div>
      </div>

      {/* Main Split View Layout (Left: PDF Canvas, Right: Exceptions & AI Assistant) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT PANEL: Document Viewer Canvas with Bounding Box Overlay */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-stone-200 p-5 shadow-sm flex flex-col h-[750px]">
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-stone-200">
            <h3 className="text-sm font-bold text-stone-900 flex items-center space-x-2">
              <FileText className="w-4 h-4 text-amber-800" />
              <span>Extracted Invoice Document View</span>
            </h3>
            {highlightedBBox && (
              <span className="text-xs text-amber-900 bg-amber-100 px-2 py-0.5 rounded border border-amber-300 font-semibold">
                🎯 Source Region Highlighted
              </span>
            )}
          </div>

          {/* Interactive Simulated Document Canvas */}
          <div className="relative flex-1 bg-stone-50 rounded-xl border border-stone-300 p-6 overflow-auto font-mono text-xs text-stone-800 shadow-inner">
            {/* Header Document Mock Rendering */}
            <div className="border-b border-stone-300 pb-4 mb-6 flex justify-between items-start">
              <div>
                <span className="text-lg font-extrabold text-stone-900 block font-sans">INVOICE</span>
                <span className="text-xs text-stone-600 font-sans">Acme Industrial Fasteners Inc.</span>
              </div>
              <div className="text-right">
                <span className="text-xs text-stone-600 block">Inv #: <strong className="text-stone-900">{invoice.invoice_number}</strong></span>
                <span className="text-xs text-stone-600 block">PO #: <strong className="text-amber-800 font-bold">{invoice.po_number}</strong></span>
                <span className="text-xs text-stone-600 block">Date: {invoice.invoice_date}</span>
              </div>
            </div>

            {/* Line Items Table Rendering */}
            <div className="space-y-4">
              <div className="grid grid-cols-12 font-bold text-stone-500 border-b border-stone-300 pb-2 text-[11px]">
                <span className="col-span-2">SKU</span>
                <span className="col-span-4">DESCRIPTION</span>
                <span className="col-span-2 text-right">QTY</span>
                <span className="col-span-2 text-right">PRICE</span>
                <span className="col-span-2 text-right">TOTAL</span>
              </div>

              {invoice.line_items.map((line) => (
                <div 
                  key={line.id} 
                  onClick={() => line.bbox && setHighlightedBBox(line.bbox)}
                  className={`grid grid-cols-12 py-2 px-1 rounded-lg transition-colors cursor-pointer relative ${
                    highlightedBBox && JSON.stringify(highlightedBBox) === JSON.stringify(line.bbox)
                      ? 'bg-amber-100 border border-amber-500 ring-2 ring-amber-500/50'
                      : 'hover:bg-stone-200/60'
                  }`}
                >
                  <span className="col-span-2 font-bold text-amber-900">{line.sku || 'N/A'}</span>
                  <span className="col-span-4 text-stone-800 font-sans">{line.description}</span>
                  <span className="col-span-2 text-right text-stone-900 font-bold">{line.quantity} {line.uom}</span>
                  <span className="col-span-2 text-right text-stone-900 font-bold">${line.unit_price.toFixed(2)}</span>
                  <span className="col-span-2 text-right text-stone-900 font-extrabold">${line.line_total.toFixed(2)}</span>

                  {/* Visual Bounding Box Overlay Marker */}
                  {line.bbox && (
                    <div className="absolute right-2 top-1 text-[9px] text-amber-900 bg-amber-200/90 px-1 rounded border border-amber-400 font-bold">
                      [{line.bbox.join(', ')}]
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Totals Section */}
            <div className="mt-8 pt-4 border-t border-stone-300 max-w-xs ml-auto space-y-1.5 text-right font-sans">
              <div className="flex justify-between text-xs">
                <span className="text-stone-600">Subtotal:</span>
                <span className="text-stone-900 font-bold">${invoice.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-stone-600">Tax ({invoice.tax_rate}%):</span>
                <span className="text-stone-900 font-bold">${invoice.tax_total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm font-extrabold pt-2 border-t border-stone-300">
                <span className="text-stone-900">Total Billed:</span>
                <span className="text-amber-900">${invoice.invoice_total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: Top Exception Details + Bottom AI Grounded Explanation Assistant */}
        <div className="lg:col-span-6 space-y-6 flex flex-col h-[750px]">
          
          {/* Top Panel: Exception List & Resolution */}
          <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-stone-900 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span>Deterministic Exceptions ({invoice.exceptions.length})</span>
              </h3>
              <span className="text-xs text-stone-500 font-medium">Single Source of Truth Evidence</span>
            </div>

            {invoice.exceptions.length === 0 ? (
              <div className="p-4 bg-emerald-100 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center space-x-2 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                <span>No reconciliation exceptions were detected. Invoice passed clean.</span>
              </div>
            ) : (
              <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                {invoice.exceptions.map((exc) => (
                  <div
                    key={exc.id}
                    onClick={() => {
                      setSelectedException(exc);
                      if (exc.bbox) setHighlightedBBox(exc.bbox);
                    }}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                      selectedException?.id === exc.id
                        ? 'bg-amber-50 border-amber-700 ring-1 ring-amber-700'
                        : 'bg-stone-50 border-stone-200 hover:border-stone-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          exc.severity === 'CRITICAL' || exc.severity === 'HIGH'
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : 'bg-amber-100 text-amber-900 border border-amber-200'
                        }`}>
                          {exc.type}
                        </span>
                        <span className="text-xs font-bold text-stone-900">Line {exc.line_no || 'Header'}</span>
                      </div>

                      <span className={`text-[10px] font-bold ${
                        exc.status === 'OVERRIDDEN' || exc.status === 'RESOLVED'
                          ? 'text-emerald-700'
                          : 'text-amber-800'
                      }`}>
                        {exc.status}
                      </span>
                    </div>

                    <p className="text-xs text-stone-700 mt-2 font-mono">{exc.rule_triggered}</p>

                    {exc.invoice_value !== null && exc.po_value !== null && (
                      <div className="mt-2 flex items-center space-x-4 text-[11px] text-stone-600 pt-2 border-t border-stone-200">
                        <span>Invoice: <strong className="text-stone-900">${exc.invoice_value}</strong></span>
                        <span>PO Authorized: <strong className="text-amber-900">${exc.po_value}</strong></span>
                        {exc.delta_pct !== null && (
                          <span>Variance: <strong className="text-rose-700">{exc.delta_pct}%</strong></span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Selected Exception Actions */}
            {selectedException && selectedException.status === 'OPEN' && (
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  onClick={() => {
                    setOverrideAction('RESOLVE');
                    setShowOverrideModal(true);
                  }}
                  className="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-lg text-xs font-bold border border-stone-300"
                >
                  Resolve
                </button>
                <button
                  onClick={() => {
                    setOverrideAction('OVERRIDE');
                    setShowOverrideModal(true);
                  }}
                  className="px-3.5 py-1.5 bg-amber-800 hover:bg-amber-900 text-white rounded-lg text-xs font-bold shadow-md shadow-amber-900/20"
                >
                  Override Exception
                </button>
              </div>
            )}
          </div>

          {/* Bottom Panel: AI Assistant Chat (Grounded Explanations) */}
          <div className="bg-white rounded-2xl border border-stone-200 p-5 shadow-sm flex-1 flex flex-col min-h-0">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-amber-800" />
                <h3 className="text-sm font-bold text-stone-900">Source-Grounded AI Explanation Assistant</h3>
              </div>
              <span className="text-[10px] text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded border border-emerald-200 font-bold">
                100% Non-Hallucinating
              </span>
            </div>

            {/* Quick Prompts Chips */}
            <div className="flex items-center space-x-2 my-2 overflow-x-auto pb-1">
              <button
                onClick={() => handleSendMessage("Why was this invoice flagged?")}
                className="px-2.5 py-1 bg-stone-100 hover:bg-stone-200 text-amber-900 rounded-full text-[11px] font-bold border border-stone-300 whitespace-nowrap"
              >
                ❓ Why flagged?
              </button>
              <button
                onClick={() => handleSendMessage("Is the tax calculation correct?")}
                className="px-2.5 py-1 bg-stone-100 hover:bg-stone-200 text-amber-900 rounded-full text-[11px] font-bold border border-stone-300 whitespace-nowrap"
              >
                🧾 Check Tax
              </button>
              <button
                onClick={() => handleSendMessage("Show price delta for line 1")}
                className="px-2.5 py-1 bg-stone-100 hover:bg-stone-200 text-amber-900 rounded-full text-[11px] font-bold border border-stone-300 whitespace-nowrap"
              >
                💵 Price Delta
              </button>
              <button
                onClick={() => handleSendMessage("What about verbal amendments?")}
                className="px-2.5 py-1 bg-stone-100 hover:bg-stone-200 text-amber-900 rounded-full text-[11px] font-bold border border-stone-300 whitespace-nowrap"
              >
                🗣️ Verbal Amendment
              </button>
            </div>

            {/* Chat Stream Messages Box */}
            <div className="flex-1 overflow-y-auto space-y-3 my-2 pr-1">
              {messages.length === 0 ? (
                <div className="text-center py-8 text-stone-500 text-xs">
                  Ask any question about why this invoice was flagged, line item price variances, quantities, or tax checks.
                </div>
              ) : (
                messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex flex-col ${m.sender === 'USER' ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl p-3.5 text-xs whitespace-pre-wrap ${
                        m.sender === 'USER'
                          ? 'bg-amber-800 text-white rounded-br-none shadow-sm'
                          : 'bg-stone-50 text-stone-800 border border-stone-200 rounded-bl-none shadow-sm'
                      }`}
                    >
                      {m.message}

                      {/* Source Field Citations */}
                      {m.sources && m.sources.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-stone-200 flex flex-wrap items-center gap-1.5">
                          <span className="text-[10px] text-stone-500 font-bold">Sources:</span>
                          {m.sources.map((src, idx) => (
                            <button
                              key={idx}
                              onClick={() => {
                                const item = invoice.line_items.find(l => src.includes(`line_items[${l.line_no - 1}]`));
                                if (item && item.bbox) setHighlightedBBox(item.bbox);
                              }}
                              className="px-2 py-0.5 bg-white hover:bg-stone-100 text-amber-900 rounded text-[10px] font-mono border border-stone-300 font-bold transition-colors"
                            >
                              📍 {src}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    <span className="text-[9px] text-stone-400 mt-1 px-1">{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                ))
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Chat Input Form */}
            <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="flex items-center space-x-2 pt-2 border-t border-stone-200">
              <input
                type="text"
                placeholder="Ask the AI assistant why this invoice was flagged..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                className="flex-1 bg-stone-50 border border-stone-300 rounded-xl px-4 py-2.5 text-xs text-stone-900 focus:outline-none focus:border-amber-800"
              />
              <button
                type="submit"
                disabled={chatLoading || !chatInput.trim()}
                className="p-2.5 bg-amber-800 hover:bg-amber-900 text-white rounded-xl shadow-md shadow-amber-900/20 disabled:opacity-50 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Override Reason Modal */}
      {showOverrideModal && selectedException && (
        <div className="fixed inset-0 z-50 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-stone-200 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-stone-900 flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-amber-800" />
              <span>Record Mandatory Exception {overrideAction}</span>
            </h3>

            <p className="text-xs text-stone-600">
              You are overriding exception <strong className="text-amber-900 font-bold">{selectedException.type}</strong> on Line {selectedException.line_no}. This action will be immutably recorded in the system audit trail.
            </p>

            <form onSubmit={handleOverrideSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Mandatory Override Reason Note</label>
                <textarea
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="e.g. Approved commercial price adjustment authorized by Procurement VP"
                  className="w-full bg-stone-50 border border-stone-300 rounded-xl p-3 text-xs text-stone-900 focus:outline-none focus:border-amber-800"
                  required
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowOverrideModal(false)}
                  className="px-4 py-2 bg-stone-100 text-stone-700 rounded-xl text-xs font-bold hover:bg-stone-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={overrideSubmitting || !overrideReason.trim()}
                  className="px-5 py-2 bg-amber-800 hover:bg-amber-900 text-white rounded-xl text-xs font-bold shadow-lg shadow-amber-900/20 disabled:opacity-50"
                >
                  {overrideSubmitting ? 'Recording Audit...' : 'Confirm Override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
