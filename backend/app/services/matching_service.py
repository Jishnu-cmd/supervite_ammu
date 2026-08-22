from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz
from app.services.normalization_service import NormalizationService
from app.models.models import POLineItem, InvoiceLineItem

class LineItemMatchingEngine:
    SIMILARITY_THRESHOLD = 75.0 # Fuzzy description threshold

    @classmethod
    def match_line_items(
        cls, 
        invoice_lines: List[InvoiceLineItem], 
        po_lines: List[POLineItem]
    ) -> List[Dict[str, Any]]:
        """
        Matches invoice lines against PO lines.
        Returns a list of match decision objects.
        """
        match_results = []
        used_po_line_ids = set()

        for inv_line in invoice_lines:
            best_match: Optional[POLineItem] = None
            match_method = "NONE"
            match_confidence = 0.0
            match_status = "UNMATCHED"

            inv_sku = NormalizationService.normalize_sku(inv_line.sku or "")
            inv_sku_key = NormalizationService.canonical_sku_key(inv_sku)
            inv_desc = NormalizationService.normalize_description(inv_line.description)

            # 1. Exact SKU Match
            if inv_sku:
                for po_line in po_lines:
                    if po_line.id in used_po_line_ids:
                        continue
                    po_sku = NormalizationService.normalize_sku(po_line.sku)
                    if inv_sku == po_sku:
                        best_match = po_line
                        match_method = "EXACT_SKU"
                        match_confidence = 1.0
                        match_status = "MATCHED"
                        break

            # 2. Normalized SKU Key Match (ignoring dashes/spaces)
            if not best_match and inv_sku_key:
                for po_line in po_lines:
                    if po_line.id in used_po_line_ids:
                        continue
                    po_sku_key = NormalizationService.canonical_sku_key(po_line.sku)
                    if inv_sku_key == po_sku_key:
                        best_match = po_line
                        match_method = "NORMALIZED_SKU"
                        match_confidence = 0.95
                        match_status = "MATCHED"
                        break

            # 3. Fuzzy Description Similarity
            if not best_match and inv_desc:
                highest_score = 0.0
                candidate = None
                for po_line in po_lines:
                    if po_line.id in used_po_line_ids:
                        continue
                    po_desc = NormalizationService.normalize_description(po_line.description)
                    score = fuzz.token_sort_ratio(inv_desc, po_desc)
                    if score > highest_score:
                        highest_score = score
                        candidate = po_line

                if candidate and highest_score >= cls.SIMILARITY_THRESHOLD:
                    best_match = candidate
                    match_method = f"FUZZY_DESCRIPTION ({highest_score:.1f}%)"
                    match_confidence = round(highest_score / 100.0, 2)
                    match_status = "MATCHED" if highest_score >= 85.0 else "LOW_CONFIDENCE_MATCH"

            # Check UOM compatibility if matched
            if best_match:
                used_po_line_ids.add(best_match.id)
                uom_ok = NormalizationService.are_uoms_compatible(inv_line.uom, best_match.uom)
                if not uom_ok and match_status == "MATCHED":
                    match_status = "PARTIAL_MATCH"

            match_results.append({
                "invoice_line_id": inv_line.id,
                "invoice_line_no": inv_line.line_no,
                "po_line_id": best_match.id if best_match else None,
                "po_line_no": best_match.line_no if best_match else None,
                "match_method": match_method,
                "confidence": match_confidence,
                "status": match_status if best_match else "UNMATCHED"
            })

        return match_results
