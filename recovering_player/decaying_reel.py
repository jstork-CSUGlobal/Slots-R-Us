"""Engine 1: the decaying reel. The substitution layer.

Purpose: substitution, containment, decay. Chance stays quarantined
here, and — correction 1 — chance produces telemetry, harmless ritual
feedback, and non-monetary decay-state observations ONLY. There is no
monetary field on any chance outcome and no path from this module to
the charity pool.

Correction 2: decay is anchored to calendar time, not spin count.
Sensory intensity declines with elapsed time since enrollment, advanced
further by verified recovery intervals. Binges and high-frequency use
SLOW decay (pause + partial reset); spinning can never make the reel
safer faster.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

from recovering_player.clock import Clock


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
    decline together as calendar staleness rises."""

    brightness: float
    novelty: float
    sound: float
    payout_theater: float
    emotional_punch: float
    frequency_allowance: int  # spins permitted per day, declining

    @property
    def stale(self) -> bool:
        return max(self.brightness, self.novelty, self.sound,
                   self.payout_theater, self.emotional_punch) <= 0.0


class CalendarDecay:
    """Taper-to-boredom anchored to wall time and recovery windows.

    Staleness in [0, 1] is computed from *effective recovery days*:

        effective = (elapsed since enrollment)
                  - (time spent inside binge pauses)
                  - (binge penalty days)
                  + (verified recovery interval bonuses)

    Spins never appear with a positive sign anywhere in that formula.
    ``observe_spin`` only feeds binge detection: when spin frequency
    inside the window crosses the threshold, decay pauses for a while
    and a penalty partially resets accrued progress. Verified recovery
    behavior is the only accelerator. Once staleness reaches 1.0 the
    stale state latches permanently.
    """

    def __init__(
        self,
        clock: Clock,
        full_term_days: float = 30.0,
        binge_window_days: float = 1.0,
        binge_spin_threshold: int = 20,
        binge_penalty_days: float = 2.0,
        binge_pause_days: float = 1.0,
    ) -> None:
        self._clock = clock
        self._enrolled_at = clock.now()
        self._full_term = full_term_days
        self._binge_window = binge_window_days
        self._binge_threshold = binge_spin_threshold
        self._binge_penalty = binge_penalty_days
        self._binge_pause = binge_pause_days

        self._recent_spins: deque[float] = deque()
        self._pauses: list[tuple[float, float]] = []
        self._penalty_days = 0.0
        self._recovery_bonus_days = 0.0
        self._binge_count = 0
        self._stale_latch = False

    # ── observation ──────────────────────────────────────────────────
    @property
    def binge_count(self) -> int:
        return self._binge_count

    def paused(self, now: float | None = None) -> bool:
        now = self._clock.now() if now is None else now
        return any(start <= now < end for start, end in self._pauses)

    def effective_days(self) -> float:
        now = self._clock.now()
        elapsed = now - self._enrolled_at
        paused = sum(
            max(0.0, min(end, now) - start) for start, end in self._pauses
        )
        return max(
            0.0,
            elapsed - paused - self._penalty_days + self._recovery_bonus_days,
        )

    @property
    def staleness(self) -> float:
        if self._stale_latch:
            return 1.0
        value = min(1.0, self.effective_days() / self._full_term)
        if value >= 1.0:
            self._stale_latch = True
        return value

    @property
    def psychologically_stale(self) -> bool:
        return self.staleness >= 1.0

    def sensory_profile(self) -> SensoryProfile:
        dim = round(1.0 - self.staleness, 4)
        return SensoryProfile(
            brightness=dim,
            novelty=dim,
            sound=dim,
            payout_theater=dim,
            emotional_punch=dim,
            frequency_allowance=int(dim * 50),
        )

    # ── the only inputs ──────────────────────────────────────────────
    def observe_spin(self) -> bool:
        """Feed binge detection. Returns True if this spin tripped a
        binge response (pause + partial reset). Never advances decay."""
        now = self._clock.now()
        self._recent_spins.append(now)
        while (self._recent_spins
               and now - self._recent_spins[0] > self._binge_window):
            self._recent_spins.popleft()
        if len(self._recent_spins) >= self._binge_threshold:
            self._binge_count += 1
            self._penalty_days += self._binge_penalty
            self._pauses.append((now, now + self._binge_pause))
            self._recent_spins.clear()
            return True
        return False

    def credit_recovery_interval(self, bonus_days: float = 0.5) -> None:
        """Verified recovery behavior is the only decay accelerator."""
        if bonus_days < 0:
            raise ValueError("recovery bonuses do not run backwards")
        self._recovery_bonus_days += bonus_days


