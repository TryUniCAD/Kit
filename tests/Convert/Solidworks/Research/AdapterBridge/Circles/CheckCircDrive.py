from math import isclose as IsClose
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchRelation


# the read parameter must retain its real profile feature owner and actual radial value through the linked sketch
def CheckCircDrive(
    DocumentValue: CadDocument,
    SketchValue: Sketch,
    Expected: CircleGeometry,
    RadialValue: SketchRelation,
) -> None:
    ParamValue = DocumentValue.parameter(CastValue(str, RadialValue.parameter_id))
    OwnerValue = next(
        Value
        for Value in DocumentValue.feature_timeline
        if Value.id == ParamValue.owner_id
    )
    assert OwnerValue.name == SketchValue.name
    assert OwnerValue.sketch_id == SketchValue.id
    assert ParamValue.id in OwnerValue.parameter_ids
    assert ParamValue.id in SketchValue.parameter_ids and ParamValue.role == "driving"
    assert ParamValue.value.unit == "mm"
    assert IsClose(
        CastValue(float, ParamValue.value.value),
        Expected.radius * (2 if RadialValue.kind == "diameter" else 1),
        rel_tol=1e-12,
    )
