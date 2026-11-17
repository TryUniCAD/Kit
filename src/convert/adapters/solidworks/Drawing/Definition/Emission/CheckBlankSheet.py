from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)


# blank sheets must retain their actual sketch aliases and the qualified unformatted paper state
def CheckBlankSheet(SheetValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    SheetFields = SheetValue.FieldsValue
    Supports = ReadBlankKids(SheetValue)
    if (
        tuple(ChildValue.ClassValue.NameValue for ChildValue in Supports)
        != ("moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c")
        or SheetFields["f408"] is not Supports[1]
        or SheetFields["f390"] is not Supports[2]
        or SheetFields["f39c"] != 0
        or SheetFields["f3c0"] != 13
        or SheetFields["f3b8"] != "*.drt"
        or SheetFields["f3f0"] != 11 * 0.0254
        or SheetFields["f3e8"] != 8.5 * 0.0254
        or SheetFields.get("has_f408") != 1
        or SheetFields.get("has_f468") != 0
        or SheetFields.get("has_f418") != 0
        or SheetFields.get("has_f450") != 0
        or SheetFields.get("f368_marker") != 65535
        or SheetFields["ink_views"]
        or NeedDrawNumber(SheetFields["f3f8"]) <= 0
        or NeedDrawNumber(SheetFields["f400"]) <= 0
    ):
        raise BodyUnsupported(
            "blank drawing Definition has unqualified sheet supports or format"
        )
    return Supports
