"""Identity artifacts live only on the deterministic track.

The full catalog from the diagram: Discharge Papers, Hall of Quitters /
Pantheon, Unlost Ledger, Recovery Relics, Quit Story, Housebreakers'
Council. Every artifact is earned, witnessed, opt-in, and permanent —
and carries the progression track's provenance seal, which the reel
side never holds. That is how "chance cannot grant identity" is made
structural rather than aspirational.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ArtifactKind(str, Enum):
    DISCHARGE_PAPERS = "discharge-papers"
    HALL_OF_QUITTERS = "hall-of-quitters-pantheon"
    UNLOST_LEDGER = "unlost-ledger"
    RECOVERY_RELIC = "recovery-relic"
    QUIT_STORY = "quit-story"
    HOUSEBREAKERS_COUNCIL = "housebreakers-council"


class _ProvenanceSeal:
    """Private mint token held only by the progression track."""

    __slots__ = ()


class ProvenanceError(RuntimeError):
    """An artifact without the progression track's seal was offered."""


@dataclass(frozen=True)
class IdentityArtifact:
    """A permanent, ceremonial identity credential.

    ``witnessed_by`` and ``opted_in`` are recorded at mint because the
    diagram demands graduation artifacts be earned, witnessed, opt-in,
    and permanent — permanence comes from the frozen dataclass plus the
    append-only collection below.
    """

    kind: ArtifactKind
    title: str
    earned_for: str
    witnessed_by: tuple[str, ...]
    opted_in: bool
    detail: dict = field(default_factory=dict)
    _seal: _ProvenanceSeal = field(default=None)  # type: ignore[assignment]

    def sealed_by(self, seal: _ProvenanceSeal) -> bool:
        return self._seal is seal


class IdentityCollection:
    """Append-only shelf on the deterministic track.

    Rejects anything not sealed by the progression track, and rejects
    artifacts minted without opt-in or without witnesses: identity here
    is ceremonial, never ambient and never accidental.
    """

    def __init__(self, seal: _ProvenanceSeal) -> None:
        self._seal = seal
        self._shelf: list[IdentityArtifact] = []

    @property
    def artifacts(self) -> tuple[IdentityArtifact, ...]:
        return tuple(self._shelf)

    def shelve(self, artifact: IdentityArtifact) -> None:
        if not artifact.sealed_by(self._seal):
            raise ProvenanceError(
                "identity artifacts may only be minted by the progression track"
            )
        if not artifact.opted_in:
            raise ProvenanceError("identity is opt-in; no ambient artifacts")
        if not artifact.witnessed_by:
            raise ProvenanceError("identity must be witnessed")
        self._shelf.append(artifact)

    def holds(self, kind: ArtifactKind) -> bool:
        return any(a.kind is kind for a in self._shelf)
