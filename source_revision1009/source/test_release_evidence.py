"""## Executive summary (read this first)
Challenge released-observation assimilation with stale, misleading and conflicting evidence.
These tests verify timing, series meaning and exact quotations. They do not test forecast
accuracy. All dates and values below are invented fixtures, not competition answers.
"""
from copy import deepcopy
import pandas as pd
import pytest

from release_evidence import infer_release_updates


def fixture(asset="CPI_ALL", end="2030-04-01", last=200., drift=.25):
    code = {"CPI_ALL": "CPIAUCSL", "UNRATE": "UNRATE", "NFP": "PAYEMS"}[asset]
    unit = {"CPI_ALL": "cpi_index_1982_84_100", "UNRATE": "percent (U-3)",
            "NFP": "thousands of jobs"}[asset]
    histories = {asset: pd.Series([last - 1, last - .5, last],
                                 index=[pd.Timestamp(end) - pd.DateOffset(months=i) for i in (2, 1, 0)])}
    stats = {asset: {"mode": "additive_level", "median_calendar_step": 30., "panels": ["macro_monthly"],
                     "last": last, "end": end, "per_step_drift": drift}}
    card = {"targets": {"asset_ids": [asset], "target_type": "level", "value_unit": unit},
            "panels": {"macro_monthly": {"frequency": "monthly", "asset_ids": [asset], "series": [code]}}}
    return histories, stats, card


def cpi(month="June", year=2030, published="2030-07-12", change="0.2", previous="May", previous_change="0.1"):
    return {"doc_id": "invented-release", "timestamp": published, "source": "BLS",
            "doc_type": "macro_release", "text": (
                "Transmission of material in this release is embargoed until 8:30 a.m. (ET) July 12, 2030\n"
                f"CONSUMER PRICE INDEX - {month.upper()} {year}\n"
                f"The Consumer Price Index for All Urban Consumers (CPI-U) rose {change} percent in {month} "
                f"on a seasonally adjusted basis, after increasing {previous_change} percent in {previous}, "
                "the U.S. Bureau of Labor Statistics reported today.")}


def unemployment(value="5.4", month="July", year=2030, published="2030-08-02"):
    return {"doc_id": "invented-jobs", "timestamp": published, "source": "BLS/BEA news release",
            "doc_type": "macro_release", "text": (
                "Transmission of material in this news release is embargoed until 8:30 a.m. (ET) August 2, 2030\n"
                f"THE EMPLOYMENT SITUATION -- {month.upper()} {year}\n"
                f"The unemployment rate rose to {value} percent in {month}, "
                "the U.S. Bureau of Labor Statistics reported today.\n"
                "HOUSEHOLD DATA Summary table A. Household data, seasonally adjusted\n")}


def run(data, docs, asof="2030-08-02"):
    histories, stats, card = data
    return infer_release_updates(histories, stats, docs, asof, card)


def test_contiguous_cpi_changes_do_not_double_count_gap_drift():
    result = run(fixture(), [cpi()])["CPI_ALL"]
    expected_level = 200 * 1.001 * 1.002
    assert result["elapsed_months"] == 2
    assert result["shift"] == pytest.approx(expected_level - 200 - .25 * 2)
    assert result["period"] == "2030-06"
    assert result["approximate_from_rounded_changes"]
    assert result["rounding_level_interval"][0] < expected_level < result["rounding_level_interval"][1]
    assert result["quote"] in cpi()["text"]
    assert result["width_adjustment"] == 1


def test_existing_observation_and_repeated_documents_do_not_move_anchor():
    assert run(fixture(end="2030-06-01"), [cpi(), cpi()]) == {}
    original = run(fixture(), [cpi()])
    assert run(fixture(), [cpi(), cpi()]) == original


def test_missing_month_cannot_be_filled_by_a_later_growth_rate():
    assert run(fixture(end="2030-03-01"), [cpi()]) == {}


def test_foreign_and_core_cpi_are_not_the_headline_national_series():
    doc = cpi()
    doc["text"] = doc["text"].replace("for All Urban Consumers (CPI-U)", "for all items less food and energy")
    assert run(fixture(), [doc]) == {}
    doc = cpi()
    doc["text"] = doc["text"].replace("U.S. Bureau of Labor Statistics", "Canadian statistics agency")
    assert run(fixture(), [doc]) == {}


def test_nonseasonal_cpi_and_annual_growth_are_not_monthly_sa_changes():
    for replacement in ["on a not seasonally adjusted basis", "over the last 12 months"]:
        doc = cpi()
        doc["text"] = doc["text"].replace("on a seasonally adjusted basis", replacement)
        assert run(fixture(), [doc]) == {}


