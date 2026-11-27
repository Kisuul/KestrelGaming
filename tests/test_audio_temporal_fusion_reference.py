"""Fixtures for exact association across clocks and causal decision replay."""

from dataclasses import replace
from fractions import Fraction as F
from itertools import permutations
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
for skill in (
    "audio-oscilloscope", "audio-stereo-correlation", "audio-pitch-tracking", "audio-tuning-analysis",
    "audio-event-segmentation", "audio-spectrogram-waterfall", "audio-onset-detection",
    "audio-beat-tracking", "audio-temporal-fusion",
):
    sys.path.insert(0, str(ROOT / "skills" / skill / "scripts"))

from reference_beat_tracking import BeatProfile, track_beats
from reference_event_segmentation import FeatureFrame, FeatureGrid, analyze_segments
from reference_onset_detection import OnsetDetector, OnsetFrame, OnsetGrid, OnsetProfile, match_onsets
from reference_oscilloscope import MAX_SAMPLE_INDEX, ScopeEpoch
from reference_temporal_fusion import (
    MAX_RECORDS, MAX_STEPS, ClockMap, CoverageSpan, DispatchStamp, Event, Frontier,
    FusionRun, ReplayStep, Retraction, SourceRoute, fuse_offline, replay_fusion,
)
from reference_tuning_analysis import TuningSupport


EPOCH = ScopeEpoch("capture", 0, F(48000), "device clock", "analysis tap", "FS", ("mono",))
LARGE_ORIGIN = 2**60 + 37


def route(source_id, span=(0, 10000), *, epoch=EPOCH):
    identity = ClockMap("identity", epoch, epoch, span, span[0], span[0])
    return SourceRoute(source_id, identity, (CoverageSpan(span, "observed"),))


def run(source_ids=("a", "b"), gate=6, *, span=(0, 10000), epoch=EPOCH, event_type="onset"):
    return FusionRun(epoch, event_type, span, gate, tuple(route(s, span, epoch=epoch) for s in source_ids))


def event(source_id, position, *, name=None, epoch=EPOCH, **fields):
    start = max(epoch.origin_sample, int(position) - 1)
    end = int(position) + 1
    fields.setdefault("support", ((start, end),))
    fields.setdefault("ready_sample_exclusive", end)
    fields.setdefault("event_type", "onset")
    return Event(source_id, str(position) if name is None else name, epoch=epoch,
                 position_sample=position, **fields)


def positions(groups):
    return [[row.position_sample for row in group.members] for group in groups]


def event_ids(group):
    return [(row.event.source_id, row.event.event_id) for row in group.members]


