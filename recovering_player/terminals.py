"""House-funded charity contributions. No user money, no winnings.

Correction 1 invariant: no user-facing real-money value may originate
from chance. This pool is the only money object in the system and it is
deliberately boring:

* It is funded once, from a house budget fixed at construction. There
  is no API that accepts user money at all.
* Contributions are triggered by eligible app-side events (clean
  episode closure, recovery check-in, milestone award, enrollment) at
  amounts fixed per event kind in a published schedule. No chance
  outcome appears anywhere in the trigger vocabulary, and no amount is
  a function of any outcome.
* Nothing is ever owed, paid, or "won in the name of" the user. The
  user owns nothing here; money only exits outward to charity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class ContributionEvent(str, Enum):
    """The only triggers that move charity money. All app-side and
    deterministic; chance events are not representable here."""

    ENROLLMENT = "enrollment"
    CLEAN_EPISODE_CLOSURE = "clean-episode-closure"
    RECOVERY_CHECK_IN = "recovery-check-in"
    MILESTONE_AWARDED = "milestone-awarded"


DEFAULT_CONTRIBUTION_SCHEDULE: Mapping[ContributionEvent, int] = {
    ContributionEvent.ENROLLMENT: 10,
    ContributionEvent.CLEAN_EPISODE_CLOSURE: 5,
    ContributionEvent.RECOVERY_CHECK_IN: 2,
    ContributionEvent.MILESTONE_AWARDED: 15,
}


@dataclass(frozen=True)
class ContributionRecord:
    event: ContributionEvent
    amount: int
    episode_id: int | None


class CharityContributionPool:
    """A budgeted, house-funded contribution pool. Exit-only."""

    def __init__(
        self,
        house_budget: int = 1_000,
        schedule: Mapping[ContributionEvent, int] | None = None,
    ) -> None:
        if house_budget < 0:
            raise ValueError("the house budget cannot be negative")
        self._budget_remaining = house_budget
        self._schedule = dict(schedule or DEFAULT_CONTRIBUTION_SCHEDULE)
        self._records: list[ContributionRecord] = []
        self._paid_out = 0

    @property
    def schedule(self) -> Mapping[ContributionEvent, int]:
        return dict(self._schedule)

    @property
    def budget_remaining(self) -> int:
        return self._budget_remaining

    @property
    def records(self) -> tuple[ContributionRecord, ...]:
        return tuple(self._records)

    @property
    def lifetime_contributed(self) -> int:
        return sum(r.amount for r in self._records)

    @property
    def balance(self) -> int:
        return self.lifetime_contributed - self._paid_out

    def trigger(self, event: ContributionEvent,
                episode_id: int | None = None) -> int:
        """Record a contribution for an eligible app-side event.

        The amount comes from the fixed schedule, capped by remaining
        budget. Returns the amount contributed (0 if budget exhausted).
        """
        amount = min(self._schedule.get(event, 0), self._budget_remaining)
        if amount <= 0:
            return 0
        self._budget_remaining -= amount
        self._records.append(
            ContributionRecord(event=event, amount=amount,
                               episode_id=episode_id)
        )
        return amount

    def disburse(self, charity: str) -> int:
        """Send the whole balance outward to *charity*."""
        amount = self.balance
        self._paid_out += amount
        return amount
