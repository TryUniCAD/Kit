"""Emit Kit-authored feature documents that mirror the native controls.

Run with Python 3.14 (ZIP method 93) from the repository root:
    /opt/homebrew/bin/python3.14 -I re/Fusion/Reconstruction/FeatureAuthoring/EmitAuthored.py [Case ...]

Cuboid cases start from the CaptureControls.py base part: a 40 x 30 mm
rectangle at the origin extruded 20 mm through the cuboid writer. Part cases
author every body from independent sketch profiles through ExtrudeSpec.
Every dimension matches its native control so the acceptance run can compare
geometry directly. Passing case names emits only those cases and merges them
into the existing manifest.
"""

import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.dont_write_bytecode = True

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import ChamferSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import CircleCurve  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import ExtrudeSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import FilletSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import LineCurve  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import PatternSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import CircularSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import MirrorSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import PlaneSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SolidMass import SolidMass  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import BuildShape  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart  # noqa: E402

OUTPUT = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Authored"


def rect(x0, y0, x1, y1):
    return (
        LineCurve((x0, y0), (x1, y0)),
        LineCurve((x1, y0), (x1, y1)),
        LineCurve((x1, y1), (x0, y1)),
        LineCurve((x0, y1), (x0, y0)),
    )


def slot(x0, y0, x1, r):
    return (
        LineCurve((x0, y0 - r), (x1, y0 - r)),
        ArcCurve((x1, y0), r, -90.0, 180.0),
        LineCurve((x1, y0 + r), (x0, y0 + r)),
        ArcCurve((x0, y0), r, 90.0, 180.0),
    )


CONCAVE = (
    LineCurve((0, 0), (40, 0)),
    LineCurve((40, 0), (40, 30)),
    LineCurve((40, 30), (30, 30)),
    ArcCurve((20, 30), 10, 180.0, 180.0),
    LineCurve((10, 30), (0, 30)),
    LineCurve((0, 30), (0, 0)),
)


def base(name="Base extrude", extent="one", against=0.0):
    return ExtrudeSpec(rect(0, 0, 40, 30), 20.0, "new", extent, against, "Base sketch", name)


POCKET = ExtrudeSpec((CircleCurve((8, 8), 3),), 20.0, "cut", "one", 0.0, "Pocket sketch", "Pocket extrude")


def hole(radius, distance, operation, name, extent="one"):
    return ExtrudeSpec((CircleCurve((20, 15), radius),), distance, operation, extent, 0.0, name + " sketch", name)


CUBOID = {
    "Fillet": (FilletSpec((40.0, 30.0), 3.0),),
    "Chamfer": (ChamferSpec((40.0, 30.0), 3.0),),
    "Shell": (ShellSpec(2.0),),
    "FilletShell": (FilletSpec((40.0, 30.0), 3.0), ShellSpec(2.0)),
    "MultiFeature": (
        FilletSpec((40.0, 30.0), 3.0, "Corner Round"),
        ChamferSpec((0.0, 0.0), 3.0, "Corner Bevel"),
        FilletSpec((40.0, 0.0), 4.0),
        ShellSpec(2.0, "Hollow"),
    ),
}

