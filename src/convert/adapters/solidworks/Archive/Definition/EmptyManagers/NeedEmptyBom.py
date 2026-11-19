from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# a present bom owner qualifies only after its concrete class and genuinely empty typed list agree
def NeedEmptyBom(Value: object) -> None:
    if (
        not isinstance(Value, ArchiveNode)
        or Value.ClassValue != RuntimeClass("moBomInfoMgr_c", 1)
        or set(Value.FieldsValue) != {"n", "f08"}
    ):
        raise ValueError("empty BOM state requires its concrete schema one manager")
    FieldsValue = Value.FieldsValue
    CountValue = FieldsValue["n"]
    RowsValue = FieldsValue["f08"]
    if (
        type(CountValue) is not int
        or CountValue != 0
        or not isinstance(RowsValue, (tuple, list))
        or len(CastValue(Sequence[object], RowsValue)) != 0
    ):
        raise ValueError("populated or inconsistent BOM manager state is unsupported")


from collections.abc import Sequence
from typing import cast as CastValue
