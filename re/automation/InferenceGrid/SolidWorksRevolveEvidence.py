# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import defaultdict
import math
import struct

from convert.adapters.solidworks.Resolved.Core import KAngleCopyDeltas, LocateFeatures
from InferenceGrid.SolidWorksFieldDiscovery import native_parameter_matches


def revolve_angles(data, stream, document, keyed_rows, projected):
    steps = defaultdict(list)
    for step in document.get("feature_timeline", {}).get("$tuple", []):
        steps[step["attributes"].get("native_object_id")].append(step)
    targets = {}
    for (owner, name), rows in keyed_rows.items():
        if (
            name != "D1"
            or len(rows) != 1
            or rows[0]["status"] != "ambiguous"
            or len(steps[owner]) != 1
        ):
            continue
        step = steps[owner][0]
        if (step.get("definition") or {}).get("$type") == "RevolutionFeature":
            targets[owner] = rows[0], step
    if not targets:
        return
    layouts = defaultdict(list)
    for layout in LocateFeatures(data):
        if layout.feature_id in targets and layout.is_revolution:
            layouts[layout.feature_id].append(layout)
    for owner, (row, step) in targets.items():
        if len(layouts[owner]) != 1:
            continue
        layout = layouts[owner][0]
        attrs = step["attributes"]
        params = projected.get((owner, row["name"]), [])
        spans = [
            s
            for s in step["provenance"]["spans"]["$tuple"]
            if s["stream"] == stream and s["record_kind"] == "feature-record"
        ]
        if len(params) != 1 or len(spans) != 1 or layout.name != row["feature"]:
            continue
        span = spans[0]
        start, end = span["offset"], span["offset"] + span["length"]
        axis, spec, scalar = (
            layout.axis_offset,
            layout.end_spec_offset,
            layout.angle_offset,
        )
        copies = layout.angle_copy_offsets
        if (
            None in (axis, spec, scalar)
            or len(copies) != len(KAngleCopyDeltas)
            or not start <= axis < axis + 4 <= spec < scalar
            or copies[-1] + 8 > end
            or end > len(data)
            or (stream, scalar) not in row["candidate_locations"]
            or len(steps[layout.axis_feature_id]) != 1
        ):
            continue
        axis_id = struct.unpack_from("<I", data, axis)[0]
        if (
            axis_id != attrs.get("axis_source_id")
            or axis_id != layout.axis_feature_id
            or attrs.get("axis_source_offset") != axis
            or attrs.get("end_spec_offset") != spec
        ):
            continue
        word = data[scalar : scalar + 8]
        if any(data[pos : pos + 8] != word for pos in copies):
            continue
        angle = struct.unpack("<d", word)[0]
        value = step["definition"]["angle"]
        if (
            not math.isfinite(angle)
            or angle == 0
            or value["unit"] != "deg"
            or not math.isclose(value["value"], math.degrees(angle), rel_tol=1e-12)
            or not native_parameter_matches(
                params[0],
                {
                    "key": (attrs["native_type"], row["name"], "angle"),
                    "stream": stream,
                    "scalar_offset": scalar,
                    "native_value": angle,
                },
            )
        ):
            continue
        yield row, {
            "verified_location": (stream, scalar),
            "copy_offsets": list(copies[1:]),
            "axis_id": axis_id,
            "axis_offset": axis,
            "end_spec_offset": spec,
            "angle_radians": angle,
        }
