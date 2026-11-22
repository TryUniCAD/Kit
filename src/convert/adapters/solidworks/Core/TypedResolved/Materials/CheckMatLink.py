from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatSlots import (
    CheckMatSlots,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the selected configuration must link the same live atom and its actual producing feature
def CheckMatLink(
    ManagerValue: CmgrGraph, ConfigValue: ArchiveNode, AtomId: int, FeatureId: int
) -> None:
    ConfigFields = ConfigValue.FieldsValue
    RowsValue = NativeRows(ConfigFields.get("f450"))
    if len(RowsValue) != 1 or ConfigFields.get("n450") != 1:
        raise BodyUnsupported("SOLIDWORKS material needs one configuration linked body")
    LinkValue = RequireNative(RowsValue[0].get("o"), "moLinkedAtomIdNode_c")
    CheckMatSlots(ManagerValue.MapValue, LinkValue)
    Fields = LinkValue.FieldsValue
    LiveOwners = NativeRecord(Fields.get("f90"))
    OtherOwners = NativeRecord(Fields.get("fd0"))
    if (
        Fields.get("f08") != AtomId
        or LiveOwners.get("n") != 1
        or NativeRows(LiveOwners.get("items")) != ({"v": FeatureId},)
        or OtherOwners.get("n") != 0
        or NativeRows(OtherOwners.get("items"))
        or any(
            Fields.get(KeyValue) != 0 for KeyValue in ("nf0", "n100", "n110", "n120")
        )
        or any(
            NativeRows(Fields.get(KeyValue))
            for KeyValue in ("ff0", "f100", "f110", "f120")
        )
    ):
        raise BodyUnsupported(
            "SOLIDWORKS material linked body disagrees with its part atom"
        )
