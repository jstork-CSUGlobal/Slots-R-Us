"""Recovering Player - a taper architecture for variable-ratio recovery.

Component map (mirrors the UML diagram; read it left-lethal, right-sacred):

    RecoveringPlayer ............ top box: the user and their journey
    ├── TaperEngine (coral) ..... designed to die
    │   ├── Reel ................ variable-ratio reinforcement
    │   └── DecayScheduler ...... poisons the reel with predictability
    ├── ProgressionEngine (teal)  permanent, deterministic, chance-free
    │   ├── MilestoneTracker .... pure function of the event log
    │   └── IdentityArtifact .... provenance-sealed identity minting
    ├── MinimumEventBus ......... the only deliberate breach in the firewall
    ├── CharityPayoutPool ....... coral terminal: money exits to charity
    └── IdentityCollection ...... teal terminal: permanent identity shelf

Governance, enforced structurally:
    * events flow taper -> progression, never back (single publish outlet)
    * the progression engine cannot influence reel odds (no inbound channel)
    * the reel cannot dispense identity (provenance seal it does not hold)
    * predictability only ratchets up; graduation is irreversible
"""

from recovering_player.bus import BreachViolation, MinimumEventBus, TaperOutlet
from recovering_player.events import (
    GraduationDeclared,
    SpinResolved,
    StakeForfeited,
    TaperEvent,
)
from recovering_player.taper_engine import (
    DecayScheduler,
    EngineRetired,
    Reel,
    TaperEngine,
)
from recovering_player.progression_engine import (
    IdentityArtifact,
    Milestone,
    MilestoneTracker,
    ProgressionEngine,
)
from recovering_player.terminals import (
    CharityPayoutPool,
    IdentityCollection,
    ProvenanceError,
)
from recovering_player.player import RecoveringPlayer

__all__ = [
    "BreachViolation",
    "MinimumEventBus",
    "TaperOutlet",
    "TaperEvent",
    "SpinResolved",
    "StakeForfeited",
    "GraduationDeclared",
    "TaperEngine",
    "Reel",
    "DecayScheduler",
    "EngineRetired",
    "ProgressionEngine",
    "MilestoneTracker",
    "Milestone",
    "IdentityArtifact",
    "CharityPayoutPool",
    "IdentityCollection",
    "ProvenanceError",
    "RecoveringPlayer",
]
