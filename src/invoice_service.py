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

        subtotal, fragile_fee = self._calculate_base_costs(inv.items)
        discount, warnings = self._calculate_discount(inv, subtotal)
        shipping = self._calculate_shipping(inv.country, subtotal)
        tax = self._calculate_tax(inv.country, subtotal - discount)

        total = max(0.0, subtotal + shipping + fragile_fee + tax - discount)

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings

    def _calculate_base_costs(self, items: List[LineItem]) -> Tuple[float, float]:
        subtotal = sum(it.unit_price * it.qty for it in items)
        fragile_fee = sum(5.0 * it.qty for it in items if it.fragile)
        return subtotal, fragile_fee

    def _calculate_shipping(self, country: str, subtotal: float) -> float:
        rates = {
            "TH": (500, 60),
            "JP": (4000, 600),
            "US": (0, 0),
            "DEFAULT": (200, 25)
        }
        
        if country == "US":
            if subtotal < 100: return 15
            return 8 if subtotal < 300 else 0
            
        threshold, fee = rates.get(country, rates["DEFAULT"])
        return fee if subtotal < threshold else 0

    def _calculate_discount(self, inv: Invoice, subtotal: float) -> Tuple[float, List[str]]:
        discount = 0.0
        warnings = []

        tier_rates = {"gold": 0.03, "platinum": 0.05}
        if inv.membership in tier_rates:
            discount += subtotal * tier_rates[inv.membership]
        elif subtotal > 3000:
            discount += 20

        if inv.coupon and inv.coupon.strip():
            code = inv.coupon.strip()
            rate = self._coupon_rate.get(code)
            if rate is not None:
                discount += subtotal * rate
            else:
                warnings.append("Unknown coupon")
                
        return discount, warnings

    def _calculate_tax(self, country: str, taxable_amount: float) -> float:
        tax_rates = {"TH": 0.07, "JP": 0.10, "US": 0.08}
        rate = tax_rates.get(country, 0.05)
        return taxable_amount * rate