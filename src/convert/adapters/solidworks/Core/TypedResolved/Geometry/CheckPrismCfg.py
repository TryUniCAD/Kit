from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigFieldSets import (
    KConfigArrays,
    KConfigZeroes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckCfgMode import (
    CheckCfgMode,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# configuration overrides and body selections cannot be ignored when recreating a solid from one active history
def CheckPrismCfg(ConfigValue: ArchiveNode) -> None:
    Fields = RequireNative(ConfigValue, "moPartConfiguration_c").FieldsValue
    CheckCfgMode(ConfigValue)
    if Fields.get("f08") != 0 or Fields.get("f0c") != 0 or Fields.get("f2c") != 0:
        raise ValueError(
            "cache free prism requires the independent active configuration zero"
        )
    for FieldName in (
        *KConfigArrays,
        "fca8",
        "fce8",
        "fd20",
        "fdc8",
        "f528",
        "f6a8",
        "fa98",
        "f600",
        "fb68",
    ):
        if not IsLineState(Fields.get(FieldName)):
            raise ValueError(
                "cache free prism has configuration overrides or body state"
            )
    if any(
        Fields.get(FieldName) != 0
        for FieldName in (
            *KConfigZeroes,
            "fc60",
            "fc64",
            "fcc8",
            "ndc8_hi",
            "ndc8_lo",
            "nca8",
            "nce8",
            "nd20",
        )
        if FieldName != "f85c"
    ):
        raise ValueError("cache free prism has unsupported configuration modes")
    BodyValue = NativeRecord(Fields.get("f4d0"))
    for FieldName in ("f10", "f60", "f100", "f80", "f68", "f58", "f78", "f70"):
        if not IsLineState(BodyValue.get(FieldName)):
            raise ValueError("cache free prism has configuration body transforms")
    if any(
        BodyValue.get(FieldName) is not None
        for FieldName in ("fb0", "fb8", "fa0", "f88", "fa8")
    ):
        raise ValueError("cache free prism has configuration geometry attachments")
    if (
        BodyValue.get("f0c") != 1
        or BodyValue.get("f08") != -1
        or any(
            BodyValue.get(FieldName) != 0
            for FieldName in (
                "has_c8",
                "has_d0",
                "has_e0",
                "has_e8",
                "has_f0",
                "has_98",
                "fd8",
                "ff8",
            )
        )
    ):
        raise ValueError("cache free prism has configuration body selector modes")
