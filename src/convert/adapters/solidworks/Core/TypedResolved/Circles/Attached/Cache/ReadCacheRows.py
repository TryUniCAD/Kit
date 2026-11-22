from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# chooser cache arrays cannot substitute a foreign object for the actual creating boss
def ReadCacheRows(
    BossValue: ArchiveNode, NameValue: str, Expected: int
) -> tuple[Mapping[str, object], ...]:
    Chooser = NativeRecord(BossValue.FieldsValue.get(NameValue))
    ListValue = NativeRecord(Chooser.get("f48"))
    RowsValue = NativeRows(ListValue.get("items"))
    if (
        Chooser.get("f68") is not BossValue
        or ListValue.get("n") != len(RowsValue)
        or len(RowsValue) != Expected
    ):
        raise ValueError(
            "SOLIDWORKS attached circle chooser does not alias its own producer"
        )
    return RowsValue
