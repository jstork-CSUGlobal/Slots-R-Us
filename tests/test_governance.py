"""Tests for the two-engine firewall doctrine.

Chance is quarantined in substitution. Identity is earned in
deterministic replacement. Variable reward can taper behavior; only
deterministic reward can rebuild identity.
"""

import random
import unittest

from recovering_player import (
    ArtifactKind,
    BehaviorKind,
    ContainmentBreach,
    Crossing,
    CrossingKind,
    EngineRetired,
    FirewallRejection,
    HardFirewall,
    IdentityArtifact,
    NotEligible,
    ProgressionTrack,
    Provenance,
    ProvenanceError,
    RecoveringPlayer,
    TaperToBoredomDecay,
    VariableRatioMimicry,
)
from recovering_player.artifacts import _ProvenanceSeal
from recovering_player.firewall import ClearedCrossing, _CheckpointStamp


def fast_player(seed: int = 7) -> RecoveringPlayer:
    """A player whose reel goes stale quickly, for test speed."""
    return RecoveringPlayer(
        rng=random.Random(seed), decay_base_step=0.05, decay_acceleration=0.01
    )


def graduate(player: RecoveringPlayer) -> None:
    """Complete the published schedule via verified behavior only."""
    player.activate_blocking_tool("site blocker")
    for _ in range(5):
        player.honor_cooldown()
    player.self_exclude("registry")


class TestHardFirewall(unittest.TestCase):
    """The four doctrine rules, verbatim from the diagram."""

    def setUp(self):
        self.firewall = HardFirewall()

    def assert_blocked(self, crossing: Crossing, rule: str):
        with self.assertRaises(FirewallRejection) as ctx:
            self.firewall.transmit(crossing)
        self.assertEqual(ctx.exception.rule, rule)

    def test_chance_cannot_grant_identity(self):
        self.assert_blocked(
            Crossing(Provenance.CHANCE, CrossingKind.IDENTITY_GRANT,
                     "reel-outcome", {"hit": True}),
            "Chance cannot grant identity.",
        )

    def test_reel_outcomes_cannot_unlock_graduation(self):
        self.assert_blocked(
            Crossing(Provenance.CHANCE, CrossingKind.GRADUATION_UNLOCK,
                     "reel-outcome", {"streak": 50}),
            "Reel outcomes cannot unlock graduation.",
        )

    def test_sweepstakes_cannot_affect_recovery_rank(self):
        self.assert_blocked(
            Crossing(Provenance.VERIFIED, CrossingKind.RECOVERY_RANK,
                     "sweepstake-win", {"won": True}),
            "Sweepstakes cannot affect recovery rank.",
        )

    def test_no_jackpot_baptism(self):
        self.assert_blocked(
            Crossing(Provenance.CHANCE, CrossingKind.IDENTITY_GRANT,
                     "reel-outcome", {"jackpot": True}),
            "No jackpot baptism.",
        )

    def test_chance_is_quarantined_entirely(self):
        self.assert_blocked(
            Crossing(Provenance.CHANCE, CrossingKind.PROGRESS_CREDIT,
                     "reel-outcome", {"hit": True}),
            "Chance stays quarantined in the substitution layer.",
        )

    def test_verified_behavior_passes(self):
        cleared = self.firewall.transmit(
            Crossing(Provenance.VERIFIED, CrossingKind.PROGRESS_CREDIT,
                     "reel-telemetry",
                     {"behavior": "taper-step", "description": "cooldown"})
        )
        self.assertTrue(cleared.stamped_by(self.firewall.stamp))

    def test_blocks_are_audited(self):
        try:
            self.firewall.transmit(
                Crossing(Provenance.CHANCE, CrossingKind.IDENTITY_GRANT,
                         "reel-outcome")
            )
        except FirewallRejection:
            pass
        self.assertEqual(len(self.firewall.blocked), 1)


