"""Coral-side money terminal: the charity payout pool.

Money committed to the substitution layer flows here immediately and
leaves only outward, to charity. There is no path that returns a cent
to the player — no personal cash-rescue fantasy — and the full funding
history is kept so the pool can always be reconciled.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FundingRecord:
    amount: int
    source: str


class CharityPayoutPool:
    """Accrues committed money and disburses it to charity. Exit-only:
    deposits are recorded irrevocably and payouts only drain outward."""

    def __init__(self) -> None:
        self._records: list[FundingRecord] = []
        self._paid_out = 0

    @property
    def lifetime_accrued(self) -> int:
        return sum(r.amount for r in self._records)

    @property
    def balance(self) -> int:
        return self.lifetime_accrued - self._paid_out

    @property
    def records(self) -> tuple[FundingRecord, ...]:
        return tuple(self._records)

    def fund(self, amount: int, source: str) -> None:
        if amount <= 0:
            raise ValueError("funding must be positive")
        self._records.append(FundingRecord(amount=amount, source=source))

    def disburse(self, charity: str) -> int:
        """Send the whole balance to *charity*. Returns the amount."""
        amount = self.balance
        self._paid_out += amount
        return amount
