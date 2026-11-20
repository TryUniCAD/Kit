from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadImplicitName import (
    ReadImplicit,
)


# lexical name projection must distinguish the witnessed explicit and implicit native owners
def ReadKernelName(
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
    AuthoredName: str | None = None,
) -> tuple[str, str | None]:
    if "SDL/TYSA_UNAME" in Attributes or "SW_INTERNAL_BODY_NAME" in Attributes:
        raise ValueError("native body has an unqualified alternate name owner")
    LabelValue = ReadImplicit(NodesValue, Attributes)
    IsWideName = not LabelValue.isascii()
    if IsWideName and AuthoredName != LabelValue:
        raise ValueError(
            "native wide body name lacks its agreeing actual archive owner"
        )
    Explicit = Attributes.get("SDL/TYSA_NAME")
    if Explicit is None:
        if IsWideName:
            raise ValueError(
                "native wide body name lacks its witnessed compatibility owner"
            )
        return LabelValue, None
    Definition = RequireXmt(NodesValue, Explicit.Integer("definition"), 80)
    FieldsValue = Explicit.Indexes("fields")
    if (
        Definition.Integer("type_id") != 8017
        or Definition.Indexes("fields") != (3,)
        or len(FieldsValue) != 1
    ):
        raise ValueError("native explicit name fields are unqualified")
    RawValue = RequireXmt(NodesValue, FieldsValue[0], 84).FieldsValue.get("values")
    if (
        not isinstance(RawValue, bytes)
        or not 1 <= len(RawValue) <= 255
        or b"\x00" in RawValue
    ):
        raise ValueError("native character compatibility payload is unqualified")
    if IsWideName:
        return LabelValue, LabelValue
    ExplicitLabel = RawValue.decode("ascii")
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
