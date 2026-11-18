from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimBase import (
    CheckDimBase,
)


# only a complete ordinary binary coincidence may contribute a fixed origin constraint to a typed rectangle
def CheckOriginRel(FieldsValue: Mapping[str, object]) -> None:
    CheckDimBase(FieldsValue)
    if (
        FieldsValue.get("f80") != 9
        or FieldsValue.get("f28") is not None
        or FieldsValue.get("fa0") != 0xFFFE
        or FieldsValue.get("fa4") != 0
        or FieldsValue.get("f50") != -1
        or any(
            FieldsValue.get(NameValue) is not None
            for NameValue in ("f108", "ext1", "ext2", "ext3")
        )
        or any(
            FieldsValue.get(NameValue) != 0
            for NameValue in ("ff8", "ffc", "f100", "f150", "f118", "f120")
        )
        or any(
            FieldsValue.get(NameValue) != -1 for NameValue in ("f110", "f114", "f154")
        )
    ):
        raise ValueError("typed origin relation has unqualified operands or mode")
