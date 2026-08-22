import json
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.models.models import Invoice, ExceptionRecord, PurchaseOrder

SYSTEM_PROMPT = """You are an expert AP Invoice Reconciliation Assistant.
Your task is to explain invoice reconciliation results, exceptions, and questions accurately and concisely to an Accounts Payable reviewer.

CRITICAL GUARDRAILS & INVARIANTS:
1. Grounding: Rely ONLY on the provided Invoice JSON, PO JSON, and Exception Records JSON. Do not invent facts, numbers, or rules.
2. No Independent Calculations: Do not calculate new financial numbers. Quote the values, deltas, percentages, and tolerances provided in the Exception Records.
3. No Invented Exceptions: If no exception exists for a category (e.g. tax, quantity), explicitly confirm that the check PASSED with stored values.
4. Disputed PO / Amendments: If the user mentions a verbal amendment, clarify that verbal agreements are not in the recorded PO revision, so the exception remains OPEN until an authorized override or PO revision is posted.
5. Source Citations: For every exception explanation, include source field references in your text like `line_items[0].unit_price` or `po.line_items[0].unit_price`.

Provide clear, professional, markdown-formatted explanations.
"""

class ExplanationService:
    @classmethod
    def generate_explanation(
        cls, 
        invoice: Invoice, 
        exceptions: List[ExceptionRecord], 
        po: PurchaseOrder, 
        user_message: str
    ) -> Tuple[str, List[str]]:
        """
        Generates a source-grounded explanation response to a reviewer's question.
        Returns (answer_markdown, list_of_source_fields).
        """
        # Construct evidence payload
        exceptions_data = []
        sources = []

        for exc in exceptions:
            exceptions_data.append({
                "exception_id": exc.exception_code,
                "line_no": exc.line_no,
                "sku": exc.sku,
                "type": exc.type,
                "severity": exc.severity,
                "invoice_value": exc.invoice_value,
                "po_value": exc.po_value,
                "delta_abs": exc.delta_abs,
                "delta_pct": exc.delta_pct,
                "tolerance_allowed": exc.tolerance_allowed,
                "rule_triggered": exc.rule_triggered,
                "invoice_source_field": exc.invoice_source_field,
                "po_source_field": exc.po_source_field,
                "status": exc.status
            })
            if exc.invoice_source_field:
                sources.append(exc.invoice_source_field)
            if exc.po_source_field:
                sources.append(exc.po_source_field)

        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "vendor_id": invoice.vendor_id,
            "po_number": invoice.po_number,
            "subtotal": invoice.subtotal,
            "tax_rate": invoice.tax_rate,
            "tax_total": invoice.tax_total,
            "invoice_total": invoice.invoice_total,
            "extraction_confidence": invoice.extraction_confidence,
            "line_items": [
                {
                    "line_no": item.line_no,
                    "sku": item.sku,
                    "description": item.description,
                    "quantity": item.quantity,
                    "uom": item.uom,
                    "unit_price": item.unit_price,
                    "line_total": item.line_total,
                    "match_status": item.match_status
                } for item in invoice.line_items
            ]
        }

        po_data = {}
        if po:
            # Active revision lines
            po_lines = []
            if po.revisions:
                active_rev = po.revisions[0]
                po_lines = [
                    {
                        "line_no": p.line_no,
                        "sku": p.sku,
                        "description": p.description,
                        "quantity_ordered": p.quantity_ordered,
                        "unit_price": p.unit_price,
                        "uom": p.uom,
                        "tax_rate": p.tax_rate,
                        "line_total": p.line_total
                    } for p in active_rev.line_items
                ]
            po_data = {
                "po_number": po.po_number,
                "current_revision": po.current_revision_number,
                "currency": po.currency,
                "line_items": po_lines
            }

        # Use Gemini API if configured
        if settings.GEMINI_API_KEY:
            try:
                import google.genai as genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = f"""User Question: "{user_message}"

INVOICE EVIDENCE:
{json.dumps(invoice_data, indent=2)}

PO EVIDENCE:
{json.dumps(po_data, indent=2)}

EXCEPTION ENGINE RESULTS (DETERMINISTIC):
{json.dumps(exceptions_data, indent=2)}
"""
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=SYSTEM_PROMPT + "\n\n" + prompt
                )
                return response.text.strip(), sources
            except Exception as e:
                print(f"Gemini explanation error: {e}")

        # Deterministic Grounded Fallback Answer Generator
        return cls._generate_deterministic_explanation(user_message, invoice_data, po_data, exceptions_data, sources)

    @classmethod
    def _generate_deterministic_explanation(
        cls, 
        message: str, 
        invoice: Dict[str, Any], 
        po: Dict[str, Any], 
        exceptions: List[Dict[str, Any]], 
        sources: List[str]
    ) -> Tuple[str, List[str]]:
        msg_lower = message.lower()

        if not exceptions:
            return (
                f"### Reconciliation Summary for Invoice #{invoice['invoice_number']}\n\n"
                f"✅ **No exceptions were detected.**\n"
                f"- Invoice total (${invoice['invoice_total']:.2f}) matches PO #{invoice['po_number']}.\n"
                f"- All line items, quantities, prices, and tax calculations passed validation within configured tolerances.",
                []
            )

        if "why" in msg_lower or "flagged" in msg_lower or "all" in msg_lower or "summary" in msg_lower:
            ans = [f"### Invoice #{invoice['invoice_number']} Reconciliation Exceptions\n"]
            ans.append(f"This invoice was flagged with **{len(exceptions)} exception(s)** by the deterministic rule engine:\n")

            for exc in exceptions:
                severity_icon = "🔴" if exc["severity"] in ["HIGH", "CRITICAL"] else "🟡"
                ans.append(f"#### {severity_icon} {exc['type']} (Line {exc['line_no'] or 'Header'})")
                
                if exc["type"] == "PRICE_MISMATCH":
                    ans.append(
                        f"- **Invoice Price**: `${exc['invoice_value']:.2f}` (`{exc['invoice_source_field']}`)\n"
                        f"- **PO Authorized Price**: `${exc['po_value']:.2f}` (`{exc['po_source_field']}`)\n"
                        f"- **Variance**: `{exc['delta_pct']}%` (${exc['delta_abs']:.2f} difference)\n"
                        f"- **Allowed Tolerance**: `{exc['tolerance_allowed']}%`\n"
                        f"- **Rule Executed**: `{exc['rule_triggered']}`"
                    )
                elif exc["type"] == "QTY_MISMATCH":
                    ans.append(
                        f"- **Invoice Quantity**: `{exc['invoice_value']}` (`{exc['invoice_source_field']}`)\n"
                        f"- **PO Remaining Quantity**: `{exc['po_value']}` (`{exc['po_source_field']}`)\n"
                        f"- **Overage**: `{exc['delta_abs']}` units above remaining authorization\n"
                        f"- **Rule Executed**: `{exc['rule_triggered']}`"
                    )
                elif exc["type"] == "TAX_CALC_ERROR":
                    ans.append(
                        f"- **Invoice Billed Tax**: `${exc['invoice_value']:.2f}` (`{exc['invoice_source_field']}`)\n"
                        f"- **Calculated Tax**: `${exc['po_value']:.2f}` (`round(subtotal * {invoice['tax_rate']}%, 2)`)\n"
                        f"- **Rounding Variance**: `${exc['delta_abs']:.2f}` > allowed tolerance `${exc['tolerance_allowed']:.2f}`"
                    )
                elif exc["type"] == "DUPLICATE_INVOICE":
                    ans.append(f"- **Duplicate Details**: `{exc['rule_triggered']}`")
                else:
                    ans.append(f"- **Rule Triggered**: `{exc['rule_triggered']}`")

                ans.append("")

            return "\n".join(ans), sources

        if "tax" in msg_lower:
            tax_excs = [e for e in exceptions if "TAX" in e["type"]]
            if not tax_excs:
                return (
                    f"### Tax Validation Passed ✅\n\n"
                    f"- **Invoice Tax Rate**: `{invoice['tax_rate']}%`\n"
                    f"- **Invoice Tax Amount**: `${invoice['tax_total']:.2f}` (`invoice.tax_total`)\n"
                    f"- **Subtotal**: `${invoice['subtotal']:.2f}`\n"
                    f"- **Validation**: `${invoice['subtotal']:.2f} × {invoice['tax_rate']}% = ${invoice['tax_total']:.2f}`.\n\n"
                    f"No tax mismatch or calculation errors were detected.",
                    ["invoice.tax_total", "invoice.tax_rate"]
                )
            else:
                exc = tax_excs[0]
                return (
                    f"### Tax Exception Flagged 🔴\n\n"
                    f"- **Rule**: `{exc['rule_triggered']}`\n"
                    f"- **Billed Tax Amount**: `${exc['invoice_value']:.2f}` (`invoice.tax_total`)\n"
                    f"- **Expected Tax Amount**: `${exc['po_value']:.2f}`\n"
                    f"- **Difference**: `${exc['delta_abs']:.2f}`",
                    ["invoice.tax_total"]
                )

        if "verbal" in msg_lower or "amend" in msg_lower or "oral" in msg_lower:
            return (
                f"### Policy Notice regarding Verbal Amendments\n\n"
                f"The active system record for PO #{invoice['po_number']} (Revision #{po.get('current_revision', 1)}) "
                f"does not contain verbal amendments.\n\n"
                f"**System Status**: The price/quantity exception remains **OPEN** until an updated PO revision is saved "
                f"or an authorized reviewer records a mandatory override note.",
                sources
            )

        # Fallback question responder
        return (
            f"Based on the deterministic reconciliation for Invoice #{invoice['invoice_number']}:\n\n"
            + "\n".join([f"- **{e['type']}**: {e['rule_triggered']}" for e in exceptions]),
            sources
        )
