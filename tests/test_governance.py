"""Governance tests for the episodic two-engine firewall.

Invariants under test, in priority order:
  1. No user-facing real-money value may originate from chance.
  2. More spinning cannot make the reel safer faster.
  3. Recovery identity persists; chance-state does not become
     identity-state. Permanence is verified within an active episode
     and across episode boundaries, not asserted as a global forever.
"""

import random
import unittest

from recovering_player import (
    ArtifactKind,
    BehaviorKind,
    CalendarDecay,
    ContainmentBreach,
    ContributionEvent,
    Crossing,
    CrossingKind,
    EngineRetired,
    EpisodeClosure,
    EpisodeTrigger,
    FirewallRejection,
    HardFirewall,
    IdentityArtifact,
    ManualClock,
    NoActiveEpisode,
    NotEligible,
    ProgressionTrack,
    Provenance,
    ProvenanceError,
    RecoveringPlayer,
    SpinOutcome,
    VariableRatioMimicry,
)
from recovering_player.artifacts import _ProvenanceSeal
from recovering_player.firewall import ClearedCrossing, _CheckpointStamp


def fast_player(seed: int = 7, full_term_days: float = 10.0,
                binge_spin_threshold: int = 15) -> tuple[RecoveringPlayer, ManualClock]:
    clock = ManualClock()
    player = RecoveringPlayer(
        clock=clock, rng=random.Random(seed),
        full_term_days=full_term_days,
        binge_spin_threshold=binge_spin_threshold,
    )
    return player, clock


def graduate(player: RecoveringPlayer, clock: ManualClock) -> None:
    """Complete the published schedule via verified behavior only."""
    player.begin_episode(EpisodeTrigger.PLANNED_TAPER_SESSION,
                         timeout_days=30.0)
    player.activate_blocking_tool("site blocker")
    for _ in range(5):
        player.honor_cooldown()
    player.self_exclude("registry")
    player.close_episode(EpisodeClosure.VERIFIED_TRANSITION)


# ─────────────────────────────────────────────────────────────────────
# Correction 1: real money is decoupled from chance entirely.
# ─────────────────────────────────────────────────────────────────────
class TestMoneyChanceDecoupling(unittest.TestCase):
    def test_spin_outcome_has_no_monetary_fields(self):
        from recovering_player.firewall import MONETARY_KEYS

        fields = set(SpinOutcome.__dataclass_fields__)
        self.assertFalse(fields & MONETARY_KEYS)
        self.assertEqual(
            fields,
            {"hit", "forced", "near_miss", "jackpot_theater",
             "staleness_observed", "binge_tripped"},
        )

    def test_reel_module_has_no_path_to_money(self):
        """Engine 1 neither imports nor references the charity pool."""
        import recovering_player.decaying_reel as mod

        with open(mod.__file__) as f:
            source = f.read()
        self.assertNotIn("CharityContributionPool", source)
        self.assertNotIn("terminals", source)

    def test_firewall_blocks_chance_money_outright(self):
        firewall = HardFirewall()
        for key in ("winnings", "payout", "amount", "prize", "donation"):
            with self.assertRaises(FirewallRejection) as ctx:
                firewall.transmit(
                    Crossing(Provenance.CHANCE, CrossingKind.PROGRESS_CREDIT,
                             "reel-outcome", {key: 100})
                )
            self.assertEqual(ctx.exception.rule,
                             "No user-facing money may originate from chance.")

    def test_contributions_are_house_funded_and_budgeted(self):
        player, _ = fast_player()
        pool = player.charity_pool
        # No API accepts user money.
        self.assertFalse(hasattr(pool, "fund"))
        self.assertFalse(hasattr(pool, "deposit"))
        # Amounts come from the published schedule, drawn from the budget.
        before = pool.budget_remaining
        amount = pool.trigger(ContributionEvent.RECOVERY_CHECK_IN)
        self.assertEqual(amount, pool.schedule[ContributionEvent.RECOVERY_CHECK_IN])
        self.assertEqual(pool.budget_remaining, before - amount)

    def test_contribution_triggers_cannot_express_chance(self):
        """The trigger vocabulary is app-side only: no spin, win, hit,
        jackpot, or sweepstake event exists in it."""
        names = {e.value for e in ContributionEvent}
        for forbidden in ("spin", "win", "hit", "jackpot", "sweepstake",
                          "near-miss", "symbol"):
            for name in names:
                self.assertNotIn(forbidden, name)

    def test_outcomes_do_not_move_charity_money(self):
        player, _ = fast_player()
        baseline = player.charity_pool.lifetime_contributed
        player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        for _ in range(10):
            player.spin()
        self.assertEqual(player.charity_pool.lifetime_contributed, baseline)
        # Closing dirty (explicit, not clean) also moves nothing.
        player.close_episode(EpisodeClosure.EXPLICIT_CLOSURE)
        self.assertEqual(player.charity_pool.lifetime_contributed, baseline)

    def test_user_owns_nothing_in_the_pool(self):
        player, _ = fast_player()
        pool = player.charity_pool
        self.assertFalse(hasattr(pool, "withdraw"))
        self.assertFalse(hasattr(pool, "payout_to_player"))
        sent = pool.disburse("charity")
        self.assertEqual(sent, pool.lifetime_contributed)
        self.assertEqual(pool.balance, 0)


