from dataclasses import replace

from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


def dimension_rectangle(document):
    sketch, = document.sketches
    left, bottom, right, top = (
        sketch.entities[0].geometry.start.x, sketch.entities[0].geometry.start.y,
        sketch.entities[2].geometry.start.x, sketch.entities[2].geometry.start.y,
    )
    profile, = sketch.closed_profile_entity_ids
    if len(profile) != 4 or sketch.constraints or sketch.parameter_ids or not (left < right and bottom < top):
        raise ValueError("fixture needs an authored rectangle with no existing relations")
    parameters = tuple(
        Parameter(f"nested:length:{role}", name, ParameterValue(length, ValueKind.KLength, "mm"),
                  ParameterRole.KDriving, owner_id=sketch.id)
        for role, name, length in (("width", "D1", right - left), ("height", "D2", top - bottom))
    )
    axes = tuple(
        SketchRelation(f"nested:axis:{index}", "horizontal" if index % 2 == 0 else "vertical", (ConstraintRef(edge),))
        for index, edge in enumerate(profile)
    )
    distances = tuple(
        SketchRelation(f"nested:distance:{index}", "distance",
                       (ConstraintRef(edge, "start"), ConstraintRef(edge, "end")), parameter.id)
        for index, (edge, parameter) in enumerate(zip(profile[:2], parameters, strict=True))
    )
    sketch = replace(sketch, constraints=(*axes, *distances), parameter_ids=tuple(row.id for row in parameters))
    result = replace(document, sketches=(sketch,), parameters=(*document.parameters, *parameters))
    result.assert_valid()
    return result


def dimension_leaves(request):
    for row in request["definitions"]:
        if row["kind"] == "part":
            part = row["request"]
            part["document"] = ToData(dimension_rectangle(FromData(part["document"])))
