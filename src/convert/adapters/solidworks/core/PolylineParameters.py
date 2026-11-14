from __future__ import annotations

import math as MathValue

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.features.FeatureExtrude import ExtrudeFeature
from interchange.records.RecordParameter import ParameterValue

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

KLengthUnits = frozenset({"", "mm", "millimeter", "millimeters"})

KAngleUnits = frozenset({"", "deg", "degree", "degrees"})


def IsExactLength(Value: ParameterValue | None, Expected: float) -> bool:
    if Value is None:
        return False
    RawValue = Value.value
    return (
        Value.kind is ValueKind.LENGTH
        and Value.unit.casefold() in KLengthUnits
        and not isinstance(RawValue, bool)
        and isinstance(RawValue, (int, float))
        and MathValue.isfinite(float(RawValue))
        and float(RawValue) == Expected
    )


def IsExactAngle(Value: ParameterValue | None, Expected: float) -> bool:
    if Value is None:
        return False
    RawValue = Value.value
    return (
        Value.kind is ValueKind.ANGLE
        and Value.unit.casefold() in KAngleUnits
        and not isinstance(RawValue, bool)
        and isinstance(RawValue, (int, float))
        and MathValue.isfinite(float(RawValue))
        and float(RawValue) == Expected
    )


def IsUnsetLength(Value: ParameterValue | None, Expected: float) -> bool:
    return Value is None or IsExactLength(Value, Expected)


def IsUnsetAngle(Value: ParameterValue | None, Expected: float) -> bool:
    return Value is None or IsExactAngle(Value, Expected)


def IsBoundLength(Value: ParameterValue | None, Expected: float) -> bool:
    if Value is None:
        return False
    RawValue = Value.value
    return (
        Value.kind is ValueKind.LENGTH
        and Value.unit.casefold() in KLengthUnits
        and not isinstance(RawValue, bool)
        and isinstance(RawValue, (int, float))
        and MathValue.isfinite(float(RawValue))
        and MathValue.isclose(float(RawValue), Expected, rel_tol=0.0, abs_tol=1e-09)
    )


def HasPolyLoss(DocumentData: CadDocument, PadId: str) -> bool:
    Configs = DocumentData.configurations
    if (
        len(Configs) != 1
        or not Configs[0].active
        or Configs[0].parent_id is not None
        or Configs[0].overrides
        or Configs[0].suppressed_feature_ids
    ):
        return True
    Features = tuple(
        Feature for Feature in DocumentData.feature_timeline if Feature.id == PadId
    )
    if len(Features) != 1:
        return True
    Definition = Features[0].definition
    if (
        not isinstance(Definition, ExtrudeFeature)
        or not IsUnsetLength(Definition.second_length, 10.0)
        or not IsUnsetLength(Definition.offset, 0.0)
        or not IsUnsetLength(Definition.second_offset, 0.0)
        or not IsUnsetAngle(Definition.draft_angle, 0.0)
        or not IsUnsetAngle(Definition.second_draft_angle, 0.0)
    ):
        return True
    DefinitionLength = Definition.length.value
    if (
        isinstance(DefinitionLength, bool)
        or not isinstance(DefinitionLength, (int, float))
        or not MathValue.isfinite(float(DefinitionLength))
    ):
        return True
    IsFreecad = DocumentData.source.format_id.casefold() == "freecad.fcstd"
    for ParamData in DocumentData.parameters:
        PathValue = ParamData.attributes.get("freecad_path")
        if (
            ParamData.owner_id != PadId
            or ParamData.expression is not None
            or ParamData.role is not ParameterRole.DRIVING
        ):
            return True
        IsDepth = (
            ParamData.value.kind is ValueKind.LENGTH and ParamData.name == "D1"
        ) or (IsFreecad and PathValue == "Length")
        if IsDepth:
            if not IsBoundLength(ParamData.value, float(DefinitionLength)):
                return True
            continue
        if IsFreecad and isinstance(PathValue, str) and PathValue in KFreecadPadProps:
            continue
        return True
    return False
