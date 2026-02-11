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

        subtotal = 0.0
        fragile_fee = 0.0
        for it in inv.items:
            line = it.unit_price * it.qty
            subtotal += line
            if it.fragile:
                fragile_fee += 5.0 * it.qty

        discount = 0.0
        if inv.membership == "gold":
            discount += subtotal * 0.03
        elif inv.membership == "platinum":
            discount += subtotal * 0.05
        elif subtotal > 3000:
            discount += 20

        code = inv.coupon.strip()
        if inv.coupon is not None and code != "" and code in self._coupon_rate:
            discount += subtotal * self._coupon_rate[code]
        elif (inv.coupon is not None and code != "") or code not in self._coupon_rate:
            warnings.append("Unknown coupon")

        
        shipping = 0.0
        tax = (subtotal - discount)
        if inv.country == "TH" and subtotal < 500:
            shipping = 60
        elif inv.country == "JP" and subtotal < 4000:
            shipping = 600
        elif inv.country == "US" and subtotal < 100:
            shipping = 15
        elif inv.country == "US" and subtotal < 300:
            shipping = 8
        elif subtotal < 200:
            shipping = 25
        else:
            shipping = 0
            tax *= 0.05

        if inv.country == "TH":
            tax *= 0.07
        elif inv.country == "JP":
            tax *= 0.10
        elif inv.country == "US":
            tax *= 0.08

        total = subtotal + shipping + fragile_fee + tax - discount
        if total < 0:
            total = 0

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings
