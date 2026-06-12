# Recovering Player

A reference implementation of the taper architecture from the UML diagram:
an app whose addictive half is **designed to die**, while its meaningful half
is **permanent, deterministic, and never touched by chance**.

Read the diagram left-lethal, right-sacred:

```
                       ┌─────────────────────┐
                       │  Recovering player  │
                       └──────────┬──────────┘
              ┌───────────────────┴────────────────────┐
   CORAL — mortal          firewall ▒▒▒▒▒▒        TEAL — sacred
┌──────────────────────┐      ▒▒▒▒▒▒▒▒▒▒    ┌──────────────────────┐
│     Taper engine     │      ▒▒▒▒▒▒▒▒▒▒    │  Progression engine  │
│  ┌────────────────┐  │      ▒▒▒▒▒▒▒▒▒▒    │ ┌──────────────────┐ │
│  │      Reel      │  │      ▒▒▒▒▒▒▒▒▒▒    │ │ Milestone tracker│ │
│  └────────────────┘  │      ▒▒▒▒▒▒▒▒▒▒    │ └──────────────────┘ │
│  ┌────────────────┐  │ ┌───────────────┐  │ ┌──────────────────┐ │
│  │ Decay scheduler│──┼─►   event bus   ├──┼►│  Identity mint   │ │
│  └────────────────┘  │ └───────────────┘  │ └──────────────────┘ │
└──────────┬───────────┘   the one breach   └──────────┬───────────┘
           ▼                                           ▼
┌──────────────────────┐                    ┌──────────────────────┐
│  Charity payout pool │                    │ Identity collection  │
└──────────────────────┘                    └──────────────────────┘
```

## Governance rules, and where each is enforced

The arrows tell the whole governance story. Every rule is **structural** —
made impossible by construction, not requested by convention:

| Rule | Enforcement |
|---|---|
| Events flow taper → progression, never back | `MinimumEventBus.issue_outlet()` creates the single publish capability exactly once; the taper engine holds it. A second call raises `BreachViolation`. Subscribers get no publish path. |
| Progression cannot influence reel odds | `progression_engine.py` has no import of, and holds no reference to, the taper engine or the outlet. There is no inbound channel to the coral side. |
| The reel cannot dispense identity | `IdentityCollection.shelve()` rejects any artifact not sealed with the `ProgressionEngine`'s private `_ProvenanceSeal` instance (raises `ProvenanceError`). The taper side never sees the seal. |
| The taper side is designed to die | `DecayScheduler` is a monotonic ratchet with no reset method; at predictability 1.0 the engine emits `GraduationDeclared`, retires, and any further spin raises `EngineRetired`. |
| The teal side is never touched by chance | No randomness, clocks, or I/O anywhere in `progression_engine.py` (tested via AST inspection of its imports). Replaying the same event log rebuilds identical state. |
| Money exits to charity, irrevocably | `CharityPayoutPool` has no public deposit method — it accrues solely from `StakeForfeited` bus events — and `disburse()` only ever empties it outward. |

## Box-by-box spec

### Recovering player — `player.py`
The top box: the user and the session they drive. `RecoveringPlayer` wires the
diagram exactly once (bus → outlet → taper; everything else listens) and then
the only verb left is `pull_lever(stake)`. All consequences propagate through
the governance structure on their own.

### Taper engine (coral) — `taper_engine.py`
The mortal subsystem. Composes the reel and the decay scheduler; emits
immutable `TaperEvent`s through its outlet; self-retires at saturation.

- **Reel** — classic variable-ratio reinforcement at predictability 0. As the
  poison rises, a growing share of spins becomes *forced*: outcomes follow a
  fixed, announced alternation instead of chance. Fully poisoned, it is pure
  pattern — no surprise, nothing left to chase.
- **Decay scheduler** — the progressive poisoning. Predictability only ratchets
  upward, and decay *accelerates* with use, so heavier play tapers faster.

### Progression engine (teal) — `progression_engine.py`
The permanent subsystem. A pure fold over the event log it observes through
the bus: deterministic milestones (`MilestoneTracker`) and, at graduation, the
minting of a provenance-sealed `IdentityArtifact`. Graduation is the moment
this engine becomes the whole app.

### Minimum event bus — `bus.py`, `events.py`
The only deliberate breach in the firewall. One inlet (the `TaperOutlet`
capability), many listeners, an append-only log. Only frozen `TaperEvent`
records may cross: `SpinResolved`, `StakeForfeited`, `GraduationDeclared`.

### Charity payout pool (coral terminal) — `terminals.py`
Where money from the chance side leaves the system. Every cent is validated
against the forfeit events on the bus log, so the pool can never hold money
the log cannot account for. Exit-only.

### Identity collection (teal terminal) — `terminals.py`
The permanent shelf of identity artifacts. Provenance-checked at the door:
only the progression engine's seal opens it.

## Running it

No dependencies beyond the Python 3.10+ standard library.

```bash
python -m recovering_player            # one full journey, default seed
python -m recovering_player 99         # different journey, same destination
python -m unittest discover -s tests   # governance invariant suite
```

Example output:

```
journey complete
  spins until graduation : 27
  final predictability   : 1.00
  taper engine retired   : True
  milestones earned      : ['first-steps', 'steady-hand', 'clear-eyed']
  identity shelf         : ['graduate']
  charity disbursement   : 85 units (lifetime accrued 85)
  bus log length         : 45 events, all coral-origin
```
