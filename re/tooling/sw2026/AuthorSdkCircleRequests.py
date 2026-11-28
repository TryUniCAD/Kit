from argparse import ArgumentParser
from dataclasses import replace
from json import dumps
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, SketchEntity, SketchRelation
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc


def make_document(name, support, center, radius, depth, kind, condition, reverse, second):
    document = MakePlainDoc(name, 1, 1, depth)
    sketch = document.sketches[0]
    circle = SketchEntity("circle/analytic", GeometryKind.KCircle, CircleGeometry(PlaneVector(*center), radius))
    radial = Parameter("parameter/radial", "D1", length(radius * (2 if kind == "diameter" else 1)), owner_id=sketch.id)
    sketch = replace(
        sketch, entities=(circle,), parameter_ids=(radial.id,), closed_profile_entity_ids=((circle.id,),),
        constraints=(SketchRelation("relation/center", "fixed", (ConstraintRef(circle.id, "center"),)),
                     SketchRelation("relation/radial", kind, (ConstraintRef(circle.id),), radial.id)),
    )
    feature = document.feature_timeline[0]
    parameters = (*document.parameters, radial)
    if second is not None:
        second_driver = Parameter("parameter/second-depth", "D2", length(second), owner_id=feature.id)
        parameters += (second_driver,)
        feature = replace(feature, parameter_ids=(*feature.parameter_ids, second_driver.id))
    plane = document.support_planes[0]
    frames = {
        "Front Plane": Transform(),
        "Right Plane": Transform(SpaceVector(0, 0, 0), SpaceVector(0, 0, -1), SpaceVector(0, 1, 0), SpaceVector(1, 0, 0)),
        "Top Plane": Transform(SpaceVector(0, 0, 0), SpaceVector(1, 0, 0), SpaceVector(0, 0, -1), SpaceVector(0, 1, 0)),
    }
    plane = replace(plane, name=support, transform=frames[support])
    definition = replace(feature.definition, end_condition=condition, reversed=reverse, symmetric=condition == ExtrudeEnd.KMidPlane,
                         second_length=None if second is None else length(second),
                         second_end_condition=None if second is None else ExtrudeEnd.KBlind)
    feature = replace(feature, definition=definition)
    return replace(document, support_planes=(plane,), sketches=(sketch,), feature_timeline=(feature,), parameters=parameters)


def length(mm):
    return ParameterValue(mm, ValueKind.KLength, "mm")


def main():
    parser = ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.is_relative_to(ROOT):
        raise ValueError("disclosed request outputs belong outside the checkout")
    out.mkdir(parents=True, exist_ok=False)
    cases = (
        ("radius", "SDK circle radius alpha", "Front Plane", (-4.275, 6.825), 8.725, 12.475, "radius", ExtrudeEnd.KBlind, False, None, (1.235, 0.875)),
        ("diameter", "SDK circle diameter beta", "Front Plane", (7.125, -5.675), 11.475, 17.825, "diameter", ExtrudeEnd.KBlind, False, None, (0.835, 1.185)),
        ("reverse-right", "SDK circle reverse right", "Right Plane", (3.113, -6.714), 7.275, 16.525, "diameter", ExtrudeEnd.KBlind, True, None, (1.17, 0.88)),
        ("mid-top", "SDK circle mid-plane top", "Top Plane", (-7.216, 2.312), 10.625, 24.175, "radius", ExtrudeEnd.KMidPlane, False, None, (0.79, 1.21)),
        ("two-front", "SDK circle two directions front", "Front Plane", (4.825, -8.113), 8.125, 13.525, "diameter", ExtrudeEnd.KTwoLengths, False, 7.425, (1.12, 1.37, 0.84)),
        ("two-rev-top", "SDK circle reversed two directions top", "Top Plane", (-2.881, 9.615), 12.375, 9.025, "radius", ExtrudeEnd.KTwoLengths, True, 15.825, (0.86, 1.27, 1.16)),
    )
    for key, name, support, center, radius, depth, kind, condition, reverse, second, edits in cases:
        document = make_document(name, support, center, radius, depth, kind, condition, reverse, second)
        request = {"document": ToData(document), "created_at": 1794974400,
                   "radial_edit_factor": edits[0], "depth_edit_factor": edits[1]}
        if second is not None:
            request["second_edit_factor"] = edits[2]
        with (out / (key + ".json")).open("x", encoding="utf-8") as file:
            file.write(dumps(request, indent=2, sort_keys=True) + "\n")
    print(len(cases))


if __name__ == "__main__":
    main()
