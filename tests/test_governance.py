"""Tests for the firewall and governance invariants of the diagram."""

import random
import unittest

from recovering_player import (
    BreachViolation,
    CharityPayoutPool,
    DecayScheduler,
    EngineRetired,
    IdentityArtifact,
    IdentityCollection,
    MinimumEventBus,
    ProgressionEngine,
    ProvenanceError,
    RecoveringPlayer,
    Reel,
    SpinResolved,
    StakeForfeited,
    TaperEngine,
)
from recovering_player.progression_engine import _ProvenanceSeal


def fast_player(seed: int = 7) -> RecoveringPlayer:
    """A player whose taper saturates quickly, for test speed."""
    return RecoveringPlayer(
        rng=random.Random(seed), decay_base_step=0.05, decay_acceleration=0.01
    )


class TestFirewallBreach(unittest.TestCase):
    def test_bus_issues_exactly_one_outlet(self):
        bus = MinimumEventBus()
        bus.issue_outlet()
        with self.assertRaises(BreachViolation):
            bus.issue_outlet()

    def test_only_taper_events_cross(self):
        bus = MinimumEventBus()
        outlet = bus.issue_outlet()
        with self.assertRaises(BreachViolation):
            outlet.publish("not an event")  # type: ignore[arg-type]

    def test_progression_has_no_publish_path(self):
        """The teal side holds no outlet and no reference to the taper."""
        bus = MinimumEventBus()
        bus.issue_outlet()
        engine = ProgressionEngine(bus)
        held = {type(v).__name__ for v in vars(engine).values()}
        self.assertNotIn("TaperOutlet", held)
        self.assertNotIn("TaperEngine", held)

    def test_events_flow_only_coral_to_teal(self):
        player = fast_player()
        player.play_until_graduation(stake=2)
        # Every event in the log is a TaperEvent emitted by the coral side.
        from recovering_player import TaperEvent

        self.assertTrue(player.bus.log)
        self.assertTrue(all(isinstance(e, TaperEvent) for e in player.bus.log))


class TestTaperEngineDies(unittest.TestCase):
    def test_predictability_only_ratchets_up(self):
        sched = DecayScheduler(base_step=0.03)
        values = [sched.tick() for _ in range(50)]
        self.assertEqual(values, sorted(values))
        self.assertEqual(values[-1], 1.0)
        self.assertFalse(hasattr(sched, "reset"))

    def test_saturated_reel_is_pure_pattern(self):
        reel = Reel(rng=random.Random(0))
        outcomes = [reel.spin(predictability=1.0) for _ in range(6)]
        self.assertTrue(all(r.forced for r in outcomes))
        self.assertEqual([r.hit for r in outcomes],
                         [True, False, True, False, True, False])

    def test_graduation_is_permanent(self):
        player = fast_player()
        player.play_until_graduation(stake=1)
        self.assertTrue(player.taper.retired)
        with self.assertRaises(EngineRetired):
            player.taper.spin(1)

    def test_graduation_declared_exactly_once(self):
        player = fast_player()
        player.play_until_graduation(stake=1)
        from recovering_player import GraduationDeclared

        declarations = [e for e in player.bus.log
                        if isinstance(e, GraduationDeclared)]
        self.assertEqual(len(declarations), 1)


class TestProgressionIsDeterministic(unittest.TestCase):
    def test_no_randomness_in_module(self):
        """The teal side imports no source of chance whatsoever."""
        import ast

        import recovering_player.progression_engine as mod

        with open(mod.__file__) as f:
            tree = ast.parse(f.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        for chancy in ("random", "secrets", "os", "time", "uuid"):
            self.assertTrue(
                not any(name == chancy or name.startswith(chancy + ".")
                        for name in imported),
                f"progression engine must not import {chancy!r}",
            )

    def test_replay_rebuilds_identical_progression(self):
        player = fast_player(seed=11)
        player.play_until_graduation(stake=3)

        replay_bus = MinimumEventBus()
        outlet = replay_bus.issue_outlet()
        replayed = ProgressionEngine(replay_bus)
        for event in player.bus.log:
            outlet.publish(event)

        self.assertEqual(replayed.milestones, player.progression.milestones)
        self.assertEqual(replayed.graduated, player.progression.graduated)


class TestTerminals(unittest.TestCase):
    def test_charity_pool_matches_event_log(self):
        player = fast_player(seed=3)
        player.play_until_graduation(stake=4)
        forfeited = sum(e.amount for e in player.bus.log
                        if isinstance(e, StakeForfeited))
        self.assertEqual(player.charity_pool.lifetime_accrued, forfeited)

    def test_charity_payout_is_exit_only(self):
        player = fast_player(seed=3)
        player.play_until_graduation(stake=4)
        before = player.charity_pool.lifetime_accrued
        sent = player.charity_pool.disburse("test charity")
        self.assertEqual(sent, before)
        self.assertEqual(player.charity_pool.balance, 0)
        self.assertFalse(hasattr(player.charity_pool, "deposit"))

    def test_reel_cannot_dispense_identity(self):
        """An artifact forged outside the progression engine is rejected."""
        player = fast_player()
        counterfeit = IdentityArtifact(
            title="fake", milestone_count=99, _seal=_ProvenanceSeal()
        )
        with self.assertRaises(ProvenanceError):
            player.identity.shelve(counterfeit)

    def test_graduation_mints_shelvable_identity(self):
        player = fast_player()
        player.play_until_graduation(stake=1)
        self.assertEqual([a.title for a in player.identity.artifacts],
                         ["graduate"])


class TestJourney(unittest.TestCase):
    def test_full_journey_terminates_with_milestones(self):
        player = fast_player(seed=42)
        spins = player.play_until_graduation(stake=2)
        self.assertGreater(spins, 0)
        self.assertTrue(player.graduated)
        names = [m.name for m in player.progression.milestones]
        self.assertIn("first-steps", names)


if __name__ == "__main__":
    unittest.main()
