from base64 import b64decode as DecodeBase
from math import isclose as IsClose
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDocument
from interchange import CadDocument, CircleGeometry, ExtrusionFeature, LineGeometry
from tests.Convert.Solidworks.Research.Cut.BlindCutInput import MakePocketInput
from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart


# both owned profiles must remain usable even when no geometry payload is requested
def AssertProfiles(Document: CadDocument) -> None:
    BossSketch, PocketSketch = Document.sketches
    assert (BossSketch.name, PocketSketch.name) == ("Sketch1", "PocketSketch")
    for Sketch in Document.sketches:
        assert Sketch.support_plane_id == "sldprt:plane:14"
        assert Sketch.attributes["support_plane_source"] == "plane-reference"
    (BossLoop,) = BossSketch.closed_profile_entity_ids
    assert len(BossLoop) == len(BossSketch.entities) == 4
    assert set(BossLoop) == {Entity.id for Entity in BossSketch.entities}
    Corners: set[tuple[float, float]] = set()
    for Entity in BossSketch.entities:
        Geometry = Entity.geometry
        assert isinstance(Geometry, LineGeometry)
        Corners.add((Geometry.start.x, Geometry.start.y))
        Corners.add((Geometry.end.x, Geometry.end.y))
    assert Corners == {(-31.9, -24.1), (26.7, -24.1), (26.7, 19.3), (-31.9, 19.3)}
    (CircleEntity,) = PocketSketch.entities
    assert PocketSketch.closed_profile_entity_ids == ((CircleEntity.id,),)
    Circle = CircleEntity.geometry
    assert isinstance(Circle, CircleGeometry)
    assert (Circle.center.x, Circle.center.y) == (9.7, -7.3)
    assert IsClose(Circle.radius, 6.41)
    (RadiusRule,) = tuple(
        Relation for Relation in PocketSketch.constraints if Relation.kind == "radius"
    )
    assert RadiusRule.parameter_id == "sldprt:parameter:25:D1"


# the fixed point targets only the centre while the radius remains driving
def AssertCenterFix(Document: CadDocument) -> None:
    _, PocketSketch = Document.sketches
    (CircleEntity,) = PocketSketch.entities
    assert not CircleEntity.fixed
    RadiusRule, CenterRule = PocketSketch.constraints
    assert RadiusRule.kind == "radius" and RadiusRule.driving
    assert RadiusRule.parameter_id == "sldprt:parameter:25:D1"
    (RadialRef,) = RadiusRule.references
    assert (RadialRef.entity_id, RadialRef.point) == (CircleEntity.id, "")
    assert CenterRule.kind == "fixed" and CenterRule.driving
    assert CenterRule.parameter_id is None
    (CenterRef,) = CenterRule.references
    assert (CenterRef.entity_id, CenterRef.point) == (CircleEntity.id, "center")
    assert CenterRule.attributes["native_code"] == 0x11
    assert CenterRule.provenance is not None
    (SpanValue,) = CenterRule.provenance.spans
    assert SpanValue.stream == "Contents/Config-0-ResolvedFeatures"
    assert SpanValue.length > 8


# cut depth and its inputs must remain attached to their actual sketch and predecessor
def AssertPocketCut(Document: CadDocument) -> None:
    NativeNodes = {Feature.name: Feature for Feature in Document.feature_timeline}
    BossNode = NativeNodes["Boss-Extrude1"]
    Pocket = NativeNodes["BlindPocket"]
    BossSketch, PocketSketch = Document.sketches
    assert BossNode.sketch_id == BossSketch.id and str(BossNode.operation) == "join"
    assert Pocket.sketch_id == PocketSketch.id and str(Pocket.operation) == "cut"
    assert BossNode.input_feature_ids == (NativeNodes["Sketch1"].id,)
    assert Pocket.input_feature_ids == (BossNode.id, NativeNodes["PocketSketch"].id)
    assert BossNode.order < NativeNodes["PocketSketch"].order < Pocket.order
    Definition = Pocket.definition
    assert isinstance(Definition, ExtrusionFeature)
    assert str(Definition.end_condition) == "blind" and Definition.reversed
    LengthValue = Definition.length
    assert LengthValue is not None
    assert LengthValue.value == 4.83 and LengthValue.unit == "mm"
    (DepthParameter,) = tuple(
        Parameter
        for Parameter in Document.parameters
        if Parameter.id in Pocket.parameter_ids
    )
    assert DepthParameter.owner_id == Pocket.id and DepthParameter.name == "D1"
    assert str(DepthParameter.role) == "driving"
    assert DepthParameter.value == Definition.length


# the generated functional pocket reaches the public sdk through its native container
def TestPocketRead(TmpPath: FilePath) -> None:
    Report = RunFreshPart(MakePocketInput("all_bodies"))
    OutputPath = TmpPath / "BlindPocketAllBodies.SLDPRT"
    BlobValue = DecodeBase(CastValue(str, Report["blob"]), validate=True)
    BytesWritten = OutputPath.write_bytes(BlobValue)
    assert BytesWritten == len(BlobValue)
    Document = OpenDocument(OutputPath, include_brep=False, include_tessellation=False)
    assert Document.validate() == ()
    assert not Document.brep_payloads and Document.brep is None
    AssertProfiles(Document)
    AssertCenterFix(Document)
    AssertPocketCut(Document)
