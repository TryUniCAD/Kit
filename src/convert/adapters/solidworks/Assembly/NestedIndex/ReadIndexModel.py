from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.Assembly import NativeAsmA, NativeAsmFile
from convert.adapters.solidworks.Assembly.NestedIndex.IndexModel import (
    IndexFileKey,
    IndexModel,
)
from convert.adapters.solidworks.Assembly.NestedIndex.IndexConflict import IndexConflict
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    ReadRows,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KitDocStream


# physical headers and typed manager selections must identify the same owned indexed definition
def ReadIndexModel(
    Archive: SldprtArchive, Definition: NativeAsmA, FileValue: NativeAsmFile
) -> IndexModel:
    VersionValue = ContainerMo(Archive.streams)
    if (
        VersionValue != 19000
        or Archive.format_version != 4
        or Definition.document_type not in ("PART", "ASSEMBLY")
        or KitDocStream in Archive.streams
    ):
        raise ValueError("nested index requires an ordinary version-19000 Config-0")
    IsAssembly = Definition.document_type == "ASSEMBLY"
    Header = ReadHeaderGraph(
        Archive.require("Contents/Config-0-ModelHeader"), VersionValue
    )
    External = RequireNode(Header.FieldsValue.get("f38"), "moExtObject_c")
    FileKey = IndexFileKey(External)
    if (
        FileKey[2] != (3 if IsAssembly else 2)
        or FileKey[3] != FileValue.creation_time
        or FileKey[1] != PureWindowsPath(FileValue.source_path)
    ):
        raise IndexConflict("nested index file does not match its physical header")
    Config = ReadConfigMut(
        Archive.require("Contents/Config-0"),
        VersionValue,
        Header,
        AssemblyValue=IsAssembly,
    )
    RootValue = RequireNode(
        Config.RootValue, "moAssembly_c" if IsAssembly else "moPart_c"
    )
    Manager = ReadCmgrMut(
        Archive.require("Contents/CMgr"), VersionValue, AssemblyValue=IsAssembly
    ).RootValue
    Current = RequireNode(
        Manager.FieldsValue.get("f360"),
        "moConfiguration_c" if IsAssembly else "moPartConfiguration_c",
    )
    RowsValue = ReadRows(RequireRecord(Manager.FieldsValue.get("f370")).get("items"))
    CurrentId = FieldInt(Current.FieldsValue, "f08")
    if len(RowsValue) != 1 or CurrentId != 0:
        raise ValueError("typed nested index requires one physical Config-0")
    if (
        RowsValue[0].get("o") is not Current
        or Manager.FieldsValue.get("f368") is not Current
        or CurrentId != Definition.configuration_id
        or ReadNodeName(Current) != Definition.configuration_name
    ):
        raise IndexConflict(
            "nested index configuration does not match its active owner"
        )
    return IndexModel(RootValue, FileKey, ReadNodeName(RootValue))
