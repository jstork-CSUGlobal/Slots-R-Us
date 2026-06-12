"""The top box: USER URGE / CRAVING / RITUAL PULL.

``RecoveringPlayer`` wires the two engines on either side of the hard
firewall and routes the user's urges. An urge can go left into the
substitution layer (spin the decaying reel, enter a charity sweepstake)
or be answered with verified behavior that crosses the firewall and
credits the progression track. Only the second path builds identity.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from recovering_player.artifacts import IdentityArtifact, IdentityCollection
from recovering_player.decaying_reel import (
    DecayingReel,
    EngineRetired,
    SpinOutcome,
    SweepstakeResult,
    TaperToBoredomDecay,
)
from recovering_player.firewall import (
    Crossing,
    CrossingKind,
    FirewallRejection,
    HardFirewall,
    Provenance,
)
from recovering_player.progression_track import BehaviorKind, ProgressionTrack
from recovering_player.terminals import CharityPayoutPool


@dataclass(frozen=True)
class UrgeRouting:
    """What the app offers when the user reports a craving."""

    substitution_available: bool
    sensory_dimmed_to: float
    suggested_behavior: BehaviorKind


class RecoveringPlayer:
    """One user's two-engine recovery journey."""

    def __init__(
        self,
        rng: random.Random | None = None,
        decay_base_step: float = 0.01,
        decay_acceleration: float = 0.002,
    ) -> None:
        self.firewall = HardFirewall()
        self.charity_pool = CharityPayoutPool()
        self.reel = DecayingReel(
            charity_pool=self.charity_pool,
            decay=TaperToBoredomDecay(decay_base_step, decay_acceleration),
            rng=rng,
        )
        self.track = ProgressionTrack(self.firewall)
        self.identity = IdentityCollection(self.track.seal)

    # ── the urge arrives ─────────────────────────────────────────────
    def feel_urge(self) -> UrgeRouting:
        return UrgeRouting(
            substitution_available=not self.reel.retired,
            sensory_dimmed_to=1.0 - self.reel.staleness,
            suggested_behavior=BehaviorKind.TAPER_STEP,
        )

    # ── left: substitution (chance, quarantined) ─────────────────────
    def spin(self) -> SpinOutcome:
        return self.reel.spin()

    def enter_sweepstake(self, committed: int) -> SweepstakeResult:
        return self.reel.enter_sweepstake(committed)

    # ── right: replacement (verified behavior crosses the firewall) ──
    def honor_cooldown(self):
        """Sit out an urge instead of spinning. Reel telemetry verifies
        it; the firewall clears it; the track credits it."""
        receipt = self.reel.honor_cooldown()
        return self._credit(BehaviorKind.TAPER_STEP, receipt.description,
                            receipt.verified_by)

    def activate_blocking_tool(self, tool: str):
        return self._credit(BehaviorKind.BLOCKING_TOOL,
                            f"activated {tool}", verified_by=tool)

    def self_exclude(self, registry: str):
        return self._credit(BehaviorKind.SELF_EXCLUSION,
                            f"enrolled in {registry}", verified_by=registry)

    def _credit(self, behavior: BehaviorKind, description: str,
                verified_by: str):
        cleared = self.firewall.transmit(
            Crossing(
                provenance=Provenance.VERIFIED,
                kind=CrossingKind.PROGRESS_CREDIT,
                source=verified_by,
                payload={
                    "behavior": behavior.value,
                    "description": description,
                    "verified_by": verified_by,
                },
            )
        )
        return self.track.credit(cleared)

    # ── ceremony ─────────────────────────────────────────────────────
    def graduation_ceremony(
        self, witnesses: tuple[str, ...], quit_story: str, opt_in: bool = True
    ) -> tuple[IdentityArtifact, ...]:
        return self.track.graduation_ceremony(
            self.identity, witnesses=witnesses, quit_story=quit_story,
            opt_in=opt_in,
        )

    # ── convenience for demos and tests ──────────────────────────────
    def burn_out_the_reel(self, max_spins: int = 10_000) -> int:
        """Spin until the ritual goes psychologically stale."""
        spins = 0
        while not self.reel.retired and spins < max_spins:
            try:
                self.reel.spin()
            except EngineRetired:
                break
            spins += 1
        return spins