class ClockTests(unittest.TestCase):
    def test_fractional_gate_at_a_large_origin(self):
        source_origin = 2**58 + 13
        master = replace(EPOCH, origin_sample=LARGE_ORIGIN)
        source = replace(EPOCH, epoch_id="44.1k", rate_hz=F(44100), origin_sample=source_origin)
        clock = ClockMap("locked", source, master, (source_origin, source_origin + 2000),
                         source_origin, LARGE_ORIGIN)
        left = event("a", LARGE_ORIGIN + 1600, epoch=master)
        right = event("b", source_origin + F(2941, 2), epoch=source)
        profile = run(gate=F(1, 2), span=(LARGE_ORIGIN, LARGE_ORIGIN + 2000), epoch=master)
        profile = replace(profile, sources=(profile.sources[0], SourceRoute("b", clock)))
        separate = fuse_offline(profile, [right, left])
        expected = LARGE_ORIGIN + F(235280, 147)
        self.assertEqual(positions(separate.groups), [[LARGE_ORIGIN + 1600], [expected]])
        self.assertEqual(float(expected), float(LARGE_ORIGIN + 1600))
        self.assertEqual(clock.map_position(source_origin + 1470), LARGE_ORIGIN + 1600)
        pair, = fuse_offline(replace(profile, maximum_span_samples=F(80, 147)), [right, left]).groups
        self.assertEqual(pair.position_sample, LARGE_ORIGIN + 1600 + F(40, 147))
        self.assertEqual(pair.support[-1][1], LARGE_ORIGIN + F(1471 * 160, 147))

    def test_event_and_evidence_have_different_upper_bounds(self):
        source = replace(EPOCH, epoch_id="decimated", rate_hz=F(24000))
        clock = ClockMap("locked", source, EPOCH, (0, 10), 0, 0)
        profile = replace(run(("a",), span=(0, 30)), sources=(SourceRoute("a", clock),))
        edge = event("a", F(19, 2), epoch=source, observed_release_sample_exclusive=11)
        position_out = event("a", 10, epoch=source, support=((9, 10),), ready_sample_exclusive=10)
        support_out = event("a", 9, epoch=source, name="support-out", support=((9, 11),),
                            ready_sample_exclusive=11)
        result = fuse_offline(profile, [edge, position_out, support_out])
        selected, = result.groups
        self.assertEqual(selected.position_sample, 19)
        self.assertEqual(selected.support, ((16, 20),))
        self.assertEqual(selected.data_ready_sample_exclusive, 20)
        self.assertIsNone(selected.evidence_release_sample_exclusive)
        self.assertEqual(selected.members[0].event.observed_release_sample_exclusive, 11)
        self.assertEqual({x.event.event_id: x.disposition for x in result.excluded},
                         {"10": "outside_mapping", "support-out": "outside_mapping"})
        self.assertIsNone(clock.map_position(10))
        self.assertEqual(clock.map_boundary(10), 20)

    def test_readiness_outside_a_valid_map_remains_unknown(self):
        profile = run(("a",), span=(0, 20))
        record = event("a", 10, ready_sample_exclusive=21, observed_release_sample_exclusive=22)
        group, = fuse_offline(profile, [record]).groups
        self.assertEqual(group.position_sample, 10)
        self.assertIsNone(group.data_ready_sample_exclusive)
        self.assertIsNone(group.evidence_release_sample_exclusive)
        self.assertEqual(group.members[0].event.ready_sample_exclusive, 21)

    def test_cropped_validity_preserves_the_original_anchor(self):
        source = replace(EPOCH, epoch_id="24k", rate_hz=F(24000), origin_sample=40)
        clock = ClockMap("locked", source, EPOCH, (50, 60), 40, 30)
        self.assertIsNone(clock.map_position(40))
        self.assertEqual(clock.map_position(50), 50)
        self.assertEqual(clock.map_boundary(60), 70)

    def test_declared_tap_offset_changes_the_association(self):
        delayed = replace(EPOCH, epoch_id="processed", tap_id="delayed route")
        first, second = event("a", 100), event("b", 112, epoch=delayed)
        profile = run(gate=1, span=(0, 200))
        corrected = ClockMap("measured offset", delayed, EPOCH, (12, 212), 12, 0)
        uncorrected = replace(corrected, mapping_id="nominal", master_anchor=12)
        for clock, expected in ((corrected, [[100, 100]]), (uncorrected, [[100], [112]])):
            config = replace(profile, sources=(profile.sources[0], SourceRoute("b", clock)))
            with self.subTest(clock=clock.mapping_id):
                self.assertEqual(positions(fuse_offline(config, [first, second]).groups), expected)


