from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# one selected stock edge must simultaneously own the radial item and the edge keeper reference
def ReadFilletRef(History: FilletHistory) -> ArchiveNode:
    Fields = History.OwnersValue.FilletValue.FieldsValue
    EdgeList = RequireNative(Fields["f848"], "suObList")
    (ChosenRow,) = NativeRows(EdgeList.FieldsValue["items"])
    Chosen = RequireNative(ChosenRow["o"], "moCompEdge_c")
    Driver = RequireNative(
        History.DriveValue.ItemValue.FieldsValue["f10"], "moCompEdge_c"
    )
    Reference = RequireNative(Chosen.FieldsValue["fe8"], "moEdgeRef_c")
    Keeper = NativeRecord(Fields["f820"])
    (KeepRow,) = NativeRows(NativeRecord(Keeper["ff0"])["items"])
    if (
        Chosen is Driver
        or Driver.FieldsValue["fe8"] is not Reference
        or KeepRow["o"] is not Reference
        or Chosen.FieldsValue.get("f18")
        != History.OwnersValue.AtomValue.FieldsValue["f140"]
        or Chosen.FieldsValue.get("f1c") != 0
        or tuple(Driver.FieldsValue.get(KeyValue) for KeyValue in ("f18", "f1c"))
        != (0, 0)
        or Reference.FieldsValue.get("fe8") != 0x200
        or Reference.FieldsValue.get("f08") != 4
    ):
        raise ValueError(
            "saved fillet radius and keeper do not own the actual selected edge"
        )
    return Reference