class TestTrackAcceptsOnlyTheFirewall(unittest.TestCase):
    def test_forged_stamp_is_rejected(self):
        firewall = HardFirewall()
        track = ProgressionTrack(firewall)
        forged = ClearedCrossing(
            crossing=Crossing(Provenance.VERIFIED,
                              CrossingKind.PROGRESS_CREDIT, "imposter",
                              {"behavior": "taper-step"}),
            _stamp=_CheckpointStamp(),
        )
        with self.assertRaises(PermissionError):
            track.credit(forged)

    def test_winning_streak_builds_nothing(self):
        """A pile of reel wins leaves rank, milestones, and identity empty."""
        player = fast_player()
        for _ in range(30):
            if player.reel.retired:
                break
            player.spin()
        self.assertEqual(player.track.recovery_rank, 0)
        self.assertEqual(player.track.milestones_awarded, ())
        self.assertEqual(player.identity.artifacts, ())


class TestDecayingReel(unittest.TestCase):
    def test_staleness_only_ratchets_up(self):
        decay = TaperToBoredomDecay(base_step=0.03)
        values = [decay.tick() for _ in range(50)]
        self.assertEqual(values, sorted(values))
        self.assertEqual(values[-1], 1.0)
        self.assertFalse(hasattr(decay, "reset"))

    def test_all_sensory_channels_decay_together(self):
        decay = TaperToBoredomDecay(base_step=0.2)
        before = decay.sensory_profile()
        for _ in range(5):
            decay.tick()
        after = decay.sensory_profile()
        self.assertLess(after.brightness, before.brightness)
        self.assertLess(after.drama, before.drama)
        self.assertLess(after.emotional_punch, before.emotional_punch)
        self.assertGreater(after.cooldown_spins, before.cooldown_spins)
        self.assertTrue(after.stale)

    def test_stale_reel_is_pure_pattern(self):
        mimicry = VariableRatioMimicry.__new__(VariableRatioMimicry)
        # Build legitimately via a reel-free path is forbidden; go through
        # the containment check with the real interior token instead.
        from recovering_player.decaying_reel import _ReelInterior

        mimicry = VariableRatioMimicry(_ReelInterior(), rng=random.Random(0))
        outcomes = [mimicry.spin(staleness=1.0) for _ in range(6)]
        self.assertTrue(all(o.forced for o in outcomes))
        self.assertEqual([o.hit for o in outcomes],
                         [True, False, True, False, True, False])

    def test_mimicry_contained_inside_reel_only(self):
        with self.assertRaises(ContainmentBreach):
            VariableRatioMimicry("not the interior")  # type: ignore[arg-type]

    def test_reel_death_is_permanent(self):
        player = fast_player()
        player.burn_out_the_reel()
        self.assertTrue(player.reel.retired)
        with self.assertRaises(EngineRetired):
            player.spin()
        with self.assertRaises(EngineRetired):
            player.enter_sweepstake(5)

    def test_sweepstake_money_only_flows_outward(self):
        player = fast_player()
        result = player.enter_sweepstake(committed=20)
        # No field of the result is payable to the player; the prize is a
        # donation in their name. No cash-rescue fantasy.
        self.assertNotIn("payout_to_player", result.__dataclass_fields__)
        self.assertGreaterEqual(result.donated_in_your_name, 20)
        # Every cent committed is in the pool, reconciled by source.
        self.assertEqual(
            player.charity_pool.lifetime_accrued,
            sum(r.amount for r in player.charity_pool.records),
        )
        self.assertGreaterEqual(player.charity_pool.lifetime_accrued, 20)
        self.assertFalse(hasattr(player.charity_pool, "withdraw"))


