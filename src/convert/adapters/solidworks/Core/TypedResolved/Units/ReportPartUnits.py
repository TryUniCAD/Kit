from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KAngleCodes,
    KLengthCodes,
    KMassCodes,
    KSystemCodes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedResolved.Units.ReadPartUnitNodes import (
    ReadUnitNodes,
)


# only measured custom document choices may be projected from the actual independent density owner
def ReportPartUnits(RootValue: ArchiveNode) -> dict[str, object]:
    if RootValue.ClassValue.NameValue != "moPart_c":
        return {}
    try:
        Units = ReadUnitNodes(RootValue)
        if FieldInt(Units["unit_system"].FieldsValue, "fb0") != KSystemCodes["custom"]:
            return {}
        LengthValue = Units["length"]
        LengthFields = LengthValue.FieldsValue
        AngleFields = Units["angle"].FieldsValue
        DensityFields = Units["density"].FieldsValue
        MassCode = FieldInt(DensityFields, "fc4")
        MassValue = next(
            (
                NameValue
                for NameValue, CodeValue in KMassCodes.items()
                if CodeValue == MassCode
            ),
            None,
        )
        if (
            FieldInt(LengthFields, "fb0") != KLengthCodes["mm"]
            or FieldInt(AngleFields, "fb0") != KAngleCodes["degree"]
            or MassValue is None
            or tuple(
                FieldInt(DensityFields, KeyValue)
                for KeyValue in ("fc0", "fc8", "fcc", "has_fb8")
            )
            != (3, 3, 0, 1)
        ):
            return {}
        DensityLength = RequireNode(DensityFields["fb8"], "moLengthUserUnits_c")
        if (
            DensityLength is LengthValue
            or DensityLength.ClassValue != LengthValue.ClassValue
            or DensityLength.FieldsValue != dict(LengthFields, fb8=None, f88=0.0)
        ):
            return {}
        PrecisionValues = tuple(
            FieldInt(FieldsValue, "f0c")
            for FieldsValue in (LengthFields, AngleFields, DensityFields)
        )
        if any(not 0 <= Value <= 16 for Value in PrecisionValues):
            return {}
    except (KeyError, TypeError, ValueError):
        return {}
    return {
        "document_units": {
            "system": "custom",
            "length": "mm",
            "angle": "degree",
            "mass": MassValue,
            "volume": "mm^3",
            "length_decimal_places": PrecisionValues[0],
            "angle_decimal_places": PrecisionValues[1],
            "mass_decimal_places": PrecisionValues[2],
        }
    }
