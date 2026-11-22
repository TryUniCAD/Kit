from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.CheckAtomFlags import (
    CheckAtomFlags,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the attached circle requires one completed visible atom under the same feature and configuration
def ReadAttachAtom(
    LinkValue: NativeLink, BossValue: ArchiveNode, BodyId: int, *, SavedBody: bool
) -> int:
    CheckAtomFlags(BossValue, SavedBody)
    Fields = BossValue.FieldsValue
    RootFields = LinkValue.ConfigValue.RootValue.FieldsValue
    Manager = NativeRecord(RootFields.get("fd88"))
    Output = NativeRecord(Fields.get("f528"))
    (OutputRow,) = NativeRows(Output.get("items"))
    (ManagerRow,) = NativeRows(Manager.get("atoms"))
    (Visibility,) = NativeRows(RootFields.get("ffe0"))
    AtomValue = RequireNative(OutputRow.get("o"), "moAtom_c")
    Values = AtomValue.FieldsValue
    BodyTag = Values.get("f180")
    if (
        (Manager.get("n6c"), Manager.get("fa8"), Manager.get("f260"), Output.get("n"))
        != (1, 19000, BodyId, 1)
        or (RootFields.get("nff4"), RootFields.get("f1010")) != (1, 1)
        or ManagerRow.get("o") is not AtomValue
        or Visibility.get("k") is not AtomValue
        or (Visibility.get("v"), Values.get("f170"), Values.get("f188")) != (0, 0, 1)
        or Values.get("f18") is not None
        or type(BodyTag) is not int
        or BodyTag <= 0
        or Values.get("f1b0") != BodyTag
    ):
        raise ValueError(
            "SOLIDWORKS attached circle aliases disagree with its visible atom"
        )
    return BodyTag
