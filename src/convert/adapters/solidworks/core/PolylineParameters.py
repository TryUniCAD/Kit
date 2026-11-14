from __future__ import annotations

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumValues import ValueKind

KFreecadPadProps = frozenset(
    {
        "AllowMultiFace",
        "AlongSketchNormal",
        "FuzzyTolerance",
        "Label",
        "Label2",
        "Length",
        "Length2",
        "Midplane",
        "Offset",
        "Offset2",
        "Refine",
        "Reversed",
        "SideType",
        "Suppressed",
        "TaperAngle",
        "TaperAngle2",
        "Type",
        "Type2",
        "UseCustomVector",
        "Visibility",
    }
)


def HasPolyLoss(DocumentData: CadDocument, PadId: str) -> bool:
    IsFreecad = DocumentData.source.format_id.casefold() == "freecad.fcstd"
    for ParamData in DocumentData.parameters:
        PathValue = ParamData.attributes.get("freecad_path")
        if ParamData.owner_id == PadId and ParamData.expression is None:
            if (
                IsFreecad
                and isinstance(PathValue, str)
                and PathValue in KFreecadPadProps
            ) or (ParamData.value.kind is ValueKind.LENGTH and ParamData.name == "D1"):
                continue
        return True
    return False
