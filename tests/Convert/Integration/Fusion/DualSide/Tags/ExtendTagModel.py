from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.Tags.FindTagRecord import FindTagRecord


# reciprocal nested extensions expose unsupported live attributes through a valid typed archive
def ExtendTagModel(Model: DocumentModel, Sample: DualCase) -> DocumentModel:
    BodyValue = Model.Bodies[0]
    History = BodyValue.History
    assert isinstance(History, JournalModel)
    Table = MakeLiveTable(History, None)
    Joint = FindTagRecord(Model, Sample, "joint")
    Clock = FindTagRecord(Model, Sample, "time")
    JointRef = next(
        Stable for Stable in Table.LiveSlots if Table.Records[Stable] == Joint
    )
    ClockRef = next(
        Stable for Stable in Table.LiveSlots if Table.Records[Stable] == Clock
    )
    Parent = History.Entities[Joint]
    assert isinstance(Parent, TagAttrib)
    Entities = tuple(
        (
            ReplaceData(Parent, Attribute=ClockRef)
            if Index == Joint
            else NestedTag(JointRef, 999) if Index == Clock else Entity
        )
        for Index, Entity in enumerate(History.Entities)
    )
    return ReplaceData(
        Model,
        Bodies=(
            ReplaceData(BodyValue, History=ReplaceData(History, Entities=Entities)),
        ),
    )