PART = {
    "ExtrudeNew": (base(),),
    "ExtrudeSymmetric": (base(extent="symmetric"),),
    "ExtrudeTwoSided": (base(extent="two", against=5.0),),
    "ExtrudeFlip": (base(extent="flip"),),
    "ProfileSlot": (ExtrudeSpec(slot(10, 10, 30, 10), 20.0, "new", "one", 0.0, "Slot sketch", "Slot extrude"),),
    "ProfileConcave": (ExtrudeSpec(CONCAVE, 20.0, "new", "one", 0.0, "Notch sketch", "Notch extrude"),),
    "ProfileCircle": (ExtrudeSpec((CircleCurve((20, 15), 10),), 20.0, "new", "one", 0.0, "Disc sketch", "Disc extrude"),),
    "ExtrudeJoin": (base(), hole(5, 30, "join", "Boss")),
    "ExtrudeCut": (base(), hole(5, 20, "cut", "Hole")),
    "ExtrudeIntersect": (base(), hole(10, 20, "intersect", "Core")),
    "ExtrudeBlindCut": (base(), hole(5, 10, "cut", "Pocket")),
    "ExtrudeSlotCut": (base(), ExtrudeSpec(slot(15, 15, 25, 5), 20.0, "cut", "one", 0.0, "Slot sketch", "Slot extrude")),
    "ExtrudeSymmetricCut": (base(), hole(5, 20, "cut", "Pocket", "symmetric")),
    "PartCutFillet": (
        base(),
        ExtrudeSpec(slot(15, 15, 25, 5), 20.0, "cut", "one", 0.0, "Slot sketch", "Slot extrude"),
        FilletSpec((40.0, 30.0), 3.0, "Corner Round"),
        ChamferSpec((0.0, 0.0), 2.0, "Corner Bevel"),
    ),
    "PartConcaveShell": (
        ExtrudeSpec(CONCAVE, 20.0, "new", "one", 0.0, "Notch sketch", "Notch extrude"),
        FilletSpec((40.0, 0.0), 4.0, "Corner Round"),
        ShellSpec(2.0, "Hollow"),
    ),
    "HoleFlat": (base(), HoleSpec((20.0, 15.0), 8.0, 10.0, FeatureName="Top hole")),
    "HoleThrough": (base(), HoleSpec((20.0, 15.0), 8.0, FeatureName="Top hole")),
    "HoleCounterboreFlat": (base(), HoleSpec((20.0, 15.0), 6.0, 10.0, 10.0, 4.0, "Top hole")),
    "HoleCounterbore": (base(), HoleSpec((20.0, 15.0), 6.0, 0.0, 10.0, 4.0, "Top hole")),
    "RectPattern": (base(), POCKET, PatternSpec(1, 3, 12.0, 2, 14.0, "Pocket grid")),
    "FeatureCircPattern": (base(), POCKET, CircularSpec(1, 2, 40.0, "Pocket arc")),
    "MirrorFeature": (base(), POCKET, PlaneSpec(20.0, "yz", "Mid plane"), MirrorSpec(1, 2, "Pocket mirror")),
    "PlaneOffset": (base(), PlaneSpec(15.0, "xy", "Offset plane")),
    "HoleGrid": (base(), HoleSpec((8.0, 8.0), 5.0, 10.0, FeatureName="Corner hole"), PatternSpec(1, 3, 12.0, 2, 14.0, "Hole grid")),
    "MultiPocketPart": (
        base(),
        ExtrudeSpec(slot(10, 22, 14, 3), 8.0, "cut", "one", 0.0, "Slot sketch", "Slot pocket"),
        HoleSpec((8.0, 8.0), 4.0, FeatureName="Corner hole"),
        PatternSpec(2, 2, 12.0, 1, 10.0, "Hole row"),
        FilletSpec((40.0, 30.0), 3.0, "Corner Round"),
        PlaneSpec(20.0, "yz", "Mid plane"),
        MirrorSpec(1, 5, "Slot mirror"),
    ),
    "MultiDiscPart": (
        ExtrudeSpec((CircleCurve((0, 0), 20),), 12.0, "new", "one", 0.0, "Disc sketch", "Disc extrude"),
        ExtrudeSpec((CircleCurve((12, 0), 3),), 6.0, "cut", "one", 0.0, "Pocket sketch", "Pocket extrude"),
        CircularSpec(1, 4, 360.0, "Pocket ring"),
        HoleSpec((0.0, 0.0), 8.0, 0.0, 14.0, 4.0, "Center bore"),
    ),
}

CASES = {**CUBOID, **PART}

