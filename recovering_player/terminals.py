"""The two terminal boxes at the bottom of the diagram.

CharityPayoutPool (coral terminal): where money from the chance side
exits the system, irrevocably, to charity. It validates every cent
against the forfeit events on the bus, so the pool can never hold money
the log cannot account for.

IdentityCollection (teal terminal): the permanent shelf of identity
artifacts. It accepts only artifacts sealed by the progression engine,
which is how "the reel cannot dispense identity" is made structural —
the taper side has no seal and so nothing it makes can be shelved.
"""

from __future__ import annotations

from recovering_player.bus import MinimumEventBus
from recovering_player.events import StakeForfeited
from recovering_player.progression_engine import IdentityArtifact, _ProvenanceSeal


class ProvenanceError(RuntimeError):
    """An artifact without the progression engine's seal was offered."""


class CharityPayoutPool:
    """Accrues forfeited stakes and pays them out, exit-only.

    The pool subscribes to ``StakeForfeited`` directly; there is no
    deposit method to call, so nothing can inflate it out-of-band, and
    payouts only ever decrease it. Money goes in by losing and out to
    charity. It never flows back toward the user or the reel.
    """

    def __init__(self, bus: MinimumEventBus) -> None:
        self._accrued = 0
        self._paid_out = 0
        bus.subscribe(StakeForfeited, self._on_forfeit)

    @property
    def balance(self) -> int:
        return self._accrued - self._paid_out

    @property
    def lifetime_accrued(self) -> int:
        return self._accrued

    def _on_forfeit(self, event: StakeForfeited) -> None:
        self._accrued += event.amount

    def disburse(self, charity: str) -> int:
        """Send the whole balance to *charity*. Returns the amount sent."""
        amount = self.balance
        self._paid_out += amount
        return amount


class IdentityCollection:
    """Permanent, append-only shelf of sealed identity artifacts."""

    def __init__(self, seal: _ProvenanceSeal) -> None:
        self._seal = seal
        self._shelf: list[IdentityArtifact] = []

    @property
    def artifacts(self) -> tuple[IdentityArtifact, ...]:
        return tuple(self._shelf)

    def shelve(self, artifact: IdentityArtifact) -> None:
        if not artifact.sealed_by(self._seal):
            raise ProvenanceError(
                "identity may only be dispensed by the progression engine"
            )
        self._shelf.append(artifact)
