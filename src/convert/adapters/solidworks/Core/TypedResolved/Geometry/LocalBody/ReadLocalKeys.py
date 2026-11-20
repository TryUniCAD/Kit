from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportKeyInput import (
    ImportKeyInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadImpKeyNodes import (
    KImportKeyRoles,
    ReadImpKeyNodes,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseKeywords, ParseXml
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadLocalExpl import (
    ReadLocalExpl,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

# these native role names distinguish the scoped index from earlier class name keyword rows
KNativeIndexRoles = frozenset(
    KindValue for _, KindValue in KImportKeyRoles.values()
) - {"Plane", "Origin", "Imported", "Notes", "Exploded Views"}


# local native roles need raw keyword identities joined to actual owners before the normalized import may provide geometry
def ReadLocalKeys(Archive: SldprtArchive) -> tuple[bool, int | None]:
    DataValue = Archive.get(KeywordsStream)
    if (
        DataValue is None
        or Archive.format_version != 4
        or ContainerMo(Archive.streams) != 19000
    ):
        return False, None
    RootValue = ParseXml(DataValue)
    Configs, RawRows = ParseKeywords(DataValue)
    CompactValue = (
        RootValue.tag == "Keywords" and FrameKeywords(RootValue, True) == DataValue
    )
    TypesValue = {RowValue.properties.get("Type") for RowValue in RawRows}
    if not (
        TypesValue.intersection(KNativeIndexRoles)
        or any(CfgValue.properties.get("Material") for CfgValue in Configs)
        or CompactValue
        and not TypesValue.intersection(KImportKeyRoles)
    ):
        return False, None
    try:
        LinkValue = ReadNativeLink(Archive, 0)
        _ = ReadLocalExpl(LinkValue)
        OwnerNodes, RowsValue, MaterialValue = ReadImpKeyNodes(
            LinkValue.ConfigValue.RootValue, LinkValue.ResolvedValue.RootsValue
        )
        CheckTreeAlias(LinkValue, OwnerNodes)
        Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000).RootValue
        FieldsValue = Manager.FieldsValue
        (ConfigRow,) = NativeRows(NativeRecord(FieldsValue["f370"])["items"])
        ConfigNode = RequireNative(ConfigRow.get("o"), "moPartConfiguration_c")
        if (
            NativeNodeId(ConfigNode) != 0
            or FieldsValue["f360"] is not ConfigNode
            or FieldsValue["f368"] is not ConfigNode
        ):
            return True, None
        IndexValue = ImportKeyInput(
            RootValue.attrib["Name"], int(RootValue.attrib["id"]), MaterialValue
        )
        ExpectedValue = MakeKeywords(
            IndexValue.TitleValue,
            IndexValue.SavedAt,
            (KeywordConfig(0, ReadNodeName(ConfigNode), MaterialValue),),
            RowsValue,
            CompactTags=True,
        )
        if DataValue != ExpectedValue:
            return True, None
        (ImportId,) = (
            RowValue.IdValue
            for RowValue in RowsValue
            if RowValue.KindValue == "Imported"
        )
    except (KeyError, TypeError, ValueError):
        return True, None
    return True, ImportId
