from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# lexical name projection must distinguish the witnessed explicit and implicit native owners
def ReadKernelName(
    NodesValue: Mapping[int, XmtNode], Attributes: Mapping[str, XmtNode]
) -> tuple[str, str | None]:
    if "SDL/TYSA_UNAME" in Attributes or "SW_INTERNAL_BODY_NAME" in Attributes:
        raise ValueError("native body has an unqualified alternate name owner")
    Implicit = Attributes["SWIMPLICITBODYNAME_ID_U"]
    Definition = RequireXmt(NodesValue, Implicit.Integer("definition"), 80)
    FieldsValue = Implicit.Indexes("fields")
    if (
        Definition.Indexes("fields") != (10, 10)
        or len(FieldsValue) != 2
        or FieldsValue[1]
    ):
        raise ValueError("native implicit name fields are unqualified")
    UnitsValue = RequireXmt(NodesValue, FieldsValue[0], 98).Indexes("values")
    if not UnitsValue or any(not 32 <= UnitValue <= 126 for UnitValue in UnitsValue):
        raise ValueError("native implicit name encoding is outside printable ascii")
    LabelValue = "".join(chr(UnitValue) for UnitValue in UnitsValue)
    Explicit = Attributes.get("SDL/TYSA_NAME")
    if Explicit is None:
        return LabelValue, None
    Definition = RequireXmt(NodesValue, Explicit.Integer("definition"), 80)
    FieldsValue = Explicit.Indexes("fields")
    if (
        Definition.Integer("type_id") != 8017
        or Definition.Indexes("fields") != (3,)
        or len(FieldsValue) != 1
    ):
        raise ValueError("native explicit name fields are unqualified")
    ExplicitLabel = RequireXmt(NodesValue, FieldsValue[0], 84).String("values")
    if (
        not 1 <= len(ExplicitLabel) <= 255
        or not ExplicitLabel.isascii()
        or not ExplicitLabel.isprintable()
        or ExplicitLabel != LabelValue
    ):
        raise ValueError(
            "native explicit and implicit body names disagree or have unqualified text"
        )
    return LabelValue, ExplicitLabel
