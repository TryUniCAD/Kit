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

KLengthFactors = {
    "": 1.0,
    "mm": 1.0,
    "millimeter": 1.0,
    "millimeters": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
    "inch": 25.4,
    "inches": 25.4,
}

KAngleUnits = frozenset({"", "deg", "degree", "degrees"})


def LengthMm(Value: ParameterValue | None) -> float | None:
    if Value is None or Value.kind is not ValueKind.LENGTH:
        return None
    RawValue = Value.value
    Factor = KLengthFactors.get(Value.unit.casefold())
    if (
        Factor is None
        or isinstance(RawValue, bool)
        or not isinstance(RawValue, (int, float))
        or not MathValue.isfinite(float(RawValue))
    ):
        return None
    return float(RawValue) * Factor


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
    Millimeters = LengthMm(Value)
    return Millimeters is not None and float(format(Millimeters, ".15g")) == float(
        format(Expected, ".15g")
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
    DefinitionLength = LengthMm(Definition.length)
    if DefinitionLength is None:
        return True
    IsFreecad = DocumentData.source.format_id.casefold() == "freecad.fcstd" or any(
        (
            ParamData.owner_id == PadId
            and ParamData.attributes.get("freecad_path") in KFreecadPadProps
            for ParamData in DocumentData.parameters
        )
    )
    PadPaths: list[str] = []
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
            if not IsBoundLength(ParamData.value, DefinitionLength):
                return True
            continue
        if IsFreecad and isinstance(PathValue, str) and PathValue in KFreecadPadProps:
            PadPaths.append(PathValue)
            continue
        return True
    return bool(PadPaths) and (
        len(PadPaths) != len(KFreecadPadProps) or set(PadPaths) != KFreecadPadProps
    )
