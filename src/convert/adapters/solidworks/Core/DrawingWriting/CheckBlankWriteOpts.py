from typing import cast as CastValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Format import (
    KDrawingFormatId,
    KDrawingSuffix,
    KPartFormatId,
)


# a blank drawing has one sheet and accepts the ordinary transactional write policy
def CheckBlankWriteOpts(OptionsValue: WriteOptions | None) -> WriteOptions:
    Settings = WriteOptions() if OptionsValue is None else OptionsValue
    if not isinstance(CastValue(object, Settings), WriteOptions):
        raise TypeError("native blank drawing requires WriteOptions")
    if (
        type(CastValue(object, Settings.overwrite)) is not bool
        or type(CastValue(object, Settings.validate)) is not bool
    ):
        raise TypeError("write overwrite and validation flags must be boolean")
    TargetFormat = Settings.destination_format
    if TargetFormat is not None and (
        type(CastValue(object, TargetFormat)) is not str
        or TargetFormat.casefold()
        not in (KPartFormatId, KDrawingFormatId, KDrawingSuffix, "slddrw")
    ):
        raise ValueError("native blank drawing requires a drawing destination format")
    PolicyKeys = {
        "final_overwrite",
        "allow_carrier",
        "require_self_contained",
        "require_native_transfers",
        "allow_non_native",
        "portable",
    }
    if Settings.configuration is not None or set(Settings.values) - (PolicyKeys | {"final_destination"}):
        raise ValueError("unsupported native blank drawing write options")
    if any(type(Settings.values[KeyValue]) is not bool for KeyValue in PolicyKeys & Settings.values.keys()):
        raise TypeError("native drawing write policy flags must be boolean")
    return Settings
