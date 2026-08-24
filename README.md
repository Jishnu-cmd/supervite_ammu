# AP Invoice Exception Assistant 🤖🧾

An AI-powered Accounts Payable (AP) invoice reconciliation and exception management system built on the core architectural invariant:

> **"AI extracts and explains; deterministic software validates and decides."**

---

## 🌟 Key Product Architecture & Principles

Traditional AI invoice processing attempts to hand two PDFs to an LLM and ask it to find differences. This produces hallucinations and unreliable financial calculations. 

The **AP Invoice Exception Assistant** separates concerns strictly:
1. **Document Extraction**: Schema-constrained extraction of invoice PDF/images (fields, line items, confidence scores, and page bounding box coordinates).
2. **Data Normalization**: Standardizing currencies, SKUs, and units of measure (e.g. `Box of 12` -> `12 EACH`).
3. **Multi-Stage Line Matching Engine**: Multi-tier matching (Exact SKU → Normalized SKU → RapidFuzz description similarity → Price Proximity).
4. **Deterministic Exception Engine (Pure Python)**: Pure business rule evaluations (`PRICE_MISMATCH`, `QTY_MISMATCH`, `TAX_RATE_MISMATCH`, `TAX_CALC_ERROR`, `LINE_NOT_ON_PO`, `DUPLICATE_INVOICE`, `OVER_PO_TOTAL`).
5. **Single Source of Truth Exception Store**: Structured evidence objects preserving raw values, deltas, variances, allowed tolerances, and field JSON pointers.
6. **Source-Grounded AI Explanation Assistant**: Interactive chat enforcing strict non-hallucination guardrails, answering user questions strictly using stored evidence and providing clickable source field citations that highlight the visual document bounding box.

---

## 🎨 UI & Design Highlights

- **Left Vertical Sidebar Layout**: Clean fixed navigation sidebar with quick action shortcuts.
- **Warm Brown & White Palette**: Deep espresso & bronze accents (`#21140e`, `amber-800`), clean off-white stone backgrounds (`bg-stone-100`), and crisp white card containers (`bg-white border-stone-200`).
- **Interactive Split-Screen Review Workspace**:
  - **Left**: Simulated PDF Document Viewer Canvas with visual bounding-box highlights.
  - **Right Top**: Exception summary cards, severity badges, variance deltas, and mandatory override note modals.
  - **Right Bottom**: Source-Grounded AI Assistant Chat with quick question chips (`Why flagged?`, `Check Tax`, `Price Delta`, `Verbal Amendment`).
- **AP Dashboard**: Recharts exception type breakdown pie chart, vendor problem frequency bar chart, and KPI metric cards.
- **PO Manager**: Cumulative partial invoicing balance tracker showing ordered, invoiced, and remaining line item quantities across PO revisions.
- **Immutable Audit Trail**: Compliance activity log recording uploads, rule executions, reviewer overrides, and chat sessions.

---

## 💻 Recommended Tech Stack

### Backend
- **Python 3.11** + **FastAPI**
- **Pydantic v2** (Canonical Schemas)
- **SQLAlchemy** + **SQLite**
- **RapidFuzz** (Fuzzy line item description matching)
- **PyMuPDF / pdfplumber** (PDF text & bounding box coordinate extraction)
- **Google Gemini API** (Schema extraction & grounded explanations, with intelligent fallback)
- **Pytest** (Automated unit tests)

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS**
- **Lucide Icons**
- **Recharts** (Interactive AP Analytics)

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm

### 1. Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```
- **API Base URL**: `http://127.0.0.1:8080/api/v1`
- **Swagger Docs**: `http://127.0.0.1:8080/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- **Web App**: `http://localhost:5173`

---

## 🧪 Running Unit Tests

```bash
cd backend
python -m pytest tests/
```

---

## 📜 License & Author

- **Repository**: [https://github.com/Jishnu-cmd/supervite_ammu.git](https://github.com/Jishnu-cmd/supervite_ammu.git)
- **Author**: Jishnu
