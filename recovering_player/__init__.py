"""Recovering Player — the two-engine firewall, episodic edition.

Chance is quarantined in substitution. Identity is earned in
deterministic replacement. Recovery identity persists; chance-state
does not become identity-state.

    RecoveringPlayer .............. top box: urges, routed episodically
    ├── Episode ................... bounded window of risk and exposure
    ├── DecayingReel (Engine 1) ... substitution layer, designed to die
    │   ├── VariableRatioMimicry .. slot feel; telemetry only, no money
    │   └── CalendarDecay ......... time-anchored taper; binges slow it
    ├── HardFirewall .............. NO IDENTITY BY CHANCE, NO MONEY BY CHANCE
    ├── ProgressionTrack (Engine 2) replacement layer, deterministic
    │   ├── VerifiedBehavior ...... taper steps, blocking tools, self-exclusion
    │   ├── CertainMilestone ...... known target, known reward, no mystery box
    │   └── graduation ceremony ... earned, witnessed, opt-in, permanent
    ├── CharityContributionPool ... house-funded, app-event triggered
    └── IdentityCollection ........ artifacts live only on the deterministic track

Invariants:
    * no user-facing real-money value may originate from chance
    * more spinning cannot make the reel safer faster
    * recovery identity persists; chance-state is episode-scoped
"""

from recovering_player.clock import Clock, ManualClock, SystemClock
from recovering_player.episode import (
    CLEAN_CLOSURES,
    Episode,
    EpisodeAlreadyClosed,
    EpisodeClosure,
    EpisodeTrigger,
    NoActiveEpisode,
)
from recovering_player.firewall import (
    MONETARY_KEYS,
    ClearedCrossing,
    Crossing,
    CrossingKind,
    FirewallRejection,
    HardFirewall,
    Provenance,
)
from recovering_player.decaying_reel import (
    CalendarDecay,
    ContainmentBreach,
    DecayingReel,
    EngineRetired,
    SensoryProfile,
    SpinOutcome,
    TaperStepReceipt,
    VariableRatioMimicry,
)
from recovering_player.progression_track import (
    DEFAULT_SCHEDULE,
    BehaviorKind,
    CertainMilestone,
    NotEligible,
    ProgressionTrack,
    VerifiedBehavior,
)
from recovering_player.artifacts import (
    ArtifactKind,
    IdentityArtifact,
    IdentityCollection,
    ProvenanceError,
)
from recovering_player.terminals import (
    DEFAULT_CONTRIBUTION_SCHEDULE,
    CharityContributionPool,
    ContributionEvent,
    ContributionRecord,
)
from recovering_player.player import RecoveringPlayer, UrgeRouting

__all__ = [
    "Clock",
    "ManualClock",
    "SystemClock",
    "Episode",
    "EpisodeTrigger",
    "EpisodeClosure",
    "CLEAN_CLOSURES",
    "NoActiveEpisode",
    "EpisodeAlreadyClosed",
    "HardFirewall",
    "Crossing",
    "ClearedCrossing",
    "CrossingKind",
    "Provenance",
    "FirewallRejection",
    "MONETARY_KEYS",
    "DecayingReel",
    "VariableRatioMimicry",
    "CalendarDecay",
    "SensoryProfile",
    "SpinOutcome",
    "TaperStepReceipt",
    "EngineRetired",
    "ContainmentBreach",
    "ProgressionTrack",
    "BehaviorKind",
    "VerifiedBehavior",
    "CertainMilestone",
    "DEFAULT_SCHEDULE",
    "NotEligible",
    "ArtifactKind",
    "IdentityArtifact",
    "IdentityCollection",
    "ProvenanceError",
    "CharityContributionPool",
    "ContributionEvent",
    "ContributionRecord",
    "DEFAULT_CONTRIBUTION_SCHEDULE",
    "RecoveringPlayer",
    "UrgeRouting",
]
