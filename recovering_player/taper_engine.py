"""Taper engine: the coral side. The part of the app designed to die.

It contains the variable-ratio reel and the decay scheduler that
progressively poisons the reel with predictability. When the reel is
fully predictable it bores its user into graduation and retires itself,
permanently. There is no API to resurrect it.

The reel handles stakes and chance only. It cannot dispense identity:
this module has no import path to, and no reference into, the
progression engine. Its sole output channel is the TaperOutlet.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from recovering_player.bus import TaperOutlet
from recovering_player.events import (
    GraduationDeclared,
    SpinResolved,
    StakeForfeited,
)


class EngineRetired(RuntimeError):
    """The taper engine has graduated its user and will not spin again."""


@dataclass(frozen=True)
class SpinResult:
    hit: bool
    predictability: float
    forced: bool


class DecayScheduler:
    """Monotonic ratchet that poisons the reel with predictability.

    Starts at 0.0 (pure variable-ratio chance) and climbs toward 1.0
    (every outcome telegraphed in advance). The ratchet only moves up;
    there is deliberately no method that lowers it. Decay accelerates
    with use, so heavier players are tapered faster.
    """

    def __init__(self, base_step: float = 0.01, acceleration: float = 0.002) -> None:
        if base_step <= 0:
            raise ValueError("decay must actually decay")
        self._base_step = base_step
        self._acceleration = acceleration
        self._predictability = 0.0
        self._ticks = 0

    @property
    def predictability(self) -> float:
        return self._predictability

    @property
    def saturated(self) -> bool:
        return self._predictability >= 1.0

    def tick(self) -> float:
        """Advance the poison one spin. Returns the new predictability."""
        self._ticks += 1
        step = self._base_step + self._acceleration * self._ticks
        self._predictability = min(1.0, self._predictability + step)
        return self._predictability


class Reel:
    """Variable-ratio reinforcement, progressively defanged.

    At predictability 0 it is a classic variable-ratio reel: each spin
    hits with ``hit_rate`` probability, independent of history. As the
    scheduler raises predictability, a growing share of spins is
    *forced*: their outcome follows a fixed, announced alternating
    pattern instead of chance. A fully poisoned reel is pure pattern —
    no surprise, no reinforcement, nothing left to chase.
    """

    def __init__(self, hit_rate: float = 0.3, rng: random.Random | None = None) -> None:
        if not 0.0 < hit_rate < 1.0:
            raise ValueError("hit_rate must be a real gamble, in (0, 1)")
        self._hit_rate = hit_rate
        self._rng = rng or random.Random()
        self._forced_cursor = 0

    def spin(self, predictability: float) -> SpinResult:
        forced = self._rng.random() < predictability
        if forced:
            # Announced pattern: strict alternation. Utterly boring on purpose.
            hit = self._forced_cursor % 2 == 0
            self._forced_cursor += 1
        else:
            hit = self._rng.random() < self._hit_rate
        return SpinResult(hit=hit, predictability=predictability, forced=forced)


class TaperEngine:
    """Coral subsystem facade: reel + decay scheduler + the one outlet.

    Lifecycle: spins resolve, stakes forfeit, predictability ratchets up,
    and at saturation the engine declares graduation and dies. Every
    externally visible effect leaves through ``outlet`` as an immutable
    TaperEvent; the engine holds no inbound channel whatsoever.
    """

    def __init__(
        self,
        outlet: TaperOutlet,
        reel: Reel | None = None,
        scheduler: DecayScheduler | None = None,
        session: int = 0,
    ) -> None:
        self._outlet = outlet
        self._reel = reel or Reel()
        self._scheduler = scheduler or DecayScheduler()
        self._session = session
        self._sequence = 0
        self._spins = 0
        self._retired = False

    @property
    def retired(self) -> bool:
        return self._retired

    @property
    def predictability(self) -> float:
        return self._scheduler.predictability

    def spin(self, stake: int) -> SpinResult:
        if self._retired:
            raise EngineRetired("graduated: the reel does not come back")
        if stake <= 0:
            raise ValueError("a spin requires a positive stake")

        result = self._reel.spin(self._scheduler.predictability)
        self._spins += 1

        self._emit(
            SpinResolved(
                session=self._session,
                sequence=self._next_seq(),
                stake=stake,
                hit=result.hit,
                predictability=result.predictability,
            )
        )
        if not result.hit:
            self._emit(
                StakeForfeited(
                    session=self._session,
                    sequence=self._next_seq(),
                    amount=stake,
                )
            )

        self._scheduler.tick()
        if self._scheduler.saturated:
            self._graduate()
        return result

    def _graduate(self) -> None:
        self._retired = True
        self._emit(
            GraduationDeclared(
                session=self._session,
                sequence=self._next_seq(),
                total_spins=self._spins,
                final_predictability=self._scheduler.predictability,
            )
        )

    def _next_seq(self) -> int:
        self._sequence += 1
        return self._sequence

    def _emit(self, event) -> None:
        self._outlet.publish(event)
