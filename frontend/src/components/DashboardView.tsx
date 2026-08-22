import { useEffect, useState } from 'react';
import type { FC } from 'react';
import { 
  FileCheck, AlertTriangle, CheckCircle2, Copy, Clock, TrendingUp, ShieldAlert, ArrowRight
} from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import type { DashboardSummary, Invoice } from '../types';
import { fetchDashboardSummary, fetchInvoices } from '../services/api';

interface DashboardProps {
  onSelectInvoice: (invoiceId: string) => void;
  onNavigateToQueue: () => void;
}

const COLORS = ['#92400e', '#d97706', '#b45309', '#059669', '#dc2626', '#78350f'];

export const DashboardView: FC<DashboardProps> = ({ onSelectInvoice, onNavigateToQueue }) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumData, invsData] = await Promise.all([
        fetchDashboardSummary(),
        fetchInvoices()
      ]);
      setSummary(sumData);
      setRecentInvoices(invsData.slice(0, 5));
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !summary) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-800"></div>
      </div>
    );
  }

  const exceptionTypeData = Object.entries(summary.exceptions_by_type).map(([name, value]) => ({
    name: name.replace('_', ' '),
    value
  }));

  const vendorData = Object.entries(summary.exceptions_by_vendor).map(([name, count]) => ({
    name: name.length > 18 ? name.substring(0, 18) + '...' : name,
    count
  }));

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-amber-950 via-[#361e10] to-amber-950 p-6 rounded-2xl border border-amber-900/40 shadow-xl flex flex-wrap items-center justify-between gap-4 text-white">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">AP Invoice Exception Analytics</h1>
          <p className="text-xs text-amber-200/80 mt-1">
            Deterministic matching rule engine results & source-grounded exception monitoring.
          </p>
        </div>
        <div className="flex items-center space-x-3 bg-amber-900/50 px-4 py-2 rounded-xl border border-amber-700/50">
          <Clock className="w-5 h-5 text-amber-400" />
          <span className="text-xs text-amber-100">Avg Rule Execution: <strong className="text-amber-300">{summary.average_processing_time_sec}s</strong></span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Processed */}
        <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-stone-500 uppercase tracking-wider">Total Processed</span>
            <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center text-amber-800">
              <FileCheck className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-stone-900 mt-2">{summary.total_invoices}</p>
          <span className="text-xs text-stone-500 mt-1 block">Invoices evaluated</span>
        </div>

        {/* Exceptions Flagged */}
        <div className="bg-white p-5 rounded-2xl border border-rose-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider">Exceptions Flagged</span>
            <div className="w-8 h-8 rounded-lg bg-rose-100 flex items-center justify-center text-rose-700">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-rose-700 mt-2">{summary.exception_invoices}</p>
          <span className="text-xs text-rose-600/80 mt-1 block">Requiring AP review</span>
        </div>

        {/* High Severity */}
        <div className="bg-white p-5 rounded-2xl border border-amber-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wider">High / Critical</span>
            <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center text-amber-800">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-amber-800 mt-2">{summary.high_severity_exceptions}</p>
          <span className="text-xs text-amber-700/80 mt-1 block">Price / Qty / Duplicate</span>
        </div>

        {/* Duplicate Flagged */}
        <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-stone-700 uppercase tracking-wider">Duplicates</span>
            <div className="w-8 h-8 rounded-lg bg-stone-100 flex items-center justify-center text-stone-700">
              <Copy className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-stone-800 mt-2">{summary.duplicate_invoices}</p>
          <span className="text-xs text-stone-500 mt-1 block">Identified by engine</span>
        </div>

        {/* Resolved / Overridden */}
        <div className="bg-white p-5 rounded-2xl border border-emerald-200 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Resolved</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-700">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-extrabold text-emerald-700 mt-2">{summary.resolved_exceptions}</p>
          <span className="text-xs text-emerald-600/80 mt-1 block">Reviewer override logged</span>
        </div>
      </div>

      {/* Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Exception Types Breakdown */}
        <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm">
          <h3 className="text-sm font-bold text-stone-900 mb-4 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-800" />
            <span>Exceptions by Rule Type</span>
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={exceptionTypeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {exceptionTypeData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e7e5e4', borderRadius: '8px', color: '#1c1917' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Vendor Exception Volume */}
        <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm">
          <h3 className="text-sm font-bold text-stone-900 mb-4 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-amber-800" />
            <span>Vendor Exception Frequency</span>
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={vendorData}>
                <XAxis dataKey="name" stroke="#78716c" fontSize={12} />
                <YAxis stroke="#78716c" fontSize={12} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e7e5e4', borderRadius: '8px', color: '#1c1917' }}
                />
                <Bar dataKey="count" fill="#92400e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Invoices Table */}
      <div className="bg-white rounded-2xl border border-stone-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-stone-200 flex items-center justify-between bg-stone-50/50">
          <div>
            <h3 className="text-base font-bold text-stone-900">Recent Invoices Needing Review</h3>
            <p className="text-xs text-slate-500 mt-0.5">Click any invoice to launch visual split-screen reviewer workspace</p>
          </div>
          <button
            onClick={onNavigateToQueue}
            className="flex items-center space-x-1.5 text-xs text-amber-800 hover:text-amber-900 font-bold"
          >
            <span>View All Invoices</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-stone-700">
            <thead className="bg-stone-100 text-xs uppercase text-stone-500 border-b border-stone-200">
              <tr>
                <th className="py-3.5 px-6 font-bold">Invoice #</th>
                <th className="py-3.5 px-6 font-bold">PO #</th>
                <th className="py-3.5 px-6 font-bold">Date</th>
                <th className="py-3.5 px-6 font-bold">Total Amount</th>
                <th className="py-3.5 px-6 font-bold">Status</th>
                <th className="py-3.5 px-6 font-bold">Exceptions</th>
                <th className="py-3.5 px-6 font-bold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-200">
              {recentInvoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-stone-50 transition-colors">
                  <td className="py-4 px-6 font-extrabold text-stone-900">{inv.invoice_number}</td>
                  <td className="py-4 px-6 font-bold text-amber-800">{inv.po_number || 'N/A'}</td>
                  <td className="py-4 px-6 text-stone-500">{inv.invoice_date || 'N/A'}</td>
                  <td className="py-4 px-6 font-bold text-stone-900">${inv.invoice_total.toFixed(2)}</td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                      inv.processing_status === 'EXCEPTION' 
                        ? 'bg-rose-100 text-rose-800 border border-rose-200' 
                        : inv.processing_status === 'APPROVED'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : 'bg-amber-100 text-amber-800 border border-amber-200'
                    }`}>
                      {inv.processing_status}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex flex-wrap gap-1">
                      {inv.exceptions.map((exc) => (
                        <span key={exc.id} className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                          {exc.type}
                        </span>
                      ))}
                      {inv.exceptions.length === 0 && (
                        <span className="text-xs text-emerald-700 font-medium">✅ Clean Match</span>
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => onSelectInvoice(inv.id)}
                      className="px-3.5 py-1.5 bg-amber-800 hover:bg-amber-900 text-white rounded-xl text-xs font-bold shadow-md shadow-amber-900/20 transition-all"
                    >
                      Review & Ask AI
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
