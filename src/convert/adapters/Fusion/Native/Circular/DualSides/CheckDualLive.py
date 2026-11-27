from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualCover import (
    CheckDualCover,
)
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualGeo import CheckDualGeo
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLinks import (
    CheckDualLinks,
)
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualRims import (
    CheckDualRims,
)
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualTags import (
    CheckDualTags,
)
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualOwners import (
    ReadDualOwners,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields
from convert.adapters.Fusion.Native.Circular.DualFrames.ReadDualFrame import (
    ReadDualFrame,
)
from convert.adapters.Fusion.Native.Circular.DualFrames.LocalDualView import (
    LocalDualView,
)
from interchange.geometry.Models.Transform import KTransformIdentity, Transform
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Geometry.Extrude.Circular.DualSide.DualMeridian import DualMeridian


# bounded live admission composes independent geometry coverage and ownership proofs without widening dispatch
def CheckDualLive(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: CircleShape,
    FirstMm: float,
    SecondMm: float,
    FirstTaper: float,
    SecondTaper: float,
    FrameValue: Transform = KTransformIdentity,
) -> GeometryState:
    if ReadDualFrame(Graph, Context) != FrameValue:
        raise ValueError("Native dual live frame must match its qualified source")
    RequireFields(
        Context.Extrude,
        {
            "directionType": 2,
            "symmetricMeasurementType": 0,
            "profileLocaltionType": 0,
            "profileOffset": None,
            "booleanOperation": 4,
        },
    )
    if len(Model.Bodies) != 1 or Model.Forms or Model.Meshes:
        raise ValueError("Native dual sides require one complete solid history")
    if (
        len(
            DualMeridian(
                Shape.Geometry.radius, FirstMm, SecondMm, FirstTaper, SecondTaper
            )
        )
        != 5
    ):
        raise ValueError("Native dual sides require two distinct physical side slopes")
    History = Model.Bodies[0].History
    if not isinstance(History, JournalModel):
        raise ValueError("Native dual sides require typed journal history")
    State = ReadDualLive(History, IntegerValue(Context.Extrude.Fields["endModelHS"]))
    Local = LocalDualView(State, FrameValue)
    CheckDualCover(Local)
    CheckDualGeo(Local, Shape, FirstMm, SecondMm, FirstTaper, SecondTaper)
    CheckDualRims(Local, Shape, FirstMm, SecondMm, FirstTaper, SecondTaper)
    Operations, Primary = ReadDualOwners(Graph, Context, Model, Shape, Local)
    CheckDualTags(Local, Shape, Operations, Primary, FirstMm, SecondMm)
    CheckDualLinks(Local, Shape, FirstMm, SecondMm)
    return State
