from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import (
    Invoice, InvoiceLineItem, PurchaseOrder, POLineItem, ExceptionRecord,
    ToleranceConfig, InvoiceHistory
)
from app.services.normalization_service import NormalizationService
from app.services.matching_service import LineItemMatchingEngine

class DeterministicRuleEngine:
    @classmethod
    def evaluate_invoice(
        cls, 
        db: Session, 
        invoice: Invoice, 
        po: Optional[PurchaseOrder] = None,
        tolerance_config: Optional[ToleranceConfig] = None
    ) -> List[ExceptionRecord]:
        """
        Runs deterministic reconciliation rules against the invoice and PO.
        Returns a list of structured ExceptionRecord objects.
        LLM DOES NOT DECIDE EXCEPTION VALIDITY - THIS CODE DECIDES.
        """
        exceptions: List[ExceptionRecord] = []

        # Load default or specific tolerance configuration
        price_tol_pct = (tolerance_config.price_variance_pct if (tolerance_config and tolerance_config.price_variance_pct is not None) else 2.0)
        tax_tol_amount = (tolerance_config.tax_rounding_amount if (tolerance_config and tolerance_config.tax_rounding_amount is not None) else 0.01)
        conf_threshold = (tolerance_config.extraction_confidence_threshold if (tolerance_config and tolerance_config.extraction_confidence_threshold is not None) else 0.80)
        
        inv_conf = invoice.extraction_confidence if invoice.extraction_confidence is not None else 1.0

        # Rule 1: Extraction Confidence Check (EXTRACTION_UNCERTAIN)
        if inv_conf < conf_threshold:
            exceptions.append(ExceptionRecord(
                exception_code=f"EXC-{invoice.invoice_number}-HEADER-EXTRACT",
                invoice_id=invoice.id,
                line_no=None,
                sku=None,
                type="EXTRACTION_UNCERTAIN",
                severity="MEDIUM",
                invoice_value=invoice.extraction_confidence,
                po_value=conf_threshold,
                delta_abs=conf_threshold - invoice.extraction_confidence,
                delta_pct=round(((conf_threshold - invoice.extraction_confidence) / conf_threshold) * 100, 2),
                tolerance_allowed=conf_threshold,
                rule_triggered=f"extraction_confidence ({invoice.extraction_confidence}) < threshold ({conf_threshold})",
                invoice_source_field="invoice.extraction_confidence",
                po_source_field=None,
                page=1,
                status="OPEN"
            ))

        # Rule 2: Duplicate Invoice Detection (DUPLICATE_INVOICE)
        existing_dup = db.query(Invoice).filter(
            Invoice.id != invoice.id,
            Invoice.vendor_id == invoice.vendor_id,
            Invoice.invoice_number == invoice.invoice_number
        ).first()

        if existing_dup:
            exceptions.append(ExceptionRecord(
                exception_code=f"EXC-{invoice.invoice_number}-DUPLICATE",
                invoice_id=invoice.id,
                line_no=None,
                sku=None,
                type="DUPLICATE_INVOICE",
                severity="CRITICAL",
                invoice_value=invoice.invoice_total,
                po_value=existing_dup.invoice_total,
                delta_abs=0.0,
                delta_pct=0.0,
                tolerance_allowed=0.0,
                rule_triggered=f"Duplicate invoice found: Vendor {invoice.vendor_id} and Invoice #{invoice.invoice_number} already processed in invoice {existing_dup.id}",
                invoice_source_field="invoice.invoice_number",
                po_source_field=None,
                page=1,
                status="OPEN"
            ))

        # Check line item extraction confidence
        for item in invoice.line_items:
            item_conf = item.confidence if item.confidence is not None else 1.0
            if item_conf < conf_threshold:
                exceptions.append(ExceptionRecord(
                    exception_code=f"EXC-{invoice.invoice_number}-L{item.line_no}-UNCERTAIN",
                    invoice_id=invoice.id,
                    line_no=item.line_no,
                    sku=item.sku,
                    type="EXTRACTION_UNCERTAIN",
                    severity="LOW",
                    invoice_value=item.confidence,
                    po_value=conf_threshold,
                    delta_abs=round(conf_threshold - item.confidence, 4),
                    delta_pct=round(((conf_threshold - item.confidence) / conf_threshold) * 100, 2),
                    tolerance_allowed=conf_threshold,
                    rule_triggered=f"line_items[{item.line_no - 1}].confidence ({item.confidence}) < threshold ({conf_threshold})",
                    invoice_source_field=f"line_items[{item.line_no - 1}].confidence",
                    bbox=item.bbox,
                    page=item.page,
                    status="OPEN"
                ))

        if not po:
            # If PO missing completely but invoice references PO number
            if invoice.po_number:
                exceptions.append(ExceptionRecord(
                    exception_code=f"EXC-{invoice.invoice_number}-PO-NOT-FOUND",
                    invoice_id=invoice.id,
                    line_no=None,
                    sku=None,
                    type="LINE_NOT_ON_PO",
                    severity="HIGH",
                    rule_triggered=f"Purchase order '{invoice.po_number}' was not found in PO repository",
                    invoice_source_field="invoice.po_number",
                    status="OPEN"
                ))
            return exceptions

        # Fetch latest active revision PO lines
        active_rev = None
        for rev in po.revisions:
            if rev.revision_number == po.current_revision_number or rev.status == "ACTIVE":
                active_rev = rev
                break
        if not active_rev and po.revisions:
            active_rev = po.revisions[0]

        po_lines = active_rev.line_items if active_rev else []
        po_lines_by_id = {p.id: p for p in po_lines}

        # Perform deterministic matching
        matches = LineItemMatchingEngine.match_line_items(invoice.line_items, po_lines)

        total_invoiced_against_po = 0.0

        for match in matches:
            inv_line = next((l for l in invoice.line_items if l.id == match["invoice_line_id"]), None)
            if not inv_line:
                continue

            inv_line.match_status = match["status"]
            inv_line.match_confidence = match["confidence"]
            inv_line.matched_po_line_id = match["po_line_id"]
            
            po_line = po_lines_by_id.get(match["po_line_id"]) if match["po_line_id"] else None

            # Rule 3: Line Not on PO (LINE_NOT_ON_PO)
            if not po_line:
                exceptions.append(ExceptionRecord(
                    exception_code=f"EXC-{invoice.invoice_number}-L{inv_line.line_no}-NO-PO",
                    invoice_id=invoice.id,
                    line_no=inv_line.line_no,
                    sku=inv_line.sku,
                    type="LINE_NOT_ON_PO",
                    severity="HIGH",
                    invoice_value=inv_line.line_total,
                    po_value=0.0,
                    rule_triggered=f"Invoice line {inv_line.line_no} ('{inv_line.description}') could not be matched to any line on PO {po.po_number}",
                    invoice_source_field=f"line_items[{inv_line.line_no - 1}]",
                    bbox=inv_line.bbox,
                    page=inv_line.page,
                    status="OPEN"
                ))
                continue

            # Rule 4: Unit of Measure Mismatch (UNIT_MISMATCH)
            if not NormalizationService.are_uoms_compatible(inv_line.uom, po_line.uom):
                exceptions.append(ExceptionRecord(
                    exception_code=f"EXC-{invoice.invoice_number}-L{inv_line.line_no}-UOM",
                    invoice_id=invoice.id,
                    line_no=inv_line.line_no,
                    sku=inv_line.sku,
                    type="UNIT_MISMATCH",
                    severity="MEDIUM",
                    rule_triggered=f"Invoice UOM ('{inv_line.uom}') is incompatible with PO UOM ('{po_line.uom}')",
                    invoice_source_field=f"line_items[{inv_line.line_no - 1}].uom",
                    po_source_field=f"po.line_items[{po_line.line_no - 1}].uom",
                    bbox=inv_line.bbox,
                    page=inv_line.page,
                    status="OPEN"
                ))

            # Rule 5: Price Mismatch (PRICE_MISMATCH)
            if po_line.unit_price > 0:
                price_diff = inv_line.unit_price - po_line.unit_price
                price_variance_pct = (price_diff / po_line.unit_price) * 100.0

                if price_variance_pct > price_tol_pct:
                    exceptions.append(ExceptionRecord(
                        exception_code=f"EXC-{invoice.invoice_number}-L{inv_line.line_no}-PRICE",
                        invoice_id=invoice.id,
                        line_no=inv_line.line_no,
                        sku=inv_line.sku or po_line.sku,
                        type="PRICE_MISMATCH",
                        severity="HIGH" if price_variance_pct > 10.0 else "MEDIUM",
                        invoice_value=round(inv_line.unit_price, 4),
                        po_value=round(po_line.unit_price, 4),
                        delta_abs=round(price_diff, 4),
                        delta_pct=round(price_variance_pct, 2),
                        tolerance_allowed=price_tol_pct,
                        rule_triggered=f"unit_price_variance ({price_variance_pct:.2f}%) > price_tolerance ({price_tol_pct}%)",
                        invoice_source_field=f"line_items[{inv_line.line_no - 1}].unit_price",
                        po_source_field=f"po.line_items[{po_line.line_no - 1}].unit_price",
                        bbox=inv_line.bbox,
                        page=inv_line.page,
                        status="OPEN"
                    ))

            # Rule 6: Quantity Mismatch with Partial Invoicing (QTY_MISMATCH)
            # Calculate cumulative quantity previously invoiced against this PO line
            prev_history = db.query(InvoiceHistory).filter(
                InvoiceHistory.po_number == po.po_number,
                InvoiceHistory.sku == po_line.sku,
                InvoiceHistory.invoice_number != invoice.invoice_number
            ).all()

            cum_prev_qty = sum(h.invoiced_quantity for h in prev_history)
            remaining_po_qty = po_line.quantity_ordered - cum_prev_qty

            if inv_line.quantity > remaining_po_qty:
                qty_over = inv_line.quantity - remaining_po_qty
                exceptions.append(ExceptionRecord(
                    exception_code=f"EXC-{invoice.invoice_number}-L{inv_line.line_no}-QTY",
                    invoice_id=invoice.id,
                    line_no=inv_line.line_no,
                    sku=inv_line.sku or po_line.sku,
                    type="QTY_MISMATCH",
                    severity="HIGH",
                    invoice_value=inv_line.quantity,
                    po_value=remaining_po_qty,
                    delta_abs=qty_over,
                    delta_pct=round((qty_over / remaining_po_qty * 100.0), 2) if remaining_po_qty > 0 else 100.0,
                    tolerance_allowed=0.0,
                    rule_triggered=f"invoice_quantity ({inv_line.quantity}) > po_remaining_quantity ({remaining_po_qty}) [PO Ordered: {po_line.quantity_ordered}, Previously Invoiced: {cum_prev_qty}]",
                    invoice_source_field=f"line_items[{inv_line.line_no - 1}].quantity",
                    po_source_field=f"po.line_items[{po_line.line_no - 1}].quantity_ordered",
                    bbox=inv_line.bbox,
                    page=inv_line.page,
                    status="OPEN"
                ))

            # Rule 7: Tax Rate Mismatch per line if specified on PO line
            if po_line.tax_rate > 0 and inv_line.tax_rate > 0:
                if abs(inv_line.tax_rate - po_line.tax_rate) > 0.01:
                    exceptions.append(ExceptionRecord(
                        exception_code=f"EXC-{invoice.invoice_number}-L{inv_line.line_no}-TAXRATE",
                        invoice_id=invoice.id,
                        line_no=inv_line.line_no,
                        sku=inv_line.sku,
                        type="TAX_RATE_MISMATCH",
                        severity="MEDIUM",
                        invoice_value=inv_line.tax_rate,
                        po_value=po_line.tax_rate,
                        delta_abs=round(abs(inv_line.tax_rate - po_line.tax_rate), 4),
                        rule_triggered=f"invoice_tax_rate ({inv_line.tax_rate}%) != expected_po_tax_rate ({po_line.tax_rate}%)",
                        invoice_source_field=f"line_items[{inv_line.line_no - 1}].tax_rate",
                        po_source_field=f"po.line_items[{po_line.line_no - 1}].tax_rate",
                        bbox=inv_line.bbox,
                        page=inv_line.page,
                        status="OPEN"
                    ))

            total_invoiced_against_po += inv_line.line_total

        # Rule 8: Tax Calculation Error (TAX_CALC_ERROR)
        if invoice.tax_rate > 0 and invoice.subtotal > 0:
            expected_tax = round((invoice.subtotal * (invoice.tax_rate / 100.0)), 2)
            tax_diff = abs(invoice.tax_total - expected_tax)

            if tax_diff > tax_tol_amount:
                exceptions.append(ExceptionRecord(
                    exception_code=f"EXC-{invoice.invoice_number}-TAX-CALC",
                    invoice_id=invoice.id,
                    line_no=None,
                    sku=None,
                    type="TAX_CALC_ERROR",
                    severity="MEDIUM",
                    invoice_value=invoice.tax_total,
                    po_value=expected_tax,
                    delta_abs=round(tax_diff, 2),
                    tolerance_allowed=tax_tol_amount,
                    rule_triggered=f"invoice_tax_amount (${invoice.tax_total:.2f}) != round(subtotal ${invoice.subtotal:.2f} * tax_rate {invoice.tax_rate}%, 2) = ${expected_tax:.2f}",
                    invoice_source_field="invoice.tax_total",
                    page=1,
                    status="OPEN"
                ))

        # Rule 9: Over PO Total (OVER_PO_TOTAL)
        po_total_authorized = sum(p.line_total for p in po_lines)
        # Check cumulative history against total PO
        prev_po_history = db.query(InvoiceHistory).filter(
            InvoiceHistory.po_number == po.po_number,
            InvoiceHistory.invoice_number != invoice.invoice_number
        ).all()
        prev_total_invoiced = sum(h.invoiced_amount for h in prev_po_history)

        total_cum_billing = prev_total_invoiced + invoice.invoice_total

        if total_cum_billing > po_total_authorized:
            overage = total_cum_billing - po_total_authorized
            exceptions.append(ExceptionRecord(
                exception_code=f"EXC-{invoice.invoice_number}-OVER-PO",
                invoice_id=invoice.id,
                line_no=None,
                sku=None,
                type="OVER_PO_TOTAL",
                severity="CRITICAL",
                invoice_value=total_cum_billing,
                po_value=po_total_authorized,
                delta_abs=round(overage, 2),
                delta_pct=round((overage / po_total_authorized * 100.0), 2) if po_total_authorized > 0 else 100.0,
                tolerance_allowed=0.0,
                rule_triggered=f"cumulative_invoicing (${total_cum_billing:.2f}) > po_permitted_value (${po_total_authorized:.2f})",
                invoice_source_field="invoice.invoice_total",
                po_source_field="po.total_value",
                page=1,
                status="OPEN"
            ))

        return exceptions