def test_index_series_and_units_are_bound_to_card_not_doc_id():
    data = fixture()
    data[2]["panels"]["macro_monthly"]["series"] = ["CPIAUCNS"]
    assert run(data, [cpi()]) == {}
    data = fixture()
    data[2]["targets"]["value_unit"] = "year on year percent"
    assert run(data, [cpi()]) == {}


def test_document_identity_does_not_create_numeric_signal():
    doc = cpi()
    doc["doc_id"] = "any renamed arbitrary identity"
    assert run(fixture(), [doc])["CPI_ALL"]["shift"] == run(fixture(), [cpi()])["CPI_ALL"]["shift"]
    doc["text"] = "No release evidence."
    assert run(fixture(), [doc]) == {}


@pytest.mark.parametrize("field,value", [("timestamp", "2031-01-01"), ("source", "Fed speech"),
                                        ("doc_type", "cb_speech"), ("source", "")])
def test_future_or_untrusted_evidence_is_ignored(field, value):
    doc = cpi()
    doc[field] = value
    assert run(fixture(), [doc]) == {}


def test_embargo_and_index_timestamp_must_agree():
    doc = cpi()
    doc["timestamp"] = "2030-07-11"
    assert run(fixture(), [doc]) == {}


def test_reissued_text_is_refused_even_if_numeric_sentence_is_plausible():
    doc = cpi()
    doc["text"] += "\nNOTE: This news release was reissued on September 1, 2030 correcting the following sentence."
    assert run(fixture(), [doc]) == {}


def test_conflicting_same_month_values_refuse_whole_asset():
    alternative = cpi(change="0.7")
    alternative["doc_id"] = "alternative"
    assert run(fixture(), [cpi(), alternative]) == {}


def test_unemployment_national_sa_level_bridges_gap_without_added_future_trend():
    data = fixture("UNRATE", last=4.5, drift=.1)
    result = run(data, [unemployment()])["UNRATE"]
    assert result["elapsed_months"] == 3
    assert result["shift"] == pytest.approx(5.4 - 4.5 - .1 * 3)
    assert not result["approximate_from_rounded_changes"]
    assert result["seasonal_adjustment"] == "seasonally adjusted"


def test_subgroup_and_nonseasonal_unemployment_are_refused():
    for old, new in [("The unemployment rate", "The unemployment rate for teenagers"),
                     ("Household data, seasonally adjusted", "Household data, not seasonally adjusted")]:
        doc = unemployment()
        doc["text"] = doc["text"].replace(old, new)
        assert run(fixture("UNRATE", last=4.5), [doc]) == {}


def test_sa_summary_cannot_override_explicit_unadjusted_headline():
    doc = unemployment()
    doc["text"] = doc["text"].replace("percent in July,", "percent in July, not seasonally adjusted,")
    assert run(fixture("UNRATE", last=4.5), [doc]) == {}


def test_december_to_january_continuity_uses_explicit_header_year():
    doc = cpi(month="January", year=2031, change="0.3", previous="December", previous_change="0.4")
    doc["timestamp"] = "2031-02-12"
    doc["text"] = doc["text"].replace("July 12, 2030", "February 12, 2031")
    result = run(fixture(end="2030-11-01"), [doc], asof="2031-02-12")["CPI_ALL"]
    assert result["period"] == "2031-01"
    assert [f["period"] for f in result["evidence"]] == ["2030-12", "2031-01"]


def test_declining_price_change_is_signed_correctly():
    doc = cpi()
    doc["text"] = doc["text"].replace("rose 0.2", "fell 0.2")
    result = run(fixture(), [doc])["CPI_ALL"]
    assert result["observed_level"] == pytest.approx(200 * 1.001 * .998)


def test_unemployment_unchanged_at_level_is_accepted():
    doc = unemployment()
    doc["text"] = doc["text"].replace("rose to", "remained unchanged at")
    assert run(fixture("UNRATE", last=4.5), [doc])["UNRATE"]["observed_level"] == 5.4


def test_nfp_change_cannot_be_added_to_unproved_panel_vintage():
    doc = unemployment()
    doc["text"] += " Total nonfarm payroll employment rose by 100,000."
    assert run(fixture("NFP", last=150000), [doc]) == {}


def test_incorrect_panel_endpoint_or_daily_cadence_refuses_update():
    data = fixture()
    data[1]["CPI_ALL"]["end"] = "2030-03-01"
    assert run(data, [cpi()]) == {}
    data = fixture()
    data[1]["CPI_ALL"]["median_calendar_step"] = 1
    assert run(data, [cpi()]) == {}


def test_input_objects_are_unchanged():
    data, docs = fixture(), [cpi()]
    card_before, docs_before = deepcopy(data[2]), deepcopy(docs)
    history_before = data[0]["CPI_ALL"].copy()
    run(data, docs)
    assert data[2] == card_before and docs == docs_before
    pd.testing.assert_series_equal(data[0]["CPI_ALL"], history_before)
