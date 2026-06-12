# Recovering Player — The Two-Engine Firewall (episodic)

A therapy-app architecture for quitting slot machines.

> **Chance is quarantined in substitution. Identity is earned in
> deterministic replacement.**

Three hard invariants, in priority order:

1. **No user-facing real-money value may originate from chance.**
2. **More spinning cannot make the reel safer faster.**
3. **Recovery identity persists; chance-state does not become
   identity-state.**

```
              ┌────────────────────────────────────┐
              │  USER URGE / CRAVING / RITUAL PULL │
              │        (opens an EPISODE)          │
              └──────┬──────────────────────┬──────┘
                     ▼                      ▼
┌────────────────────────────┐ ║ ┌────────────────────────────┐
│  ENGINE 1: DECAYING REEL   │ ║ │ ENGINE 2: PROGRESSION TRACK│
│  (substitution layer)      │ ║ │ (replacement layer)        │
│  · variable-ratio mimicry  │X║ │ · verified behavior        │
│    (telemetry, no money)   │X║ │ · certain milestones       │
│  · calendar-anchored decay │X║ │ · ceremonial identity      │
│    (binges slow it)        │ ║ │                            │
└─────────────┬──────────────┘ ║ └─────────────┬──────────────┘
  chance stays quarantined,    ║    identity is earned only here,
  scoped to its episode   HARD FIREWALL  permanent once earned
              ▼          NO IDENTITY OR        ▼
┌────────────────────────┐ MONEY BY CHANCE ┌──────────────────────────┐
│ CHARITY CONTRIBUTION   │                 │ IDENTITY ARTIFACTS live  │
│ POOL (house-funded,    │                 │ only on the deterministic│
│ app-event triggered)   │                 │ track                    │
└────────────────────────┘                 └──────────────────────────┘
```

## 1. Money is decoupled from chance entirely

Chance produces telemetry, harmless ritual feedback, and non-monetary
decay-state observations only. `SpinOutcome` has six fields — `hit`,
`forced`, `near_miss`, `jackpot_theater`, `staleness_observed`,
`binge_tripped` — and none is monetary. The reel module has no import
of, and no reference to, any money object.

Charity is modeled as a **house-funded, budgeted contribution pool**
(`terminals.py`). It is funded once at construction from a house
budget; there is no API that accepts user money. Contributions are
triggered by eligible app-side events at fixed scheduled amounts —
enrollment, clean episode closure, recovery check-in, milestone award —
and chance events are not representable in the trigger vocabulary. The
user never owns winnings, never has money "redirected in their name,"
and never receives a cent: money only exits outward to charity.

The firewall additionally blocks, by rule, any chance-provenance
crossing carrying a monetary payload key: *"No user-facing money may
originate from chance."*

## 2. Decay is anchored to calendar time; binges slow it

`CalendarDecay` (`decaying_reel.py`) computes staleness from
*effective recovery days*:

```
effective = elapsed since enrollment
          − time inside binge pauses
          − binge penalty days
          + verified recovery interval bonuses
```

Spins never appear with a positive sign in that formula. Reel
intensity, frequency allowance, brightness, novelty, sound, payout
theater, and emotional punch all decline as calendar staleness rises.
`observe_spin()` feeds only binge detection: crossing the spin-frequency
threshold inside the window pauses decay and applies a partial reset
penalty. Verified recovery behavior (e.g. an honored cooldown) is the
only accelerator. A property test pins the invariant: at equal wall
time, staleness(binge) ≤ staleness(light use) ≤ staleness(abstinent),
with binging strictly worse. Once staleness reaches 1.0 it latches; the
reel is retired permanently.

## 3. The episode model

Gambling behavior is episodic (`episode.py`), not a single permanent
linear state. An episode opens with a **reported urge, planned taper
session, relapse-risk window, or recovery check-in**, and closes by
**timeout, explicit closure, cooldown completion, or verified
transition to non-use**.

All reel-side activity requires an active episode. Spin telemetry,
urge counts, and exposure observations are recorded on the episode and
sealed inside it at closure — closed episodes reject new state. Firewall
crossings carry their `episode_id`, so doctrine decisions are auditable
per episode, and the permanence tests verify that forbidden crossings
stay blocked both **within an active episode** and **across episode
boundaries** (replaying a closed episode's chance telemetry later is
still blocked). Identity artifacts, once deterministically earned at the
witnessed, opt-in, once-only ceremony, persist across all later
episodes — including relapse-risk ones.

## Firewall doctrine (all enforced, all tested)

| Rule | Enforcement |
|---|---|
| No user-facing money may originate from chance | Firewall blocks CHANCE crossings with monetary payload keys; chance outcomes have no monetary fields; the pool's trigger vocabulary is app-side only. |
| Chance cannot grant identity | Firewall blocks CHANCE `IDENTITY_GRANT`; artifacts require the track's private seal. |
| Reel outcomes cannot unlock graduation | Firewall blocks CHANCE `GRADUATION_UNLOCK`; eligibility is a pure function of verified behaviors. |
| Sweepstakes cannot affect recovery rank | Sweepstake-sourced rank/progress crossings blocked (vestigial guard; no sweepstake exists anymore). |
| No jackpot baptism | Jackpot-tagged crossings into identity blocked. |
| Chance stays quarantined | Blanket rule: CHANCE provenance never crosses at all. |
| Identity is earned only here | `ProgressionTrack.credit` accepts only firewall-stamped crossings with VERIFIED provenance. |
| Earned, witnessed, opt-in, permanent | Collection rejects unsealed/unwitnessed/non-opt-in artifacts; ceremony latches only after success. |
| No mystery box | Milestone targets, relics, ranks fixed at construction, readable before play. |

## Running it

No dependencies beyond the Python 3.10+ standard library.

```bash
python -m recovering_player            # one episodic journey, manual clock
python -m unittest discover -s tests   # 34-test invariant suite
```
