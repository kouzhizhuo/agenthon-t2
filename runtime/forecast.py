"""Executive summary: forecast joint distributions from cutoff-safe numeric and dated text evidence.

The solver never imports evaluation targets or normalization scales. Its three output files
follow the published Track 2 contract. Statistical uncertainty is separate from gate validity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any
import tomllib

import numpy as np
import pandas as pd

from horizon_contract import monthly_horizon_steps, HorizonMetadataError
from return_contract import log_return_steps

METHOD = "spec-evidence-pooled-joint-v2-current-contract"
OUTPUT_FILES = {"forecast.parquet", "forecast_meta.json", "forecast_rationale.md"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_card(panels: Path) -> Path:
    for path in (panels / "card.toml", panels.parent / "card.toml"):
        if path.is_file():
            return path
    raise ValueError("card.toml must be in the panels directory or its parent")


def read_panels(directory: Path) -> tuple[dict[str, pd.DataFrame], list[dict[str, Any]]]:
    paths = sorted(p for p in directory.glob("*.parquet") if not p.name.startswith("._"))
    if not paths:
        paths = sorted(p for p in directory.parent.glob("*.parquet") if not p.name.startswith("._"))
    if not paths:
        raise ValueError("no parquet panels in the requested directory or its parent")
    return {p.stem: pd.read_parquet(p) for p in paths}, [
        {"file": p.name, "sha256": sha256(p)} for p in paths
    ]


def extract_history(panels: dict[str, pd.DataFrame], assets: list[str], asof: str):
    cutoff = pd.Timestamp(asof)
    histories, info = {}, {}
    for asset in assets:
        pieces = []
        for name, frame in panels.items():
            acol = next((c for c in ("asset", "asset_id") if c in frame), None)
            if acol is None or "date" not in frame or "value" not in frame:
                continue
            sub = frame.loc[frame[acol].astype(str) == asset, ["date", "value"]].copy()
            sub["date"] = pd.to_datetime(sub["date"], errors="raise")
            sub = sub.loc[sub.date <= cutoff].sort_values("date")
            if len(sub):
                sub["panel"] = name
                pieces.append(sub)
        if not pieces:
            raise ValueError(f"no pre-asof observations for {asset}")
        sub = pd.concat(pieces).sort_values("date")
        conflicts = sub.groupby("date").value.nunique()
        if (conflicts > 1).any():
            raise ValueError(f"conflicting same-date observations for {asset}")
        sub = sub.drop_duplicates("date")
        values = pd.to_numeric(sub.value, errors="raise").to_numpy(float)
        if not np.isfinite(values).all() or len(values) < 3:
            raise ValueError(f"nonfinite or inadequate history for {asset}")
        series = pd.Series(values, index=pd.DatetimeIndex(sub.date), name=asset)
        histories[asset] = series
        info[asset] = {"n_observations": len(series), "start": str(series.index.min().date()),
                       "end": str(series.index.max().date()), "panels": sorted(set(sub.panel)),
                       "median_calendar_step": float(series.index.to_series().diff().dt.days.median())}
    return histories, info


def safe_changes(series: pd.Series, mode: str) -> tuple[pd.Series, int]:
    """Convert simple factor returns to log steps, rejecting gaps on all semantic branches."""
    dates = series.index.to_series()
    gaps = dates.diff().dt.days
    limit = max(float(gaps.median()) * 10, 5)
    if mode == "cumulative_return":
        changes = pd.Series(log_return_steps(series.to_numpy()), index=series.index, name=series.name)
    elif mode == "log_level":
        if (series <= 0).any():
            raise ValueError("FX log-level model requires positive observed prices")
        changes = np.log(series).diff()
    else:
        changes = series.diff()
    rejected = int((gaps > limit).sum())
    return changes.where(gaps <= limit).dropna(), rejected


def read_text(text_dir: Path, asof: str) -> list[dict[str, Any]]:
    index_path = text_dir / "corpus_index.json"
    if not index_path.is_file():
        raise ValueError("input text corpus requires corpus_index.json; absent evidence cannot pass silently")
    index = json.loads(index_path.read_text())
    docs = []
    for item in index.get("documents", []):
        timestamp = str(item.get("timestamp", ""))[:10]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", timestamp):
            raise ValueError("each indexed document needs a valid publication date")
        if timestamp > asof:
            continue
        relative = item.get("file", item.get("path"))
        if not relative:
            raise ValueError("each indexed document needs a file or path")
        path = (text_dir / relative).resolve()
        if not path.is_relative_to(text_dir.resolve()):
            raise ValueError("text path escapes the input corpus")
        text = path.read_text(errors="replace")
        docs.append({"doc_id": item.get("doc_id", path.name), "timestamp": timestamp,
                     "file": relative, "sha256": sha256(path), "text": text})
    return docs


STRESS_PHRASES = ("financial crisis", "financial stress", "market volatility", "highly uncertain",
                  "heightened uncertainty", "bank failures", "banking turmoil", "pandemic",
                  "coronavirus", "liquidity strains", "geopolitical tensions")


def text_adjustments(docs: list[dict[str, Any]], asof: str) -> dict[str, Any]:
    """Bound uncertainty widening by dated matching passages; this is a heuristic, not confidence."""
    matches = []
    for doc in docs:
        age = (pd.Timestamp(asof) - pd.Timestamp(doc["timestamp"])).days
        if age > 120:
            continue
        normalized = " ".join(doc["text"].lower().split())
        for phrase in STRESS_PHRASES:
            pos = normalized.find(phrase)
            if pos >= 0:
                matches.append({"doc_id": doc["doc_id"], "timestamp": doc["timestamp"],
                                "phrase": phrase, "passage": normalized[max(0, pos-80):pos+len(phrase)+80],
                                "weight": float(np.exp(-age / 45.0))})
    stress = min(1.0, sum(m["weight"] for m in matches) / 4.0)
    return {"stress_index": stress, "volatility_multiplier": 1 + .20 * stress,
            "directional_mean_adjustment": 0.0, "matches": matches,
            "qualification": "phrase evidence supports a bounded uncertainty heuristic; predictive value is unverified"}


def effective_steps(horizons: list[int], median_calendar_step: float,
                    asof: str | None = None, last_date: str | None = None) -> list[int]:
    """Horizons are business days; map monthly observed panels to approximately 21 BD per row."""
    if median_calendar_step > 20:
        if asof is not None and last_date is not None:
            last = pd.Timestamp(last_date).to_period("M")
            # Monthly observation dates identify their reporting month. Add publication lag
            # between the latest numeric observation and asof before extrapolating.
            return [max(1, (pd.Timestamp(asof) + pd.offsets.BDay(h)).to_period("M").ordinal - last.ordinal)
                    for h in horizons]
        return [max(1, int(round(h / 21.0))) for h in horizons]
    return list(horizons)


def correlation_matrix(changes: pd.DataFrame) -> np.ndarray:
    count, dims = len(changes), len(changes.columns)
    corr = changes.corr(min_periods=20).to_numpy(float)
    corr = np.nan_to_num(corr, nan=0.0)
    np.fill_diagonal(corr, 1.0)
    shrink = min(.5, max(.05, dims / max(count, 1)))
    corr = (1-shrink) * corr + shrink * np.eye(dims)
    vals, vecs = np.linalg.eigh(corr)
    corr = np.einsum('ik,jk->ij',vecs * np.maximum(vals,1e-8),vecs,optimize=False)
    scales = np.sqrt(np.diag(corr))
    return corr / np.outer(scales, scales)


def coherent_300_samples(histories, assets, horizons, target_type, step_map, n_draws, seed):
    """Published M0-style 300-row coherent walk, with current log1p return semantics.

    This is a baseline distribution generator, never a scorer or an official scale loader.
    M0's documentation still describes raw return rows; call this current_semantic_300.
    """
    steps = {}
    for asset in sorted(assets):
        tail = histories[asset].tail(300)
        if target_type == "log_return" and float(np.median(np.abs(tail))) >= .2:
            raise ValueError("return panel fails baseline magnitude tripwire")
        mode = "cumulative_return" if target_type == "log_return" else "additive_level"
        steps[asset], _ = safe_changes(tail, mode)
    aligned = pd.DataFrame(steps).dropna().sort_index()
    if len(aligned) < 2:
        raise ValueError("baseline needs two date-aligned gap-safe steps")
    ordered = list(aligned.columns)
    mu = aligned.mean().to_numpy()
    sigma = np.atleast_2d(np.cov(aligned.to_numpy(), rowvar=False, ddof=1))
    cells = [(a, int(step)) for a in assets for step in step_map[a]]
    positions = [ordered.index(a) for a, _ in cells]
    counts = np.array([step for _, step in cells])
    anchors = np.array([0. if target_type == "log_return" else float(histories[a].iloc[-1]) for a, _ in cells])
    mean = anchors + counts * mu[positions]
    cov = np.minimum.outer(counts, counts) * sigma[np.ix_(positions, positions)]
    cov += 1.1e-9 * np.eye(len(cells))
    fallback = False
    try:
        chol = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError:
        cov = np.diag(np.diag(cov));chol = np.linalg.cholesky(cov);fallback = True
    rng = np.random.default_rng(seed)
    samples = mean + np.einsum('ni,ji->nj', rng.standard_normal((n_draws, len(cells))), chol, optimize=False)
    return samples.reshape(n_draws, len(assets), len(horizons)), {
        "generator": "current_semantic_300; published M0-style trailing 300-row mean/covariance with log1p correction",
        "aligned_steps": len(aligned), "mean": mean.tolist(), "covariance": cov.tolist(),
        "diagonal_fallback": fallback, "is_official_M0_or_scale": False}


def forecast_samples(panels: dict[str, pd.DataFrame], card: dict[str, Any], asof: str,
                     docs: list[dict[str, Any]], n_draws: int, seed: int,
                     variant: str = "pool_numeric", forecast_spec: dict[str, Any] | None = None) -> tuple[np.ndarray, dict[str, Any]]:
    """Joint forecast: explicit target semantics, covariance, adaptive scale and continuous tails."""
    targets = card["targets"]
    assets = list(targets["asset_ids"])
    if targets.get('target_type','level') not in {'level','yield','log_return'}:
        raise ValueError("unsupported target_type")
    if any(isinstance(h,bool) or not isinstance(h,int) for h in targets['horizons']):
        raise ValueError("horizons must be declared integers, without coercion")
    horizons = list(targets["horizons"])
    if not assets or len(set(assets)) != len(assets) or not horizons or len(set(horizons)) != len(horizons):
        raise ValueError("target grid must be nonempty and unique")
    if any(h < 1 for h in horizons):
        raise ValueError("horizons must be positive")
    histories, history_info = extract_history(panels, assets, asof)
    modes, changes, stats = {}, {}, {}
    for asset in assets:
        panel_names = " ".join(history_info[asset]["panels"])
        if targets.get("target_type") == "log_return":
            mode = "cumulative_return"
        elif "fx" in panel_names:
            mode = "log_level"
        else:
            mode = "additive_level"
        modes[asset] = mode
        inc, rejected = safe_changes(histories[asset], mode)
        if len(inc) < 2:
            raise ValueError(f"not enough gap-safe increments for {asset}")
        changes[asset] = inc
        long = inc.tail(756 if history_info[asset]["median_calendar_step"] <= 20 else 60)
        recent = inc.tail(63 if history_info[asset]["median_calendar_step"] <= 20 else 12)
        sd_long, sd_recent = float(long.std()), float(recent.std())
        sd = np.sqrt(.4 * sd_long**2 + .6 * sd_recent**2)
        floor = max(abs(float(histories[asset].iloc[-1])) * 1e-8, 1e-8)
        sd = max(float(sd), floor)
        # A monthly trend uses observable increments. Daily asset drift remains zero.
        drift = 0.0
        if history_info[asset]["median_calendar_step"] > 20 and asset != "UNRATE":
            drift = float(.5 * recent.mean() + .5 * long.tail(36).mean())
        kurt = max(0.0, float(long.kurt())) if len(long) > 8 else 0.0
        df = float(np.clip(4 + 6 / max(kurt, .2), 5, 30))
        stats[asset] = {**history_info[asset], "mode": mode, "last": float(histories[asset].iloc[-1]),
                        "gap_spanning_changes_excluded": rejected, "n_changes": len(inc),
                        "long_sd": sd_long, "recent_sd": sd_recent, "selected_sd": sd,
                        "per_step_drift": drift, "excess_kurtosis": kurt, "tail_df": df}
    increment_frame = pd.DataFrame(changes).sort_index()
    corr = correlation_matrix(increment_frame.tail(756))
    chol = np.linalg.cholesky(corr)
    monthly_assets = [a for a in assets if stats[a]["median_calendar_step"] > 20]
    if monthly_assets:
        if len(monthly_assets) != len(assets) or targets.get("target_type", "level") != "level":
            raise ValueError("monthly target grids require exclusively monthly level observations")
        resolved = monthly_horizon_steps(assets, horizons, {a: stats[a]["end"] for a in assets},
                                         asof=asof, card=card, forecast_spec=forecast_spec)
        step_map = {a: [int(x) for x in resolved[ai]] for ai, a in enumerate(assets)}
        horizon_source = "explicit supplied monthly observation-period metadata"
    else:
        step_map = {a: list(horizons) for a in assets}
        horizon_source = "declared daily business-observation horizon keys"
    all_steps = sorted(set(x for xs in step_map.values() for x in xs))
    rng = np.random.default_rng(seed)
    robust = variant != "gaussian_semantic"
    tail_df = float(np.median([stats[a]["tail_df"] for a in assets]))
    regime_scale = np.sqrt((tail_df - 2) / rng.chisquare(tail_df, size=n_draws)) if robust else np.ones(n_draws)
    text = text_adjustments(docs, asof)
    vol_multiplier = text["volatility_multiplier"] if variant == "spec_evidence" else 1.0
    # Interval innovations create Cov(X_h1,X_h2) proportional to min(h1,h2), exactly.
    processes, cumulative, previous = {}, np.zeros((n_draws, len(assets))), 0
    for step in all_steps:
        # Explicit contraction avoids spurious Accelerate BLAS floating-point warnings on
        # macOS; it is the same matrix product and preserves all subsequent finite checks.
        z = np.einsum('ni,ji->nj',rng.standard_normal((n_draws,len(assets))),chol,optimize=False)
        cumulative = cumulative + z * regime_scale[:, None] * np.sqrt(step-previous)
        processes[step] = cumulative.copy()
        previous = step
    out = np.empty((n_draws, len(assets), len(horizons)))
    for ai, asset in enumerate(assets):
        stat = stats[asset]
        for hi, step in enumerate(step_map[asset]):
            shift = stat["per_step_drift"] * step
            disturbance = processes[step][:, ai] * stat["selected_sd"] * vol_multiplier
            if modes[asset] == "cumulative_return":
                out[:, ai, hi] = shift + disturbance
            elif modes[asset] == "log_level":
                out[:, ai, hi] = stat["last"] * np.exp(shift + disturbance)
            else:
                out[:, ai, hi] = stat["last"] + shift + disturbance
    baseline_record = None
    if variant in {"current_semantic_300", "pool_numeric"}:
        baseline, baseline_record = coherent_300_samples(histories, assets, horizons,
            targets.get("target_type", "level"), step_map, n_draws, seed)
        if variant == "current_semantic_300":
            out = baseline
        else:
            # Equal distribution pooling chosen before outcomes: whole joint draws retain
            # each component's dependence. This is not averaging means or fitting weights.
            alternate = np.arange(n_draws) % 2 == 1
            out[alternate] = baseline[alternate]
    if not np.isfinite(out).all():
        raise ValueError("nonfinite forecasts")
    evidence = {"method": METHOD, "variant": variant, "asof": asof, "seed": seed,
                "compiled_contract": {"source": "card.toml [targets] and published exact file/grid contract",
                                      "files": sorted(OUTPUT_FILES), "columns": ["draw","asset","horizon","value"],
                                      "asset_order": assets, "horizon_order": horizons,
                                      "n_draws":n_draws, "expected_rows":n_draws*len(assets)*len(horizons),
                                      "draw_range":[0,n_draws-1], "target_semantics":targets.get('target_type','level'),
                                      "bound_asof":asof},
                "executed_internal_checks": {"all_values_finite":bool(np.isfinite(out).all()),
                                             "sample_shape":list(out.shape),
                                             "target_histories_at_or_before_asof":all(s['end'] <= asof for s in stats.values()),
                                             "indexed_documents_at_or_before_asof":all(d['timestamp'] <= asof for d in docs),
                                             "correlation_symmetric":bool(np.allclose(corr,corr.T)),
                                             "correlation_positive_eigenvalues":bool((np.linalg.eigvalsh(corr)>0).all()),
                                             "official_gates_run_in_solver":False,
                                             "predictive_accuracy_checked_in_solver":False},
                "distribution_pool": {"weight_robust_numeric": .5, "weight_current_semantic_300": .5} if variant == "pool_numeric" else None,
                "baseline_record": baseline_record, "stats": stats, "cross_asset_correlation": corr.tolist(), "joint_tail_df": tail_df,
                "effective_panel_steps": step_map, "horizon_source": horizon_source,
                "return_transform": "log1p(decimal simple returns); sum log steps; zero future anchor",
                "volatility_multiplier_applied": vol_multiplier,
                "text_adjustment": text, "documents": [{k:v for k,v in d.items() if k != "text"} for d in docs],
                "unknowns": ["withheld future accuracy", "future monthly release-vintage convention",
                             "causal and predictive validity of stress phrase adjustment"],
                "formal_validity_is_predictive_confidence": False}
    return out, evidence


def write_outputs(samples: np.ndarray, card: dict[str, Any], asof: str, output: Path,
                  evidence: dict[str, Any]) -> None:
    if output.name != "forecast.parquet":
        raise ValueError("contract requires output basename forecast.parquet")
    output.parent.mkdir(parents=True, exist_ok=True)
    unexpected = {p.name for p in output.parent.iterdir() if not p.name.startswith('._')} - OUTPUT_FILES
    if unexpected:
        raise ValueError(f"output directory has unexpected entries: {sorted(unexpected)}")
    assets, horizons = card["targets"]["asset_ids"], card["targets"]["horizons"]
    n, na, nh = samples.shape
    if (na,nh) != (len(assets),len(horizons)) or not 200 <= n <= 20000 or not np.isfinite(samples).all():
        raise ValueError("samples violate finite exact-grid or draw-count contract")
    if n*na*nh > 5_000_000:
        raise ValueError("samples exceed official row ceiling")
    frame = pd.DataFrame({"draw": np.repeat(np.arange(n, dtype=np.int64), na*nh),
                          "asset": np.tile(np.repeat(assets, nh), n),
                          "horizon": np.tile(horizons, n*na), "value": samples.reshape(-1)})
    frame.to_parquet(output, index=False)
    meta = {"unit_id": card["task"]["id"], "asof": asof, "representation": "samples",
            "asset_ids": assets, "horizons": horizons, "n_draws": n,
            "target": card["targets"].get("target_type", "level"),
            "rationale": {"file": "forecast_rationale.md", "method": METHOD}}
    (output.parent / "forecast_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    ledger = []
    for asset in assets:
        s = evidence["stats"][asset]
        for horizon, steps in zip(horizons, evidence["effective_panel_steps"][asset]):
            anchor = 0.0 if s["mode"] == "cumulative_return" else s["last"]
            ledger.append(f"| {asset} | {horizon} | {steps} | {s['mode']} | {anchor:.9g} | "
                          f"{s['per_step_drift']*steps:.9g} | {s['selected_sd']:.9g} | "
                          f"{evidence['volatility_multiplier_applied']:.6g} |")
    rationale = "## Executive summary (read this first)\n\n" + (
        f"A cutoff-safe joint distribution for {card['task']['id']} at {asof}. "
        "Executed internal checks establish structural properties; official gate status and future accuracy are separate.\n\n"
        "1. Read each target history from every supplied panel, with date <= asof. Record hashes and observation dates below.\n"
        "2. Transform decimal simple factor returns with log1p before forecasting their sum. Respect FX log-level and additive-level targets; exclude gap-spanning steps.\n"
        "3. Blend 40% long-window variance and 60% recent variance; monthly non-unemployment levels get an observable trend.\n"
        "4. Estimate and shrink cross-asset correlation. Shared interval innovations preserve cross-horizon covariance.\n"
        "5. Pool two complete joint distributions with fixed 50:50 weights: the robust numeric walk above and "
        "a coherent Gaussian walk fitted to trailing 300 observations with observable mean drift and sample covariance. "
        "Alternating whole joint draws preserves each component's cross-cell dependence. No fitted pooling weight is used. "
        "Dated text is recorded as evidence; the selected pooled model applies no text-driven mean or scale adjustment.\n\n"
        "| asset | horizon BD | panel steps | semantic mode | anchor | drift in model coordinate | step sd | vol multiplier |\n"
        "|---|---|---|---|---|---|---|---|\n" + "\n".join(ledger) + "\n\n"
        "For additive levels and cumulative returns: center = anchor + drift. "
        "For FX: value = last * exp(drift + shock), so the ledger drift is in log-price units. "
        "Monthly steps come from each supplied observation month and the last observed panel month; horizon keys remain unchanged. Future release-vintage uncertainty remains.\n\n"
        "The ledger above describes the robust component. The baseline_record below supplies the Gaussian component's "
        "full cell mean and covariance; distribution_pool states the mixing weights. The evidence is an arithmetic "
        "and provenance record. None of its checks measures hidden target accuracy.\n\n"
        "```json\n" + json.dumps(evidence, indent=2) + "\n```\n")
    (output.parent / "forecast_rationale.md").write_text(rationale)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("verb", choices=["forecast"])
    parser.add_argument("--panels", type=Path, required=True)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--asof", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-draws", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)
    card_path = find_card(args.panels)
    card = tomllib.loads(card_path.read_text())
    trusted_asof = card.get('forecast',{}).get('asof',card['provenance']['data_cutoff'])
    if args.asof != str(trusted_asof)[:10]:
        raise ValueError("CLI asof must equal the card data_cutoff")
    floor = max(200, int(card.get("scoring", {}).get("params", {}).get("n_draws_min", 200)))
    if not floor <= args.n_draws <= 20000:
        raise ValueError("draw count outside card floor / official 20000 ceiling")
    seed = args.seed if args.seed is not None else int(os.environ.get("QFBENCH_SEED", "0"))
    spec_path = next((p for p in (args.panels / "forecast_spec.json", args.panels.parent / "forecast_spec.json") if p.is_file()), None)
    forecast_spec = json.loads(spec_path.read_text()) if spec_path else None
    panels, hashes = read_panels(args.panels)
    docs = read_text(args.text, args.asof)
    samples, evidence = forecast_samples(panels, card, args.asof, docs, args.n_draws, seed, forecast_spec=forecast_spec)
    evidence["input_panel_hashes"] = hashes
    evidence["card_sha256"] = sha256(card_path)
    evidence["forecast_spec_sha256"] = sha256(spec_path) if spec_path else None
    write_outputs(samples, card, args.asof, args.out, evidence)
    print(json.dumps({"method": METHOD, "files_written": sorted(OUTPUT_FILES),
                      "n_draws": args.n_draws, "cells": len(card['targets']['asset_ids'])*len(card['targets']['horizons'])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
