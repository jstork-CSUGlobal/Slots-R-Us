"""Demo: one full recovery journey, from first pull to graduation.

Run with:  python -m recovering_player [seed]
"""

from __future__ import annotations

import random
import sys

from recovering_player import RecoveringPlayer


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    player = RecoveringPlayer(rng=random.Random(seed))

    spins = player.play_until_graduation(stake=5)

    print("journey complete")
    print(f"  spins until graduation : {spins}")
    print(f"  final predictability   : {player.taper.predictability:.2f}")
    print(f"  taper engine retired   : {player.taper.retired}")
    print(f"  milestones earned      : "
          f"{[m.name for m in player.progression.milestones]}")
    print(f"  identity shelf         : "
          f"{[a.title for a in player.identity.artifacts]}")

    sent = player.charity_pool.disburse("local harm-reduction fund")
    print(f"  charity disbursement   : {sent} units "
          f"(lifetime accrued {player.charity_pool.lifetime_accrued})")
    print(f"  bus log length         : {len(player.bus.log)} events, "
          f"all coral-origin")


if __name__ == "__main__":
    main()