class AssociationTests(unittest.TestCase):
    def test_anchor_span_is_independent_of_arrival_order_and_prevents_chaining(self):
        profile = run(("a", "b", "c"), gate=10)
        records = [event("c", 18), event("a", 0), event("b", 9)]
        initial = fuse_offline(profile, records)
        self.assertEqual(positions(initial.groups), [[0, 9], [18]])
        for order in permutations(records):
            self.assertEqual(fuse_offline(profile, order), initial)

    def test_inclusive_gate_and_competitor_available_to_later_groups(self):
        initial = [event("a", t) for t in (0, 2, 7)]
        result = fuse_offline(run(), initial + [event("b", 6)])
        self.assertEqual(positions(result.groups), [[0, 6], [2], [7]])
        self.assertEqual(result.groups[0].gate_end_sample, 6)
        self.assertEqual([row.position_sample for row in result.groups[0].competitors], [2])
        self.assertEqual([row.position_sample for row in result.groups[1].competitors], [7])

    def test_equal_time_ties_use_source_and_event_identity(self):
        records = [event("b", 5), event("a", 5, name="second"), event("a", 5, name="first")]
        for order in permutations(records):
            first, second = fuse_offline(run(("b", "a"), gate=0), order).groups
            self.assertEqual(event_ids(first), [("a", "first"), ("b", "5")])
            self.assertEqual(event_ids(second), [("a", "second")])
            self.assertEqual(first.competitors, second.members)

    def test_weighted_label_residual_and_ready_times_stay_distinct(self):
        a = event("a", 4800, support=((4650, 4920),), weight=2,
                  ready_sample_exclusive=5280, observed_release_sample_exclusive=5300)
        b = event("b", 4848, support=((4748, 5000),), weight=1,
                  ready_sample_exclusive=5520, observed_release_sample_exclusive=5600)
        result, = fuse_offline(run(gate=48), [b, a]).groups
        self.assertEqual(result.position_sample, 4816)
        self.assertEqual(result.residual_samples, (-16, 32))
        self.assertEqual(result.support, ((4650, 5000),))
        self.assertEqual(result.data_ready_sample_exclusive, 5520)
        self.assertEqual((result.data_ready_sample_exclusive - result.position_sample) / 48, F(44, 3))
        self.assertEqual(result.evidence_release_sample_exclusive, 5600)
        no_report, = fuse_offline(run(gate=48), [a, replace(b, observed_release_sample_exclusive=None)]).groups
        self.assertIsNone(no_report.evidence_release_sample_exclusive)

    def test_support_union_merges_touching_intervals_and_leaves_holes(self):
        a = event("a", 5, support=((0, 4), (8, 10)), ready_sample_exclusive=12)
        b = event("b", 6, support=((6, 8),), ready_sample_exclusive=9)
        result, = fuse_offline(run(), [b, a]).groups
        self.assertEqual(result.support, ((0, 4), (6, 10)))
        self.assertEqual(result.members[0].event.support, ((0, 4), (8, 10)))

    def test_incompatible_epochs_and_context_keep_their_provenance(self):
        observation = event("a", 7200, role="observation")
        prediction = event("b", 7200, role="prediction", support=((5700, 5900),),
                           ready_sample_exclusive=6000)
        segment = event("c", 7200, event_type="section change")
        old_epoch = event("b", 7200, epoch=replace(EPOCH, epoch_id="past"), name="old")
        unknown = event("u", 7200)
        result = fuse_offline(run(("a", "b", "c"), gate=0), [segment, prediction, unknown, observation, old_epoch])
        self.assertEqual(positions(result.groups), [[7200]])
        self.assertEqual([(e.event.source_id, e.disposition) for e in result.excluded],
                         [("b", "context"), ("b", "incompatible_epoch"), ("c", "context"), ("u", "unmapped_source")])
        self.assertEqual((result.excluded[0].position_sample - result.excluded[0].ready_sample_exclusive) / 48, 25)
        self.assertIsNone(result.excluded[1].position_sample)
        self.assertIs(result.excluded[-1].event, unknown)

    def test_measured_quiet_and_missing_coverage_have_distinct_evidence(self):
        profile = run(gate=6, span=(0, 30))
        a, b = profile.sources
        gap = replace(b, coverage=(
            CoverageSpan((0, 4), "observed"), CoverageSpan((4, 9), "gap"),
            CoverageSpan((9, 30), "observed"),
        ))
        observed, = fuse_offline(profile, [event("a", 5)]).groups
        unavailable = fuse_offline(replace(profile, sources=(a, gap)), [event("a", 5), event("b", 5)])
        self.assertEqual(positions(unavailable.groups), [[5]])
        self.assertEqual(observed.incomplete_sources, ())
        self.assertEqual(unavailable.groups[0].incomplete_sources, ("b",))
        self.assertEqual(unavailable.excluded[0].disposition, "source_gap")
        self.assertEqual(unavailable.run.sources[1].coverage[1].span, (4, 9))

    def test_coverage_includes_the_gate_end_only_inside_the_analysis_span(self):
        profile = run(gate=4, span=(0, 10))
        a, b = profile.sources
        b = replace(b, coverage=(CoverageSpan((0, 4), "observed"), CoverageSpan((4, 8), "observed")))
        profile = replace(profile, sources=(a, b))
        interior, = fuse_offline(profile, [event("a", 4)]).groups
        earlier, = fuse_offline(profile, [event("a", F(7, 2))]).groups
        clipped, = fuse_offline(run(gate=4, span=(0, 10)), [event("a", 8)]).groups
        self.assertEqual(interior.incomplete_sources, ("b",))
        self.assertEqual(earlier.incomplete_sources, ())
        self.assertEqual(clipped.incomplete_sources, ())

    def test_separate_runs_enforce_a_discontinuity(self):
        a, b = event("a", 9), event("b", 11)
        full = run(gate=3, span=(0, 20))
        before = fuse_offline(replace(full, span=(0, 10), sources=tuple(
            replace(s, coverage=(CoverageSpan((0, 10), "observed"),)) for s in full.sources)), [a, b])
        after = fuse_offline(replace(full, span=(11, 20), sources=tuple(
            replace(s, coverage=(CoverageSpan((11, 20), "observed"),)) for s in full.sources)), [a, b])
        self.assertEqual(positions(before.groups), [[9]])
        self.assertEqual(positions(after.groups), [[11]])
        self.assertEqual(before.excluded[0].disposition, "outside_run")
        self.assertEqual(after.excluded[0].disposition, "outside_run")


