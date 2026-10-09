"""## Executive summary (read this first)
Check observable strategy integration and task-bound as-of validation.
These controls use synthetic inputs and verify behavioral differences.
"""
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import forecast


def test_trusted_asof_accepts_each_official_location_and_validates_date():
    assert forecast.trusted_asof({"forecast": {"asof": "2031-02-14"}}) == "2031-02-14"
    assert forecast.trusted_asof({"provenance": {"data_cutoff": "2031-02-14"}}) == "2031-02-14"
    with pytest.raises(ValueError):
        forecast.trusted_asof({"forecast": {"asof": "2031-99-99"}})
    with pytest.raises(ValueError):
        forecast.trusted_asof({})


def test_release_pool_innovation_subtracts_already_forecast_gap(monkeypatch, tmp_path):
    import release_evidence
    dates = pd.date_range("2028-01-01", periods=36, freq="MS")
    levels = 100 + np.arange(36) * .4 + np.sin(np.arange(36)) * .1
    frame = pd.DataFrame({"date": dates, "asset": "INDEX", "value": levels})
    card = {"task": {"id": "t2-synthetic-release"}, "targets": {
        "asset_ids": ["INDEX"], "horizons": [42, 65], "target_type": "level",
        "observation_periods": ["2031-03", "2031-04"], "value_unit": "index"}}
    monkeypatch.setattr(release_evidence, "infer_release_updates", lambda *a: {
        "INDEX": {"elapsed_months": 1, "observed_change": 2.0, "quote": "synthetic publication"}})
    baseline, base_evidence = forecast.forecast_samples({"macro": frame}, card, "2031-02-14", [], 1000, 31, variant="pool_numeric")
    samples, evidence = forecast.forecast_samples({"macro": frame}, card, "2031-02-14", [], 1000, 31, variant="release_numeric")
    record = evidence["verified_release_updates"]["INDEX"]
    gaussian_drift = (base_evidence["baseline_record"]["mean"][0] - levels[-1]) / 3
    expected = 2 - .5 * (base_evidence["stats"]["INDEX"]["per_step_drift"] + gaussian_drift)
    np.testing.assert_allclose(samples - baseline, expected, atol=1e-13)
    np.testing.assert_allclose(samples.std(axis=0), baseline.std(axis=0), atol=1e-13)
    assert record["applied_shift"] == expected
    forecast.write_outputs(samples, card, "2031-02-14", tmp_path / "forecast.parquet", evidence)
    assert evidence["method"] in (tmp_path / "forecast_meta.json").read_text()
    assert (tmp_path / "forecast_rationale.md").read_text().startswith("## Executive summary (read this first)")
