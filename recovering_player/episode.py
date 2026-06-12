"""The episode model: gambling behavior is episodic, not a single
permanent linear state.

An episode begins with a reported urge, a planned taper session, a
relapse-risk window, or a recovery check-in. It ends through timeout,
explicit closure, cooldown completion, or a verified transition to
non-use.

Everything chance-flavored is scoped to its episode: spin telemetry,
urge counts, sensory exposure observations. When the episode closes,
that state is sealed inside the closed episode record and has no
mechanism to leak forward. Identity artifacts, once deterministically
earned, are the only thing that persists by design — recovery identity
persists; chance-state does not become identity-state.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EpisodeTrigger(str, Enum):
    REPORTED_URGE = "reported-urge"
    PLANNED_TAPER_SESSION = "planned-taper-session"
    RELAPSE_RISK_WINDOW = "relapse-risk-window"
    RECOVERY_CHECK_IN = "recovery-check-in"


class EpisodeClosure(str, Enum):
    TIMEOUT = "timeout"
    EXPLICIT_CLOSURE = "explicit-closure"
    COOLDOWN_COMPLETE = "cooldown-complete"
    VERIFIED_TRANSITION = "verified-transition-to-non-use"


#: Closures that count as a clean, app-side completion event. These may
#: trigger a house-funded charity contribution; chance outcomes may not.
CLEAN_CLOSURES = frozenset(
    {EpisodeClosure.COOLDOWN_COMPLETE, EpisodeClosure.VERIFIED_TRANSITION}
)


class NoActiveEpisode(RuntimeError):
    """Reel-side activity was attempted outside any episode."""


class EpisodeAlreadyClosed(RuntimeError):
    """A closed episode was asked to accept new state."""


@dataclass
class Episode:
    """One bounded window of relapse risk and taper exposure."""

    trigger: EpisodeTrigger
    opened_at: float
    episode_id: int = field(default_factory=itertools.count(1).__next__)
    closed_at: float | None = None
    closure: EpisodeClosure | None = None
    timeout_days: float = 1.0

    # Episode-scoped chance/ritual state. Dies with the episode.
    spin_count: int = 0
    urge_count: int = 0
    chance_telemetry: list[dict[str, Any]] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return self.closure is None

    def _require_active(self) -> None:
        if not self.active:
            raise EpisodeAlreadyClosed(
                f"episode {self.episode_id} closed ({self.closure})"
            )

    def record_urge(self) -> None:
        self._require_active()
        self.urge_count += 1

    def record_spin(self, telemetry: dict[str, Any]) -> None:
        self._require_active()
        self.spin_count += 1
        self.chance_telemetry.append(dict(telemetry))

    def expired(self, now: float) -> bool:
        return self.active and (now - self.opened_at) >= self.timeout_days

    def close(self, closure: EpisodeClosure, at: float) -> None:
        self._require_active()
        self.closure = closure
        self.closed_at = at
