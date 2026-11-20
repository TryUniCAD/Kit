from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.Display.DisplayOwner import DisplayOwner
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    ReadRows,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KitResolvedStream


# xml visibility can be published only while native selected ownership agrees
def CheckDisplay(Archive: SldprtArchive, DisplayValue: DisplayOwner) -> None:
    VersionValue = ContainerMo(Archive.streams)
    if (
        VersionValue != 19000
        or DisplayValue.ConfigId != 0
        or Archive.format_version != 4
        or KitResolvedStream in Archive.streams
    ):
        raise ValueError(
            "assembly display state requires ordinary version 19000 Config-0"
        )
    Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), VersionValue)
    RootsValue = Manager.RootValue.FieldsValue
    ActiveValue = RequireNode(RootsValue.get("f360"), "moConfiguration_c")
    ConfigsValue = RequireRecord(RootsValue.get("f370"))
    (ConfigRow,) = ReadRows(ConfigsValue.get("items"))
    if (
        FieldInt(ConfigsValue, "n") != 1
        or ConfigRow.get("o") is not ActiveValue
        or RootsValue.get("f368") is not ActiveValue
        or FieldInt(ActiveValue.FieldsValue, "f08") != DisplayValue.ConfigId
        or ReadNodeName(ActiveValue) != DisplayValue.ConfigName
    ):
        raise ValueError(
            "assembly display state does not own the selected binary configuration"
        )
    Header = ReadHeaderGraph(
        Archive.require("Contents/Config-0-ModelHeader"), VersionValue
    )
    ConfigValue = ReadConfigMut(
        Archive.require("Contents/Config-0"), VersionValue, Header
    )
    if any(
        Report.get("completed") is not True
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
        for Report in (Manager.ReportValue, ConfigValue.ReportValue)
    ):
        raise ValueError(
            "assembly display state requires complete typed configuration owners"
        )
    ModelValue = RequireNode(ConfigValue.RootValue, "moAssembly_c")
    if ReadNodeName(ModelValue) != DisplayValue.ModelNativeName:
        raise ValueError("assembly display state refers to a foreign binary model")
    Occurrences = RequireRecord(
        RequireRecord(ModelValue.FieldsValue.get("f68")).get("list")
    )
    RowsValue = ReadRows(Occurrences.get("items"))
    if FieldInt(Occurrences, "n") != len(RowsValue) or len(RowsValue) != len(
        DisplayValue.MemberValues
    ):
        raise ValueError("assembly display state omits a live occurrence")
    for RowValue, MemberValue in zip(RowsValue, DisplayValue.MemberValues, strict=True):
        NodeValue = RequireNode(RowValue.get("o"), "moReference_c")
        LinkValue = RequireNode(NodeValue.FieldsValue.get("f4f8"), "moExtFeature_c")
        if (
            FieldInt(NodeValue.FieldsValue, "f08") != MemberValue.FeatureId
            or FieldInt(LinkValue.FieldsValue, "f44") != MemberValue.FeatureId
            or LinkValue.FieldsValue.get("f50") is not NodeValue
            or ReadNodeName(NodeValue) != MemberValue.NativeName
            or FieldInt(NodeValue.FieldsValue, "hidden") != 0
            or sum(
                ItemValue.EntryValue is NodeValue
                for ItemValue in ConfigValue.MapValue.EntriesValue
            )
            != 1
        ):
            raise ValueError(
                "assembly display visibility does not bind the actual binary occurrence"
            )
