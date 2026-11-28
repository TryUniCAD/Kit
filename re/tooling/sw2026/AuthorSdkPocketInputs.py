from argparse import ArgumentParser
from dataclasses import replace
from json import dumps
from math import pi
from ntpath import join as windows_join
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(root), str(root / "src")]

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc


def neutral_document(name, width, height, boss_depth, center, radius, cut_depth, radial_mode):
    original = MakePlainDoc(name, width, height, boss_depth)
    boss = replace(original.feature_timeline[0], name="BaseBoss")
    boss_sketch = replace(original.sketches[0], name="BossProfile")
    body = replace(original.bodies[0], name=boss.name, final_feature_id="feature/pocket")
    entity = SketchEntity("edge/pocket", GeometryKind.KCircle, CircleGeometry(PlaneVector(*center), radius))
    sketch = Sketch("sketch/pocket", "PocketCircle", boss_sketch.support_plane_id, (entity,),
                    closed_profile_entity_ids=((entity.id,),))
    cut_length = ParameterValue(cut_depth, ValueKind.KLength, "mm")
    cut = FeatureStep(body.final_feature_id, "BlindPocket", FeatureKind.KExtrusion, 1,
                      input_feature_ids=(boss.id,), sketch_id=sketch.id, parameter_ids=("parameter/pocket-depth",),
                      operation=BooleanOp.KCutOperation, definition=ExtrudeFeature(cut_length, ExtrudeEnd.KBlind, True))
    driver = Parameter(cut.parameter_ids[0], "D1", cut_length, ParameterRole.KDriving, owner_id=cut.id)
    parameters = (driver, original.parameters[0])
    if radial_mode is not None:
        radial_value = ParameterValue(radius * (2 if radial_mode == "diameter" else 1), ValueKind.KLength, "mm")
        radial = Parameter("parameter/pocket-radial", "D1", radial_value, ParameterRole.KDriving, owner_id=sketch.id)
        sketch = replace(sketch, parameter_ids=(radial.id,), constraints=(
            SketchRelation("constraint/pocket-center", "fixed", (ConstraintRef(entity.id, "center"),)),
            SketchRelation("constraint/pocket-radial", radial_mode, (ConstraintRef(entity.id),), radial.id),
        ))
        parameters += (radial,)
    return replace(original, parameters=parameters, sketches=(boss_sketch, sketch),
                   feature_timeline=(boss, cut), bodies=(body,))


def prediction(width, height, boss_depth, center, radius, cut_depth):
    boss_volume = width * height * boss_depth
    pocket_volume = pi * radius**2 * cut_depth
    volume = boss_volume - pocket_volume
    centroid = [-pocket_volume * value / volume for value in center]
    centroid.append((boss_volume * boss_depth / 2 - pocket_volume * cut_depth / 2) / volume)
    return {"body_count": 1, "volume_m3": volume * 1e-9,
            "area_m2": (2 * width * height + 2 * (width + height) * boss_depth + 2 * pi * radius * cut_depth) * 1e-6,
            "com_m": [value * 0.001 for value in centroid]}


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def main():
    parser = ArgumentParser(description="Author three disclosed neutral blind-pocket controls")
    parser.add_argument("output", type=Path)
    parser.add_argument("--native-directory", required=True)
    parser.add_argument("--written-at", type=int, required=True)
    args = parser.parse_args()
    args.output.mkdir()
    controls = (
        ("SdkPocketA", 47.0, 33.0, 18.0, (4.0, -3.0), 5.6, 4.2, 6.8, "radius"),
        ("SdkPocketWideBeta", 77.4, 26.8, 11.7, (-7.0, 1.4), 3.4, 2.3, 5.3, "diameter"),
        ("SdkPocketFree", 61.7, 37.9, 14.3, (7.4, 4.2), 4.1, 3.8, 7.9, None),
    )
    cases = []
    for name, width, height, boss_depth, center, radius, cut_depth, edit_depth, radial_mode in controls:
        document = neutral_document(name, width, height, boss_depth, center, radius, cut_depth, radial_mode)
        request = {"document": ToData(document), "written_at": args.written_at,
                   "native_path": windows_join(args.native_directory, name + ".SLDPRT")}
        write(args.output / (name + ".Request.json"), request)
        cases.append({
            "name": name, "feature_roles": ["BossProfile", "BaseBoss", "PocketCircle", "BlindPocket"],
            "radial_mode": radial_mode,
            "geometry": {
                "boss_depth_mm": boss_depth, "cut_depth_mm": cut_depth, "edit_depth_mm": edit_depth,
                "boss_profile": {"kind": "rectangle", "center_mm": [0.0, 0.0], "width_mm": width, "height_mm": height},
                "cut_profile": {"kind": "circle", "center_mm": list(center), "radius_mm": radius},
            },
            "independent_geometry": {
                "initial": prediction(width, height, boss_depth, center, radius, cut_depth),
                "edited": prediction(width, height, boss_depth, center, radius, edit_depth),
            },
        })
    write(args.output / "Cases.json", {"cases": cases, "heldout_sources_read": 0})


if __name__ == "__main__":
    main()
