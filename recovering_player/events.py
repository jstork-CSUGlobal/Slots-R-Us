"""Events that cross the firewall, coral side to teal side.

These are the only things allowed through the breach. They are frozen
(immutable) records of what already happened on the taper side: the
progression engine can read history, never write it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaperEvent:
    """Base class for everything the taper engine emits."""

    session: int
    sequence: int


@dataclass(frozen=True)
class SpinResolved(TaperEvent):
    """One pull of the reel, fully resolved."""

    stake: int
    hit: bool
    predictability: float


@dataclass(frozen=True)
class StakeForfeited(TaperEvent):
    """Money left the user. It is already bound for charity."""

    amount: int


@dataclass(frozen=True)
class GraduationDeclared(TaperEvent):
    """The reel has become fully predictable and has retired itself."""

    total_spins: int
    final_predictability: float
