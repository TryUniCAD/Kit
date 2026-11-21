from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrRows import ReadCmgrRows
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the local expression requires the selected configuration and its directory row to agree
def CheckEqConfig(RootValue: ArchiveNode, NameValue: str) -> None:
    FieldsValue = RootValue.FieldsValue
    RowsValue = ReadCmgrRows(RootValue)
    if (
        len(RowsValue) != 1
        or FieldsValue.get("f40c") != 1
        or FieldsValue.get("f658") not in (0, 1)
    ):
        raise ValueError(
            "local width-depth equation requires one ordinary configuration"
        )
    ConfigValue = RequireNative(RowsValue[0], "moPartConfiguration_c")
    ConfigFields = ConfigValue.FieldsValue
    if (
        FieldsValue.get("f360") is not ConfigValue
        or FieldsValue.get("f368") is not ConfigValue
        or ConfigFields.get("f08") != 0
        or ConfigFields.get("f0c") != 0
        or ConfigFields.get("f2c") not in (0, 0x200)
        or ReadNativeName(ConfigValue) != NameValue
    ):
        raise ValueError("local width-depth equation does not own selected Config-0")
