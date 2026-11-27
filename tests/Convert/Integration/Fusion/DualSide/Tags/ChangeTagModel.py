from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.Tags.ChangeTagGraph import ChangeTagGraph
from tests.Convert.Integration.Fusion.DualSide.Tags.ChangeTagNode import ChangeTagNode
from tests.Convert.Integration.Fusion.DualSide.Tags.FindTagRecord import FindTagRecord
from tests.Convert.Integration.Fusion.DualSide.Tags.ExtendTagModel import ExtendTagModel


# typed source editing preserves actual archive serialization for every attribution counterexample
def ChangeTagModel(
    Model: DocumentModel, Sample: DualCase, CaseName: str
) -> DocumentModel:
    if CaseName in ("body_uuid", "history_end", "allocator_owner"):
        return ChangeTagGraph(Model, CaseName)
    if CaseName == "extended_tag":
        return ExtendTagModel(Model, Sample)
    RoleName = (
        "sketch"
        if CaseName.startswith("sketch")
        else (
            "time"
            if CaseName == "time_value"
            else (
                "body"
                if CaseName.startswith("body")
                else (
                    "first"
                    if CaseName == "side_operation"
                    else (
                        "lower"
                        if CaseName == "cap_label"
                        else "rim_lower" if CaseName == "rim_label" else "joint"
                    )
                )
            )
        )
    )
    Record = FindTagRecord(Model, Sample, RoleName)
    BodyValue = Model.Bodies[0]
    History = BodyValue.History
    assert isinstance(History, JournalModel)
    Table = MakeLiveTable(History, None)
    Reference = next(
        Stable for Stable in Table.LiveSlots if Table.Records[Stable] == Record
    )
    Entities = tuple(
        ChangeTagNode(Entity, CaseName, Reference) if Index == Record else Entity
        for Index, Entity in enumerate(History.Entities)
    )
    return ReplaceData(
        Model,
        Bodies=(
            ReplaceData(BodyValue, History=ReplaceData(History, Entities=Entities)),
        ),
    )