# ─────────────────────────────────────────────────────────────────────
# Correction 2: decay is calendar-anchored; binges slow it.
# ─────────────────────────────────────────────────────────────────────
class TestCalendarDecay(unittest.TestCase):
    def test_time_alone_advances_decay(self):
        clock = ManualClock()
        decay = CalendarDecay(clock, full_term_days=10.0)
        self.assertEqual(decay.staleness, 0.0)
        clock.advance(days=5)
        self.assertAlmostEqual(decay.staleness, 0.5)
        clock.advance(days=5)
        self.assertEqual(decay.staleness, 1.0)

    def test_spins_alone_never_advance_decay(self):
        clock = ManualClock()
        decay = CalendarDecay(clock, full_term_days=10.0,
                              binge_spin_threshold=1_000)
        for _ in range(500):
            decay.observe_spin()
        self.assertEqual(decay.staleness, 0.0)

    def test_binge_slows_decay_pause_and_penalty(self):
        clock = ManualClock()
        decay = CalendarDecay(clock, full_term_days=10.0,
                              binge_spin_threshold=10,
                              binge_penalty_days=2.0, binge_pause_days=1.0)
        clock.advance(days=4)  # 0.4 accrued
        tripped = [decay.observe_spin() for _ in range(10)]
        self.assertTrue(any(tripped))
        self.assertTrue(decay.paused())
        # Penalty partially reset accrued progress.
        self.assertAlmostEqual(decay.effective_days(), 2.0)  # 4 - 2 penalty
        # During the pause, time passing does not accrue.
        clock.advance(days=1)
        self.assertAlmostEqual(decay.effective_days(), 2.0)
        # After the pause, accrual resumes.
        clock.advance(days=1)
        self.assertAlmostEqual(decay.effective_days(), 3.0)

    def test_more_spinning_cannot_make_the_reel_safer_faster(self):
        """Two identical timelines; one binges. At equal wall time, the
        binger's staleness is never higher than the abstainer's."""

        def staleness_after(spins_per_day: int) -> float:
            clock = ManualClock()
            decay = CalendarDecay(clock, full_term_days=10.0,
                                  binge_spin_threshold=15)
            for _ in range(8):
                for _ in range(spins_per_day):
                    decay.observe_spin()
                clock.advance(days=1)
            return decay.staleness

        calm = staleness_after(spins_per_day=0)
        light = staleness_after(spins_per_day=5)
        binge = staleness_after(spins_per_day=40)
        self.assertGreaterEqual(calm, light)
        self.assertGreaterEqual(light, binge)
        self.assertLess(binge, calm)  # binging strictly hurt

    def test_verified_recovery_is_the_only_accelerator(self):
        clock = ManualClock()
        decay = CalendarDecay(clock, full_term_days=10.0)
        clock.advance(days=2)
        before = decay.staleness
        decay.credit_recovery_interval(bonus_days=1.0)
        self.assertGreater(decay.staleness, before)
        with self.assertRaises(ValueError):
            decay.credit_recovery_interval(bonus_days=-1.0)

    def test_all_sensory_channels_decline_with_time(self):
        clock = ManualClock()
        decay = CalendarDecay(clock, full_term_days=10.0)
        before = decay.sensory_profile()
        clock.advance(days=9)
        after = decay.sensory_profile()
        for channel in ("brightness", "novelty", "sound", "payout_theater",
                        "emotional_punch"):
            self.assertLess(getattr(after, channel), getattr(before, channel))
        self.assertLess(after.frequency_allowance, before.frequency_allowance)

    def test_staleness_latches_permanently(self):
        clock = ManualClock()
        decay = CalendarDecay(clock, full_term_days=10.0)
        clock.advance(days=10)
        self.assertEqual(decay.staleness, 1.0)
        # Even a later binge penalty cannot un-stale the reel.
        for _ in range(50):
            decay.observe_spin()
        self.assertEqual(decay.staleness, 1.0)

    def test_retired_reel_stays_retired(self):
        player, clock = fast_player(full_term_days=5.0)
        clock.advance(days=5)
        self.assertTrue(player.reel.retired)
        player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        with self.assertRaises(EngineRetired):
            player.spin()


