from io import BytesIO
from math import isclose as IsClose

from pytest import raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from tests.Convert.Solidworks.NestedWriting.CheckDriverRefs import CheckDriverRefs
from tests.Convert.Solidworks.NestedWriting.MakeAxisGap import MakeAxisGap
from tests.Convert.Solidworks.NestedWriting.MakeDimNest import MakeDimNest


# the strict reader must recover three independent editable parameters and construct their one solid
def TestDimLeafRead() -> None:
    Candidates = PrepNestedAsm(
        MakeDimNest(Translated=True), r"C:\KitNestedQueue\QueueFrame.SLDASM", 1794011937
    )
    PartPath, Target = Candidates[0]
    assert PartPath.stem == "QueuePlate"
    PartValue = OpenDocument(BytesIO(Target.BytesValue), source_format=KPartFormatId)
    (SketchValue,) = PartValue.sketches
    assert len(SketchValue.constraints) == 6
    CheckDriverRefs(SketchValue)
    SketchIds = SketchValue.parameter_ids
    assert len(SketchIds) == 2
    (BodyValue,) = PartValue.bodies
    assert BodyValue.final_feature_id is not None
    BossValue = PartValue.feature(BodyValue.final_feature_id)
    assert BossValue.sketch_id == SketchValue.id
    (DepthId,) = BossValue.parameter_ids
    WidthParam, HeightParam, DepthParam = (
        PartValue.parameter(Identity) for Identity in (*SketchIds, DepthId)
    )
    assert len({WidthParam.id, HeightParam.id, DepthParam.id}) == 3
    assert tuple(
        Quantity.value.value for Quantity in (WidthParam, HeightParam, DepthParam)
    ) == (12.5, 9.0, 7.5)
    assert WidthParam.attributes["native_value"] == 12.5 * 0.001
    assert PartValue.brep is not None and len(PartValue.brep.faces) == 6
    assert BodyValue.topology.volume is not None
    assert IsClose(BodyValue.topology.volume, 12.5 * 9.0 * 7.5)


# a recognized rectangle without its native axes must report the loss before strict projection
def TestNoAxis() -> None:
    Candidates = PrepNestedAsm(
        MakeDimNest(), r"C:\KitNestedQueue\QueueFrame.SLDASM", 1794011937
    )
    Payload = MakeAxisGap(Candidates[0][1].BytesValue)
    Diagnostic = "invalid typed dimensioned cold leaf"
    for Geometry in (False, True):
        with RaisesError(SldprtFormat, match=Diagnostic):
            _ = OpenDocument(
                Payload, source_format=KPartFormatId, include_brep=Geometry
            )
    Partial = OpenDocument(
        Payload, source_format=KPartFormatId, include_brep=False, strict=False
    )
    assert len(Partial.sketches) == 1
    assert any(Diagnostic in Record.message for Record in Partial.diagnostics)