EDITS = {
    "Fillet": [{"feature": "Fillet", "expression": "4 mm"}],
    "Chamfer": [{"feature": "Chamfer", "expression": "2 mm"}],
    "Shell": [{"feature": "Shell", "expression": "3 mm"}],
    "FilletShell": [{"feature": "Shell", "expression": "1.5 mm"}, {"feature": "height", "expression": "25 mm"}],
    "MultiFeature": [{"feature": "Corner Round", "expression": "5 mm"}, {"feature": "height", "expression": "25 mm"}],
    "ExtrudeNew": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "ExtrudeSymmetric": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "16 mm"}],
    "ExtrudeTwoSided": [{"feature": "Base extrude", "role": "AgainstDistance", "expression": "8 mm"}],
    "ExtrudeFlip": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "-12 mm"}],
    "ProfileSlot": [{"feature": "Slot extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "ProfileConcave": [{"feature": "Notch extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "ProfileCircle": [{"feature": "Disc extrude", "role": "AlongDistance", "expression": "15 mm"}],
    "ExtrudeJoin": [{"feature": "Boss", "role": "AlongDistance", "expression": "35 mm"}],
    "ExtrudeCut": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "ExtrudeIntersect": [{"feature": "Core", "role": "AlongDistance", "expression": "15 mm"}],
    "ExtrudeBlindCut": [{"feature": "Pocket", "role": "AlongDistance", "expression": "6 mm"}],
    "ExtrudeSlotCut": [{"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "ExtrudeSymmetricCut": [{"feature": "Pocket", "role": "AlongDistance", "expression": "12 mm"}],
    "PartCutFillet": [{"feature": "Corner Round", "expression": "4 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "PartConcaveShell": [{"feature": "Hollow", "expression": "1.5 mm"}, {"feature": "Notch extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "HoleFlat": [{"feature": "Top hole", "role": "HoleDiameter", "expression": "6 mm"}, {"feature": "Top hole", "role": "HoleDepth", "expression": "12 mm"}],
    "HoleThrough": [{"feature": "Top hole", "role": "HoleDiameter", "expression": "10 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "HoleCounterboreFlat": [{"feature": "Top hole", "role": "CBDiameter", "expression": "12 mm"}, {"feature": "Top hole", "role": "CBDepth", "expression": "3 mm"}],
    "HoleCounterbore": [{"feature": "Top hole", "role": "HoleDiameter", "expression": "5 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "RectPattern": [{"feature": "Pocket grid", "role": "uSpaceDistance", "expression": "11 mm"}, {"feature": "Pocket grid", "role": "CountV", "expression": "1"}],
    "FeatureCircPattern": [{"feature": "Pocket arc", "role": "TotalAngle", "expression": "30 deg"}],
    "MirrorFeature": [{"feature": "Mid plane", "role": "AlongDistance", "expression": "18 mm"}],
    "PlaneOffset": [{"feature": "Offset plane", "role": "AlongDistance", "expression": "12 mm"}, {"feature": "Base extrude", "role": "AlongDistance", "expression": "25 mm"}],
    "HoleGrid": [{"feature": "Hole grid", "role": "vSpaceDistance", "expression": "12 mm"}, {"feature": "Corner hole", "role": "HoleDepth", "expression": "8 mm"}],
    "MultiPocketPart": [{"feature": "Hole row", "role": "uSpaceDistance", "expression": "10 mm"}, {"feature": "Corner Round", "expression": "4 mm"}, {"feature": "Mid plane", "role": "AlongDistance", "expression": "21 mm"}],
    "MultiDiscPart": [{"feature": "Pocket ring", "role": "countU", "expression": "6"}, {"feature": "Center bore", "role": "CBDiameter", "expression": "16 mm"}],
}


def mm(value):
    return f"{value:g} mm"


def curve_step(curve):
    if isinstance(curve, LineCurve):
        return {"kind": "line", "start_cm": [v / 10.0 for v in curve.StartMm], "end_cm": [v / 10.0 for v in curve.FinishMm]}
    if isinstance(curve, CircleCurve):
        return {"kind": "circle", "center_cm": [v / 10.0 for v in curve.CenterMm], "radius_cm": curve.RadiusMm / 10.0}
    start = math.radians(curve.StartDegrees)
    return {
        "kind": "arc",
        "center_cm": [v / 10.0 for v in curve.CenterMm],
        "start_cm": [(curve.CenterMm[0] + curve.RadiusMm * math.cos(start)) / 10.0, (curve.CenterMm[1] + curve.RadiusMm * math.sin(start)) / 10.0],
        "sweep_rad": math.radians(curve.SweepDegrees),
    }


def step(feature):
    if isinstance(feature, ExtrudeSpec):
        return {
            "kind": "extrude",
            "profile": [curve_step(curve) for curve in feature.Profile],
            "amount": mm(feature.DistanceMm),
            "against": mm(feature.AgainstMm),
            "operation": feature.Operation,
            "extent": feature.Extent,
            "sketch": feature.SketchName,
            "name": feature.FeatureName,
        }
    if isinstance(feature, HoleSpec):
        result = {"kind": "hole", "center_cm": [v / 10.0 for v in feature.CenterMm], "diameter": mm(feature.DiameterMm), "name": feature.FeatureName}
        if feature.DepthMm:
            result["depth"] = mm(feature.DepthMm)
        if feature.BoreDiameterMm:
            result.update(bore_diameter=mm(feature.BoreDiameterMm), bore_depth=mm(feature.BoreDepthMm))
        return result
    if isinstance(feature, ShellSpec):
        return {"kind": "shell", "amount": mm(feature.ThicknessMm), "name": feature.FeatureName}
    if isinstance(feature, PatternSpec):
        return {"kind": "pattern", "source": feature.SourceIndex, "count_u": feature.CountU, "spacing_u": mm(feature.SpacingUMm), "count_v": feature.CountV, "spacing_v": mm(feature.SpacingVMm), "name": feature.FeatureName}
    if isinstance(feature, CircularSpec):
        return {"kind": "circular", "source": feature.SourceIndex, "count": feature.Count, "angle": f"{feature.TotalDegrees:g} deg", "name": feature.FeatureName}
    if isinstance(feature, PlaneSpec):
        return {"kind": "plane", "base": feature.BasePlane, "offset": mm(feature.OffsetMm), "name": feature.FeatureName}
    if isinstance(feature, MirrorSpec):
        return {"kind": "mirror", "source": feature.SourceIndex, "plane": feature.PlaneIndex, "name": feature.FeatureName}
    amount = feature.RadiusMm if isinstance(feature, FilletSpec) else feature.DistanceMm
    return {
        "kind": "fillet" if isinstance(feature, FilletSpec) else "chamfer",
        "corner_cm": [feature.CornerMm[0] / 10.0, feature.CornerMm[1] / 10.0],
        "amount": mm(amount),
        "name": feature.FeatureName,
    }


def expectation(solid):
    shape = BuildShape(solid)
    edges = {use.Edge for face in shape.Faces for loop in face.Loops for use in loop}
    mass = SolidMass(solid)
    return {"volume_cm3": mass["volume"], "area_cm2": mass["area"], "faces": len(shape.Faces), "edges": len(edges)}


def spec(name, features):
    if name in PART:
        return DocumentSpec(Title="Kit " + name, ParamName="height", LengthMm=20.0, ProfileKind="part", BodyName="Body1", Features=features)
    return DocumentSpec(
        Title="Kit " + name,
        ParamName="height",
        LengthMm=20.0,
        ProfileKind="cuboid",
        SketchName="Base Sketch",
        ExtrusionName="Base Extrude",
        BodyName="Body1",
        WidthMm=40.0,
        DepthMm=30.0,
        Features=features,
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    unknown = only - set(CASES)
    if unknown:
        raise SystemExit("Unknown cases: " + ", ".join(sorted(unknown)))
    path = OUTPUT / "Manifest.json"
    manifest = json.loads(path.read_text()) if only and path.exists() else {}
    for name, features in CASES.items():
        if only and name not in only:
            continue
        value = spec(name, features)
        payload = EmitDocument(value)
        start, stages = SolvePart(value)
        target = OUTPUT / (name + ".f3d")
        target.write_bytes(payload)
        solids = ([] if start is None else [start]) + [stage.After for stage in stages]
        manifest[name] = {
            "file": target.name,
            "base": "part" if name in PART else "cuboid",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "features": [repr(feature) for feature in features],
            "steps": [step(feature) for feature in features],
            "edits": EDITS[name],
            "kit_states": [expectation(solid) for solid in solids],
        }
        print(name, len(payload), manifest[name]["sha256"][:16], manifest[name]["kit_states"][-1])
    path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
