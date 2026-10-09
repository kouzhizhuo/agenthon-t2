"""## Executive summary (read this first)
Use verified, already published US macro observations that are absent from a lagged panel.
This module reads no files, calls no model, and forecasts no future release. It accepts
only national seasonally adjusted headline CPI changes and U-3 unemployment levels.
It returns auditable anchor innovations for a caller to apply to whole joint draws.
Rounded CPI changes imply an approximate level, not an exact published index value.
"""
from __future__ import annotations

from datetime import date
import math
import re
from typing import Any, Mapping

_MONTHS = {name.lower(): i for i, name in enumerate(
    ("January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"), 1)}
_MONTH = "(?:" + "|".join(_MONTHS) + ")"
_NUMBER = r"(?:\d+(?:\.\d+)?)"
_CORRECTION = re.compile(
    r"(?:\b(?:corrected|correction|erratum|reissued)\b|news\s+release\s+was\s+(?:reissued|corrected)|"
    r"this\s+(?:news\s+)?release\s+(?:has\s+been|was)\s+(?:corrected|reissued)|"
    r"(?:correction|erratum)\s*[:\-]|reissued\s+on|"
    r"correcting\s+(?:the|a)\s+(?:following\s+)?(?:sentence|table|figure))", re.I)


def _ordinal(period: str) -> int:
    parsed = date.fromisoformat(period + "-01")
    return parsed.year * 12 + parsed.month - 1


def _period_label(ordinal: int) -> str:
    year, month = divmod(ordinal, 12)
    return f"{year:04d}-{month + 1:02d}"


def _declared_series(asset: str, stat: Mapping[str, Any], card: Mapping[str, Any]) -> str | None:
    targets = card.get("targets", {})
    if targets.get("target_type", "level") != "level":
        return None
    if asset not in targets.get("asset_ids", []):
        return None
    if stat.get("mode") != "additive_level" or float(stat.get("median_calendar_step", 0)) <= 20:
        return None
    unit = str(targets.get("value_unit", "")).lower()
    required = {"CPI_ALL": "CPIAUCSL", "UNRATE": "UNRATE"}.get(asset)
    if required is None:
        return None  # PAYEMS changes cannot be added across unproved panel vintages.
    if asset == "CPI_ALL" and not ("index" in unit and "1982" in unit and "100" in unit):
        return None
    if asset == "UNRATE" and not ("percent" in unit and "u-3" in unit):
        return None
    for name in stat.get("panels", []):
        panel = card.get("panels", {}).get(name, {})
        if (panel.get("frequency") == "monthly" and asset in panel.get("asset_ids", [])
                and required in panel.get("series", [])):
            # The official FRED series code specifies seasonal adjustment. An explicit
            # conflicting declaration must not be overridden by that code.
            seasonal = str(panel.get("seasonal_adjustment", "seasonally adjusted")).lower()
            if seasonal in {"seasonally adjusted", "sa"}:
                return required
    return None


def _release(doc: Mapping[str, Any], cutoff: date) -> tuple[str, date] | None:
    if doc.get("doc_type") != "macro_release":
        return None
    source = str(doc.get("source", "")).lower()
    if not (source == "bls" or "bureau of labor statistics" in source or "bls/" in source):
        return None
    try:
        stamp = date.fromisoformat(str(doc.get("timestamp", ""))[:10])
    except ValueError:
        return None
    text = doc.get("text")
    if stamp > cutoff or not isinstance(text, str) or _CORRECTION.search(text):
        return None
    embargo = re.search(r"Transmission\s+of\s+material.{0,160}?embargoed\s+until(.{0,250})",
                        text, re.I | re.S)
    if not embargo:
        return None
    publication = re.search(rf"({_MONTH})\s+(\d{{1,2}}),?\s+(\d{{4}})",
                            embargo.group(1), re.I)
    if not publication:
        return None
    try:
        parsed = date(int(publication[3]), _MONTHS[publication[1].lower()], int(publication[2]))
    except ValueError:
        return None
    if parsed != stamp:
        return None
    return text, stamp


