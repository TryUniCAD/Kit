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


def IsPadValue(
    Value: ParameterValue | None, KindValue: ValueKind, Expected: object
) -> bool:
    if Value is None or Value.kind is not KindValue:
        return False
    RawValue = Value.value
    if KindValue is ValueKind.LENGTH:
        Millimeters = LengthMm(Value)
        return Millimeters is not None and Millimeters == float(Expected)  # type: ignore[arg-type]
    if KindValue in {ValueKind.NUMBER, ValueKind.ANGLE}:
        return (
            not isinstance(RawValue, bool)
            and isinstance(RawValue, (int, float))
            and MathValue.isfinite(float(RawValue))
            and float(RawValue) == float(Expected)  # type: ignore[arg-type]
        )
    return RawValue == Expected


def PadValues(
    FeatureName: str, Definition: ExtrudeFeature
) -> dict[str, tuple[ValueKind, object]]:
    return {
        "AllowMultiFace": (ValueKind.BOOLEAN, True),
        "AlongSketchNormal": (ValueKind.BOOLEAN, True),
        "FuzzyTolerance": (ValueKind.NUMBER, -1.0),
        "Label": (ValueKind.STRING, FeatureName),
        "Label2": (ValueKind.STRING, ""),
        "Length2": (ValueKind.LENGTH, 10.0),
        "Midplane": (ValueKind.BOOLEAN, Definition.symmetric),
        "Offset": (ValueKind.LENGTH, 0.0),
        "Offset2": (ValueKind.LENGTH, 0.0),
        "Refine": (ValueKind.BOOLEAN, True),
        "Reversed": (ValueKind.BOOLEAN, Definition.reversed),
        "SideType": (ValueKind.INTEGER, 2 if Definition.symmetric else 0),
        "Suppressed": (ValueKind.BOOLEAN, False),
        "TaperAngle": (ValueKind.ANGLE, 0.0),
        "TaperAngle2": (ValueKind.ANGLE, 0.0),
        "Type": (ValueKind.INTEGER, 0),
        "Type2": (ValueKind.INTEGER, 0),
        "UseCustomVector": (ValueKind.BOOLEAN, False),
        "Visibility": (ValueKind.BOOLEAN, True),
    }


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
        or Definition.second_end_condition is not None
        or bool(Definition.up_to_reference)
        or bool(Definition.second_up_to_reference)
    ):
        return True
    DefinitionLength = LengthMm(Definition.length)
    if DefinitionLength is None:
        return True
    Direction = Definition.direction
    if Direction is not None and (
        Direction.x != 0.0 or Direction.y != 0.0 or Direction.z != 1.0
    ):
        return True
    IsFreecad = DocumentData.source.format_id.casefold() == "freecad.fcstd" or any(
        (
            ParamData.owner_id == PadId
            and ParamData.attributes.get("freecad_path") in KFreecadPadProps
            for ParamData in DocumentData.parameters
        )
    )
    return HasPadParamLoss(
        DocumentData,
        PadId,
        DefinitionLength,
        IsFreecad,
        PadValues(Features[0].name, Definition),
    )


def HasPadParamLoss(
    DocumentData: CadDocument,
    PadId: str,
    DefinitionLength: float,
    IsFreecad: bool,
    ExpectedValues: dict[str, tuple[ValueKind, object]],
) -> bool:
    PadPaths: list[str] = []
    for ParamData in DocumentData.parameters:
        PathValue = ParamData.attributes.get("freecad_path")
        if (
            ParamData.owner_id != PadId
            or ParamData.expression is not None
            or ParamData.role is not ParameterRole.DRIVING
        ):
            return True
        if IsFreecad and isinstance(PathValue, str) and PathValue in KFreecadPadProps:
            if PathValue == "Length":
                if not IsBoundLength(ParamData.value, DefinitionLength):
                    return True
                continue
            Expected = ExpectedValues.get(PathValue)
            if Expected is None or not IsPadValue(
                ParamData.value, Expected[0], Expected[1]
            ):
                return True
            PadPaths.append(PathValue)
            continue
        if ParamData.value.kind is ValueKind.LENGTH and ParamData.name == "D1":
            if not IsBoundLength(ParamData.value, DefinitionLength):
                return True
            continue
        return True
    ExpectedPaths = set(KFreecadPadProps) - {"Length"}
    return bool(PadPaths) and (
        len(PadPaths) != len(ExpectedPaths) or set(PadPaths) != ExpectedPaths
    )
