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
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        # 1. Calculate base line items
        subtotal = sum(it.unit_price * it.qty for it in inv.items)
        fragile_fee = sum(5.0 * it.qty for it in inv.items if it.fragile)

        # 2. Calculate dynamic components
        shipping = self._get_shipping(inv.country, subtotal)
        discount, warnings = self._get_discount(inv, subtotal)
        
        # 3. Calculate Tax (applied on subtotal AFTER discount)
        tax = self._get_tax(inv.country, subtotal - discount)

        # 4. Final Aggregation
        total = max(0.0, subtotal + shipping + fragile_fee + tax - discount)

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings

    def _get_shipping(self, country: str, subtotal: float) -> float:
        if country == "TH":
            return 60 if subtotal < 500 else 0
        if country == "JP":
            return 600 if subtotal < 4000 else 0
        if country == "US":
            if subtotal < 100: return 15
            return 8 if subtotal < 300 else 0
        
        # Default / Other countries
        return 25 if subtotal < 200 else 0

    def _get_discount(self, inv: Invoice, subtotal: float) -> Tuple[float, List[str]]:
        discount = 0.0
        warnings = []

        # Membership Logic
        if inv.membership == "gold":
            discount += subtotal * 0.03
        elif inv.membership == "platinum":
            discount += subtotal * 0.05
        elif subtotal > 3000:
            discount += 20

        # Coupon Logic
        coupon_code = (inv.coupon or "").strip()
        if coupon_code:
            rate = self._coupon_rate.get(coupon_code)
            if rate is not None:
                discount += subtotal * rate
            else:
                warnings.append("Unknown coupon")
                
        return discount, warnings

    def _get_tax(self, country: str, taxable_amount: float) -> float:
        rates = {"TH": 0.07, "JP": 0.10, "US": 0.08}
        return taxable_amount * rates.get(country, 0.05)