# ─────────────────────────────────────────────────────────────────────
# Correction 3: the episode model and rescoped permanence.
# ─────────────────────────────────────────────────────────────────────
class TestEpisodeModel(unittest.TestCase):
    def test_reel_activity_requires_an_episode(self):
        player, _ = fast_player()
        with self.assertRaises(NoActiveEpisode):
            player.spin()
        with self.assertRaises(NoActiveEpisode):
            player.feel_urge()
        with self.assertRaises(NoActiveEpisode):
            player.honor_cooldown()

    def test_episode_opens_and_closes_with_diagrammed_vocabulary(self):
        self.assertEqual(
            {t.value for t in EpisodeTrigger},
            {"reported-urge", "planned-taper-session",
             "relapse-risk-window", "recovery-check-in"},
        )
        self.assertEqual(
            {c.value for c in EpisodeClosure},
            {"timeout", "explicit-closure", "cooldown-complete",
             "verified-transition-to-non-use"},
        )

    def test_episode_timeout_closes_automatically(self):
        player, clock = fast_player()
        episode = player.begin_episode(EpisodeTrigger.RELAPSE_RISK_WINDOW,
                                       timeout_days=1.0)
        clock.advance(days=2)
        self.assertIsNone(player.active_episode)
        self.assertEqual(episode.closure, EpisodeClosure.TIMEOUT)

    def test_chance_telemetry_is_episode_scoped(self):
        player, _ = fast_player()
        ep1 = player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        for _ in range(5):
            player.spin()
        player.close_episode(EpisodeClosure.EXPLICIT_CLOSURE)
        ep2 = player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        self.assertEqual(ep1.spin_count, 5)
        self.assertEqual(ep2.spin_count, 0)
        self.assertEqual(ep2.chance_telemetry, [])

    def test_closed_episode_accepts_no_new_state(self):
        from recovering_player import EpisodeAlreadyClosed

        player, _ = fast_player()
        episode = player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        player.close_episode(EpisodeClosure.EXPLICIT_CLOSURE)
        with self.assertRaises(EpisodeAlreadyClosed):
            episode.record_spin({"hit": True})

    def test_forbidden_crossings_blocked_within_active_episode(self):
        player, _ = fast_player()
        episode = player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        for kind, payload, rule in [
            (CrossingKind.IDENTITY_GRANT, {"hit": True},
             "Chance cannot grant identity."),
            (CrossingKind.GRADUATION_UNLOCK, {"streak": 9},
             "Reel outcomes cannot unlock graduation."),
            (CrossingKind.IDENTITY_GRANT, {"jackpot": True},
             "No jackpot baptism."),
            (CrossingKind.PROGRESS_CREDIT, {"winnings": 10},
             "No user-facing money may originate from chance."),
        ]:
            with self.assertRaises(FirewallRejection) as ctx:
                player.firewall.transmit(
                    Crossing(Provenance.CHANCE, kind, "reel-outcome",
                             payload, episode_id=episode.episode_id)
                )
            self.assertEqual(ctx.exception.rule, rule)

    def test_forbidden_crossings_blocked_across_episode_boundary(self):
        """Chance facts from a closed episode stay blocked later."""
        player, _ = fast_player()
        ep1 = player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        player.spin()
        player.close_episode(EpisodeClosure.EXPLICIT_CLOSURE)
        player.begin_episode(EpisodeTrigger.RECOVERY_CHECK_IN)
        with self.assertRaises(FirewallRejection):
            player.firewall.transmit(
                Crossing(Provenance.CHANCE, CrossingKind.IDENTITY_GRANT,
                         "reel-outcome",
                         dict(ep1.chance_telemetry[0]),
                         episode_id=ep1.episode_id)
            )

    def test_sweepstake_sources_remain_blocked(self):
        player, _ = fast_player()
        with self.assertRaises(FirewallRejection) as ctx:
            player.firewall.transmit(
                Crossing(Provenance.VERIFIED, CrossingKind.RECOVERY_RANK,
                         "sweepstake-win", {"won": True})
            )
        self.assertEqual(ctx.exception.rule,
                         "Sweepstakes cannot affect recovery rank.")

    def test_verified_behavior_carries_its_episode(self):
        player, _ = fast_player()
        episode = player.begin_episode(EpisodeTrigger.PLANNED_TAPER_SESSION)
        player.honor_cooldown()
        behavior = player.track.behaviors[-1]
        self.assertEqual(behavior.episode_id, episode.episode_id)

    def test_winning_streak_in_an_episode_builds_nothing(self):
        player, _ = fast_player()
        player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        for _ in range(14):  # below binge threshold; pure chance exposure
            player.spin()
        self.assertEqual(player.track.recovery_rank, 0)
        self.assertEqual(player.track.milestones_awarded, ())
        self.assertEqual(player.identity.artifacts, ())


