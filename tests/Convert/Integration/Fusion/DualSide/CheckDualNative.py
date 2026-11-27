from hashlib import sha256 as HashBytes

from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCoverage import (
    CheckCoverage,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import FaceCoedges
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanStore import CheckSpanStore
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField, SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Parameters.ReadParameters import CheckBinding
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.brep.Topology.BrepModel import BrepModel
from tests.Convert.Integration.Fusion.DualSide.CheckDualCones import CheckDualCones
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualState import ReadDualState
from tests.Convert.Integration.Fusion.DualSide.ReadDualFaces import ReadDualFaces
from tests.Convert.Integration.Fusion.DualSide.CheckDualRims import CheckDualRims
from tests.Convert.Integration.Fusion.DualSide.CheckDualCaps import CheckDualCaps
from tests.Convert.Integration.Fusion.DualSide.CheckDualRings import CheckDualRings
from tests.Convert.Integration.Fusion.DualSide.CheckDualMass import CheckDualMass


# a real native archive independently binds every side driver and solved carrier
def CheckDualNative(Sample: DualCase, Geometry: BrepModel) -> None:
    Payload = Sample.Source.read_bytes()
    assert HashBytes(Payload).hexdigest() == Sample.Digest
    Model = ReadDocument(Payload)
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    CheckDualMass(Sample, Context)
    for FieldName, NativeName, Wanted in (
        ("rAlongDistance", "AlongDistance", Sample.FirstMm / 10),
        ("rAgainstDistance", "AgainstDistance", Sample.SecondMm / 10),
        ("rTaperAngle", "TaperAngle", Sample.FirstTaper),
        ("side2TaperAngle", "Side2TaperAngle", Sample.SecondTaper),
    ):
        Binding = ResolveField(Graph, Context.Extrude, FieldName, "DcDoubleParameter")
        Parameter = CheckBinding(Graph, Binding, Context)
        assert Parameter.Fields["name"] == NativeName
        SameNumbers((NumberValue(Parameter.Fields["value"]),), (Wanted,))
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    State = ReadDualState(History, IntegerValue(Context.Extrude.Fields["endModelHS"]))
    CheckCoverage(State)
    CheckDualRims(State)
    Bodies = tuple(Value for Value in State.Entities if isinstance(Value, BodyNode))
    assert len(Bodies) == 1
    CheckSpanStore(Graph, Context, Model, Bodies[0])
    Faces = ReadDualFaces(State, Bodies[0])
    assert len(Faces) == len(Geometry.faces)
    assert all(FaceCoedges(State, FaceValue) for FaceValue in Faces)
    CheckDualCaps(State, Faces, Sample)
    Cones = tuple(Value for Value in State.Entities if isinstance(Value, ConeNode))
    if Sample.FirstTaper != -Sample.SecondTaper:
        CheckDualCones(Cones, Sample)
    CheckDualRings(State, Sample, len(Geometry.edges))
