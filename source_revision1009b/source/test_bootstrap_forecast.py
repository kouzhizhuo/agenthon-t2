"""## Executive summary (read this first)
Check that bootstrap draws retain their center and joint path dependence.
Unequal gap-separated segments must not change uniform reservoir weights.
Synthetic data only. No task answers, reference scales, or live model calls.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import bootstrap_forecast as bootstrap


def test_segment_successors_are_uniform_and_do_not_cross_gaps():
    dates = pd.DatetimeIndex([
        "2030-01-01", "2030-02-01", "2031-01-01", "2031-02-01",
        "2031-03-01", "2031-04-01",
    ])
    successor = bootstrap._segment_successors(dates, 100)
    np.testing.assert_array_equal(successor, [1, 0, 3, 4, 5, 2])
    np.testing.assert_array_equal(np.sort(successor), np.arange(6))
    # A permutation preserves uniform row weights exactly. A forced terminal
    # restart instead increases weights near each segment's end.
    centered = np.arange(6, dtype=float) - 2.5
    assert centered[successor].mean() == 0


def test_unequal_segments_keep_zero_mean_and_joint_horizon_paths(monkeypatch):
    dates = pd.DatetimeIndex([
        "2030-01-01", "2030-02-01", "2031-01-01", "2031-02-01",
        "2031-03-01", "2031-04-01",
    ])
    a = pd.Series(np.arange(6, dtype=float) - 2.5, index=dates, name="A")
    changes = {"A": a, "B": -a}
    assets, horizons, n_draws = ["A", "B"], [12, 60], 20000
    card = {"targets": {"asset_ids": assets, "horizons": horizons}}
    stats = {asset: {
        "median_calendar_step": 31, "mode": "additive_level", "last": 100.,
        "selected_sd": 1., "per_step_drift": 0.,
    } for asset in assets}
    base = np.full((n_draws, 2, 2), 100.)
    evidence = {"stats": stats, "effective_panel_steps": {a: horizons for a in assets}}
    monkeypatch.setattr(bootstrap.retained, "forecast_samples", lambda *a, **k: (base.copy(), evidence.copy()))
    monkeypatch.setattr(bootstrap.retained, "extract_history", lambda *a, **k: (changes, {}))
    monkeypatch.setattr(bootstrap.retained, "safe_changes", lambda s, mode: (s, 0))
    samples, report = bootstrap.forecast_samples({}, card, "2031-04-30", [], n_draws, 73691)
    robust = samples[::2] - 100.
    # No hidden drift may come from circular boundaries or unequal segment sizes.
    assert np.max(np.abs(robust.mean(axis=0))) < .35
    # The same sampled innovation row drives both assets at every horizon.
    np.testing.assert_allclose(robust[:, 0, :] + robust[:, 1, :], 0., atol=1e-12)
    # Longer horizons reuse the shorter path. Independently sampled margins would
    # destroy the positive covariance of the nested cumulative trajectories.
    covariance = np.cov(robust[:, 0, :], rowvar=False)
    assert covariance[0, 1] > .5 * covariance[0, 0]
    assert report["block_bootstrap"]["applied"] is True
    np.testing.assert_array_equal(samples[1::2], base[1::2])