class TestProgressionTrack(unittest.TestCase):
    def test_schedule_is_published_before_any_behavior(self):
        player = fast_player()
        schedule = player.track.schedule
        self.assertTrue(schedule)
        for milestone in schedule:
            self.assertTrue(milestone.target)        # known target
            self.assertTrue(milestone.reward_relic)  # known reward
            self.assertGreater(milestone.reward_rank, 0)

    def test_no_randomness_imported_on_the_track(self):
        import ast

        import recovering_player.progression_track as mod

        with open(mod.__file__) as f:
            tree = ast.parse(f.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        for chancy in ("random", "secrets", "os", "time", "uuid"):
            self.assertFalse(
                any(n == chancy or n.startswith(chancy + ".")
                    for n in imported),
                f"progression track must not import {chancy!r}",
            )

    def test_progress_comes_only_from_the_three_behaviors(self):
        self.assertEqual(
            {k.value for k in BehaviorKind},
            {"taper-step", "blocking-tool", "self-exclusion"},
        )

    def test_replay_rebuilds_identical_track(self):
        player = fast_player(seed=11)
        graduate(player)

        firewall = HardFirewall()
        replayed = ProgressionTrack(firewall)
        for cleared in player.firewall.cleared:
            replayed.credit(firewall.transmit(cleared.crossing))

        self.assertEqual(replayed.recovery_rank, player.track.recovery_rank)
        self.assertEqual(replayed.milestones_awarded,
                         player.track.milestones_awarded)
        self.assertEqual(replayed.graduation_eligible,
                         player.track.graduation_eligible)


class TestCeremonialIdentity(unittest.TestCase):
    def test_ceremony_requires_complete_schedule(self):
        player = fast_player()
        player.honor_cooldown()
        with self.assertRaises(NotEligible):
            player.graduation_ceremony(witnesses=("sponsor",),
                                       quit_story="too soon")

    def test_full_catalog_minted_once(self):
        player = fast_player()
        graduate(player)
        artifacts = player.graduation_ceremony(
            witnesses=("sponsor",), quit_story="kept score, kept the money"
        )
        self.assertEqual({a.kind for a in artifacts}, set(ArtifactKind))
        again = player.graduation_ceremony(witnesses=("sponsor",),
                                           quit_story="again?")
        self.assertEqual(again, ())
        self.assertEqual(len(player.identity.artifacts), len(ArtifactKind))

    def test_identity_is_opt_in(self):
        player = fast_player()
        graduate(player)
        artifacts = player.graduation_ceremony(
            witnesses=("sponsor",), quit_story="no thanks", opt_in=False
        )
        self.assertEqual(artifacts, ())
        self.assertEqual(player.identity.artifacts, ())

    def test_unsealed_artifact_rejected(self):
        player = fast_player()
        counterfeit = IdentityArtifact(
            kind=ArtifactKind.DISCHARGE_PAPERS,
            title="fake papers",
            earned_for="nothing",
            witnessed_by=("nobody",),
            opted_in=True,
            _seal=_ProvenanceSeal(),
        )
        with self.assertRaises(ProvenanceError):
            player.identity.shelve(counterfeit)

    def test_unwitnessed_artifact_rejected(self):
        player = fast_player()
        graduate(player)
        with self.assertRaises(ProvenanceError):
            player.graduation_ceremony(witnesses=(), quit_story="alone")

    def test_unlost_ledger_records_money_kept(self):
        player = fast_player()
        graduate(player)
        artifacts = player.graduation_ceremony(witnesses=("sponsor",),
                                               quit_story="kept it")
        ledger = next(a for a in artifacts
                      if a.kind is ArtifactKind.UNLOST_LEDGER)
        self.assertEqual(ledger.detail["unlost_total"],
                         player.track.unlost_total)
        self.assertGreater(ledger.detail["unlost_total"], 0)


class TestFullJourney(unittest.TestCase):
    def test_both_engines_end_in_their_designed_states(self):
        player = fast_player(seed=42)
        player.enter_sweepstake(committed=25)
        player.burn_out_the_reel()
        graduate(player)
        player.graduation_ceremony(witnesses=("sponsor", "council"),
                                   quit_story="done")

        self.assertTrue(player.reel.retired)            # engine 1 died
        self.assertTrue(player.track.graduation_eligible)
        self.assertTrue(player.identity.holds(ArtifactKind.DISCHARGE_PAPERS))
        self.assertEqual(player.charity_pool.disburse("fund"),
                         player.charity_pool.lifetime_accrued)


if __name__ == "__main__":
    unittest.main()
