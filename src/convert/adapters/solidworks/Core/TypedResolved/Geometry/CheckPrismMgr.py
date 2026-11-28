from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigFieldSets import (
    KManagerArrays,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismCfg import (
    CheckPrismCfg,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the separate manager must prove a sole selected configuration rather than trusting keyword names or the first stored lane
def CheckPrismMgr(ManagerValue: CmgrGraph) -> None:
    Fields = ManagerValue.RootValue.FieldsValue
    RowsValue = NativeRows(NativeRecord(Fields.get("f370")).get("items"))
    if len(RowsValue) != 1 or Fields.get("f40c") != 1 or Fields.get("f658") != 0:
        raise ValueError("cache free prism requires one ordinary manager configuration")
    ConfigValue = RequireNative(RowsValue[0].get("o"), "moPartConfiguration_c")
    if Fields.get("f360") is not ConfigValue or Fields.get("f368") is not ConfigValue:
        raise ValueError(
            "cache free prism manager selection does not alias its actual configuration"
        )
    for CountName, FieldName in KManagerArrays:
        if Fields.get(CountName) != 0 or not IsLineState(Fields.get(FieldName)):
            raise ValueError(
                "cache free prism manager has additional contexts or references"
            )
    if Fields.get("f75c") != 2 or any(
        Fields.get(FieldName) != 0
        for FieldName in ("f55c", "f758", "f818", "f81c", "f860", "has8a0")
    ):
        raise ValueError("cache free prism manager has alternate constructor selectors")
    if (
        Fields.get("f6d0") is not None
        or not IsLineState(Fields.get("f5b0"))
        or not IsLineState(Fields.get("f730"))
    ):
        raise ValueError(
            "cache free prism manager has additional selection or attachment owners"
        )
    CheckPrismCfg(ConfigValue)
