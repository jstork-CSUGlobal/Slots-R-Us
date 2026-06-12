"""Engine 1: the decaying reel. The substitution layer.

Purpose: substitution, containment, decay. Chance stays quarantined
here. The reel contains the slot ritual, redirects its charge, then
deliberately decays it into boredom:

* Variable-ratio mimicry — the slot feel, allowed only inside the reel
  as controlled substitution. Token stakes; no money can be won back.
* Charity sweepstakes — salience redirects outward. Wins are donations
  made in the player's name; there is no personal cash-rescue fantasy.
* Taper-to-boredom decay — frequency, brightness, drama, and emotional
  punch all decline together until the ritual is psychologically stale,
  at which point the engine retires itself for good.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from recovering_player.terminals import CharityPayoutPool


class EngineRetired(RuntimeError):
    """The reel went psychologically stale and will not spin again."""


class _ReelInterior:
    """Private token: variable-ratio mechanics may exist only inside
    the reel. Constructing mimicry without it is a containment breach."""

    __slots__ = ()


class ContainmentBreach(RuntimeError):
    """Variable-ratio mechanics were instantiated outside the reel."""


@dataclass(frozen=True)
class SensoryProfile:
    """How loud the ritual is allowed to be right now. All channels
    decay together; cooldown grows so frequency falls."""

    brightness: float
    drama: float
    emotional_punch: float
    cooldown_spins: int

    @property
    def stale(self) -> bool:
        return max(self.brightness, self.drama, self.emotional_punch) <= 0.0


class TaperToBoredomDecay:
    """Monotonic staleness ratchet driving every sensory channel down.

    Staleness climbs from 0.0 to 1.0 and only climbs — there is no
    method that refreshes the ritual. Decay accelerates with use, so
    heavier play tapers faster.
    """

    def __init__(self, base_step: float = 0.01, acceleration: float = 0.002) -> None:
        if base_step <= 0:
            raise ValueError("decay must actually decay")
        self._base_step = base_step
        self._acceleration = acceleration
        self._staleness = 0.0
        self._ticks = 0

    @property
    def staleness(self) -> float:
        return self._staleness

    @property
    def psychologically_stale(self) -> bool:
        return self._staleness >= 1.0

    def tick(self) -> float:
        self._ticks += 1
        step = self._base_step + self._acceleration * self._ticks
        self._staleness = min(1.0, self._staleness + step)
        return self._staleness

    def sensory_profile(self) -> SensoryProfile:
        dim = 1.0 - self._staleness
        return SensoryProfile(
            brightness=round(dim, 4),
            drama=round(dim, 4),
            emotional_punch=round(dim, 4),
            cooldown_spins=int(self._staleness * 10),
        )


@dataclass(frozen=True)
class SpinOutcome:
    """One pull. Tokens only — hits pay nothing, they just feel like
    hits. Provenance is always CHANCE; this never crosses the firewall."""

    hit: bool
    forced: bool
    staleness: float
    jackpot: bool


class VariableRatioMimicry:
    """The contained slot feel, progressively replaced by pattern.

    At staleness 0 each spin hits with ``hit_rate`` independently. As
    staleness rises, a growing share of spins is *forced* onto a fixed,
    announced alternation. Fully stale, the reel is pure pattern.
    """

    def __init__(
        self,
        interior: _ReelInterior,
        hit_rate: float = 0.3,
        jackpot_rate: float = 0.02,
        rng: random.Random | None = None,
    ) -> None:
        if not isinstance(interior, _ReelInterior):
            raise ContainmentBreach(
                "variable-ratio mechanics are allowed only inside the reel"
            )
        if not 0.0 < hit_rate < 1.0:
            raise ValueError("hit_rate must be in (0, 1)")
        self._hit_rate = hit_rate
        self._jackpot_rate = jackpot_rate
        self._rng = rng or random.Random()
        self._forced_cursor = 0

    def spin(self, staleness: float) -> SpinOutcome:
        forced = self._rng.random() < staleness
        if forced:
            hit = self._forced_cursor % 2 == 0
            self._forced_cursor += 1
            jackpot = False
        else:
            hit = self._rng.random() < self._hit_rate
            jackpot = hit and self._rng.random() < self._jackpot_rate
        return SpinOutcome(hit=hit, forced=forced, staleness=staleness,
                           jackpot=jackpot)


@dataclass(frozen=True)
class SweepstakeResult:
    """A charity sweepstake draw. The prize is a donation in the
    player's name; nothing is payable to the player."""

    won: bool
    donated_in_your_name: int
    beneficiary: str


class CharitySweepstakes:
    """Salience redirected outward.

    The player commits the money they would have gambled; it funds the
    charity pool immediately and irrevocably. A winning draw directs an
    extra matched donation in the player's name. At no point does any
    path return money to the player — there is no cash-rescue fantasy
    to chase.
    """

    def __init__(
        self,
        pool: CharityPayoutPool,
        win_rate: float = 0.1,
        match_factor: int = 2,
        rng: random.Random | None = None,
    ) -> None:
        self._pool = pool
        self._win_rate = win_rate
        self._match_factor = match_factor
        self._rng = rng or random.Random()

    def enter(self, committed: int, beneficiary: str = "harm-reduction fund") -> SweepstakeResult:
        if committed <= 0:
            raise ValueError("a sweepstake entry requires a positive commitment")
        self._pool.fund(committed, source="sweepstake-entry")
        won = self._rng.random() < self._win_rate
        donated = committed * self._match_factor if won else committed
        if won:
            self._pool.fund(committed * (self._match_factor - 1),
                            source="sweepstake-match")
        return SweepstakeResult(won=won, donated_in_your_name=donated,
                                beneficiary=beneficiary)


@dataclass(frozen=True)
class TaperStepReceipt:
    """Evidence of verified behavior, attested by reel telemetry.

    This is a fact about what the user *did* (honored the taper), not
    about how any spin *landed* — which is why it may cross the
    firewall when spin outcomes may not.
    """

    description: str
    staleness_at_completion: float
    verified_by: str = "reel-telemetry"


class DecayingReel:
    """Engine 1 facade: mimicry + sweepstakes + decay, and nothing else.

    The reel is mortal by design. Every spin ticks the decay; when the
    ritual is psychologically stale the engine retires permanently and
    the substitution layer's job is done.
    """

    def __init__(
        self,
        charity_pool: CharityPayoutPool,
        decay: TaperToBoredomDecay | None = None,
        rng: random.Random | None = None,
    ) -> None:
        interior = _ReelInterior()
        self._mimicry = VariableRatioMimicry(interior, rng=rng)
        self._sweepstakes = CharitySweepstakes(charity_pool, rng=rng)
        self._decay = decay or TaperToBoredomDecay()
        self._retired = False
        self._spins = 0
        self._honored_cooldowns = 0

    @property
    def retired(self) -> bool:
        return self._retired

    @property
    def staleness(self) -> float:
        return self._decay.staleness

    @property
    def sensory_profile(self) -> SensoryProfile:
        return self._decay.sensory_profile()

    def spin(self) -> SpinOutcome:
        if self._retired:
            raise EngineRetired("psychologically stale: the ritual is over")
        outcome = self._mimicry.spin(self._decay.staleness)
        self._spins += 1
        self._decay.tick()
        if self._decay.psychologically_stale:
            self._retired = True
        return outcome

    def enter_sweepstake(self, committed: int) -> SweepstakeResult:
        if self._retired:
            raise EngineRetired("psychologically stale: the ritual is over")
        return self._sweepstakes.enter(committed)

    def honor_cooldown(self) -> TaperStepReceipt:
        """The user sat out the cooldown instead of spinning through an
        urge. That is a taper step: verified behavior, not an outcome."""
        self._honored_cooldowns += 1
        self._decay.tick()
        if self._decay.psychologically_stale:
            self._retired = True
        return TaperStepReceipt(
            description=f"honored cooldown #{self._honored_cooldowns}",
            staleness_at_completion=self._decay.staleness,
        )
