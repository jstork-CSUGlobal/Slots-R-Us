"""Recovering Player — the two-engine firewall.

Chance is quarantined in substitution. Identity is earned in
deterministic replacement.

    RecoveringPlayer .............. top box: user urge / craving / ritual pull
    ├── DecayingReel (Engine 1) ... substitution layer, designed to die
    │   ├── VariableRatioMimicry .. slot feel, contained, tokens only
    │   ├── CharitySweepstakes .... salience redirected outward
    │   └── TaperToBoredomDecay ... every sensory channel ratchets down
    ├── HardFirewall .............. NO IDENTITY BY CHANCE (4 doctrine rules)
    ├── ProgressionTrack (Engine 2) replacement layer, deterministic
    │   ├── VerifiedBehavior ...... taper steps, blocking tools, self-exclusion
    │   ├── CertainMilestone ...... known target, known reward, no mystery box
    │   └── graduation ceremony ... earned, witnessed, opt-in, permanent
    ├── CharityPayoutPool ......... money exits outward, never back
    └── IdentityCollection ........ artifacts live only on the deterministic track

Firewall doctrine: variable reward can taper behavior; only
deterministic reward can rebuild identity.
"""

from recovering_player.firewall import (
    ClearedCrossing,
    Crossing,
    CrossingKind,
    FirewallRejection,
    HardFirewall,
    Provenance,
)
from recovering_player.decaying_reel import (
    CharitySweepstakes,
    ContainmentBreach,
    DecayingReel,
    EngineRetired,
    SensoryProfile,
    SpinOutcome,
    SweepstakeResult,
    TaperStepReceipt,
    TaperToBoredomDecay,
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
from recovering_player.terminals import CharityPayoutPool, FundingRecord
from recovering_player.player import RecoveringPlayer, UrgeRouting

__all__ = [
    "HardFirewall",
    "Crossing",
    "ClearedCrossing",
    "CrossingKind",
    "Provenance",
    "FirewallRejection",
    "DecayingReel",
    "VariableRatioMimicry",
    "CharitySweepstakes",
    "TaperToBoredomDecay",
    "SensoryProfile",
    "SpinOutcome",
    "SweepstakeResult",
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
    "CharityPayoutPool",
    "FundingRecord",
    "RecoveringPlayer",
    "UrgeRouting",
]
