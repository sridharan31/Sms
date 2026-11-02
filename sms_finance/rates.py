"""Currency conversion between USD, AED and INR.

Rates are expressed as "units of currency per 1 USD".  AED is pegged to the
USD at 3.6725.  The INR rate floats, so override it with the live rate
(``--usd-inr`` on the command line) for accurate numbers.
"""

DEFAULT_RATES = {
    "USD": 1.0,
    "AED": 3.6725,
    "INR": 88.0,
}

CURRENCIES = ("USD", "AED", "INR")


class Converter:
    def __init__(self, rates=None):
        self.rates = dict(DEFAULT_RATES)
        if rates:
            self.rates.update({k: v for k, v in rates.items() if v})
        for cur, rate in self.rates.items():
            if rate <= 0:
                raise ValueError(f"Rate for {cur} must be positive, got {rate}")

    def convert(self, amount, from_cur, to_cur):
        if from_cur == to_cur:
            return amount
        usd = amount / self.rates[from_cur]
        return usd * self.rates[to_cur]

    def all_currencies(self, amount, from_cur):
        """Return {"USD": x, "AED": y, "INR": z} for an amount."""
        return {cur: self.convert(amount, from_cur, cur) for cur in CURRENCIES}
