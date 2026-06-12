"""Demo: an episodic journey through the two-engine firewall.

Run with:  python -m recovering_player [seed]
"""

from __future__ import annotations

import random
import sys

from recovering_player import (
    Crossing,
    CrossingKind,
    EpisodeClosure,
    EpisodeTrigger,
    FirewallRejection,
    ManualClock,
    Provenance,
    RecoveringPlayer,
)


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    clock = ManualClock()
    player = RecoveringPlayer(
        clock=clock, rng=random.Random(seed),
        full_term_days=10.0, binge_spin_threshold=15,
    )

    print("== enrollment ==")
    print(f"  house charity budget   : {player.charity_pool.budget_remaining} "
          f"(enrollment contribution already made)")

    print("\n== episode 1: reported urge, then a binge ==")
    ep1 = player.begin_episode(EpisodeTrigger.REPORTED_URGE)
    player.feel_urge()
    binged = False
    for _ in range(20):
        outcome = player.spin()
        binged = binged or outcome.binge_tripped
    print(f"  20 rapid spins, binge tripped: {binged} "
          f"(decay paused + penalized; staleness {player.reel.staleness:.2f})")
    player.close_episode(EpisodeClosure.EXPLICIT_CLOSURE)
    print(f"  episode 1 closed; its {ep1.spin_count} spins of chance "
          f"telemetry are sealed inside it")

    print("\n== five quiet days pass: calendar does the tapering ==")
    clock.advance(days=5)
    print(f"  staleness now {player.reel.staleness:.2f} with zero spins taken")
    print("  (the binge cost 2 penalty days and a 1-day pause; "
          "spinning only ever slows the taper)")

    print("\n== the firewall holds, within and across episodes ==")
    attempts = [
        Crossing(Provenance.CHANCE, CrossingKind.IDENTITY_GRANT,
                 "reel-outcome", {"hit": True}, episode_id=ep1.episode_id),
        Crossing(Provenance.CHANCE, CrossingKind.PROGRESS_CREDIT,
                 "reel-outcome", {"winnings": 100}),
        Crossing(Provenance.CHANCE, CrossingKind.GRADUATION_UNLOCK,
                 "reel-outcome", {"streak": 7}),
        Crossing(Provenance.CHANCE, CrossingKind.IDENTITY_GRANT,
                 "reel-outcome", {"jackpot": True}),
    ]
    for attempt in attempts:
        try:
            player.firewall.transmit(attempt)
        except FirewallRejection as rejection:
            print(f"  BLOCKED: {rejection.rule}")

    print("\n== episode 2: planned taper session, verified behavior ==")
    player.begin_episode(EpisodeTrigger.PLANNED_TAPER_SESSION,
                         timeout_days=10.0)
    player.activate_blocking_tool("site blocker")
    for _ in range(5):
        player.honor_cooldown()
        clock.advance(days=1)
    player.self_exclude("state self-exclusion registry")
    player.close_episode(EpisodeClosure.VERIFIED_TRANSITION)
    print(f"  recovery rank          : {player.track.recovery_rank}")
    print(f"  milestones awarded     : "
          f"{[m.name for m in player.track.milestones_awarded]}")
    print(f"  reel retired by time   : {player.reel.retired} "
          f"(staleness {player.reel.staleness:.2f})")

    print("\n== ceremony (permanent, beyond all episodes) ==")
    artifacts = player.graduation_ceremony(
        witnesses=("sponsor", "housebreakers' council"),
        quit_story="I stopped feeding the machine and let the calendar win.",
    )
    for artifact in artifacts:
        print(f"  minted: {artifact.title}")

    print("\n== house money went one way ==")
    print(f"  contributions: "
          f"{[(r.event.value, r.amount) for r in player.charity_pool.records]}")
    sent = player.charity_pool.disburse("harm-reduction fund")
    print(f"  disbursed {sent} to charity; user-owned winnings: none, ever")
    print(f"  firewall audit: {len(player.firewall.blocked)} blocked, "
          f"{len(player.firewall.cleared)} cleared")


if __name__ == "__main__":
    main()
