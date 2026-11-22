from io import BytesIO
from math import isclose as IsClose

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.PrepareNestedAssembly import (
    PrepNestedAsm,
)
from tests.Convert.Solidworks.NestedWriting.MakeDimNest import MakeDimNest


# the strict reader must recover three independent editable parameters and construct their one solid
def TestDimLeafRead() -> None:
    Candidates = PrepNestedAsm(
        MakeDimNest(), r"C:\KitNestedQueue\QueueFrame.SLDASM", 1794011937
    )
    PartPath, Target = Candidates[0]
    assert PartPath.stem == "QueuePlate"
    PartValue = OpenDocument(BytesIO(Target.BytesValue), source_format=KPartFormatId)
    (SketchValue,) = PartValue.sketches
    assert len(SketchValue.constraints) == 6
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
    assert all(
        type(Quantity.value.value) in (int, float)
        and IsClose(float(Quantity.value.value), LengthValue)
        for Quantity, LengthValue in zip(
            (WidthParam, HeightParam, DepthParam), (17.0, 9.0, 7.5), strict=True
        )
    )
    assert PartValue.brep is not None and len(PartValue.brep.faces) == 6
    assert BodyValue.topology.volume is not None
    assert IsClose(BodyValue.topology.volume, 17.0 * 9.0 * 7.5)
