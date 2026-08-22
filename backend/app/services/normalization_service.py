import re

class NormalizationService:
    UOM_MAP = {
        "EA": "EACH",
        "EACH": "EACH",
        "PCS": "EACH",
        "PIECE": "EACH",
        "PIECES": "EACH",
        "BOX": "BOX",
        "BX": "BOX",
        "BOX-12": "BOX_12",
        "12 EACH": "BOX_12",
        "BOX OF 12": "BOX_12",
        "PK": "PACK",
        "PACK": "PACK",
        "SET": "SET"
    }

    CURRENCY_MAP = {
        "$": "USD",
        "USD": "USD",
        "US DOLLAR": "USD",
        "€": "EUR",
        "EUR": "EUR",
        "£": "GBP",
        "GBP": "GBP"
    }

    @classmethod
    def normalize_sku(cls, sku: str) -> str:
        if not sku:
            return ""
        # Strip trailing/leading spaces, normalize to uppercase
        return sku.strip().upper()

    @classmethod
    def canonical_sku_key(cls, sku: str) -> str:
        """Key used for fuzzy matching (remove non-alphanumeric)"""
        if not sku:
            return ""
        return re.sub(r'[^A-Z0-9]', '', sku.upper())

    @classmethod
    def normalize_uom(cls, uom: str) -> str:
        if not uom:
            return "EACH"
        cleaned = uom.strip().upper()
        return cls.UOM_MAP.get(cleaned, cleaned)

    @classmethod
    def normalize_description(cls, desc: str) -> str:
        if not desc:
            return ""
        # Collapse multiple spaces and trim
        cleaned = re.sub(r'\s+', ' ', desc.strip().lower())
        return cleaned

    @classmethod
    def normalize_currency(cls, curr: str) -> str:
        if not curr:
            return "USD"
        cleaned = curr.strip().upper()
        return cls.CURRENCY_MAP.get(cleaned, "USD")

    @classmethod
    def are_uoms_compatible(cls, uom1: str, uom2: str) -> bool:
        norm1 = cls.normalize_uom(uom1)
        norm2 = cls.normalize_uom(uom2)
        if norm1 == norm2:
            return True
        # EACH and PIECE compatible
        compatible_groups = [
            {"EACH", "PIECE", "PCS"},
            {"BOX", "BX"},
        ]
        for group in compatible_groups:
            if norm1 in group and norm2 in group:
                return True
        return False
