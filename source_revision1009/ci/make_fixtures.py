"""## Executive summary (read this first)
Create small invented forecasting inputs for Linux container and official gate checks.
No future observations, target answers or reference outputs are generated. The resulting
daily-return and monthly-release fixtures test semantic paths, not predictive quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import uuid

import numpy as np
import pandas as pd


def card(identifier, assets, horizons, asof, target, frequency, unit, canary):
    return f'''# ## Executive summary (read this first)
# Invented input-only fixture. No target outcome is included.
schema_version = "2.0"
[task]
id = "{identifier}"
track = "forecasting"
title = "Invented Linux semantic fixture"
split = "public-dev"
[metadata]
category = "T2-F1"
asset_panel = "{frequency}"
[provenance]
license = "MIT"
data_source = "invented deterministic fixture"
data_cutoff = "{asof}"
[contamination]
canary_guid = "{canary}"
[scoring]
verifier = "t2.crps_composite"
metric = "crps_composite"
admissibility_gates = ["g0_integrity", "g1_schema", "g2_cutoff_resource", "g3_domain_semantics"]
[scoring.params]
representation = "samples"
n_draws_min = 200
require_samples = true
tail_levels = [0.01, 0.05, 0.95, 0.99]
joint = "variogram"
[environment]
cpus = 2
memory = "4G"
gpu = false
network = "none"
[text]
source = "invented synthetic release"
path = "text/"
cutoff = "{asof}"
cutoff_checked = true
n_documents = 1
[targets]
asset_ids = {json.dumps(assets)}
horizons = {json.dumps(horizons)}
target_type = "{target}"
target_frequency = "{frequency}"
value_unit = "{unit}"
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("fixture destination must be empty")
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ("daily_return", "monthly_release"):
        root = args.output / name
        (root / "panels").mkdir(parents=True)
        (root / "text").mkdir()
        if name == "daily_return":
            dates = pd.bdate_range("2028-01-03", periods=600)
            asof = dates[-1].date().isoformat()
            assets, horizons, target = ["SYN_MKT", "SYN_HML"], [21, 63], "log_return"
            frames = [pd.DataFrame({"asset": asset, "date": dates,
                                   "value": .0002 + .007 * np.sin(np.arange(len(dates)) * (.7 + i * .13))})
                      for i, asset in enumerate(assets)]
            pd.concat(frames).to_parquet(root / "panels/factors_daily.parquet", index=False)
            text = "Published economic discussion indicates uncertainty about inflation, demand and employment."
            corpus = {"documents": [{"doc_id": "invented-context", "timestamp": asof,
                                      "source": "invented synthetic source", "doc_type": "cb_speech", "file": "context.txt"}]}
            (root / "text/context.txt").write_text(text)
            body = card("synthetic-daily-return", assets, horizons, asof, target, "daily",
                        "decimal cumulative log return", str(uuid.uuid4()))
            body += '''[panels]
panel_ids = ["factors_daily"]
[panels.factors_daily]
frequency = "business_daily"
asset_ids = ["SYN_MKT", "SYN_HML"]
series = ["SYN_MKT", "SYN_HML"]
'''
            spec = {"targets": {"asset_ids": assets, "horizons": horizons, "target_type": target}}
        else:
            dates = pd.date_range("2026-01-01", periods=51, freq="MS")
            asof = "2030-05-12"
            assets, horizons, target = ["CPI_ALL"], [42, 65], "level"
            values = 200 + .4 * np.arange(len(dates)) + .1 * np.sin(np.arange(len(dates)) * .8)
            pd.DataFrame({"asset": "CPI_ALL", "date": dates, "value": values}).to_parquet(
                root / "panels/macro_monthly.parquet", index=False)
            text = ("Transmission of material in this release is embargoed until 8:30 a.m. (ET) May 12, 2030\n"
                    "CONSUMER PRICE INDEX - APRIL 2030\n"
                    "The Consumer Price Index for All Urban Consumers (CPI-U) rose 0.2 percent in April on a "
                    "seasonally adjusted basis, after increasing 0.1 percent in March, the U.S. Bureau of Labor "
                    "Statistics reported today. This is an invented release fixture, not market data.")
            corpus = {"documents": [{"doc_id": "invented-cpi-release", "timestamp": asof,
                                      "source": "BLS", "doc_type": "macro_release", "file": "release.txt"}]}
            (root / "text/release.txt").write_text(text)
            body = card("synthetic-monthly-release", assets, horizons, asof, target, "monthly",
                        "cpi_index_1982_84_100", str(uuid.uuid4()))
            body += '''observation_periods = ["2030-07", "2030-08"]
[panels]
panel_ids = ["macro_monthly"]
[panels.macro_monthly]
frequency = "monthly"
asset_ids = ["CPI_ALL"]
series = ["CPIAUCSL"]
'''
            spec = {"targets": {"asset_ids": assets, "horizons": horizons, "target_type": target,
                                "observation_periods": ["2030-07", "2030-08"]}}
        (root / "card.toml").write_text(body)
        (root / "forecast_spec.json").write_text(json.dumps(spec, indent=2) + "\n")
        (root / "text/corpus_index.json").write_text(json.dumps(corpus, indent=2) + "\n")
    manifest = [{"path": p.relative_to(args.output).as_posix(), "bytes": p.stat().st_size,
                 "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(args.output.rglob("*")) if p.is_file()]
    (args.output / "FIXTURE_MANIFEST.json").write_text(json.dumps({"executive_summary": "Input-only invented fixture hashes.",
                                                                  "files": manifest}, indent=2) + "\n")
    print(json.dumps({"fixture_directories": 2, "files": len(manifest), "future_outcomes": 0}))


if __name__ == "__main__":
    main()
