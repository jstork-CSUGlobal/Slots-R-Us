# Recovering Player — The Two-Engine Firewall

A therapy-app architecture for quitting slot machines, implemented from the
diagram. The motto is the whole design:

> **Chance is quarantined in substitution. Identity is earned in
> deterministic replacement.**
>
> **Firewall doctrine: variable reward can taper behavior; only
> deterministic reward can rebuild identity.**

```
              ┌────────────────────────────────────┐
              │  USER URGE / CRAVING / RITUAL PULL │
              └──────┬──────────────────────┬──────┘
                     ▼                      ▼
┌────────────────────────────┐ ║ ┌────────────────────────────┐
│  ENGINE 1: DECAYING REEL   │ ║ │ ENGINE 2: PROGRESSION TRACK│
│  (substitution layer)      │ ║ │ (replacement layer)        │
│  · variable-ratio mimicry  │X║ │ · verified behavior        │
│  · charity sweepstakes     │X║ │ · certain milestones       │
│  · taper-to-boredom decay  │X║ │ · ceremonial identity      │
│  PURPOSE: substitution,    │ ║ │ PURPOSE: replacement,      │
│  containment, decay        │ ║ │ status, durable identity   │
└─────────────┬──────────────┘ ║ └─────────────┬──────────────┘
   chance stays quarantined    ║    identity is earned only here
              ▼           HARD FIREWALL        ▼
┌────────────────────────┐ NO IDENTITY  ┌─────────────────────────────┐
│  CHARITY PAYOUT POOL   │  BY CHANCE   │ IDENTITY ARTIFACTS live only│
│  (money exits outward) │              │ on the deterministic track  │
└────────────────────────┘              └─────────────────────────────┘
```

## How the app stops slot-machining for money

The user's urge is real, so the app does not pretend it away — it routes it.

**Engine 1, the decaying reel** (`decaying_reel.py`), is the substitution
layer: contain the slot ritual, redirect the charge, then deliberately decay
it into boredom.

- **Variable-ratio mimicry** — the slot *feel*, allowed only inside the reel
  as controlled substitution. Token stakes; hits pay nothing, they just feel
  like hits. Constructing the mechanics outside the reel raises
  `ContainmentBreach`.
- **Charity sweepstakes** — salience redirects outward. The money the user
  would have gambled funds the charity pool immediately and irrevocably; a
  winning draw directs a *matched donation in their name*. No field of a
  sweepstake result is payable to the player: no personal cash-rescue fantasy.
- **Taper-to-boredom decay** — frequency, brightness, drama, and emotional
  punch decline together on a monotonic staleness ratchet (no reset method,
  decay accelerates with use) until the ritual is psychologically stale and
  the engine retires permanently (`EngineRetired`).

**The hard firewall** (`firewall.py`) sits between the engines. Every fact
that wants to cross is a provenance-tagged `Crossing`; the firewall applies
the four doctrine rules verbatim and keeps an audit log of blocks:

1. *Chance cannot grant identity.*
2. *Reel outcomes cannot unlock graduation.*
3. *Sweepstakes cannot affect recovery rank.*
4. *No jackpot baptism.*

The pass it issues (`ClearedCrossing`) carries a private checkpoint stamp
only the firewall holds, and the progression track rejects anything without
it — there is no way to route around the checkpoint.

**Engine 2, the progression track** (`progression_track.py`), is the
replacement layer: earned milestones, verified progress, recovery capital,
and ceremonial identity repair.

- **Verified behavior** — progress comes from taper steps (e.g. honoring a
  cooldown through an urge, attested by reel telemetry), blocking tools, or
  self-exclusion. Nothing else credits.
- **Certain milestones** — the entire schedule (known targets, known relic
  rewards, known rank) is published before the first behavior is credited.
  No mystery box. The track imports no randomness, clocks, or I/O (enforced
  by an AST test), and replaying the same behaviors rebuilds the same track.
- **Ceremonial identity** — graduation requires the complete schedule, is
  opt-in, must be witnessed, happens once, and is permanent.

**Identity artifacts live only on the deterministic track**
(`artifacts.py`): Discharge Papers · Hall of Quitters / Pantheon · Unlost
Ledger (money kept by tapering) · Recovery Relics · Quit Story ·
Housebreakers' Council. Every artifact carries the track's provenance seal,
which the reel side never holds.

**The charity payout pool** (`terminals.py`) is the coral side's only money
terminal: funding records are irrevocable, reconciliation against the ledger
always balances, and disbursement only drains outward.

## Governance rules and where each is enforced

| Diagram rule | Enforcement |
|---|---|
| Chance cannot grant identity | `HardFirewall` blocks CHANCE-provenance `IDENTITY_GRANT`; artifacts also need the track's private seal (`ProvenanceError`). |
| Reel outcomes cannot unlock graduation | Firewall blocks CHANCE `GRADUATION_UNLOCK`; graduation eligibility is a pure function of verified behaviors. A 30-spin winning streak leaves rank 0, zero milestones, zero artifacts (tested). |
| Sweepstakes cannot affect recovery rank | Firewall blocks any sweepstake-sourced rank or progress crossing. |
| No jackpot baptism | Firewall blocks any jackpot-tagged crossing into identity. |
| Chance stays quarantined here | Blanket rule: CHANCE provenance never crosses at all; mimicry is constructible only inside the reel. |
| Identity is earned only here | `ProgressionTrack.credit` accepts only firewall-stamped crossings with VERIFIED provenance. |
| Earned, witnessed, opt-in, permanent | `IdentityCollection.shelve` rejects unsealed, unwitnessed, or non-opt-in artifacts; frozen dataclasses + append-only shelf; ceremony held once. |
| No mystery box | Milestone targets, relics, and ranks are fixed at construction and readable before play. |
| No cash-rescue fantasy | Sweepstake results have no player-payable field; the pool has no withdraw path; disbursement is exit-only. |

## Running it

No dependencies beyond the Python 3.10+ standard library.

```bash
python -m recovering_player            # one full journey, default seed
python -m recovering_player 99         # different seed, same governance
python -m unittest discover -s tests   # 26-test doctrine suite
```

The demo shows the urge arriving, the reel decaying toward staleness, the
firewall blocking all four doctrine violations by name, the published
milestone schedule completing through verified behavior, and the ceremony
minting the full artifact catalog — while every committed cent exits to
charity.
