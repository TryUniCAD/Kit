from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# unknown array element semantics must stop admission instead of becoming a generic raw payload
def CheckPacked(
    ScopeValue: FieldScope,
    NodeValue: ArchiveNode,
    RuleValue: NativeField,
    ItemCount: int,
) -> None:
    if RuleValue.ModeValue == "Empty":
        if ItemCount:
            raise BodyUnsupported(
                "generic native array element grammar is unavailable for nonempty payloads"
            )
        return
    WidthValue = ReadScopeValue(ScopeValue, RuleValue.OtherName)
    if (
        RuleValue.ModeValue != "Double"
        or WidthValue != 8
        or RuleValue.TypeValue != "f64"
        or NodeValue.ClassValue.NameValue
        not in ("moDisplayDistanceDim_c", "moDisplayAngularDim_c")
    ):
        raise BodyUnsupported(
            "packed native values require the proven ordinary display binary64 owner"
        )