class ReplayTests(unittest.TestCase):
    def test_frontier_can_precede_a_cropped_analysis_span(self):
        profile = run(("a",), span=(30, 70))
        first, second = replay_fusion(profile, [
            ReplayStep((event("a", 40),), (Frontier("a", 20, 50),)),
            ReplayStep(frontiers=(Frontier("a", 47, 55),)),
        ])
        self.assertEqual(positions(first.provisional), [[40]])
        self.assertEqual(second.newly_committed[0].group.position_sample, 40)

    def test_frontier_equality_allows_a_later_record_at_the_gate_edge(self):
        profile = run(gate=48)
        a, b = event("a", 4800), event("b", 4848, name="second")
        added = event("b", 4848, name="first")
        frames = replay_fusion(profile, [
            ReplayStep((a, b), (Frontier("a", 4900, 5600), Frontier("b", 4848, 5500))),
            ReplayStep((added,), (Frontier("b", 4850, 5760),)),
        ])
        self.assertEqual(frames[0].newly_committed, ())
        self.assertEqual(event_ids(frames[0].provisional[0]), [("a", "4800"), ("b", "second")])
        closed, = frames[1].newly_committed
        self.assertEqual(event_ids(closed.group), [("a", "4800"), ("b", "first")])
        self.assertEqual([row.event for row in closed.group.competitors], [b])
        self.assertEqual(closed.decision_ready_sample_exclusive, 5760)
        self.assertEqual(len(frames[1].provisional), 1)

    def test_weighted_replay_uses_independent_dispatch_clock(self):
        profile = run(gate=48)
        a = event("a", 4800, weight=2, ready_sample_exclusive=5280)
        b = event("b", 4848, ready_sample_exclusive=5520)
        frontiers = (Frontier("a", 4900, 5500), Frontier("b", 4850, 5760))
        for block, delivered in ((240, 5760), (1024, 6144)):
            stamp = DispatchStamp("simulation", 2 + F(delivered, 48000))
            frame, = replay_fusion(profile, [ReplayStep((b, a), frontiers, stamp)])
            committed, = frame.newly_committed
            self.assertEqual(committed.group.position_sample, 4816)
            self.assertEqual(committed.group.data_ready_sample_exclusive, 5520)
            self.assertEqual(committed.decision_ready_sample_exclusive, 5760)
            self.assertEqual((committed.decision_ready_sample_exclusive - 4816) / 48, F(59, 3))
            self.assertEqual(((5760 + block - 1) // block) * block, delivered)
            self.assertEqual(committed.dispatch, stamp)
            self.assertIsNone(committed.group.evidence_release_sample_exclusive)

    def test_late_earlier_anchor_changes_provisional_group_only(self):
        prefix = ReplayStep((event("a", 9), event("b", 14)), dispatch=DispatchStamp("host", 4))
        added = ReplayStep((event("c", 4),), dispatch=DispatchStamp("host", 5))
        first, second = replay_fusion(run(("a", "b", "c")), [prefix, added])
        self.assertEqual(positions(first.provisional), [[9, 14]])
        self.assertEqual(positions(second.provisional), [[4, 9], [14]])
        self.assertEqual((first.step.dispatch.seconds, second.step.dispatch.seconds), (4, 5))
        self.assertEqual(first.newly_committed, second.newly_committed)

    def test_committed_prefix_survives_distinct_legal_continuations(self):
        prefix = ReplayStep((event("a", 0), event("b", 6)),
                            (Frontier("a", 9, 9), Frontier("b", 9, 9), Frontier("c", 9, 9)))
        outcomes = []
        for late in ((event("a", 9), event("c", 13)), (event("b", 9), event("c", 28))):
            continuations = [prefix, ReplayStep(late, tuple(Frontier(s, None, 40) for s in ("a", "b", "c")))]
            early, later = replay_fusion(run(("a", "b", "c")), continuations)
            self.assertEqual(positions([entry.group for entry in early.newly_committed]), [[0, 6]])
            self.assertTrue(all(entry.group.anchor_sample >= 9 for entry in later.newly_committed))
            outcomes.append((early, later))
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertNotEqual(outcomes[0][1], outcomes[1][1])

    def test_competitor_and_predecessor_can_delay_commitment(self):
        profile = run(gate=2)
        records = [event("a", 0), event("a", 1, ready_sample_exclusive=120),
                   event("b", 2), event("b", 8)]
        committed = replay_fusion(profile, [
            ReplayStep(tuple(records), (Frontier("a", None, 110), Frontier("b", None, 110))),
        ])[0].newly_committed
        self.assertEqual(positions([x.group for x in committed]), [[0, 2], [1], [8]])
        self.assertEqual([x.group.data_ready_sample_exclusive for x in committed], [3, 120, 9])
        self.assertEqual([x.decision_ready_sample_exclusive for x in committed], [120, 120, 120])

    def test_missing_source_needs_explicit_finalization_and_remains_partial(self):
        profile = run(span=(0, 20))
        profile = replace(profile, sources=(profile.sources[0], SourceRoute("b", None)))
        first, second = replay_fusion(profile, [
            ReplayStep((event("a", 5), event("b", 5)), (Frontier("a", None, 10),)),
            ReplayStep(frontiers=(Frontier("b", None, 12),)),
        ])
        self.assertEqual(first.newly_committed, ())
        self.assertEqual(first.excluded[0].disposition, "unmapped_source")
        closed, = second.newly_committed
        self.assertEqual(closed.group.incomplete_sources, ("b",))
        self.assertEqual(closed.decision_ready_sample_exclusive, 12)

    def test_unknown_closure_or_data_has_no_invented_ready_boundary(self):
        for ready, closure in ((None, 30), (11, None)):
            with self.subTest(ready=ready, closure=closure):
                entry = replay_fusion(run(("a",)), [
                    ReplayStep((event("a", 10, ready_sample_exclusive=ready),), (Frontier("a", None, closure),)),
                ])[0].newly_committed[0]
                self.assertEqual(entry.group.data_ready_sample_exclusive, ready)
                self.assertIsNone(entry.decision_ready_sample_exclusive)

    def test_revisions_and_retractions_preserve_previous_snapshots(self):
        first = event("a", 7, name="same")
        corrected = replace(first, revision=1, position_sample=9, ready_sample_exclusive=12)
        records = replay_fusion(run(("a",)), [
            ReplayStep((first,)), ReplayStep((corrected,)), ReplayStep((Retraction("a", "same", 2),)),
            ReplayStep((replace(first, revision=3),), (Frontier("a", None, 15),)),
        ])
        self.assertEqual([positions(frame.provisional) for frame in records], [[[7]], [[9]], [], []])
        self.assertEqual(records[0].provisional[0].members[0].event.revision, 0)
        self.assertEqual(records[-1].newly_committed[0].group.members[0].event.revision, 3)

    def test_guaranteed_frontier_rejects_inserts_and_both_sides_of_a_revision(self):
        first = event("a", 2, name="first")
        prefix = ReplayStep((first, event("a", 20, name="later")), (Frontier("a", 10, 25),))
        for change in (
            event("a", 9), replace(first, revision=1, position_sample=11),
            event("a", 8, name="later", revision=1), Retraction("a", "first", 1),
        ):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "violates a guaranteed frontier"):
                replay_fusion(run(("a",)), [prefix, ReplayStep((change,))])
        self.assertEqual(replay_fusion(run(("a",)), [prefix])[0].newly_committed[0].group.position_sample, 2)

    def test_reject_retreat_old_revisions_and_updates_after_end(self):
        first = event("a", 10)
        profile = run(("a",))
        checks = (
            (ReplayStep((first,)), ReplayStep((first,))),
            (ReplayStep((first,), (Frontier("a", 10),)), ReplayStep(frontiers=(Frontier("a", 9),))),
            (ReplayStep(frontiers=(Frontier("a", None),)), ReplayStep((first,))),
            (ReplayStep(frontiers=(Frontier("a", None),)), ReplayStep(frontiers=(Frontier("a", 100),))),
            (ReplayStep(frontiers=(Frontier("typo", 10),)),),
            (ReplayStep((Retraction("a", "10", 0),)),),
        )
        for steps in checks:
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                replay_fusion(profile, steps)


class IntegrationTests(unittest.TestCase):
    def test_selected_segmentation_cut_keeps_late_left_readiness(self):
        origin = LARGE_ORIGIN
        epoch = replace(EPOCH, origin_sample=origin)
        grid = FeatureGrid(epoch, 960, 240, "level", ("FS",))
        frames = []
        for i, level in enumerate([0] * 4 + [2] * 4):
            start = origin + 240 * i
            end = start + 960
            ready = origin + 2800 if i == 1 else end
            release = origin + ((ready - origin + 1023) // 1024) * 1024
            support = TuningSupport(epoch, start, end, end, ready, release)
            frames.append(FeatureFrame(grid, i, support, (level,)))
        segmentation = analyze_segments(grid, frames, frame_count=8,
                                        analysis_span_twice=(2 * origin, 2 * (origin + 2640)))
        cut, = segmentation.boundaries
        boundary = Event("cut", "b4", "section change", epoch, F(cut.position_sample_twice, 2),
                         (cut.peak_sample_support,), cut.peak_ready_sample_exclusive,
                         observed_release_sample_exclusive=cut.peak_evidence_release_sample_exclusive)
        config = run(("cut",), span=(origin, origin + 4000), epoch=epoch, event_type="section change")
        fused, = fuse_offline(config, [boundary]).groups
        self.assertEqual(fused.position_sample - origin, F(2639, 2))
        self.assertEqual(cut.score.ready_sample_exclusive - origin, 2160)
        self.assertEqual(fused.data_ready_sample_exclusive - origin, 2800)
        self.assertEqual(fused.evidence_release_sample_exclusive - origin, 3072)
        self.assertEqual(fused.support, ((origin + 240, origin + 2400),))
        evaluation = match_onsets([2 * origin + 2639], [int(2 * fused.position_sample)],
                                  tolerance_sample_twice=0,
                                  eligible_interval_twice=(2 * origin, 2 * (origin + 4000)))
        self.assertEqual(evaluation.f1, 1)

    def test_coincident_onset_and_offline_beat_keep_separate_evidence(self):
        grid = OnsetGrid(EPOCH, (1.0, 1.0), 2, 2)
        detector = OnsetDetector(grid, OnsetProfile(background=1))
        points, onsets = [], {}
        for i, level in enumerate((0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 4)):
            frame = OnsetFrame(grid, 2 * i, 2 * i + 2, (0.0, float(level)), 0.0)
            point, detected = detector.push(frame, observed_release_sample_exclusive=2 * i + 2)
            points.append(point)
            if detected is not None:
                onsets[detected.estimated_sample_twice] = detected
        beats = track_beats(points, BeatProfile(6), period_frames=2, observed_release_sample_exclusive=32)
        beat = next(b for segment in beats.segments for b in segment.beats if b.center_sample_twice in onsets)
        onset = onsets[beat.center_sample_twice]
        position = F(onset.estimated_sample_twice, 2)
        signal_boundary = event("attack", position, support=((0, onset.ready_sample_exclusive),),
                                ready_sample_exclusive=onset.ready_sample_exclusive,
                                observed_release_sample_exclusive=onset.observed_release_sample_exclusive)
        beat_boundary = event("pulse", position, event_type="beat", support=((0, beats.ready_sample_exclusive),),
                              ready_sample_exclusive=beats.ready_sample_exclusive,
                              observed_release_sample_exclusive=beats.observed_release_sample_exclusive)
        result = fuse_offline(run(("attack", "pulse"), gate=0), [beat_boundary, signal_boundary])
        self.assertEqual(result.groups[0].members[0].event, signal_boundary)
        context, = result.excluded
        self.assertEqual(context.disposition, "context")
        self.assertEqual(context.position_sample, result.groups[0].position_sample)
        self.assertGreater(context.ready_sample_exclusive, result.groups[0].data_ready_sample_exclusive)
        self.assertEqual(context.evidence_release_sample_exclusive, 32)


class ValidationTests(unittest.TestCase):
    def test_reject_invalid_positions_supports_weights_and_maps(self):
        raw = event("a", 4)
        clock = route("a").mapping
        near_end = replace(EPOCH, epoch_id="edge", origin_sample=MAX_SAMPLE_INDEX - 2)
        cases = (
            lambda: replace(raw, position_sample=4.0), lambda: replace(raw, weight=True),
            lambda: replace(raw, weight=0), lambda: replace(raw, support=((4, 4),)),
            lambda: replace(raw, ready_sample_exclusive=4),
            lambda: replace(raw, observed_release_sample_exclusive=4), lambda: replace(raw, role="unknown"),
            lambda: replace(clock, source_anchor=-1), lambda: replace(clock, master_anchor=1),
            lambda: replace(clock, master=near_end, master_anchor=near_end.origin_sample),
            lambda: SourceRoute("a", None, (CoverageSpan((0, 10), "observed"),)),
        )
        for i, check in enumerate(cases):
            with self.subTest(check=i), self.assertRaises(ValueError):
                check()

    def test_snapshot_identity_and_run_bounds(self):
        profile = run()
        first = event("a", 1)
        with self.assertRaises(ValueError):
            fuse_offline(profile, [first, replace(first, revision=1)])
        with self.assertRaises(ValueError):
            fuse_offline(profile, [first] * (MAX_RECORDS + 1))
        with self.assertRaises(ValueError):
            replay_fusion(profile, [ReplayStep()] * (MAX_STEPS + 1))
        with self.assertRaises(ValueError):
            replace(profile, sources=(profile.sources[0], profile.sources[0]))
        with self.assertRaises(ValueError):
            replace(profile, master=replace(EPOCH, epoch_id="other"))
        with self.assertRaises(ValueError):
            replace(profile, maximum_span_samples=-1)
