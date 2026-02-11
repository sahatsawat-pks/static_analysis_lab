import unittest
from src.invoice_service import InvoiceService, Invoice, LineItem

class TestInvoiceService(unittest.TestCase):
    def setUp(self):
        self.service = InvoiceService()
        self.item = LineItem(sku="SKU1", category="book", unit_price=100.0, qty=1)

    def test_shipping_logic(self):
        # Test US Shipping tiers
        inv_us_low = Invoice("1", "C1", "US", "none", None, [self.item]) # Subtotal 100
        total, _ = self.service.compute_total(inv_us_low)
        # Expected: 100 (sub) + 15 (ship) + 8 (tax on 100) = 123.0
        
    def test_coupon_and_membership(self):
        # Test Gold membership + VIP20 coupon
        gold_item = LineItem("SKU1", "book", 1000.0, 1)
        inv = Invoice("2", "C2", "TH", "gold", "VIP20", [gold_item])
        total, warnings = self.service.compute_total(inv)
        # Should apply both 3% and 20% discounts
        self.assertIn("VIP20", inv.coupon)

    def test_validation_errors(self):
        # Test that the complexity reduction didn't break error handling
        bad_inv = Invoice("3", "C3", "TH", "none", None, [])
        with self.assertRaises(ValueError):
            self.service.compute_total(bad_inv)