# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
import math

from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.ParseDisplay import KInformationStream, ParseDisplay


def keyword_evidence(streams, discovered, document):
    data = streams.get("swXmlContents/KeyWords")
    if not data:
        return {"status": "no_keyword_stream"}
    try:
        configs, features = ParseKeywords(data)
    except ValueError as error:
        return {"status": "keyword_refusal", "reason": str(error)[:256]}
    display = ParseDisplay(streams.get(KInformationStream, b""))
    if len(configs) != 1 or not display:
        return {"status": "unresolved_configuration_or_display"}
    base = "Contents/Config-" + str(configs[0].configuration_id)
    owner_ids = {f["id"]: f["attributes"].get("native_object_id") for f in document.get("feature_timeline", {}).get("$tuple", [])}
    projected = {}
    for param in document.get("parameters", {}).get("$tuple", []):
        projected.setdefault((owner_ids.get(param.get("owner_id")), param["name"]), []).append(param)
    rows, uses = [], Counter()
    budget = 2_000_000
    for feature in features:
        for dim in feature.dimensions:
            if dim.value_mm is None or not math.isfinite(dim.value_mm):
                continue
            candidates = discovered.get(dim.name, [])
            budget -= len(candidates) + 1
            if budget < 0:
                return {"status": "comparison_budget_exhausted"}
            if dim.kind == "angle":
                expected, tolerance = math.radians(dim.value_mm), 1e-12
            else:
                unit = {"mm": 0.001, "in": 0.0254}.get(display.UnitName)
                if unit is None:
                    continue
                expected = dim.value_mm * unit
                tolerance = 0.5 * unit * 10 ** -display.Decimals
            matches = [(r["stream"], r["offset"]) for r in candidates
                       if r["stream"] in (base, base + "-ResolvedFeatures") and
                       math.isclose(r["system_value"], expected, rel_tol=1e-12, abs_tol=tolerance)]
            uses.update(matches)
            rows.append({"feature_id": feature.object_id, "feature": feature.name, "name": dim.name,
                         "display_text": dim.source_text, "candidate_locations": matches})
    counts = Counter()
    for row in rows:
        locations = row["candidate_locations"]
        if not locations:
            status = "no_matching_record"
        elif len(locations) != 1 or uses[locations[0]] != 1:
            status = "ambiguous"
        else:
            status = "unique_cross_stream_match"
            params = projected.get((row["feature_id"], row["name"]), [])
            if len(params) == 1:
                row["reader_span_matches"] = any(
                    (s["stream"], s["offset"]) == locations[0] and s["length"] == 8 and s.get("record_kind") == "dimension-scalar"
                    for s in params[0].get("provenance", {}).get("spans", {}).get("$tuple", []))
        row["status"] = status
        counts[status] += 1
    return {"status": "compared", "configuration_id": configs[0].configuration_id,
            "display_unit": display.UnitName, "counts": counts, "dimensions": rows}
