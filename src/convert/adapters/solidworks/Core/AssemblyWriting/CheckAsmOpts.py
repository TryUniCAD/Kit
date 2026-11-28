from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.AssemblyWriting.AsmOptionNames import (
    KAsmOptionNames,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Container.Format import (
    KAsmSuffix,
)


# existing companion backup limitations require assembly replacement to stay closed while all admitted options retain exact domains
def CheckAsmOpts(
    OptionsValue: WriteOptions | None, *, Measured: bool = False
) -> WriteOptions:
    SettingsValue = WriteOptions() if OptionsValue is None else OptionsValue
    RequireAsm(
        type(CastValue(object, SettingsValue)) is WriteOptions,
        "assembly writing requires ordinary write options",
    )
    RequireAsm(
        type(CastValue(object, SettingsValue.overwrite)) is bool
        and not SettingsValue.overwrite
        and SettingsValue.values.get("final_overwrite", False) is False,
        "assembly overwrite awaits separate shared transaction repair",
    )
    RequireAsm(
        type(CastValue(object, SettingsValue.validate)) is bool,
        "write validation flag requires its exact boolean domain",
    )
    FormatValue = SettingsValue.destination_format
    RequireAsm(
        FormatValue is None
        or FormatValue.casefold() in ("solidworks.sldasm", "sldasm", KAsmSuffix),
        "assembly writing requires an assembly destination format",
    )
    Allowed = KAsmOptionNames
    if Measured:
        Allowed = Allowed | {KPartMeasureOpt, "defer_native_delivery"}
    RequireAsm(
        set(SettingsValue.values) <= Allowed,
        "assembly writing has unsupported options",
    )
    for NameValue, FieldValue in SettingsValue.values.items():
        if NameValue in ("final_destination", "native_destination"):
            RequireAsm(
                isinstance(FieldValue, (str, FilePath)),
                "assembly destination option requires path text",
            )
        elif NameValue != KPartMeasureOpt:
            RequireAsm(
                type(FieldValue) is bool,
                "assembly policy option requires its exact boolean domain",
            )
    return SettingsValue
