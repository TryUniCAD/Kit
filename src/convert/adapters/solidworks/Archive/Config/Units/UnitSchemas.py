from types import MappingProxyType

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the measured ordinary unit table has a concrete root descriptor
KUnitTableClass = RuntimeClass("moUnitsTable_c", 1)

# the native table stores unit owners in stable ordinal roles
KUnitRowClasses = tuple(
    RuntimeClass(NameValue, 1)
    for NameValue in (
        "moLengthUserUnits_c",
        "moAngleUserUnits_c",
        "moNumberUserUnits_c",
        "moDensityUnits_c",
        "moFloatNumberUserUnits_c",
        "moSpringConstantUnits_c",
        "moUnitSysUnits_c",
        "moForceUnits_c",
        "moStressUnits_c",
        "moGravityUnits_c",
        "moLinearMotorUnits_c",
        "moRotaryMotorUnits_c",
        "moPowerUnits_c",
        "moEnergyUnits_c",
        "moTimeUnits_c",
        "moFrequencyUserUnits_c",
    )
)

# concrete schema admission must exclude inherited and embedded layout names
KUnitSchemas = MappingProxyType(
    {
        ClassValue.NameValue: (ClassValue.SchemaValue,)
        for ClassValue in (KUnitTableClass, *KUnitRowClasses)
    }
)
