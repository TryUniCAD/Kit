from pathlib import Path as FilePath

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ClassIndex import ClassIndex
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.EncodeString import EncodeString
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.EncodeTag import EncodeTag
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt


# a typed extra root exercises compatibility admission without inventing an unknown body grammar
def MakeCmgrExtra(ParentPath: FilePath) -> FilePath:
    Archive = SldprtArchive.from_bytes(ParentPath.read_bytes())
    CmgrBytes = Archive.require("Contents/CMgr")
    GraphValue = ReadCmgrMut(CmgrBytes, 19000)
    MapValue = ArchiveMaps(GraphValue.MapValue.CounterValue, GraphValue.MapValue)
    ClassSlot = ClassIndex(MapValue, RuntimeClass("moNodeName_c", 1))
    assert ClassSlot is not None
    ExtraBytes = EncodeTag(ArchiveTag("ClassRef", ClassSlot)) + EncodeString(
        CStringValue("authored additional manager root", True), IsSourceFrame=True
    )
    Streams = dict(Archive.streams)
    Streams["Contents/CMgr"] = CmgrBytes + ExtraBytes
    TargetPath = ParentPath.with_stem("ExtendedManager")
    with TargetPath.open("xb") as Output:
        _ = Output.write(build_sldprt(Streams))
    return TargetPath
