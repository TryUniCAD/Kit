"""Emit Kit-authored feature documents that mirror the native controls.

Run with Python 3.14 (ZIP method 93) from the repository root:
    /opt/homebrew/bin/python3.14 -I re/Fusion/Reconstruction/FeatureAuthoring/EmitAuthored.py

The base part matches CaptureControls.py: a 40 x 30 mm rectangle at the
origin extruded 20 mm. Every feature dimension matches its native control so
the acceptance run can compare geometry directly.
"""

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.dont_write_bytecode = True

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import ChamferSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import FilletSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SolidMass import SolidMass  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import BuildShape  # noqa: E402
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart  # noqa: E402

OUTPUT = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Authored"

CASES = {
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


EDITS = {
    "Fillet": [{"feature": "Fillet", "expression": "4 mm"}],
    "Chamfer": [{"feature": "Chamfer", "expression": "2 mm"}],
    "Shell": [{"feature": "Shell", "expression": "3 mm"}],
    "FilletShell": [{"feature": "Shell", "expression": "1.5 mm"}, {"feature": "height", "expression": "25 mm"}],
    "MultiFeature": [{"feature": "Corner Round", "expression": "5 mm"}, {"feature": "height", "expression": "25 mm"}],
}


def step(feature):
    if isinstance(feature, ShellSpec):
        return {"kind": "shell", "amount": f"{feature.ThicknessMm:g} mm", "name": feature.FeatureName}
    amount = feature.RadiusMm if isinstance(feature, FilletSpec) else feature.DistanceMm
    return {
        "kind": "fillet" if isinstance(feature, FilletSpec) else "chamfer",
        "corner_cm": [feature.CornerMm[0] / 10.0, feature.CornerMm[1] / 10.0],
        "amount": f"{amount:g} mm",
        "name": feature.FeatureName,
    }


def expectation(solid):
    shape = BuildShape(solid)
    edges = {use.Edge for face in shape.Faces for loop in face.Loops for use in loop}
    mass = SolidMass(solid)
    return {"volume_cm3": mass["volume"], "area_cm2": mass["area"], "faces": len(shape.Faces), "edges": len(edges)}


def spec(name, features):
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
    manifest = {}
    for name, features in CASES.items():
        if only and name not in only:
            continue
        value = spec(name, features)
        payload = EmitDocument(value)
        base, stages = SolvePart(value)
        path = OUTPUT / (name + ".f3d")
        path.write_bytes(payload)
        manifest[name] = {
            "file": path.name,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "features": [repr(feature) for feature in features],
            "steps": [step(feature) for feature in features],
            "edits": EDITS[name],
            "kit_states": [expectation(solid) for solid in (base, *(stage.After for stage in stages))],
        }
        print(name, len(payload), manifest[name]["sha256"][:16])
    (OUTPUT / "Manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
