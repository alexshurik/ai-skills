import unittest
from decimal import Decimal
from src.amounts import cents


class AmountTest(unittest.TestCase):
    def test_conversion(self):
        self.assertEqual(cents(Decimal("1.23")), 123)
