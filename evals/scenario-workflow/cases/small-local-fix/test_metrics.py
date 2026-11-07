import unittest
from metrics import summarize

class MetricsTest(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(summarize([2, 4]), 3)
