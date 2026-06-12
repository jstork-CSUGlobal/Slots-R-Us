"""The top box: USER URGE / CRAVING / RITUAL PULL.

``RecoveringPlayer`` wires the two engines on either side of the hard
firewall and routes the user's urges — episodically. All reel-side
activity happens inside an episode; verified behavior crosses the
firewall tagged with its episode; charity contributions are triggered
only by eligible app-side events (enrollment, clean episode closure,
check-ins, milestone awards) from a house budget, never by chance and
never with user money.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from recovering_player.artifacts import IdentityArtifact, IdentityCollection
from recovering_player.clock import Clock, ManualClock
from recovering_player.decaying_reel import (
    CalendarDecay,
    DecayingReel,
    SpinOutcome,
)
from recovering_player.episode import (
    CLEAN_CLOSURES,
    Episode,
    EpisodeClosure,
    EpisodeTrigger,
    NoActiveEpisode,
)
from recovering_player.firewall import (
    Crossing,
    CrossingKind,
    HardFirewall,
    Provenance,
)
from recovering_player.progression_track import BehaviorKind, ProgressionTrack
from recovering_player.terminals import (
    CharityContributionPool,
    ContributionEvent,
)


@dataclass(frozen=True)
class UrgeRouting:
    """What the app offers when the user reports a craving."""

    episode_id: int
    substitution_available: bool
    sensory_dimmed_to: float
    suggested_behavior: BehaviorKind


class RecoveringPlayer:
    """One user's episodic, two-engine recovery journey."""

    def __init__(
        self,
        clock: Clock | None = None,
        rng: random.Random | None = None,
        full_term_days: float = 30.0,
        house_budget: int = 1_000,
        binge_spin_threshold: int = 20,
    ) -> None:
        self.clock = clock or ManualClock()
        self.firewall = HardFirewall()
        self.charity_pool = CharityContributionPool(house_budget=house_budget)
        self.reel = DecayingReel(
            decay=CalendarDecay(
                self.clock,
                full_term_days=full_term_days,
                binge_spin_threshold=binge_spin_threshold,
            ),
            rng=rng,
        )
        self.track = ProgressionTrack(self.firewall)
        self.identity = IdentityCollection(self.track.seal)
        self._episodes: list[Episode] = []
        self.charity_pool.trigger(ContributionEvent.ENROLLMENT)

    # ── episode lifecycle ────────────────────────────────────────────
    @property
    def episodes(self) -> tuple[Episode, ...]:
        return tuple(self._episodes)

    @property
    def active_episode(self) -> Episode | None:
        self._sweep_timeouts()
        for episode in reversed(self._episodes):
            if episode.active:
                return episode
        return None

    def begin_episode(self, trigger: EpisodeTrigger,
                      timeout_days: float = 1.0) -> Episode:
        if self.active_episode is not None:
            raise RuntimeError("an episode is already active; close it first")
        episode = Episode(trigger=trigger, opened_at=self.clock.now(),
                          timeout_days=timeout_days)
        self._episodes.append(episode)
        if trigger is EpisodeTrigger.RECOVERY_CHECK_IN:
            self.charity_pool.trigger(ContributionEvent.RECOVERY_CHECK_IN,
                                      episode_id=episode.episode_id)
        return episode

    def close_episode(self, closure: EpisodeClosure) -> Episode:
        episode = self.active_episode
        if episode is None:
            raise NoActiveEpisode("no episode to close")
        episode.close(closure, at=self.clock.now())
        if closure in CLEAN_CLOSURES:
            self.charity_pool.trigger(
                ContributionEvent.CLEAN_EPISODE_CLOSURE,
                episode_id=episode.episode_id,
            )
        return episode

    def _sweep_timeouts(self) -> None:
        now = self.clock.now()
        for episode in self._episodes:
            if episode.expired(now):
                episode.close(EpisodeClosure.TIMEOUT, at=now)

    def _require_episode(self) -> Episode:
        episode = self.active_episode
        if episode is None:
            raise NoActiveEpisode(
                "reel-side activity requires an active episode"
            )
        return episode

    # ── the urge arrives (inside an episode) ─────────────────────────
    def feel_urge(self) -> UrgeRouting:
        episode = self._require_episode()
        episode.record_urge()
        return UrgeRouting(
            episode_id=episode.episode_id,
            substitution_available=not self.reel.retired,
            sensory_dimmed_to=1.0 - self.reel.staleness,
            suggested_behavior=BehaviorKind.TAPER_STEP,
        )

    # ── left: substitution (chance, quarantined, episode-scoped) ─────
    def spin(self) -> SpinOutcome:
        episode = self._require_episode()
        outcome = self.reel.spin()
        episode.record_spin({
            "hit": outcome.hit,
            "forced": outcome.forced,
            "near_miss": outcome.near_miss,
            "jackpot_theater": outcome.jackpot_theater,
            "staleness_observed": outcome.staleness_observed,
            "binge_tripped": outcome.binge_tripped,
        })
        return outcome

    # ── right: replacement (verified behavior crosses the firewall) ──
    def honor_cooldown(self):
        episode = self._require_episode()
        receipt = self.reel.honor_cooldown()
        return self._credit(BehaviorKind.TAPER_STEP, receipt.description,
                            receipt.verified_by, episode.episode_id)

    def activate_blocking_tool(self, tool: str):
        episode = self.active_episode
        return self._credit(
            BehaviorKind.BLOCKING_TOOL, f"activated {tool}", verified_by=tool,
            episode_id=episode.episode_id if episode else None,
        )

    def self_exclude(self, registry: str):
        episode = self.active_episode
        return self._credit(
            BehaviorKind.SELF_EXCLUSION, f"enrolled in {registry}",
            verified_by=registry,
            episode_id=episode.episode_id if episode else None,
        )

    def _credit(self, behavior: BehaviorKind, description: str,
                verified_by: str, episode_id: int | None):
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
                episode_id=episode_id,
            )
        )
        newly_awarded = self.track.credit(cleared)
        for _ in newly_awarded:
            self.charity_pool.trigger(ContributionEvent.MILESTONE_AWARDED,
                                      episode_id=episode_id)
        return newly_awarded

    # ── ceremony (permanent, beyond all episodes) ────────────────────
    def graduation_ceremony(
        self, witnesses: tuple[str, ...], quit_story: str, opt_in: bool = True
    ) -> tuple[IdentityArtifact, ...]:
        return self.track.graduation_ceremony(
            self.identity, witnesses=witnesses, quit_story=quit_story,
            opt_in=opt_in,
        )
