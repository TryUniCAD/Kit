from hashlib import sha256 as HashBytes

from pytest import approx as NearValue, mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.Features.FeatureDistExt import DistanceExtrude
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Api.Fusion.SavedCuboid.SavedCase import SavedCase
from tests.Convert.Api.Fusion.SavedCuboid.SavedCases import KSavedCases
from tests.Convert.Api.Fusion.SavedCuboid.SavedSource import SavedSource


# fixed cuboid admission must not contradict its one sided solved solid with a symmetric feature
@MarkTests.parametrize("CaseValue", KSavedCases)
@MarkTests.parametrize("Measurement", (1, 2))
def TestSavedExtent(CaseValue: SavedCase, Measurement: int) -> None:
    Payload = SavedSource(CaseValue).read_bytes()
    assert HashBytes(Payload).hexdigest() == CaseValue.DigestValue
    Original = OpenDocument(Payload, source_format="f3d")
    Definition = Original.feature_timeline[-1].definition
    assert isinstance(Definition, DistanceExtrude)
    assert Definition.SideMode == "one_sided"
    assert Original.bodies[0].topology.volume == NearValue(
        CaseValue.WidthMm * CaseValue.DepthMm * CaseValue.HeightMm
    )
    Model = ReadDocument(Payload)
    Feature = BuildGraph(Model).OneClass("DcExtrudeFeature")
    Changes = (
        ("directionType", 3),
        ("symmetricMeasurementType", Measurement),
        ("extendFaceOption", 1),
        ("side2ExtendFaceOption", 1),
        ("side2TaperAngle", Feature.Fields["rTaperAngle"]),
    )
    for FieldName, Value in Changes:
        Model = ChangeField(Model, Feature.ObjectId, FieldName, Value)
    Altered = EmitParsed(Model)
    Decoded = BuildGraph(ReadDocument(Altered)).OneClass("DcExtrudeFeature")
    assert all(Decoded.Fields[FieldName] == Value for FieldName, Value in Changes)
    with RaisesError(
        ValueError, match="fixed rectangle requires a one sided extrusion"
    ):
        _ = OpenDocument(Altered, source_format="f3d")
