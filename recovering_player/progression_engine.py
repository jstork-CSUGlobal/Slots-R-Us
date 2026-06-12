"""Progression engine: the teal side. Permanent, deterministic, sacred.

It is never touched by chance: there is no random source anywhere in
this module, and every state transition is a pure function of the event
log it has observed. Replaying the same log always rebuilds the same
progression.

It listens to the bus and only listens. It holds no TaperOutlet and no
reference to the taper engine, so it cannot influence reel odds even in
principle. What it *can* do is the one thing the reel cannot: dispense
identity, by minting provenance-sealed artifacts for the collection.
"""

from __future__ import annotations

from dataclasses import dataclass

from recovering_player.bus import MinimumEventBus
from recovering_player.events import (
    GraduationDeclared,
    SpinResolved,
    StakeForfeited,
    TaperEvent,
)


@dataclass(frozen=True)
class Milestone:
    """A permanent, deterministic checkpoint. Once earned, never revoked."""

    name: str
    earned_at_event: int


class _ProvenanceSeal:
    """Private mint token. Only the progression engine can construct
    artifacts because only it holds the seal instance."""

    __slots__ = ()


@dataclass(frozen=True)
class IdentityArtifact:
    """A permanent identity credential. Sealed at mint, immutable after."""

    title: str
    milestone_count: int
    _seal: _ProvenanceSeal

    def sealed_by(self, seal: _ProvenanceSeal) -> bool:
        return self._seal is seal


class MilestoneTracker:
    """Deterministic milestone ledger driven purely by observed events.

    Thresholds are fixed at construction; awarding a milestone is a pure
    function of (events seen so far). No clocks, no randomness, no
    outside input.
    """

    DEFAULT_THRESHOLDS: dict[str, int] = {
        "first-steps": 1,
        "steady-hand": 10,
        "clear-eyed": 25,
    }

    def __init__(self, spin_thresholds: dict[str, int] | None = None) -> None:
        self._thresholds = dict(spin_thresholds or self.DEFAULT_THRESHOLDS)
        self._spins_seen = 0
        self._events_seen = 0
        self._milestones: list[Milestone] = []

    @property
    def milestones(self) -> tuple[Milestone, ...]:
        return tuple(self._milestones)

    def observe(self, event: TaperEvent) -> list[Milestone]:
        self._events_seen += 1
        if isinstance(event, SpinResolved):
            self._spins_seen += 1
        earned = []
        for name, threshold in sorted(self._thresholds.items(), key=lambda kv: kv[1]):
            if self._spins_seen >= threshold and not self._has(name):
                milestone = Milestone(name=name, earned_at_event=self._events_seen)
                self._milestones.append(milestone)
                earned.append(milestone)
        return earned

    def _has(self, name: str) -> bool:
        return any(m.name == name for m in self._milestones)


class ProgressionEngine:
    """Teal subsystem facade: subscribes to the breach, accumulates the
    permanent record, and mints identity at graduation.

    Everything here survives the taper engine's death; graduation is the
    moment this engine becomes the whole app.
    """

    def __init__(
        self,
        bus: MinimumEventBus,
        tracker: MilestoneTracker | None = None,
    ) -> None:
        self._tracker = tracker or MilestoneTracker()
        self._seal = _ProvenanceSeal()
        self._forfeits_witnessed = 0
        self._graduated = False
        self._minted: list[IdentityArtifact] = []
        bus.subscribe(TaperEvent, self._on_event)

    @property
    def seal(self) -> _ProvenanceSeal:
        return self._seal

    @property
    def graduated(self) -> bool:
        return self._graduated

    @property
    def milestones(self) -> tuple[Milestone, ...]:
        return self._tracker.milestones

    @property
    def minted(self) -> tuple[IdentityArtifact, ...]:
        return tuple(self._minted)

    def _on_event(self, event: TaperEvent) -> None:
        self._tracker.observe(event)
        if isinstance(event, StakeForfeited):
            self._forfeits_witnessed += 1
        if isinstance(event, GraduationDeclared):
            self._graduated = True
            self._mint(
                IdentityArtifact(
                    title="graduate",
                    milestone_count=len(self._tracker.milestones),
                    _seal=self._seal,
                )
            )

    def _mint(self, artifact: IdentityArtifact) -> None:
        self._minted.append(artifact)
