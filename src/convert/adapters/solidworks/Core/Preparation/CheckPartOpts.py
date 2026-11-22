from typing import cast as CastValue
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.MeasFields import KPartMeasureOpt


# internal preparation must preserve standard option semantics without introducing a public switch that enables unqualified native writing
def CheckPartOpts(OptionsValue: WriteOptions | None) -> WriteOptions:
    SettingsValue: WriteOptions = (
        WriteOptions() if OptionsValue is None else OptionsValue
    )
    if not isinstance(CastValue(object, SettingsValue), WriteOptions):
        raise TypeError("plain part preparation requires ordinary WriteOptions")
    if any(
        type(Value) is not bool
        for Value in (
            CastValue(object, SettingsValue.overwrite),
            CastValue(object, SettingsValue.validate),
        )
    ):
        raise TypeError("write overwrite and validation flags must be boolean")
    if SettingsValue.configuration is not None and (
        type(CastValue(object, SettingsValue.configuration)) is not str
        or not SettingsValue.configuration
    ):
        raise TypeError("write configuration must be nonempty text or absent")
    DestinationFormat = SettingsValue.destination_format
    if DestinationFormat is not None and (
        type(CastValue(object, DestinationFormat)) is not str
        or DestinationFormat.casefold()
        not in ("solidworks.sldprt", "sldprt", ".sldprt")
    ):
        raise ValueError("plain part preparation requires a part destination format")
    AllowedNames = {
        "final_destination",
        "final_overwrite",
        "allow_carrier",
        "require_self_contained",
        "require_native_transfers",
        "allow_non_native",
        "portable",
        KPartMeasureOpt,
    }
    if set(SettingsValue.values) - AllowedNames:
        raise ValueError("unsupported plain part preparation options")
    for NameValue, FieldValue in SettingsValue.values.items():
        if (
            NameValue not in ("final_destination", KPartMeasureOpt)
            and type(FieldValue) is not bool
        ):
            raise TypeError("write policy options must be boolean: " + NameValue)
    return SettingsValue