def _facts(doc: Mapping[str, Any], cutoff: date, series: str) -> list[dict[str, Any]]:
    accepted = _release(doc, cutoff)
    if accepted is None:
        return []
    text, stamp = accepted
    title = "CONSUMER\\s+PRICE\\s+INDEX" if series == "CPIAUCSL" else "THE\\s+EMPLOYMENT\\s+SITUATION"
    header = re.search(rf"{title}[^a-z0-9]{{1,12}}({_MONTH})\s+(\d{{4}})", text, re.I)
    if not header:
        return []
    month, year = _MONTHS[header[1].lower()], int(header[2])
    period = f"{year:04d}-{month:02d}"
    if _ordinal(period) > _ordinal(stamp.strftime("%Y-%m")):
        return []
    body = text[header.end():header.end() + 1800]
    # Require the national release attribution near the headline, rather than
    # applying a subgroup or local table value to the national target.
    if not re.search(r"U\.S\.\s+Bureau\s+of\s+Labor\s+Statistics", body, re.I):
        return []
    base = {"period": period, "publication_date": stamp.isoformat(),
            "doc_id": str(doc.get("doc_id", "")), "doc_sha256": doc.get("sha256"),
            "source": doc["source"], "doc_type": doc["doc_type"], "series": series,
            "seasonal_adjustment": "seasonally adjusted"}
    if series == "CPIAUCSL":
        pattern = (rf"The\s+Consumer\s+Price\s+Index\s+for\s+All\s+Urban\s+Consumers\s*"
                   rf"\(CPI-U\)\s+(increased|rose|decreased|fell|declined)\s+({_NUMBER})\s+percent"
                   rf"\s+in\s+({_MONTH})\s+on\s+a\s+seasonally\s+adjusted\s+basis"
                   rf"(?:,?\s+after\s+(increasing|rising|decreasing|falling|declining)\s+"
                   rf"({_NUMBER})\s+percent\s+in\s+({_MONTH}))?")
        match = re.search(pattern, body, re.I)
        if not match or _MONTHS[match[3].lower()] != month:
            return []
        facts = []
        for ordinal, direction, number in [(_ordinal(period), match[1], match[2])]:
            sign = -1 if direction.lower() in {"decreased", "fell", "declined"} else 1
            digits = len(number.partition(".")[2])
            facts.append({**base, "period": _period_label(ordinal), "kind": "monthly_change_percent",
                          "value": sign * float(number), "rounding_half_width_percent": .5 * 10 ** -digits,
                          "quote": match[0], "quote_header": header[0]})
        if match[4] and _MONTHS[match[6].lower()] == ((_ordinal(period) - 1) % 12 + 1):
            sign = -1 if match[4].lower() in {"decreasing", "falling", "declining"} else 1
            digits = len(match[5].partition(".")[2])
            facts.append({**base, "period": _period_label(_ordinal(period) - 1),
                          "kind": "monthly_change_percent", "value": sign * float(match[5]),
                          "rounding_half_width_percent": .5 * 10 ** -digits,
                          "quote": match[0], "quote_header": header[0]})
        return facts
    pattern = (rf"The\s+unemployment\s+rate\s+(?:rose|increased|fell|declined|decreased|"
               rf"was|remained|held|stayed)(?:\s+unchanged)?(?:\s+(?:at|to))?\s+({_NUMBER})"
               rf"\s+percent\s+in\s+({_MONTH})")
    match = re.search(pattern, body, re.I)
    seasonal = re.search(r"HOUSEHOLD\s+DATA\s+Summary\s+table\s+A\.\s+Household\s+data,\s+seasonally\s+adjusted",
                         text, re.I)
    if not match or not seasonal or _MONTHS[match[2].lower()] != month:
        return []
    trailing_sentence = re.split(r"[.!?]", body[match.end():match.end() + 300], maxsplit=1)[0]
    if re.search(r"not\s+seasonally\s+adjusted|unadjusted", trailing_sentence, re.I):
        return []
    value = float(match[1])
    if not 0 <= value <= 100:
        return []
    return [{**base, "kind": "level_percent", "value": value, "quote": match[0],
             "quote_header": header[0], "seasonal_quote": seasonal[0]}]


