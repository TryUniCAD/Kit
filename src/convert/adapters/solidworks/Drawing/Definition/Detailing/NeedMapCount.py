from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# decoded counts must agree while fresh graph counts remain derived from their actual rows
def NeedMapCount(
    FieldsValue: Mapping[str, object], FieldName: str, RowCount: int
) -> None:
    CountValue = FieldsValue.get(FieldName, RowCount)
    if (
        type(CountValue) is not int
        or CountValue != RowCount
        or not 0 <= CountValue < (1 << 31)
    ):
        raise BodyUnsupported("drawing detailing index count disagrees with its rows")
