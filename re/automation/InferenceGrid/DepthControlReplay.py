# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import defaultdict
import hashlib
import math
import struct

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.ParseDisplay import (
    KInformationStream,
    ParseDisplay,
)
from InferenceGrid.SolidWorksDimensionEvidence import capture_sets, dimensions
from InferenceGrid.SolidWorksExtrusionDepths import extrusion_records
from InferenceGrid.SolidWorksFieldDiscovery import (
    discovery_inventory,
    records,
    single_dimension_change,
)
from InferenceInputs import read_file


def replay_depth_edit(root, source, stall, experiment):
    recipe, parameter = {
        "vary blind boss depth": ("P03", "depth_mm"),
        "vary blind cut depth": ("P04", "cut_depth_mm"),
    }[experiment]
    result = {
        "controlled_change": experiment,
        "source_sha256": stall["source_sha256"],
        "status": "missing_discovery_control",
        "comparisons": [],
        "target_matches": [],
    }
    raw = read_file(source, 128 * 1024 * 1024)
    if hashlib.sha256(raw).hexdigest() != stall["source_sha256"]:
        return {**result, "status": "source_changed"}
    streams = SldprtArchive.FromBytes(raw).Streams
    configs, features = ParseKeywords(streams["swXmlContents/KeyWords"])
    if len(configs) != 1:
        return {**result, "status": "unsupported_configuration"}
    stream = "Contents/Config-" + str(configs[0].configuration_id) + "-ResolvedFeatures"
    target = streams[stream]
    sets = capture_sets(root)
    eligible = discovery_inventory(root, sets)
    result["stream"] = stream
    wanted = {"Extrusion": {("Extrusion", parameter, "length")}}
    signatures = []
    for folder, receipt, report, files in sets:
        if receipt["recipe_id"] != recipe:
            continue
        baseline = next(
            (name for name in files if name.endswith("-baseline-a.SLDPRT")), None
        )
        for edit in report["observations"]["edits"]:
            if edit["parameter"] != parameter:
                continue
            names = (baseline, edit["saved_file"])
            if any(name not in files for name in names):
                continue
            saves = []
            for name in names:
                pin = files[name]["sha256"]
                if pin not in eligible or pin == stall["source_sha256"]:
                    break
                control = read_file(eligible[pin], 16 * 1024 * 1024)
                if hashlib.sha256(control).hexdigest() != pin:
                    break
                saved = records(SldprtArchive.FromBytes(control).Streams, wanted)
                opened = report["observations"].get("reopened_files", {}).get(name, {})
                if (
                    not saved
                    or saved[1] == target
                    or opened.get("open_status") != {"errors": 0, "warnings": 0}
                ):
                    break
                saves.append((saved, dimensions(opened)))
            if len(saves) != 2 or saves[0][0][1] == saves[1][0][1]:
                continue
            changed = single_dimension_change(saves[0][0], saves[1][0])
            if not changed or changed["key"] != ("Extrusion", parameter, "length"):
                continue
            owner = next(
                name
                for ident, _, name in saves[0][0][4]
                if ident == changed["feature_id"]
            )
            if any(
                len(values := [v for f, n, v in oracle if (f, n) == (owner, parameter)])
                != 1
                or not math.isclose(
                    values[0], changed[side + "_value"], rel_tol=1e-12, abs_tol=1e-14
                )
                for (_, oracle), side in zip(saves, ("input", "control"))
            ):
                continue
            signatures.append(set(changed["matching_copies"]))
            result["comparisons"].append(
                {
                    **changed,
                    "save_sha256": [files[name]["sha256"] for name in names],
                    "reopen_measurements_sha256": receipt["measurement_receipt_sha256"],
                }
            )
    if not signatures:
        return result
    copies = sorted(set.intersection(*signatures))
    if len(copies) < 2 or any(b[0] - a[0] < 8 for a, b in zip(copies, copies[1:])):
        return {**result, "status": "no_discriminating_copies"}
    intervals, scalars = extrusion_records(target, features)
    display = ParseDisplay(streams.get(KInformationStream, b""))
    scale = {"mm": 0.001, "in": 0.0254}.get(display.UnitName) if display else None
    if scale is None:
        return {**result, "status": "unsupported_display_unit"}
    result["searched_fields"] = []
    fields = {(row["feature_id"], row["parameter"]) for row in stall["targets"]}
    by_name = defaultdict(list)
    for scalar in scalars:
        by_name[scalar.name].append(scalar)
    for feature, start, end in intervals:
        if len(feature.dimensions) != 1:
            continue
        dim = feature.dimensions[0]
        if dim.kind != "length" or (feature.object_id, dim.name) not in fields:
            continue
        if dim.value_mm is None or not math.isfinite(dim.value_mm):
            continue
        result["searched_fields"].append(
            {"feature_id": feature.object_id, "field": dim.name}
        )
        for scalar in by_name[dim.name]:
            pos = scalar.value_offset
            if (
                not start <= pos < end
                or pos + copies[-1][0] + 8 > end
                or not 0 < scalar.value < math.inf
            ):
                continue
            if not math.isclose(
                scalar.value, dim.value_mm * scale, rel_tol=1e-12, abs_tol=1e-14
            ):
                continue
            if all(
                target[pos + off : pos + off + 8]
                == struct.pack("<d", scalar.value * sign)
                for off, sign in copies
            ):
                result["target_matches"].append(
                    {
                        "feature_id": feature.object_id,
                        "field": dim.name,
                        "offset": pos,
                        "value": scalar.value,
                    }
                )
    return {
        **result,
        "status": (
            "candidate_correspondence"
            if result["target_matches"]
            else (
                "no_target_match"
                if result["searched_fields"]
                else "no_applicable_field"
            )
        ),
    }
