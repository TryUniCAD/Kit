from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedDrawNumber,
)


# the admitted front orientation must retain its actual unrotated unit scale frame and finite placement
def CheckViewFrame(ViewValue: ArchiveNode) -> None:
    FieldsValue = ViewValue.FieldsValue
    FrameValue = NeedConceptMap(FieldsValue["f5e0"])
    Position = NeedConceptMap(FieldsValue["f778"])
    if (
        FrameValue["has_matrix"] != 0
        or FrameValue["f70"] != 1.0
        or FrameValue["f78"] != 0
        or Position["z"] != 0.0
        or int(NeedDrawNumber(FieldsValue["f610"])) & 48 != 16
    ):
        raise BodyUnsupported(
            "front drawing Definition has an unqualified projection frame"
        )
    for FieldName in ("f58", "f60", "f68"):
        _ = NeedDrawNumber(FrameValue[FieldName])
    for FieldName in ("x", "y", "z"):
        _ = NeedDrawNumber(Position[FieldName])
