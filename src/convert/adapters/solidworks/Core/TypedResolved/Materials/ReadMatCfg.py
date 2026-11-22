from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Core.TypedResolved.Materials.ReadMatText import (
    ReadMatText,
)
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerGraph import ManagerGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Materials.CheckMatSlots import (
    CheckMatSlots,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# full manager pointers and the lightweight directory must identify the same physical configuration
def ReadMatCfg(
    ManagerValue: CmgrGraph, HeaderValue: ManagerGraph, PartValue: ArchiveNode
) -> ArchiveNode:
    ManagerFields = ManagerValue.RootValue.FieldsValue
    DirectoryList = NativeRecord(ManagerFields.get("f370"))
    ConfigRows = NativeRows(DirectoryList.get("items"))
    HeaderList = NativeRecord(HeaderValue.RootValue.FieldsValue.get("f08"))
    HeaderRows = NativeRows(HeaderList.get("items"))
    if (
        len(ConfigRows) != 1
        or len(HeaderRows) != 1
        or (ManagerFields.get("f40c"), DirectoryList.get("n"), HeaderList.get("n"))
        != (1, 1, 1)
    ):
        raise BodyUnsupported(
            "SOLIDWORKS assigned material requires one configuration directory row"
        )
    ConfigValue = RequireNative(ConfigRows[0].get("o"), "moPartConfiguration_c")
    HeaderRow = RequireNative(HeaderRows[0].get("o"), "dmConfigHeader_c")
    Fields = ConfigValue.FieldsValue
    Directory = HeaderRow.FieldsValue
    NameNode = RequireNative(Fields.get("f18"), "moNodeName_c")
    CheckMatSlots(ManagerValue.MapValue, ManagerValue.RootValue, ConfigValue, NameNode)
    CheckMatSlots(HeaderValue.MapValue, HeaderValue.RootValue, HeaderRow)
    FlagsValue = Directory.get("f44")
    if (
        ManagerFields.get("f360") is not ConfigValue
        or ManagerFields.get("f368") is not ConfigValue
        or tuple(Fields.get(NameValue) for NameValue in ("f08", "f0c", "f6a0"))
        != (0, 0, None)
        or tuple(Directory.get(NameValue) for NameValue in ("f08", "f30", "f34", "f40"))
        != (1, 0, -1, 0)
        or ReadMatText(Directory.get("f10")) != ReadNativeName(ConfigValue)
        or Directory.get("f38") != Fields.get("f860")
        or Directory.get("f48") != Fields.get("fbd0")
        or type(FlagsValue) is not int
        or FlagsValue & 0xFFFFFFFF != Fields.get("f4c4")
        or Directory.get("f50") != PartValue.FieldsValue.get("f1300")
    ):
        raise BodyUnsupported(
            "SOLIDWORKS material directory does not own the selected Config-0"
        )
    return ConfigValue
