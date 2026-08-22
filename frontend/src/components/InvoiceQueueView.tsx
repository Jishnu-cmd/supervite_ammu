import { useState, useEffect } from 'react';
import type { FC, FormEvent } from 'react';
import { Search, Upload, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import type { Invoice } from '../types';
import { fetchInvoices, uploadInvoice } from '../services/api';

interface InvoiceQueueProps {
  onSelectInvoice: (invoiceId: string) => void;
  showUploadModal: boolean;
  setShowUploadModal: (show: boolean) => void;
}

export const InvoiceQueueView: FC<InvoiceQueueProps> = ({ 
  onSelectInvoice, showUploadModal, setShowUploadModal 
}) => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'EXCEPTION' | 'APPROVED' | 'MATCHED'>('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  
  // Upload modal state
  const [file, setFile] = useState<File | null>(null);
  const [poNumber, setPoNumber] = useState('PO-88213');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const data = await fetchInvoices();
      setInvoices(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;

    try {
      setUploading(true);
      setUploadError(null);
      const newInv = await uploadInvoice(file, poNumber);
      setShowUploadModal(false);
      setFile(null);
      await loadInvoices();
      onSelectInvoice(newInv.id);
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const filteredInvoices = invoices.filter(inv => {
    if (filter === 'EXCEPTION' && inv.processing_status !== 'EXCEPTION') return false;
    if (filter === 'APPROVED' && inv.processing_status !== 'APPROVED') return false;
    if (filter === 'MATCHED' && inv.processing_status !== 'MATCHED') return false;

    if (search) {
      const q = search.toLowerCase();
      return (
        inv.invoice_number.toLowerCase().includes(q) ||
        (inv.po_number && inv.po_number.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-stone-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Invoice Processing Queue</h1>
          <p className="text-xs text-stone-500 mt-1">Manage invoice extractions, matching results, and deterministic exceptions</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadInvoices}
            className="p-2.5 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl border border-stone-300 transition-colors"
            title="Refresh list"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-amber-800 hover:bg-amber-900 text-white rounded-xl font-bold text-xs shadow-lg shadow-amber-900/20 transition-all"
          >
            <Upload className="w-4 h-4" />
            <span>Upload New Invoice</span>
          </button>
        </div>
      </div>

      {/* Search & Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by Invoice # or PO #..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-white border border-stone-300 rounded-xl pl-10 pr-4 py-2 text-sm text-stone-900 focus:outline-none focus:border-amber-800 transition-colors shadow-sm"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-2 bg-white p-1.5 rounded-xl border border-stone-200 shadow-sm w-full sm:w-auto overflow-x-auto">
          {(['ALL', 'EXCEPTION', 'MATCHED', 'APPROVED'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                filter === tab 
                  ? 'bg-amber-800 text-white shadow-sm' 
                  : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Invoice Grid Cards */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-800"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredInvoices.map((inv) => (
            <div
              key={inv.id}
              onClick={() => onSelectInvoice(inv.id)}
              className="bg-white rounded-2xl border border-stone-200 p-6 hover:border-amber-700/60 hover:shadow-xl transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-extrabold text-amber-900 tracking-wide uppercase">#{inv.invoice_number}</span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                    inv.processing_status === 'EXCEPTION' 
                      ? 'bg-rose-100 text-rose-800 border border-rose-200' 
                      : inv.processing_status === 'APPROVED'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                      : 'bg-amber-100 text-amber-800 border border-amber-200'
                  }`}>
                    {inv.processing_status}
                  </span>
                </div>

                <h4 className="text-base font-bold text-stone-900 group-hover:text-amber-800 transition-colors">
                  PO: {inv.po_number || 'Unlinked'}
                </h4>
                <p className="text-xs text-stone-500 mt-1">Date: {inv.invoice_date || 'N/A'}</p>

                <div className="mt-4 pt-4 border-t border-stone-100 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-stone-400 uppercase tracking-wider block font-bold">Billed Total</span>
                    <span className="text-lg font-extrabold text-stone-900">${inv.invoice_total.toFixed(2)}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-stone-400 uppercase tracking-wider block font-bold">Extraction Confidence</span>
                    <span className="text-xs font-bold text-emerald-700">{Math.round(inv.extraction_confidence * 100)}%</span>
                  </div>
                </div>
              </div>

              {/* Exception Badges Footer */}
              <div className="mt-4 pt-3 border-t border-stone-100 flex items-center justify-between">
                <div className="flex flex-wrap gap-1">
                  {inv.exceptions.slice(0, 2).map((exc) => (
                    <span key={exc.id} className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                      {exc.type}
                    </span>
                  ))}
                  {inv.exceptions.length > 2 && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-stone-100 text-stone-600">
                      +{inv.exceptions.length - 2}
                    </span>
                  )}
                  {inv.exceptions.length === 0 && (
                    <span className="text-xs text-emerald-700 font-bold flex items-center space-x-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Passed Clean</span>
                    </span>
                  )}
                </div>

                <span className="text-xs font-bold text-amber-800 group-hover:translate-x-1 transition-transform">
                  Review &rarr;
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-stone-200 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-stone-200 pb-3">
              <h3 className="text-base font-bold text-stone-900 flex items-center space-x-2">
                <Upload className="w-4 h-4 text-amber-800" />
                <span>Upload Invoice Document</span>
              </h3>
              <button onClick={() => setShowUploadModal(false)} className="text-stone-400 hover:text-stone-900">✕</button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Target Purchase Order Number</label>
                <input
                  type="text"
                  value={poNumber}
                  onChange={(e) => setPoNumber(e.target.value)}
                  placeholder="e.g. PO-88213"
                  className="w-full bg-stone-50 border border-stone-300 rounded-xl px-3.5 py-2 text-sm text-stone-900 focus:outline-none focus:border-amber-800"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-stone-700 mb-1">Select File (PDF, PNG, JPEG)</label>
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-stone-500 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-amber-800 file:text-white hover:file:bg-amber-900"
                  required
                />
              </div>

              {uploadError && (
                <div className="p-3 bg-rose-100 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center space-x-2 font-medium">
                  <AlertCircle className="w-4 h-4" />
                  <span>{uploadError}</span>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 bg-stone-100 text-stone-700 rounded-xl text-xs font-bold hover:bg-stone-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !file}
                  className="px-5 py-2 bg-amber-800 hover:bg-amber-900 text-white rounded-xl text-xs font-bold shadow-lg shadow-amber-900/20 disabled:opacity-50"
                >
                  {uploading ? 'Processing & Extracting...' : 'Upload & Reconcile'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
