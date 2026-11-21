from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot

# disclosed native saves exercise constructor empty and populated mass cache slots in both orders
KSavedCircleCases = (
    ("CircleRadiusBoss-open-save.SLDPRT", (1,)),
    ("CircleRadiusBoss-fresh-reopen.SLDPRT", (1, 0)),
    ("CircleRadiusBoss-edited-fresh-reopen.SLDPRT", (0, 1)),
)


# each native save must keep its actual cache records and direct master ownership
def VerifySavedCfg(ArchiveValue: SldprtArchive, CountsValue: tuple[int, ...]) -> None:
    VersionValue = ContainerMo(ArchiveValue.streams)
    assert VersionValue == 19000
    DataValue = ArchiveValue.require("Contents/Config-0")
    HeaderValue = ReadHeaderGraph(
        ArchiveValue.require("Contents/Config-0-ModelHeader"), VersionValue
    )
    ConfigValue = ReadConfigMut(DataValue, VersionValue, HeaderValue)
    ModelFields = ConfigValue.RootValue.FieldsValue
    MasterValue = ArchiveNode.RequireNode(ModelFields["f1018"])
    assert MasterValue.ClassValue == RuntimeClass("moSheetMetalMaster_c", 1)
    assert MasterValue.FieldsValue["f358"] == []
    assert MasterValue.IndexValue is None
    assert all(
        Entry.EntryValue is not MasterValue
        for Entry in ConfigValue.MapValue.EntriesValue
    )
    RecordsValue = CastValue(list[dict[str, object]], ModelFields["f1628"])
    assert tuple(
        len(CastValue(list[object], RecordValue["f08"])) for RecordValue in RecordsValue
    ) == (CountsValue)
    assert [(RecordValue.get("f18") is not None) for RecordValue in RecordsValue] == [
        CountValue > 0 for CountValue in CountsValue
    ]
    OutputValue, RebuiltValue = WriteConfigMut(
        ConfigValue.RootValue, VersionValue, HeaderValue
    )
    assert OutputValue == DataValue and RebuiltValue.MapValue == ConfigValue.MapValue
    ManagerData = ArchiveValue.require("Contents/CMgr")
    ManagerValue = ReadCmgrMut(ManagerData, VersionValue)
    assert WriteCmgrMut(ManagerValue.RootValue, VersionValue) == ManagerData
    PropertyLists = [
        Entry.EntryValue
        for Entry in ManagerValue.MapValue.EntriesValue
        if isinstance(Entry.EntryValue, ArchiveNode)
        and Entry.EntryValue.ClassValue == RuntimeClass("moCustomPropertyList", 1)
    ]
    assert len(PropertyLists) == 1 and PropertyLists[0].FieldsValue["items"] == []
    MasterValue.FieldsValue["f358"] = [{"o": None}]
    try:
        _ = WriteConfigMut(ConfigValue.RootValue, VersionValue, HeaderValue)
    except BodyUnsupported as ErrorValue:
        assert "nonempty sheet metal master body list" in str(ErrorValue)
    else:
        raise AssertionError("nonempty direct sheet metal list was emitted")


# linked archive reemission must preserve actual saved metadata and allocate no direct master slot
def TestSavedConfig() -> None:
    CorpusPath = KRepoRoot / "re/solidworks/v2026/corpus/circle-saves"
    for NameValue, CountsValue in KSavedCircleCases:
        ArchiveValue = SldprtArchive.from_bytes((CorpusPath / NameValue).read_bytes())
        VerifySavedCfg(ArchiveValue, CountsValue)
