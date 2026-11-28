from math import isclose as IsClose
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDoc
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from tests.Convert.Solidworks.Research.AdapterBridge.Circles.CheckCircDrive import (
    CheckCircDrive,
)


# public readback must preserve the radial driver and fixed centre ownership of the actual written circle
def CheckCircRead(TargetValue: FilePath | bytes, InputValue: CadDocument) -> None:
    DocumentValue = OpenDoc(
        TargetValue,
        source_format="solidworks.sldprt",
        include_brep=False,
        include_tessellation=False,
    )
    assert len(DocumentValue.bodies) == len(DocumentValue.sketches) == 1
    SketchValue = DocumentValue.sketches[0]
    CirclesValue = tuple(
        Value
        for Value in SketchValue.entities
        if isinstance(Value.geometry, CircleGeometry)
    )
    PointsValue = tuple(
        Value
        for Value in SketchValue.entities
        if isinstance(Value.geometry, PointGeometry)
    )
    assert len(CirclesValue) == len(PointsValue) == 1
    CircleValue = CastValue(CircleGeometry, CirclesValue[0].geometry)
    Expected = CastValue(CircleGeometry, InputValue.sketches[0].entities[0].geometry)
    assert CircleValue.center == Expected.center
    assert IsClose(CircleValue.radius, Expected.radius, rel_tol=1e-12)
    assert CastValue(PointGeometry, PointsValue[0].geometry).point == CircleValue.center
    RadialValue, FixedValue = SketchValue.constraints
    assert RadialValue.kind == InputValue.sketches[0].constraints[1].kind
    assert RadialValue.references[0].entity_id == CirclesValue[0].id
    assert FixedValue.kind == "fixed"
    assert FixedValue.references[0].entity_id == PointsValue[0].id
    assert SketchValue.closed_profile_entity_ids == ((CirclesValue[0].id,),)
    CheckCircDrive(DocumentValue, SketchValue, Expected, RadialValue)
    BossValue = next(
        Value
        for Value in DocumentValue.feature_timeline
        if Value.name == InputValue.feature_timeline[0].name
    )
    assert BossValue.sketch_id == SketchValue.id
    DefinitionValue = CastValue(ExtrudeFeature, BossValue.definition)
    ExpectedEnd = CastValue(ExtrudeFeature, InputValue.feature_timeline[0].definition)
    assert DefinitionValue.end_condition == "blind"
    assert DefinitionValue.reversed is ExpectedEnd.reversed
    assert DefinitionValue.length == ExpectedEnd.length
    assert DefinitionValue.second_length is None
