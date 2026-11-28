from __future__ import annotations

from dataclasses import replace

from interchange.Enums.EnumValues import ValueKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.serialization.EncodeData import ToData
from interchange.serialization.Deserialize import FromData
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc
from tests.Convert.Solidworks.Research.Drawing.SdkLinked.MakeLinkedJob import MakeLinkedJob


def dimensioned_rectangle(name, width, height, depth, kind):
    document = MakePlainDoc(name, width, height, depth)
    sketch = document.sketches[0]
    if kind not in ("corner-anchored", "center-anchored"):
        raise ValueError("origin pair input requires a complete declared anchor family")
    left, bottom = (0.0, 0.0) if kind == "corner-anchored" else (-width / 2, -height / 2)
    vertices = ((left, bottom), (left + width, bottom), (left + width, bottom + height), (left, bottom + height))
    entities = tuple(replace(entity, geometry=LineGeometry(PlaneVector(*vertices[index]), PlaneVector(*vertices[(index + 1) % 4])))
                     for index, entity in enumerate(sketch.entities))
    parameters = tuple(Parameter("parameter/" + label, "D" + str(index + 1),
                                 ParameterValue(length, ValueKind.KLength, "mm"), owner_id=sketch.id)
                       for index, (label, length) in enumerate((("width", width), ("height", height))))
    axes = tuple(SketchRelation("relation/axis/" + str(index), "horizontal" if index % 2 == 0 else "vertical", (ConstraintRef(entity.id),))
                 for index, entity in enumerate(entities))
    values = tuple(SketchRelation("relation/length/" + str(index), "distance",
                                  (ConstraintRef(entities[index].id, "start"), ConstraintRef(entities[index].id, "end")), parameter.id)
                   for index, parameter in enumerate(parameters))
    return replace(document, sketches=(replace(sketch, entities=entities, constraints=(*axes, *values),
                                              parameter_ids=tuple(parameter.id for parameter in parameters)),),
                   parameters=(*parameters, document.parameters[0]))


def make_job(name, width, height, depth, orientation, scale, position, kind="corner-anchored"):
    job = MakeLinkedJob(name, width * 1000.0, height * 1000.0, depth * 1000.0, orientation, scale)
    child_name = name + "Child"
    job["schema"] = "kit.sw2026.sdk-origin-drawing-process.v1"
    job["part"]["document"] = ToData(dimensioned_rectangle(child_name, width * 1000.0, height * 1000.0, depth * 1000.0, kind))
    left, bottom = (0.0, 0.0) if kind == "corner-anchored" else (-width / 2, -height / 2)
    job["child_policy"] = {"kind": kind, "width_text_m": [left + width / 2, bottom - height * 0.3],
                           "height_text_m": [left + width * 1.3, bottom + height / 2], "route_centerline": False}
    job["origin_display"] = {"selection": "actual-child-origin", "population_argument": 0}
    drawing = FromData(job["drawing_document"])
    sheet = drawing.Sheets[0]
    view = replace(sheet.Views[0], PositionValue=PlaneVector(*position))
    job["drawing_document"] = ToData(replace(drawing, Sheets=(replace(sheet, Views=(view,)),)))
    return job
