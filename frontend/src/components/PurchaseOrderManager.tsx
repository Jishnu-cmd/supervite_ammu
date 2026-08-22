import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { ShoppingBag, Sliders, Layers, PackageCheck } from 'lucide-react';
import type { PurchaseOrder } from '../types';
import { fetchPurchaseOrders } from '../services/api';

export const PurchaseOrderManager: FC = () => {
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPo, setSelectedPo] = useState<PurchaseOrder | null>(null);

  useEffect(() => {
    loadPOs();
  }, []);

  const loadPOs = async () => {
    try {
      setLoading(true);
      const data = await fetchPurchaseOrders();
      setPos(data);
      if (data.length > 0) setSelectedPo(data[0]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-800"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Purchase Order & Revision Management</h1>
          <p className="text-xs text-stone-500 mt-1">PO line authorizations, revision history, and cumulative partial invoicing tracking</p>
        </div>
        <div className="flex items-center space-x-2 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200 text-xs text-amber-900 font-bold">
          <Layers className="w-4 h-4 text-amber-800" />
          <span>Active PO Revisions: <strong className="text-amber-950">{pos.length}</strong></span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left List of POs */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-stone-200 p-5 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-stone-900 mb-2 flex items-center space-x-2">
            <ShoppingBag className="w-4 h-4 text-amber-800" />
            <span>Active Purchase Orders</span>
          </h3>

          {pos.map((po) => (
            <div
              key={po.id}
              onClick={() => setSelectedPo(po)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                selectedPo?.id === po.id
                  ? 'bg-amber-50 border-amber-800 ring-1 ring-amber-800'
                  : 'bg-stone-50 border-stone-200 hover:border-stone-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-stone-900">{po.po_number}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                  Rev #{po.current_revision}
                </span>
              </div>
              <p className="text-xs text-stone-500 mt-1">{po.vendor_name}</p>
              <div className="mt-3 flex items-center justify-between text-[11px] text-stone-500 pt-2 border-t border-stone-200">
                <span>Items: <strong className="text-stone-900">{po.line_items.length}</strong></span>
                <span>Status: <strong className="text-emerald-700">{po.status}</strong></span>
              </div>
            </div>
          ))}
        </div>

        {/* Right PO Line Item Details & Partial Invoicing Table */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-stone-200 p-6 shadow-sm space-y-6">
          {selectedPo ? (
            <>
              <div className="flex items-center justify-between border-b border-stone-200 pb-4">
                <div>
                  <h2 className="text-xl font-bold text-stone-900">{selectedPo.po_number} Details</h2>
                  <p className="text-xs text-stone-500">Vendor: {selectedPo.vendor_name} | Currency: {selectedPo.currency}</p>
                </div>
                <div className="flex items-center space-x-2 bg-stone-50 px-3 py-1.5 rounded-xl border border-stone-200 text-xs">
                  <Sliders className="w-4 h-4 text-amber-800" />
                  <span className="text-stone-700 font-medium">Default Price Tolerance: <strong className="text-amber-900 font-bold">2.0%</strong></span>
                </div>
              </div>

              {/* Line Items Partial Invoicing Balance Table */}
              <div>
                <h3 className="text-sm font-bold text-stone-900 mb-3 flex items-center space-x-2">
                  <PackageCheck className="w-4 h-4 text-emerald-700" />
                  <span>PO Line Item Balances (Partial Invoicing Tracker)</span>
                </h3>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-stone-700">
                    <thead className="bg-stone-100 text-stone-600 uppercase font-bold border-b border-stone-200">
                      <tr>
                        <th className="py-3 px-4">Line #</th>
                        <th className="py-3 px-4">SKU</th>
                        <th className="py-3 px-4">Description</th>
                        <th className="py-3 px-4 text-right">Authorized</th>
                        <th className="py-3 px-4 text-right">Invoiced</th>
                        <th className="py-3 px-4 text-right">Remaining</th>
                        <th className="py-3 px-4 text-right">Unit Price</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-200 font-mono">
                      {selectedPo.line_items.map((line) => (
                        <tr key={line.id} className="hover:bg-stone-50">
                          <td className="py-3.5 px-4 font-bold text-stone-500">{line.line_no}</td>
                          <td className="py-3.5 px-4 font-extrabold text-amber-900">{line.sku}</td>
                          <td className="py-3.5 px-4 font-sans text-stone-900">{line.description}</td>
                          <td className="py-3.5 px-4 text-right font-bold text-stone-900">{line.quantity_ordered} {line.uom}</td>
                          <td className="py-3.5 px-4 text-right font-bold text-amber-800">{line.quantity_invoiced || 0}</td>
                          <td className="py-3.5 px-4 text-right font-bold text-emerald-700">{line.quantity_remaining ?? line.quantity_ordered}</td>
                          <td className="py-3.5 px-4 text-right font-extrabold text-stone-900">${line.unit_price.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-stone-500 text-sm">Select a PO to view authorized lines</div>
          )}
        </div>
      </div>
    </div>
  );
};