# ─────────────────────────────────────────────────────────────────────
# Identity remains deterministic, sealed, and persistent across episodes.
# ─────────────────────────────────────────────────────────────────────
class TestIdentityPersistence(unittest.TestCase):
    def test_artifacts_persist_across_later_episodes(self):
        player, clock = fast_player()
        graduate(player, clock)
        artifacts = player.graduation_ceremony(
            witnesses=("sponsor",), quit_story="the calendar won"
        )
        self.assertEqual({a.kind for a in artifacts}, set(ArtifactKind))
        # A later relapse-risk episode cannot touch the shelf.
        player.begin_episode(EpisodeTrigger.RELAPSE_RISK_WINDOW)
        if not player.reel.retired:
            player.spin()
        player.close_episode(EpisodeClosure.EXPLICIT_CLOSURE)
        self.assertEqual(len(player.identity.artifacts), len(ArtifactKind))

    def test_ceremony_requires_complete_schedule(self):
        player, _ = fast_player()
        player.begin_episode(EpisodeTrigger.PLANNED_TAPER_SESSION)
        player.honor_cooldown()
        with self.assertRaises(NotEligible):
            player.graduation_ceremony(witnesses=("sponsor",),
                                       quit_story="too soon")

    def test_ceremony_is_opt_in_witnessed_and_once(self):
        player, clock = fast_player()
        graduate(player, clock)
        declined = player.graduation_ceremony(
            witnesses=("sponsor",), quit_story="not yet", opt_in=False
        )
        self.assertEqual(declined, ())
        with self.assertRaises(ProvenanceError):
            player.graduation_ceremony(witnesses=(), quit_story="alone")
        first = player.graduation_ceremony(witnesses=("sponsor",),
                                           quit_story="now")
        self.assertTrue(first)
        again = player.graduation_ceremony(witnesses=("sponsor",),
                                           quit_story="again?")
        self.assertEqual(again, ())

    def test_unsealed_artifact_rejected(self):
        player, _ = fast_player()
        counterfeit = IdentityArtifact(
            kind=ArtifactKind.DISCHARGE_PAPERS, title="fake papers",
            earned_for="nothing", witnessed_by=("nobody",), opted_in=True,
            _seal=_ProvenanceSeal(),
        )
        with self.assertRaises(ProvenanceError):
            player.identity.shelve(counterfeit)

    def test_forged_firewall_stamp_rejected(self):
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

    def test_track_is_deterministic_and_replayable(self):
        import ast

        import recovering_player.progression_track as mod

        with open(mod.__file__) as f:
            tree = ast.parse(f.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        for chancy in ("random", "secrets", "os", "time", "uuid"):
            self.assertFalse(
                any(n == chancy or n.startswith(chancy + ".")
                    for n in imported))

        player, clock = fast_player(seed=11)
        graduate(player, clock)
        firewall = HardFirewall()
        replayed = ProgressionTrack(firewall)
        for cleared in player.firewall.cleared:
            replayed.credit(firewall.transmit(cleared.crossing))
        self.assertEqual(replayed.recovery_rank, player.track.recovery_rank)
        self.assertEqual(replayed.milestones_awarded,
                         player.track.milestones_awarded)


# ─────────────────────────────────────────────────────────────────────
# Containment and the full journey.
# ─────────────────────────────────────────────────────────────────────
class TestContainmentAndJourney(unittest.TestCase):
    def test_mimicry_contained_inside_reel_only(self):
        with self.assertRaises(ContainmentBreach):
            VariableRatioMimicry("not the interior")  # type: ignore[arg-type]

    def test_stale_reel_is_pure_pattern(self):
        from recovering_player.decaying_reel import _ReelInterior

        mimicry = VariableRatioMimicry(_ReelInterior(), rng=random.Random(0))
        outcomes = [mimicry.spin(staleness=1.0) for _ in range(6)]
        self.assertTrue(all(forced for _, forced, _, _ in outcomes))
        self.assertEqual([hit for hit, _, _, _ in outcomes],
                         [True, False, True, False, True, False])

    def test_full_journey(self):
        player, clock = fast_player(seed=42, full_term_days=10.0)
        player.begin_episode(EpisodeTrigger.REPORTED_URGE)
        for _ in range(10):
            player.spin()
        player.close_episode(EpisodeClosure.COOLDOWN_COMPLETE)
        clock.advance(days=4)
        graduate(player, clock)
        clock.advance(days=10)
        player.graduation_ceremony(witnesses=("sponsor", "council"),
                                   quit_story="done")
        self.assertTrue(player.reel.retired)
        self.assertTrue(player.track.graduation_eligible)
        self.assertTrue(player.identity.holds(ArtifactKind.DISCHARGE_PAPERS))
        # Every contribution traces to an app-side event, never chance.
        self.assertTrue(all(isinstance(r.event, ContributionEvent)
                            for r in player.charity_pool.records))
        self.assertEqual(player.charity_pool.disburse("fund"),
                         player.charity_pool.lifetime_contributed)


if __name__ == "__main__":
    unittest.main()
