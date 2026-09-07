import unittest

from src.retry import backoff_delay


class BackoffDelayTests(unittest.TestCase):
    def test_first_attempt_uses_base_delay(self):
        self.assertAlmostEqual(backoff_delay(1), 0.1)

    def test_delay_doubles_per_attempt(self):
        self.assertAlmostEqual(backoff_delay(2), 0.2)
        self.assertAlmostEqual(backoff_delay(3), 0.4)

    def test_cap_is_respected(self):
        self.assertAlmostEqual(backoff_delay(20), 5.0)

    def test_invalid_attempt_rejected(self):
        with self.assertRaises(ValueError):
            backoff_delay(0)


if __name__ == "__main__":
    unittest.main()
