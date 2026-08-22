import type { FC } from 'react';
import { ShieldCheck, LayoutDashboard, FileText, ShoppingBag, History, Database, Upload, UserCheck } from 'lucide-react';

interface NavbarProps {
  activeTab: 'dashboard' | 'queue' | 'review' | 'pos' | 'audit';
  setActiveTab: (tab: 'dashboard' | 'queue' | 'review' | 'pos' | 'audit') => void;
  onSeedClick: () => void;
  onUploadClick: () => void;
}

export const Navbar: FC<NavbarProps> = ({ activeTab, setActiveTab, onSeedClick, onUploadClick }) => {
  return (
    <aside className="w-64 bg-[#21140e] text-stone-200 border-r border-amber-950/40 flex flex-col fixed left-0 top-0 bottom-0 z-50 shadow-2xl">
      {/* Sidebar Header / Brand Logo */}
      <div className="p-5 border-b border-amber-950/60 flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-700 to-amber-500 flex items-center justify-center shadow-lg shadow-amber-900/40">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div>
          <span className="font-bold text-base text-white tracking-tight block">AP Invoice Assistant</span>
          <span className="text-[10px] text-amber-400 font-medium tracking-wide">Deterministic + AI Rules</span>
        </div>
      </div>

      {/* Vertical Navigation Items */}
      <div className="flex-1 py-6 px-3 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-amber-500/70">Main Navigation</div>

        <button
          onClick={() => setActiveTab('dashboard')}
          className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'dashboard'
              ? 'bg-amber-700 text-white shadow-lg shadow-amber-900/30'
              : 'text-stone-300 hover:text-white hover:bg-amber-950/50'
          }`}
        >
          <LayoutDashboard className="w-4 h-4 text-amber-400" />
          <span>Dashboard</span>
        </button>

        <button
          onClick={() => setActiveTab('queue')}
          className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'queue' || activeTab === 'review'
              ? 'bg-amber-700 text-white shadow-lg shadow-amber-900/30'
              : 'text-stone-300 hover:text-white hover:bg-amber-950/50'
          }`}
        >
          <FileText className="w-4 h-4 text-amber-400" />
          <span>Invoice Queue</span>
        </button>

        <button
          onClick={() => setActiveTab('pos')}
          className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'pos'
              ? 'bg-amber-700 text-white shadow-lg shadow-amber-900/30'
              : 'text-stone-300 hover:text-white hover:bg-amber-950/50'
          }`}
        >
          <ShoppingBag className="w-4 h-4 text-amber-400" />
          <span>PO Manager</span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'audit'
              ? 'bg-amber-700 text-white shadow-lg shadow-amber-900/30'
              : 'text-stone-300 hover:text-white hover:bg-amber-950/50'
          }`}
        >
          <History className="w-4 h-4 text-amber-400" />
          <span>Audit Trail</span>
        </button>
      </div>

      {/* Action Buttons & User Profile Footer */}
      <div className="p-4 border-t border-amber-950/60 space-y-2.5 bg-[#190e0a]">
        <button
          onClick={onUploadClick}
          className="w-full flex items-center justify-center space-x-2 py-2.5 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white rounded-xl text-xs font-bold shadow-lg shadow-amber-900/30 transition-all"
        >
          <Upload className="w-4 h-4" />
          <span>Upload Invoice</span>
        </button>

        <button
          onClick={onSeedClick}
          className="w-full flex items-center justify-center space-x-2 py-2 bg-amber-950/80 hover:bg-amber-900/60 text-amber-300 border border-amber-800/40 rounded-xl text-xs font-semibold transition-colors"
        >
          <Database className="w-3.5 h-3.5 text-amber-400" />
          <span>Seed Demo Data</span>
        </button>

        <div className="pt-2 flex items-center space-x-2.5 text-xs text-stone-400">
          <div className="w-7 h-7 rounded-full bg-amber-800 flex items-center justify-center text-white font-bold text-[10px]">
            <UserCheck className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-bold text-white block text-[11px]">AP Reviewer</span>
            <span className="text-[10px] text-amber-400/80 block">Finance Ops Team</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
