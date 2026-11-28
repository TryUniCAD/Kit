from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# explicit saved counts must agree while fresh counts derive from actual colour rows
def NeedViewCount(FieldsValue: Mapping[str, object], RowCount: int) -> None:
    CountValue = FieldsValue.get("nf68", RowCount)
    if (
        type(CountValue) is not int
        or CountValue != RowCount
        or not 0 <= CountValue < (1 << 31)
    ):
        raise BodyUnsupported("drawing view state colour count disagrees with rows")
