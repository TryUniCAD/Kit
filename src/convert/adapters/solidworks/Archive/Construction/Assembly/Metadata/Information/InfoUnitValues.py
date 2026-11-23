from convert.adapters.solidworks.Archive.Construction.Units.MakeDualLength import (
    MakeDualLength,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KLengthCodes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedResolved.Units.ReadPartUnitNodes import (
    ReadUnitNodes,
)


# unit publication must follow the actual document and dual format owners independently of analysis units
def InfoUnitValues(RootValue: ArchiveNode) -> dict[str, str | int | bool]:
    NodeValues = ReadUnitNodes(RootValue)
    Values = {
        NameValue: NodeValue.FieldsValue for NameValue, NodeValue in NodeValues.items()
    }
    LengthValue = Values["length"]
    PrimaryCode = FieldInt(LengthValue, "fb0")
    DualValue = ReadInfoDual(LengthValue.get("fb8"), PrimaryCode).FieldsValue
    DensityValue = Values["density"]
    if (
        FieldInt(DensityValue, "has_fb8")
        or FieldInt(DensityValue, "fcc") not in (0, 1)
        or FieldInt(DensityValue, "fc0") != FieldInt(DensityValue, "fc8")
    ):
        raise ValueError(
            "assembly information needs the ordinary inherited mass length and volume"
        )
    return {
        "SW_UnitSystem": FieldInt(Values["unit_system"], "fb0") + 1,
        "SW_UnitsLinear": PrimaryCode,
        "SW_UnitsLinearDecimalDisplay": FieldInt(LengthValue, "f10"),
        "SW_UnitsLinearDecimalPlaces": FieldInt(LengthValue, "f0c"),
        "SW_UnitsLinearFractionDenominator": FieldInt(LengthValue, "f28"),
        "SW_UnitsDualLinear": FieldInt(DualValue, "fb0"),
        "SW_UnitsTimeUnits": FieldInt(Values["time"], "fb0") + 1,
        "SW_UnitsPowerUnits": FieldInt(Values["power"], "fb0") + 1,
        "SW_UnitsEnergyUnits": FieldInt(Values["energy"], "fb0") + 1,
        "SW_UnitsDualLinearDecimalDisplay": FieldInt(DualValue, "f10"),
        "SW_UnitsDualLinearDecimalPlaces": FieldInt(DualValue, "f0c"),
        "SW_UnitsDualLinearFractionDenominator": FieldInt(DualValue, "f28"),
        "SW_UnitsAngular": FieldInt(Values["angle"], "fb0"),
        "SW_UnitsAngularDecimalPlaces": FieldInt(Values["angle"], "f0c"),
        "SW_UnitsMassPropLength": PrimaryCode,
        "SW_UnitsMassPropDecimalPlaces": FieldInt(DensityValue, "f0c"),
        "SW_UnitsMassPropMass": FieldInt(DensityValue, "fc4") + 1,
        "SW_UnitsMassPropVolume": FieldInt(DensityValue, "fc0") + 1,
        "SW_UnitsTimeDecimalPlaces": FieldInt(Values["time"], "f0c"),
        "SW_UnitsForce": FieldInt(Values["force"], "fb0") + 1,
        "SW_UnitsForceDecimalPlaces": FieldInt(Values["force"], "f0c"),
        "SW_UnitsPowerDecimalPlaces": FieldInt(Values["power"], "f0c"),
        "SW_UnitsEnergyDecimalPlaces": FieldInt(Values["energy"], "f0c"),
        "SW_UnitsDecimalRounding": 0,
        "SW_UnitsLinearFeetAndInchesFormat": 1,
        "SW_UnitsLinearRoundToNearestFraction": 0,
        "SW_UnitsDualLinearRoundToNearestFraction": 0,
        "SW_UnitsDualLinearFeetAndInchesFormat": 1,
    }


# the same missing dual length owner must make the shared constructor choice for its actual primary code
def ReadInfoDual(DualValue: object, PrimaryCode: int) -> ArchiveNode:
    if DualValue is not None:
        return RequireNode(DualValue, "moLengthUserUnits_c")
    for NameValue, CodeValue in KLengthCodes.items():
        if CodeValue == PrimaryCode:
            return MakeDualLength(NameValue)
    raise ValueError("assembly information has an unqualified primary length code")
