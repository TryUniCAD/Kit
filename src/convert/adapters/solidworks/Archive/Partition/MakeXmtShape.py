from convert.adapters.solidworks.Archive.Partition.ShapeFields import ShapeFields
from convert.adapters.solidworks.Archive.Partition.XmtShape import XmtShape


# unchanged base layouts and explicit deltas share one original schema construction path
def MakeXmtShape(
    NameValue: str, BaseText: str, CurrentText: str | None = None
) -> XmtShape:
    BaseValue = ShapeFields(BaseText)
    return XmtShape(
        NameValue,
        BaseValue,
        BaseValue if CurrentText is None else ShapeFields(CurrentText),
    )