@dataclass(frozen=True)
class SpinOutcome:
    """One pull. Pure ritual telemetry: symbols, a hit feeling, theater
    intensity, decay-state observation. No monetary fields exist on
    this type, and nothing here is owed to anyone."""

    hit: bool
    forced: bool
    near_miss: bool
    jackpot_theater: bool
    staleness_observed: float
    binge_tripped: bool


class VariableRatioMimicry:
    """The contained slot feel, progressively replaced by pattern.

    At staleness 0 each spin hits with ``hit_rate`` independently. As
    calendar staleness rises, a growing share of spins is *forced* onto
    a fixed, announced alternation. Fully stale, the reel is pure
    pattern. Hits, near-misses, and jackpot theater are feelings, not
    funds.
    """

    def __init__(
        self,
        interior: _ReelInterior,
        hit_rate: float = 0.3,
        jackpot_theater_rate: float = 0.02,
        near_miss_rate: float = 0.15,
        rng: random.Random | None = None,
    ) -> None:
        if not isinstance(interior, _ReelInterior):
            raise ContainmentBreach(
                "variable-ratio mechanics are allowed only inside the reel"
            )
        if not 0.0 < hit_rate < 1.0:
            raise ValueError("hit_rate must be in (0, 1)")
        self._hit_rate = hit_rate
        self._jackpot_theater_rate = jackpot_theater_rate
        self._near_miss_rate = near_miss_rate
        self._rng = rng or random.Random()
        self._forced_cursor = 0

    def spin(self, staleness: float) -> tuple[bool, bool, bool, bool]:
        """Returns (hit, forced, near_miss, jackpot_theater)."""
        forced = self._rng.random() < staleness
        if forced:
            hit = self._forced_cursor % 2 == 0
            self._forced_cursor += 1
            return hit, True, False, False
        hit = self._rng.random() < self._hit_rate
        near_miss = (not hit) and self._rng.random() < self._near_miss_rate
        theater = hit and self._rng.random() < self._jackpot_theater_rate
        return hit, False, near_miss, theater


@dataclass(frozen=True)
class TaperStepReceipt:
    """Evidence of verified behavior, attested by reel telemetry.

    A fact about what the user *did* (honored the taper), not about how
    any spin *landed* — which is why it may cross the firewall when
    spin outcomes may not.
    """

    description: str
    staleness_at_completion: float
    verified_by: str = "reel-telemetry"


class DecayingReel:
    """Engine 1 facade: mimicry + calendar decay, and nothing else.

    The reel is mortal by design: when calendar staleness reaches 1.0
    the ritual is psychologically stale and the engine retires
    permanently. The reel holds no money object of any kind.
    """

    def __init__(
        self,
        decay: CalendarDecay,
        rng: random.Random | None = None,
    ) -> None:
        self._mimicry = VariableRatioMimicry(_ReelInterior(), rng=rng)
        self._decay = decay
        self._honored_cooldowns = 0

    @property
    def retired(self) -> bool:
        return self._decay.psychologically_stale

    @property
    def staleness(self) -> float:
        return self._decay.staleness

    @property
    def sensory_profile(self) -> SensoryProfile:
        return self._decay.sensory_profile()

    @property
    def decay(self) -> CalendarDecay:
        return self._decay

    def spin(self) -> SpinOutcome:
        if self.retired:
            raise EngineRetired("psychologically stale: the ritual is over")
        staleness = self._decay.staleness
        hit, forced, near_miss, theater = self._mimicry.spin(staleness)
        binge_tripped = self._decay.observe_spin()
        return SpinOutcome(
            hit=hit,
            forced=forced,
            near_miss=near_miss,
            jackpot_theater=theater,
            staleness_observed=staleness,
            binge_tripped=binge_tripped,
        )

    def honor_cooldown(self) -> TaperStepReceipt:
        """The user sat out an urge instead of spinning through it.
        Verified behavior: credits a recovery interval to the decay."""
        self._honored_cooldowns += 1
        self._decay.credit_recovery_interval()
        return TaperStepReceipt(
            description=f"honored cooldown #{self._honored_cooldowns}",
            staleness_at_completion=self._decay.staleness,
        )
