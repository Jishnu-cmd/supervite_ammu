import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardView } from './components/DashboardView';
import { InvoiceQueueView } from './components/InvoiceQueueView';
import { InvoiceReviewWorkspace } from './components/InvoiceReviewWorkspace';
import { PurchaseOrderManager } from './components/PurchaseOrderManager';
import { AuditTrailView } from './components/AuditTrailView';
import { seedDemoData } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'queue' | 'review' | 'pos' | 'audit'>('dashboard');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const handleSelectInvoice = (id: string) => {
    setSelectedInvoiceId(id);
    setActiveTab('review');
  };

  const handleSeedData = async () => {
    try {
      await seedDemoData();
      setNotification('Demo data (PRD Section 39 Demo Scenario) seeded successfully!');
      setTimeout(() => setNotification(null), 4000);
      if (activeTab === 'dashboard') {
        window.location.reload();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-stone-100 text-stone-900 flex font-sans">
      {/* Left Sidebar Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onSeedClick={handleSeedData}
        onUploadClick={() => {
          setActiveTab('queue');
          setShowUploadModal(true);
        }}
      />

      {/* Main Content Container (Padded left by 16rem / 64 tailwind units for left sidebar) */}
      <div className="flex-1 pl-64 flex flex-col min-h-screen">
        {/* Notification Toast */}
        {notification && (
          <div className="fixed bottom-6 right-6 z-50 bg-amber-800 text-white px-5 py-3 rounded-2xl shadow-2xl font-semibold text-xs animate-bounce flex items-center space-x-2 border border-amber-700">
            <span>✨</span>
            <span>{notification}</span>
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
          {activeTab === 'dashboard' && (
            <DashboardView
              onSelectInvoice={handleSelectInvoice}
              onNavigateToQueue={() => setActiveTab('queue')}
            />
          )}

          {activeTab === 'queue' && (
            <InvoiceQueueView
              onSelectInvoice={handleSelectInvoice}
              showUploadModal={showUploadModal}
              setShowUploadModal={setShowUploadModal}
            />
          )}

          {activeTab === 'review' && selectedInvoiceId && (
            <InvoiceReviewWorkspace
              invoiceId={selectedInvoiceId}
              onBack={() => setActiveTab('queue')}
            />
          )}

          {activeTab === 'pos' && (
            <PurchaseOrderManager />
          )}

          {activeTab === 'audit' && (
            <AuditTrailView />
          )}
        </main>

        {/* Global Footer */}
        <footer className="bg-stone-200/80 border-t border-stone-300/60 py-4 text-center text-xs text-stone-600 font-medium">
          AP Invoice Exception Assistant &copy; 2026. Deterministic Reconciliation Engine & Grounded AI Explanation Architecture.
        </footer>
      </div>
    </div>
  );
}

export default App;