def infer_release_updates(histories: Mapping[str, Any], stats: Mapping[str, Any],
                          docs: list[Mapping[str, Any]], asof: str,
                          card: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Return observed anchor innovations; caller keeps the original forecast spread.

    ``shift = released_level - panel_last - per_step_drift * elapsed_months``
    removes the gap trend already forecast by that numerical component. The result
    also provides ``observed_change`` and ``elapsed_months`` so a pooled caller can
    subtract its pooled gap drift instead. Every target period must still be after
    the new anchor; the caller resolves this with the official monthly contract.
    """
    try:
        cutoff = date.fromisoformat(asof)
    except ValueError:
        return {}
    updates = {}
    for asset, stat in stats.items():
        series = _declared_series(asset, stat, card)
        if not series or asset not in histories:
            continue
        history = histories[asset]
        try:
            last_date = date.fromisoformat(str(stat["end"])[:10])
            last = float(history.iloc[-1])
            drift = float(stat["per_step_drift"])
            history_last_date = date.fromisoformat(str(history.index[-1])[:10])
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
        if history_last_date != last_date or last_date > cutoff or not (math.isfinite(last) and math.isfinite(drift)):
            continue
        try:
            recorded_last = float(stat.get("last", last))
        except (ValueError, TypeError):
            continue
        if not math.isclose(last, recorded_last, rel_tol=0, abs_tol=0):
            continue
        anchor = _ordinal(last_date.strftime("%Y-%m"))
        collected: dict[int, list[dict[str, Any]]] = {}
        for doc in docs:
            for fact in _facts(doc, cutoff, series):
                step = _ordinal(fact["period"])
                if step > anchor:
                    collected.setdefault(step, []).append(fact)
        if not collected:
            continue
        # Conflicting supplied observations are evidence ambiguity, not a reason
        # to select whichever release is closer to a desired forecast.
        if any(len({(f["kind"], f["value"]) for f in facts}) != 1
               for facts in collected.values()):
            continue
        selected = {p: sorted(fs, key=lambda f: (f["publication_date"], f["doc_id"]))[0]
                    for p, fs in collected.items()}
        if series == "UNRATE":
            newest = max(selected)
            evidence = [selected[newest]]
            level = evidence[0]["value"]
            lower = upper = level
            approximate = False
        else:
            # A rounded monthly percentage is relative to the previous month's
            # SA index. Missing intervening months cannot be interpolated.
            newest, level, lower, upper, evidence = anchor, last, last, last, []
            if last <= 0:
                continue
            while newest + 1 in selected:
                fact = selected[newest + 1]
                value, radius = fact["value"], fact["rounding_half_width_percent"]
                if value - radius <= -100:
                    break
                level *= 1 + value / 100
                lower *= 1 + (value - radius) / 100
                upper *= 1 + (value + radius) / 100
                evidence.append(fact)
                newest += 1
            if not evidence:
                continue
            approximate = True
        elapsed = newest - anchor
        change = level - last
        updates[asset] = {"shift": change - drift * elapsed,
                          "observed_change": change, "elapsed_months": elapsed,
                          "panel_anchor_period": _period_label(anchor),
                          "period": _period_label(newest), "observed_level": level,
                          "approximate_from_rounded_changes": approximate,
                          "rounding_level_interval": [lower, upper],
                          "unit": "index 1982-84=100" if series == "CPIAUCSL" else "percent U-3",
                          "series": series, "seasonal_adjustment": "seasonally adjusted",
                          "doc_id": evidence[-1]["doc_id"], "quote": evidence[-1]["quote"],
                          "evidence": evidence, "future_observation_predicted": False,
                          "width_adjustment": 1.0,
                          "vintage_limit": "as-published text versus supplied panel snapshot; future revisions remain unknown"}
    return updates
