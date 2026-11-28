# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the
# PolyForm Strict License 1.0.0 and voids all licenses granted to you
# under it immediately and permanently.

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.BrepCodec.Prism.Validation.CheckPrismFrame import CheckPrismFrame
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import KFaceCorners


def predict(frame, new_height_cm):
    old_top = frame.CornersCm[4][2]
    base = frame.CornersCm[0][2]
    if not 0 < new_height_cm or not 0 < old_top - base:
        raise ValueError("Prediction requires a positive cuboid span")

    def move_top(value):
        if value[2] == old_top:
            return value[:2] + (base + new_height_cm,)
        return value

    def move_edge(edge):
        first = frame.CornersCm[edge.StartCorner]
        last = frame.CornersCm[edge.EndCorner]
        curve = edge.Curve
        if first[2] == last[2]:
            return replace(edge, Curve=replace(curve, OriginCm=move_top(curve.OriginCm)))
        if not (
            first[2] == base and last[2] == old_top and edge.LowerParam == 0
            and curve.DirectionCm == (0.0, 0.0, 1.0)
            and curve.LowerBound is None and curve.UpperBound is None
        ):
            raise ValueError("Unmeasured vertical carrier profile")
        return replace(edge, UpperParam=new_height_cm)

    planes = tuple(
        replace(plane, OriginCm=move_top(plane.OriginCm))
        if all(frame.CornersCm[index][2] == old_top for index in corners) else plane
        for plane, corners in zip(frame.Planes, KFaceCorners, strict=True)
    )
    return replace(
        frame, CornersCm=tuple(map(move_top, frame.CornersCm)),
        Edges=tuple(map(move_edge, frame.Edges)), Planes=planes,
    )


def compare(before_path, after_path):
    before_bytes, after_bytes = before_path.read_bytes(), after_path.read_bytes()
    before = ReadDocument(before_bytes)
    after = ReadDocument(after_bytes)
    height_cm = NumberValue(SelectExtrusion(BuildGraph(after)).Along.Fields["value"])
    matches = {}
    for previous, measured in (
        (before.Bodies[0].History, after.Bodies[0].History),
        (before.Snapshots[0].Snapshot, after.Snapshots[0].Snapshot),
    ):
        model = replace(previous.Model, Height=height_cm * 10)
        if measured.Model != model:
            raise ValueError("Native pair changes cuboid dimensions outside the height")
        frame = predict(previous.Frame, height_cm)
        CheckPrismFrame(model, frame)
        matches[type(previous).__name__] = frame == measured.Frame
    return {
        "group": before_path.parent.name,
        "before_sha256": sha256(before_bytes).hexdigest(),
        "after_sha256": sha256(after_bytes).hexdigest(),
        "height_cm": height_cm,
        "exact_frame_matches": matches,
    }


def main():
    parser = argparse.ArgumentParser(description="Check analytic cuboid height frame prediction")
    parser.add_argument("--pair", nargs=2, metavar=("BEFORE", "AFTER"), action="append", required=True, type=Path)
    args = parser.parse_args()
    comparisons = [compare(before, after) for before, after in args.pair]
    print(json.dumps(comparisons, indent=2))
    if not all(all(result["exact_frame_matches"].values()) for result in comparisons):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
