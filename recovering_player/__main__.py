"""Demo: one journey through the two-engine firewall.

Run with:  python -m recovering_player [seed]
"""

from __future__ import annotations

import random
import sys

from recovering_player import (
    Crossing,
    CrossingKind,
    FirewallRejection,
    Provenance,
    RecoveringPlayer,
)


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    player = RecoveringPlayer(
        rng=random.Random(seed), decay_base_step=0.04, decay_acceleration=0.01
    )

    print("== the urge arrives ==")
    routing = player.feel_urge()
    print(f"  substitution available : {routing.substitution_available}")
    print(f"  sensory level          : {routing.sensory_dimmed_to:.2f}")

    print("\n== engine 1: substitution, containment, decay ==")
    jackpot_seen = None
    for _ in range(8):
        outcome = player.spin()
        if outcome.jackpot:
            jackpot_seen = outcome
    result = player.enter_sweepstake(committed=20)
    print(f"  8 spins taken, staleness now {player.reel.staleness:.2f}")
    print(f"  sweepstake: won={result.won}, "
          f"{result.donated_in_your_name} donated to {result.beneficiary}")

    print("\n== the firewall holds ==")
    attempts = [
        Crossing(Provenance.CHANCE, CrossingKind.IDENTITY_GRANT,
                 "reel-outcome", {"hit": True}),
        Crossing(Provenance.CHANCE, CrossingKind.GRADUATION_UNLOCK,
                 "reel-outcome", {"streak": 7}),
        Crossing(Provenance.CHANCE, CrossingKind.RECOVERY_RANK,
                 "sweepstake", {"won": True}),
        Crossing(Provenance.CHANCE, CrossingKind.IDENTITY_GRANT,
                 "reel-outcome", {"jackpot": True}),
    ]
    for attempt in attempts:
        try:
            player.firewall.transmit(attempt)
        except FirewallRejection as rejection:
            print(f"  BLOCKED ({attempt.source}): {rejection.rule}")

    print("\n== engine 2: replacement, status, durable identity ==")
    print(f"  published schedule: "
          f"{[m.name for m in player.track.schedule]} (no mystery box)")
    player.activate_blocking_tool("site blocker")
    for _ in range(5):
        player.honor_cooldown()
    player.self_exclude("state self-exclusion registry")
    print(f"  recovery rank          : {player.track.recovery_rank}")
    print(f"  milestones awarded     : "
          f"{[m.name for m in player.track.milestones_awarded]}")
    print(f"  unlost ledger          : {player.track.unlost_total} kept")

    print("\n== ceremony ==")
    artifacts = player.graduation_ceremony(
        witnesses=("sponsor", "housebreakers' council"),
        quit_story="I stopped feeding the machine and started keeping score.",
    )
    for artifact in artifacts:
        print(f"  minted: {artifact.title} ({artifact.earned_for})")

    print("\n== money went one way ==")
    sent = player.charity_pool.disburse("harm-reduction fund")
    print(f"  charity disbursement   : {sent} "
          f"(lifetime {player.charity_pool.lifetime_accrued})")
    print(f"  firewall audit         : {len(player.firewall.blocked)} blocked, "
          f"{len(player.firewall.cleared)} cleared")
    if jackpot_seen:
        print("  (a jackpot landed during play; it baptized nothing)")


if __name__ == "__main__":
    main()
