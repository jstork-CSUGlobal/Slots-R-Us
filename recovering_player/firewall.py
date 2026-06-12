"""The hard firewall: NO IDENTITY BY CHANCE.

Everything that wants to cross from Engine 1 (the decaying reel) into
Engine 2 (the progression track) must pass through here as a tagged
``Crossing``. The firewall applies the four doctrine rules and either
clears the crossing or blocks it with an audit record:

    1. Chance cannot grant identity.
    2. Reel outcomes cannot unlock graduation.
    3. Sweepstakes cannot affect recovery rank.
    4. No jackpot baptism.

The pass it issues, ``ClearedCrossing``, can only be constructed by the
firewall itself — the progression track refuses anything else — so there
is no way to route around the checkpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Provenance(str, Enum):
    """Where a fact came from. This is what the firewall judges."""

    CHANCE = "chance"        # reel outcomes, sweepstake draws
    VERIFIED = "verified"    # taper steps, blocking tools, self-exclusion


class CrossingKind(str, Enum):
    """What a crossing is trying to do on the deterministic side."""

    PROGRESS_CREDIT = "progress-credit"
    GRADUATION_UNLOCK = "graduation-unlock"
    RECOVERY_RANK = "recovery-rank"
    IDENTITY_GRANT = "identity-grant"


@dataclass(frozen=True)
class Crossing:
    """A request to move a fact from the reel side to the track side.

    ``episode_id`` scopes the crossing to the episode it arose in, so
    firewall decisions are auditable per episode and the same doctrine
    is verifiably applied within an episode and across its boundary.
    """

    provenance: Provenance
    kind: CrossingKind
    source: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    episode_id: int | None = None


#: Payload keys that denote user-facing monetary value. A CHANCE
#: crossing carrying any of these is blocked outright: no user-facing
#: real-money value may originate from chance.
MONETARY_KEYS = frozenset(
    {"amount", "money", "payout", "winnings", "prize", "donation",
     "cash", "stake_return", "credit"}
)


class FirewallRejection(RuntimeError):
    """A crossing violated firewall doctrine."""

    def __init__(self, rule: str, crossing: Crossing) -> None:
        super().__init__(f"firewall blocked {crossing.kind.value} "
                         f"from {crossing.source!r}: {rule}")
        self.rule = rule
        self.crossing = crossing


class _CheckpointStamp:
    """Private token proving a crossing went through the firewall."""

    __slots__ = ()


@dataclass(frozen=True)
class ClearedCrossing:
    """A crossing the firewall has inspected and passed."""

    crossing: Crossing
    _stamp: _CheckpointStamp

    def stamped_by(self, stamp: _CheckpointStamp) -> bool:
        return self._stamp is stamp


class HardFirewall:
    """The checkpoint between substitution and replacement.

    Doctrine: variable reward can taper behavior; only deterministic
    reward can rebuild identity. Concretely: VERIFIED provenance passes,
    CHANCE provenance never reaches progress, rank, graduation, or
    identity. Every block is recorded for audit.
    """

    DOCTRINE = (
        "variable reward can taper behavior; "
        "only deterministic reward can rebuild identity"
    )

    def __init__(self) -> None:
        self._stamp = _CheckpointStamp()
        self._blocked: list[FirewallRejection] = []
        self._cleared: list[ClearedCrossing] = []

    @property
    def stamp(self) -> _CheckpointStamp:
        return self._stamp

    @property
    def blocked(self) -> tuple[FirewallRejection, ...]:
        return tuple(self._blocked)

    @property
    def cleared(self) -> tuple[ClearedCrossing, ...]:
        return tuple(self._cleared)

    def transmit(self, crossing: Crossing) -> ClearedCrossing:
        rule = self._violated_rule(crossing)
        if rule is not None:
            rejection = FirewallRejection(rule, crossing)
            self._blocked.append(rejection)
            raise rejection
        cleared = ClearedCrossing(crossing=crossing, _stamp=self._stamp)
        self._cleared.append(cleared)
        return cleared

    @staticmethod
    def _violated_rule(crossing: Crossing) -> str | None:
        chance = crossing.provenance is Provenance.CHANCE
        if chance and MONETARY_KEYS.intersection(crossing.payload):
            return "No user-facing money may originate from chance."
        if chance and crossing.payload.get("jackpot"):
            return "No jackpot baptism."
        if chance and crossing.kind is CrossingKind.IDENTITY_GRANT:
            return "Chance cannot grant identity."
        if chance and crossing.kind is CrossingKind.GRADUATION_UNLOCK:
            return "Reel outcomes cannot unlock graduation."
        if crossing.source.startswith("sweepstake") and crossing.kind in (
            CrossingKind.RECOVERY_RANK,
            CrossingKind.PROGRESS_CREDIT,
        ):
            return "Sweepstakes cannot affect recovery rank."
        if chance:
            # Blanket quarantine: chance is contained in substitution.
            return "Chance stays quarantined in the substitution layer."
        return None
