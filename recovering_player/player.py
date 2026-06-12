"""Recovering player: the top box. The human, and the session they drive.

The orchestrator wires the whole diagram together exactly once per
recovery journey: it asks the bus for its single outlet, hands that
outlet to the taper engine, and points everything else at the listening
side of the bus. After wiring, the only thing the player can actually
do is pull the lever — every consequence propagates through the
governance structure on its own.
"""

from __future__ import annotations

import random

from recovering_player.bus import MinimumEventBus
from recovering_player.progression_engine import ProgressionEngine
from recovering_player.taper_engine import DecayScheduler, EngineRetired, Reel, TaperEngine
from recovering_player.terminals import CharityPayoutPool, IdentityCollection


class RecoveringPlayer:
    """One user's complete journey from variable-ratio hook to graduation."""

    def __init__(
        self,
        rng: random.Random | None = None,
        decay_base_step: float = 0.01,
        decay_acceleration: float = 0.002,
    ) -> None:
        self.bus = MinimumEventBus()
        self.taper = TaperEngine(
            outlet=self.bus.issue_outlet(),
            reel=Reel(rng=rng),
            scheduler=DecayScheduler(decay_base_step, decay_acceleration),
        )
        self.progression = ProgressionEngine(self.bus)
        self.charity_pool = CharityPayoutPool(self.bus)
        self.identity = IdentityCollection(self.progression.seal)

    @property
    def graduated(self) -> bool:
        return self.progression.graduated

    def pull_lever(self, stake: int) -> bool:
        """One spin. Returns True if the reel is still alive afterwards."""
        try:
            self.taper.spin(stake)
        except EngineRetired:
            return False
        return not self.taper.retired

    def play_until_graduation(self, stake: int = 1, max_spins: int = 10_000) -> int:
        """Drive sessions until the taper engine dies. Returns spin count."""
        spins = 0
        while not self.taper.retired and spins < max_spins:
            self.pull_lever(stake)
            spins += 1
        if self.graduated:
            for artifact in self.progression.minted:
                if artifact not in self.identity.artifacts:
                    self.identity.shelve(artifact)
        return spins
