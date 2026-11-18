from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Named.Checks.CheckNamedFrame import (
    CheckNamedFrame,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)


# named orientations extend only the proven projection fields while annotation and display payloads remain excluded
def CheckNamedState(ViewValue: ArchiveNode, OrientationValue: str) -> None:
    CheckNamedFrame(ViewValue, OrientationValue)
    FieldsValue = ViewValue.FieldsValue
    if (
        FieldsValue["f1030"] != 1
        or any(
            FieldsValue[FieldName] != 0
            for FieldName in (
                "f798",
                "has_f6c8",
                "has_f8e0",
                "has_f9d8",
                "has_fb50",
                "na10",
                "na18",
                "has_fe78",
            )
        )
        or any(FieldsValue[FieldName] for FieldName in ("f858", "ff48", "ff60"))
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
            "named drawing Definition excludes unqualified annotation and display payloads"
        )
