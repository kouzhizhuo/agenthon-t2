"""## Executive summary (read this first)
Pool a stationary joint block bootstrap with the retained Gaussian component.
Sample aligned innovation rows in circular blocks within gap-separated segments.
Circular wrapping is a resampling boundary, not an observed transition across a gap.
Uniform restarts and successor permutations preserve each reservoir's zero mean.
Preserve complete joint paths.
This candidate fits only supplied histories and uses no outcomes or scoring scales.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import forecast as retained

METHOD = "v3-joint-stationary-block-pool"


def _segment_successors(index: pd.DatetimeIndex, gap_limit: float) -> np.ndarray:
    """Give every gap-separated segment its own circular successor permutation.

    A uniformly sampled row remains uniform after this permutation, including when
    segments have different lengths. Wrapping to a segment's start is the conventional
    circular bootstrap boundary. No segment can advance into one across a date gap.
    """
    size = len(index)
    if not size:
        raise ValueError("A bootstrap reservoir must contain at least one row")
    gaps = np.diff(index.to_numpy()).astype("timedelta64[D]").astype(float)
    starts = np.r_[0, np.flatnonzero(gaps > gap_limit) + 1]
    ends = np.r_[starts[1:] - 1, size - 1]
    successors = np.arange(1, size + 1, dtype=np.int64)
    successors[ends] = starts
    return successors


def forecast_samples(panels, card, asof, docs, n_draws, seed,
                     variant="block_pool", forecast_spec=None):
    # The release variant's input ledger is useful; the bootstrap itself remains numeric.
    base, evidence = retained.forecast_samples(
        panels, card, asof, docs, n_draws, seed, variant="pool_numeric",
        forecast_spec=forecast_spec)
    assets = list(card["targets"]["asset_ids"])
    horizons = list(card["targets"]["horizons"])
    histories, _ = retained.extract_history(panels, assets, asof)
    stats = evidence["stats"]
    monthly = all(stats[a]["median_calendar_step"] > 20 for a in assets)
    long_window, recent_window, block_length = (60, 12, 3) if monthly else (756, 63, 10)
    changes = pd.DataFrame({a: retained.safe_changes(histories[a], stats[a]["mode"])[0]
                            for a in assets}).sort_index().dropna().tail(long_window)
    # Too little common data cannot support serially dependent joint resampling.
    if len(changes) < 2 * block_length:
        evidence["block_bootstrap"] = {"applied": False, "reason": "insufficient aligned history"}
        return base, evidence
    long = changes.to_numpy(float)
    recent = long[-recent_window:]
    dates = changes.index.to_series()
    gap_limit = max(float(dates.diff().dt.days.median()) * 10, 5)
    long_successor = _segment_successors(changes.index, gap_limit)
    recent_successor = _segment_successors(changes.index[-len(recent):], gap_limit)
    long = long - long.mean(axis=0)
    recent = recent - recent.mean(axis=0)
    # Normalize each reservoir to the unchanged V2 selected per-step spread.
    sd = np.array([stats[a]["selected_sd"] for a in assets])
    long = long * sd / np.maximum(long.std(axis=0, ddof=1), 1e-12)
    recent = recent * sd / np.maximum(recent.std(axis=0, ddof=1), 1e-12)
    counts = evidence["effective_panel_steps"]
    needed = sorted({s for v in counts.values() for s in v})
    max_steps = max(needed)
    rng = np.random.default_rng(seed)
    robust_ids = np.flatnonzero(np.arange(n_draws) % 2 == 0)
    n = len(robust_ids)
    choose_recent = rng.random(n) < .6
    index = np.zeros(n, dtype=np.int64)
    cumulative = np.zeros((n, len(assets)))
    snapshots = {}
    for step in range(1, max_steps + 1):
        restart = np.ones(n, dtype=bool) if step == 1 else rng.random(n) < 1 / block_length
        if np.any(restart):
            choose_recent[restart] = rng.random(int(restart.sum())) < .6
            sizes = np.where(choose_recent[restart], len(recent), len(long))
            index[restart] = (rng.random(int(restart.sum())) * sizes).astype(np.int64)
        other = ~restart
        advance_recent = other & choose_recent
        advance_long = other & ~choose_recent
        index[advance_recent] = recent_successor[index[advance_recent]]
        index[advance_long] = long_successor[index[advance_long]]
        increment = np.empty_like(cumulative)
        increment[choose_recent] = recent[index[choose_recent]]
        increment[~choose_recent] = long[index[~choose_recent]]
        cumulative += increment
        if step in needed:
            snapshots[step] = cumulative.copy()
    for ai, asset in enumerate(assets):
        s = stats[asset]
        for hi, step in enumerate(counts[asset]):
            value = snapshots[step][:, ai] + s["per_step_drift"] * step
            if s["mode"] == "log_level":
                value = s["last"] * np.exp(value)
            elif s["mode"] == "additive_level":
                value = s["last"] + value
            base[robust_ids, ai, hi] = value
    if not np.isfinite(base).all():
        raise ValueError("nonfinite block-bootstrap samples")
    evidence["method"] = METHOD
    evidence["variant"] = variant
    evidence["block_bootstrap"] = {"applied": True, "aligned_rows": len(changes),
        "expected_block_length": block_length, "recent_probability": .6,
        "robust_draws": n, "gaussian_draws": n_draws - n,
        "boundary_rule": "circular successor within each gap-separated segment",
        "uniform_reservoir_invariant": True,
        "preserves_serial_and_cross_asset_dependence": True}
    return base, evidence
