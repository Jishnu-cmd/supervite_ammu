import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { ShieldCheck } from 'lucide-react';
import type { AuditLog } from '../types';
import { fetchAuditLogs } from '../services/api';

export const AuditTrailView: FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await fetchAuditLogs();
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-stone-200 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">System Audit & Compliance Log</h1>
          <p className="text-xs text-stone-500 mt-1">Immutable record of document uploads, rule executions, reviewer overrides, and AI chat sessions</p>
        </div>
        <div className="flex items-center space-x-2 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200 text-xs text-emerald-800 font-bold">
          <ShieldCheck className="w-4 h-4 text-emerald-700" />
          <span>Immutable Audit Log Active</span>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-stone-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center min-h-[40vh]">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-800"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-stone-700">
              <thead className="bg-stone-100 text-stone-600 uppercase font-bold border-b border-stone-200">
                <tr>
                  <th className="py-3.5 px-6">Timestamp</th>
                  <th className="py-3.5 px-6">Entity</th>
                  <th className="py-3.5 px-6">Action</th>
                  <th className="py-3.5 px-6">User</th>
                  <th className="py-3.5 px-6">Details & Override Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-200 font-mono">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-stone-50 transition-colors">
                    <td className="py-4 px-6 text-stone-500">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-4 px-6">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                        {log.entity_type}:{log.entity_id.substring(0, 8)}
                      </span>
                    </td>
                    <td className="py-4 px-6 font-bold text-stone-900">
                      {log.action}
                    </td>
                    <td className="py-4 px-6 text-stone-700 font-sans">
                      {log.user_id}
                    </td>
                    <td className="py-4 px-6 font-sans text-stone-800">
                      <pre className="text-[11px] text-stone-700 whitespace-pre-wrap bg-stone-50 p-2.5 rounded-xl border border-stone-200 max-w-lg shadow-inner">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
