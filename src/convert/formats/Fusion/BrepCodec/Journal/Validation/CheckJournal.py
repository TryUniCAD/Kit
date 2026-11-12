from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckAllocTags import (
    CheckAllocTags,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckNode import CheckNode
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckStream import CheckStream
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckStates import CheckStates
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeStateNode import MakeStateNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader


def CheckJournal(Model: JournalModel) -> None:
    if Model.Header != BrepHeader(23200, 2, 3, 50.0, 1e-6, 1e-10):
        raise ValueError("Unsupported Fusion journal header profile")
    if type(Model.Entities) is not tuple or type(Model.States) is not tuple:
        raise ValueError("Fusion journal tables must be immutable tuples")
    if (
        type(Model.ActiveCount) is not int
        or not 1 <= Model.ActiveCount <= len(Model.Entities) <= 1024
        or not 2 <= len(Model.States) <= 256
    ):
        raise ValueError("Fusion journal entity/state quotas exceeded")
    if (
        not isinstance(Model.Entities[0], AsmRoot)
        or sum(isinstance(Value, AsmRoot) for Value in Model.Entities) != 1
    ):
        raise ValueError("Fusion journal requires one initial ASM header entity")
    if (
        sum(
            isinstance(Value, BodyNode) for Value in Model.Entities[: Model.ActiveCount]
        )
        != 1
    ):
        raise ValueError("Fusion journal requires one active body root")
    CheckStream(Model)
    CheckStates(Model)
    CheckAllocTags(Model)
    for Entity in Model.Entities:
        CheckNode(Entity)
    for State in Model.States:
        _ = EmitWireRecord(MakeStateNode(State))
