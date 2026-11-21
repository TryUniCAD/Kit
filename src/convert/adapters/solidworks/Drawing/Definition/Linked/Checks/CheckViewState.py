from convert.adapters.solidworks.Drawing.Definition.Rendering.ReadRenderState import (
    ReadRenderState,
)
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Linked.Checks.CheckViewFrame import (
    CheckViewFrame,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)


# one qualified front view must reject other view families and every unproved annotation or display payload
def CheckViewState(ViewValue: ArchiveNode) -> None:
    CheckViewFrame(ViewValue)
    _ = ReadRenderState(ViewValue, 19000)
    FieldsValue = ViewValue.FieldsValue
    if (
        FieldsValue["f1018"] != "*Front"
        or FieldsValue["f1010"] != 0
        or FieldsValue["f1030"] != 1
        or (FieldsValue["f780"], FieldsValue["f788"]) != (1.0, 1.0)
        or any(
            FieldsValue[FieldName] != 0
            for FieldName in (
                "f798",
                "has_f6c8",
                "has_f8e0",
                "has_f9d8",
                "na10",
                "na18",
                "has_fe78",
            )
        )
        or any(FieldsValue[FieldName] for FieldName in ("f858", "ff48"))
        or any(
            NeedConceptMap(FieldsValue[FieldName])["items"]
            for FieldName in (
                "fd28",
                "f900",
                "fb78",
                "fa20",
                "fa68",
                "fab0",
                "faf8",
                "fc28",
                "fc70",
                "fcb8",
                "fd48",
                "ff70",
            )
        )
        or any(
            FieldsValue[FieldName] is not None
            for FieldName in (
                "f968",
                "f8f8",
                "f640",
                "f658",
                "fb58",
                "f1008",
            )
        )
        or not FieldsValue["has_f648"]
    ):
        raise BodyUnsupported(
            "front drawing Definition excludes unqualified view families and display payloads"
        )
