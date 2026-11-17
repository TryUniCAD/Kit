from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)


# a linked view must belong to the one active unformatted sheet with its original support aliases
def CheckFrontSheet(
    SheetValue: ArchiveNode, ModelValue: ArchiveNode
) -> tuple[ArchiveNode, ...]:
    FieldsValue = SheetValue.FieldsValue
    Children = ReadBlankKids(SheetValue)
    if (
        tuple(NodeValue.ClassValue.NameValue for NodeValue in Children)
        != ("moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c", "moAbsoluteView")
        or FieldsValue["owner"] is not ModelValue
        or any(
            NodeValue.FieldsValue["owner"] is not SheetValue for NodeValue in Children
        )
        or FieldsValue["f408"] is not Children[1]
        or FieldsValue["f390"] is not Children[2]
        or (FieldsValue["f39c"], FieldsValue["f3c0"], FieldsValue["f3b8"])
        != (0, 13, "*.drt")
        or (FieldsValue["f3f0"], FieldsValue["f3e8"]) != (11 * 0.0254, 8.5 * 0.0254)
        or FieldsValue.get("has_f408") != 1
        or any(
            FieldsValue.get(FieldName) != 0
            for FieldName in ("has_f468", "has_f418", "has_f450")
        )
        or FieldsValue.get("f368_marker") != 65535
        or FieldsValue["ink_views"]
        or NeedDrawNumber(FieldsValue["f3f8"]) <= 0
        or NeedDrawNumber(FieldsValue["f400"]) <= 0
    ):
        raise BodyUnsupported(
            "front drawing Definition requires one qualified active sheet and view"
        )
    return Children
