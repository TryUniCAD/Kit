from hashlib import sha256 as HashBytes

from pytest import approx as ApproxValue, mark as MarkTests

from convert.api.ApiOpen import OpenDocument
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimLive import CheckRimLive
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.Fillets.GetFilletVals import GetFilletVals
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)
from tests.Convert.Integration.Fusion.RimFillet.Policy.RimPolicyCase import (
    RimPolicyCase,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.CheckRimMeasure import (
    CheckRimMeasure,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.ReadRimApi import ReadRimApi


# strict sdk inspection must expose complete bound fillet intent and actual source geometry through json restoration
@MarkTests.parametrize("Sample", ReadPolicyCases())
def CheckRimRead(Sample: RimPolicyCase) -> None:
    Document = OpenDocument(Sample.Source)
    Document.AssertValid()
    Restored = CadDocument.from_json(Document.to_json())
    Restored.AssertValid()
    assert Restored == Document and Document.metadata["fusion.read_only"] is True
    assert len(Document.feature_timeline) == 3 and len(Document.selections) == 1
    assert len(Document.parameters) == len(Sample.Parameters)
    Extrude, Fillet = Document.feature_timeline[1:]
    assert isinstance(Extrude.definition, DistanceExtrude)
    assert isinstance(Fillet.definition, RadiusFillet)
    Parameters = {Value.id: Value for Value in Document.parameters}
    Selected = {Value.id: Value for Value in Document.selections}
    Radius, Weight = GetFilletVals(Fillet, Fillet.definition, Parameters, Selected)
    assert Radius > 0 and Weight == 1
    assert Fillet.input_feature_ids == (Extrude.id,)
    assert Parameters[Fillet.definition.RadiusParameterId].owner_id == Fillet.id
    assert Parameters[Fillet.definition.WeightParameterId].owner_id == Fillet.id
    assert GetDistValues(Extrude, Extrude.definition, Parameters).LowerMm == 0
    CheckRimMeasure(Document, ReadRimApi(Sample.CaseName))
    Encoded = Sample.Source.read_bytes()
    assert HashBytes(Encoded).hexdigest() == Sample.Digest
    Model = ReadDocument(Encoded)
    Graph = BuildGraph(Model)
    Context = ReadRimContext(Graph)
    _, Current = CheckRimLive(
        Model, Graph, Context, ReadCircle(Graph, Context.Extrusion)
    )
    assert Document.brep is not None
    for Actual, Expected in zip(
        sorted(
            (Value.point.x, Value.point.y, Value.point.z)
            for Value in Document.brep.vertices
        ),
        sorted(
            tuple(Coordinate * 10 for Coordinate in Value.PositionCm)
            for Value in Current.Entities
            if isinstance(Value, PointNode)
        ),
        strict=True,
    ):
        assert Actual == ApproxValue(Expected, rel=0, abs=1e-7)
