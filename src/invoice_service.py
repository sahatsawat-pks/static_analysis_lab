from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]

class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05
        }

    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if inv is None:
            problems.append("Invoice is missing")
            return problems
        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")
        for it in inv.items:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in ("book", "food", "electronics", "other"):
                problems.append(f"Unknown category for {it.sku}")
        return problems

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        # 1. Calculate base metrics using generator expressions
        subtotal = sum(it.unit_price * it.qty for it in inv.items)
        fragile_fee = sum(5.0 * it.qty for it in inv.items if it.fragile)

        # 2. Shipping Logic (Mapping: {Country: (Threshold, Fee)})
        shipping_rules = {
            "TH": (500, 60),
            "JP": (4000, 600),
            "US": (100, 15) if subtotal < 100 else (300, 8),
            "DEFAULT": (200, 25)
        }
        
        threshold, fee = shipping_rules.get(inv.country, shipping_rules["DEFAULT"])
        shipping = fee if subtotal < threshold else 0

        # 3. Discount Logic
        membership_rates = {"gold": 0.03, "platinum": 0.05}
        if inv.membership in membership_rates:
            discount = subtotal * membership_rates[inv.membership]
        else:
            discount = 20.0 if subtotal > 3000 else 0.0

        # Coupon Logic
        coupon_code = (inv.coupon or "").strip()
        if coupon_code:
            if coupon_code in self._coupon_rate:
                discount += subtotal * self._coupon_rate[coupon_code]
            else:
                warnings.append("Unknown coupon")

        # 4. Tax Logic (Mapping: {Country: Rate})
        tax_rates = {"TH": 0.07, "JP": 0.10, "US": 0.08, "DEFAULT": 0.05}
        rate = tax_rates.get(inv.country, tax_rates["DEFAULT"])
        tax = (subtotal - discount) * rate

        # 5. Final Calculation
        total = max(0.0, subtotal + shipping + fragile_fee + tax - discount)

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings