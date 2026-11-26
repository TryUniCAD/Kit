from pytest import raises as Raises

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# swapping existing passive identities isolates root order from membership validation
def TestRootOrder() -> None:
    Source = SavedSource(KSavedCases[0]).read_bytes()
    assert (
        OpenDocument(Source, source_format="f3d").metadata["fusion.read_only"] is True
    )
    Original = ReadDocument(Source)
    Graph = BuildGraph(Original)
    Serializer = Graph.OneClass("BRepSerializer")
    Generator = ResolveField(
        Graph, Serializer, "topEntityPIDGenerator", "PassiveIdGenerator"
    )
    First, Second, Third = SeriesItems(Generator.Fields["scanOrderIndex"])
    Changed = ChangeField(
        Original,
        Generator.ObjectId,
        "scanOrderIndex",
        ValueSeries((Second, First, Third)),
    )
    assert Changed != Original
    Payload = EmitParsed(Changed)
    assert ReadDocument(Payload) == Changed
    with Raises(ValueError, match="passive identities disagree with its roots"):
        _ = OpenDocument(Payload, source_format="f3d")
