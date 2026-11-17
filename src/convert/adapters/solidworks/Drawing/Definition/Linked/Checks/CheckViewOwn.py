from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import (
    ReadBlankKids,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode,
)


# ordered support pairs must bind their actual planes and containing drawing instead of matching numeric identifiers
def CheckViewOwn(ViewValue: ArchiveNode, ModelValue: ArchiveNode) -> None:
    FieldsValue = ViewValue.FieldsValue
    Children = ReadBlankKids(ViewValue)
    if (
        tuple(NodeValue.ClassValue.NameValue for NodeValue in Children)
        != (
            "moDetailFolder_c",
            "moRefPlane_c",
            "moProfileFeature_c",
            "moRefPlane_c",
            "moProfileFeature_c",
        )
        or any(
            NodeValue.FieldsValue["owner"] is not ViewValue for NodeValue in Children
        )
        or FieldsValue["f630"] is not Children[0]
        or FieldsValue["f7c8"] is not Children[2]
        or FieldsValue["fde0"] is not Children[4]
        or (FieldsValue["has_f7c8"], FieldsValue["has_fde0"]) != (1, 1)
    ):
        raise BodyUnsupported(
            "front drawing Definition has invalid view support ownership"
        )
    for PlaneValue, ProfileValue in (
        (Children[1], Children[2]),
        (Children[3], Children[4]),
    ):
        Wrapper = NeedConceptNode(
            ProfileValue.FieldsValue["pd_f78"], "moCompRefPlane_c"
        )
        Component = NeedConceptNode(Wrapper.FieldsValue["f58"], "moUnitComponent_c")
        if (
            Wrapper.FieldsValue["ff8"] is not PlaneValue
            or Component.FieldsValue["owner"] is not ModelValue
            or Component.FieldsValue["has_ext"] != 0
        ):
            raise BodyUnsupported(
                "front drawing Definition has a foreign support plane or component"
            )
    if (
        NeedConceptNode(Children[1].FieldsValue["f6f8"]).ClassValue.NameValue
        != "moDrawingRefPlnData_c"
        or NeedConceptNode(Children[3].FieldsValue["f6f8"]).ClassValue.NameValue
        != "moAbsoluteRefPlnData_c"
    ):
        raise BodyUnsupported(
            "front drawing Definition has unqualified support plane roles"
        )
