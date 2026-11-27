from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLabel import (
    ReadDualLabel,
)
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# source mutations must target actual live records rather than assuming saved offsets
def FindTagRecord(Model: DocumentModel, Sample: DualCase, RoleName: str) -> int:
    Context = SelectExtrusion(BuildGraph(Model))
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    StateId = IntegerValue(Context.Extrude.Fields["endModelHS"])
    Table = MakeLiveTable(History, StateId)
    Stable = tuple(sorted(Table.LiveSlots))
    State = ReadDualLive(History, StateId)
    for Index, Entity in enumerate(State.Entities):
        if isinstance(Entity, SketchAttrib) and RoleName == "sketch":
            return Table.Records[Stable[Index]]
        if isinstance(Entity, TimeAttrib) and RoleName == "time":
            return Table.Records[Stable[Index]]
        if not isinstance(Entity, TagAttrib):
            continue
        Physical = (
            "body"
            if isinstance(State.Entities[Entity.Links.OwnerRef], BodyNode)
            else ReadDualLabel(
                State, Entity.Links.OwnerRef, Sample.FirstMm, Sample.SecondMm
            )
        )
        if Physical == RoleName:
            return Table.Records[Stable[Index]]
    raise ValueError("Requested live physical tag record is absent")
