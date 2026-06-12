"""Calendar time as an injectable dependency.

Decay is anchored to wall time, not spin count, so the time source must
be explicit and controllable in tests. Units are days (float).
"""

from __future__ import annotations

import time
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float:
        """Current time in days since an arbitrary epoch."""
        ...


class SystemClock:
    """Real wall time, expressed in days."""

    def now(self) -> float:
        return time.time() / 86_400.0


class ManualClock:
    """Deterministic clock for tests and demos. Only moves forward."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def now(self) -> float:
        return self._now

    def advance(self, days: float) -> float:
        if days < 0:
            raise ValueError("time does not run backwards")
        self._now += days
        return self._now
