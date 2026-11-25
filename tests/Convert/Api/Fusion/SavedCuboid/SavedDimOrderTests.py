from pytest import mark as MarkTests

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.SavedCuboid.SwapSavedDims import SwapSavedDims
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# independently ordered native lists must keep their actual width and depth expression owners after ordinary public import
@MarkTests.parametrize(
    ("ReverseDrivers", "ReverseCompute"),
    ((False, False), (True, False), (True, True)),
)
def TestDimOrder(ReverseDrivers: bool, ReverseCompute: bool) -> None:
    Source = SavedSource(KSavedCases[1]).read_bytes()
    Changed = SwapSavedDims(ReadDocument(Source), ReverseDrivers, ReverseCompute)
    Payload = EmitParsed(Changed)
    Document = OpenDocument(Payload, source_format="f3d")
    Parameters = {Value.id: Value for Value in Document.parameters}
    SeenRoles: dict[str, str] = {}
    for Relation in Document.sketches[0].constraints:
        if Relation.parameter_id is None:
            continue
        Expression = Parameters[Relation.parameter_id].expression
        assert Expression is not None
        (Driver,) = Expression.parameter_ids
        SeenRoles[Relation.kind] = Parameters[Driver].name
    assert SeenRoles == {"distance_x": "kitWidth", "distance_y": "kitDepth"}
    assert tuple(SeenRoles) == ("distance_y", "distance_x")
    assert Document.metadata["fusion.read_only"] is True
    assert (
        CheckContract(Document.metadata["fusion.native_state"], "model", 2) == Changed
    )
