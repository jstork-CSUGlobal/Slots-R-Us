"""Engine 2: the progression track. The replacement layer.

Purpose: replacement, status, durable identity. Identity is earned
only here. Deterministic and never touched by chance:

* Verified behavior — progress comes from taper steps, blocking tools,
  or self-exclusion. Nothing else credits.
* Certain milestones — known target, known reward. The whole schedule
  is published before the first behavior is credited. No mystery box.
* Ceremonial identity — graduation artifacts are earned, witnessed,
  opt-in, and permanent.

The track accepts input only as ``ClearedCrossing`` objects stamped by
the hard firewall, so chance physically cannot reach it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from recovering_player.artifacts import (
    ArtifactKind,
    IdentityArtifact,
    IdentityCollection,
    _ProvenanceSeal,
)
from recovering_player.firewall import (
    ClearedCrossing,
    CrossingKind,
    HardFirewall,
    Provenance,
)


class BehaviorKind(str, Enum):
    """The only three sources of progress the diagram recognizes."""

    TAPER_STEP = "taper-step"
    BLOCKING_TOOL = "blocking-tool"
    SELF_EXCLUSION = "self-exclusion"


@dataclass(frozen=True)
class VerifiedBehavior:
    kind: BehaviorKind
    description: str
    verified_by: str


@dataclass(frozen=True)
class CertainMilestone:
    """Known target, known reward, fixed before play. No mystery box."""

    name: str
    target: dict[BehaviorKind, int]
    reward_rank: int
    reward_relic: str


DEFAULT_SCHEDULE: tuple[CertainMilestone, ...] = (
    CertainMilestone(
        name="first-honored-cooldown",
        target={BehaviorKind.TAPER_STEP: 1},
        reward_rank=1,
        reward_relic="relic of the first refusal",
    ),
    CertainMilestone(
        name="tools-installed",
        target={BehaviorKind.BLOCKING_TOOL: 1},
        reward_rank=2,
        reward_relic="relic of the locked door",
    ),
    CertainMilestone(
        name="steady-taper",
        target={BehaviorKind.TAPER_STEP: 5},
        reward_rank=3,
        reward_relic="relic of the long exhale",
    ),
    CertainMilestone(
        name="self-excluded",
        target={BehaviorKind.SELF_EXCLUSION: 1},
        reward_rank=5,
        reward_relic="relic of the closed account",
    ),
)


class NotEligible(RuntimeError):
    """Graduation ceremony requested before the schedule is complete."""


class ProgressionTrack:
    """Engine 2 facade: a deterministic ledger of verified behavior.

    Recovery rank, milestone awards, and graduation eligibility are all
    pure functions of the credited behaviors. Replaying the same
    behaviors rebuilds the same track, always.
    """

    def __init__(
        self,
        firewall: HardFirewall,
        schedule: tuple[CertainMilestone, ...] = DEFAULT_SCHEDULE,
        unlost_per_taper_step: int = 25,
    ) -> None:
        self._stamp = firewall.stamp
        self._schedule = schedule
        self._seal = _ProvenanceSeal()
        self._counts: dict[BehaviorKind, int] = {k: 0 for k in BehaviorKind}
        self._behaviors: list[VerifiedBehavior] = []
        self._awarded: list[CertainMilestone] = []
        self._recovery_rank = 0
        self._unlost_per_taper_step = unlost_per_taper_step
        self._ceremony_held = False

    # ── published upfront: no mystery box ────────────────────────────
    @property
    def schedule(self) -> tuple[CertainMilestone, ...]:
        return self._schedule

    @property
    def seal(self) -> _ProvenanceSeal:
        return self._seal

    @property
    def recovery_rank(self) -> int:
        return self._recovery_rank

    @property
    def milestones_awarded(self) -> tuple[CertainMilestone, ...]:
        return tuple(self._awarded)

    @property
    def behaviors(self) -> tuple[VerifiedBehavior, ...]:
        return tuple(self._behaviors)

    @property
    def unlost_total(self) -> int:
        """Money not lost: deterministic counterfactual savings."""
        return self._counts[BehaviorKind.TAPER_STEP] * self._unlost_per_taper_step

    @property
    def graduation_eligible(self) -> bool:
        return len(self._awarded) == len(self._schedule)

    # ── the only inbound door ────────────────────────────────────────
    def credit(self, cleared: ClearedCrossing) -> list[CertainMilestone]:
        if not cleared.stamped_by(self._stamp):
            raise PermissionError(
                "the progression track accepts only crossings stamped "
                "by the hard firewall"
            )
        crossing = cleared.crossing
        if crossing.provenance is not Provenance.VERIFIED:
            raise PermissionError("only verified behavior credits progress")
        if crossing.kind is not CrossingKind.PROGRESS_CREDIT:
            raise PermissionError("the track credits behavior, nothing else")

        behavior = VerifiedBehavior(
            kind=BehaviorKind(crossing.payload["behavior"]),
            description=str(crossing.payload.get("description", "")),
            verified_by=str(crossing.payload.get("verified_by", crossing.source)),
        )
        self._behaviors.append(behavior)
        self._counts[behavior.kind] += 1
        return self._award_due_milestones()

    def _award_due_milestones(self) -> list[CertainMilestone]:
        newly = []
        for milestone in self._schedule:
            if milestone in self._awarded:
                continue
            if all(self._counts[k] >= n for k, n in milestone.target.items()):
                self._awarded.append(milestone)
                self._recovery_rank = max(self._recovery_rank,
                                          milestone.reward_rank)
                newly.append(milestone)
        return newly

    # ── ceremonial identity ──────────────────────────────────────────
    def graduation_ceremony(
        self,
        collection: IdentityCollection,
        witnesses: tuple[str, ...],
        quit_story: str,
        opt_in: bool = True,
    ) -> tuple[IdentityArtifact, ...]:
        """Mint the full artifact catalog. Earned, witnessed, opt-in,
        permanent — and held exactly once."""
        if not self.graduation_eligible:
            raise NotEligible(
                "graduation requires the complete milestone schedule"
            )
        if self._ceremony_held:
            return ()
        if not opt_in:
            return ()
        self._ceremony_held = True

        def mint(kind: ArtifactKind, title: str, earned_for: str,
                 detail: dict | None = None) -> IdentityArtifact:
            return IdentityArtifact(
                kind=kind,
                title=title,
                earned_for=earned_for,
                witnessed_by=witnesses,
                opted_in=opt_in,
                detail=detail or {},
                _seal=self._seal,
            )

        artifacts = (
            mint(ArtifactKind.DISCHARGE_PAPERS, "discharge papers",
                 "completing the certain-milestone schedule"),
            mint(ArtifactKind.HALL_OF_QUITTERS, "hall of quitters / pantheon",
                 "permanent enrollment among those who walked away"),
            mint(ArtifactKind.UNLOST_LEDGER, "unlost ledger",
                 "money kept by tapering",
                 {"unlost_total": self.unlost_total}),
            mint(ArtifactKind.RECOVERY_RELIC, "recovery relics",
                 "each certain milestone",
                 {"relics": [m.reward_relic for m in self._awarded]}),
            mint(ArtifactKind.QUIT_STORY, "quit story",
                 "telling it in your own words", {"story": quit_story}),
            mint(ArtifactKind.HOUSEBREAKERS_COUNCIL, "housebreakers' council",
                 "a seat among those who beat the house by leaving it"),
        )
        for artifact in artifacts:
            collection.shelve(artifact)
        return artifacts
