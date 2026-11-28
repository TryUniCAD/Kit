from types import MappingProxyType

from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmXmlRoles import (
    KAsmXmlRoles,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.SortKeyRow import (
    SortKeyRow,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import (
    ReadNotesInput,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

# part roots share the ordinary role vocabulary and add their own datum body and material roles
KImportRootRoles = MappingProxyType(
    {
        **{
            ClassName: KAsmXmlRoles[ClassName]
            for ClassName in (
                "moCommentsFolder_c",
                "moDetailCabinet_c",
                "moDocsFolder_c",
                "moEnvFolder_c",
                "moEqnFolder_c",
                "moFavoriteFolder_c",
                "moHistoryFolder_c",
                "moInkMarkupFolder_c",
                "moOriginProfileFeature_c",
                "moSelectionSetFolder_c",
                "moSensorFolder_c",
            )
        },
        "moBaseBody_c": ("Feature", "Imported"),
        "moMaterialFolder_c": ("Feature", "SOLIDWORKS Materials"),
        "moRefPlane_c": ("Feature", "Plane"),
        "moSolidBodyFolder_c": ("Feature", "Solid Bodies"),
        "moSurfaceBodyFolder_c": ("Feature", "Surface Bodies"),
    }
)

# member roles are indexed through their cabinet environment or direct configuration owner
KImportKeyRoles = MappingProxyType(
    {
        **KImportRootRoles,
        "moAmbientLight_c": KAsmXmlRoles["moAmbientLight_c"],
        "moDirectionLight_c": KAsmXmlRoles["moDirectionLight_c"],
        "moNotesAreaFtrFolder_c": KAsmXmlRoles["moNotesAreaFtrFolder_c"],
        "moPrtExplViewManager_c": KAsmXmlRoles["moExplViewManager_c"],
    }
)


# keyword rows derive from each actual typed containment lane and its persistent identity
def ReadImpKeyNodes(
    OwnerValue: ArchiveNode, RootsValue: tuple[ArchiveNode | None, ...]
) -> tuple[tuple[ArchiveNode, ...], tuple[KeywordFeature, ...], str]:
    _ = RequireNative(OwnerValue, "moPart_c")
    Roots = tuple(RequireNative(NodeValue) for NodeValue in RootsValue)
    EnvValue = RequireNative(OwnerValue.FieldsValue["f1e0"], "moEnvFolder_c")
    if sum(NodeValue is EnvValue for NodeValue in Roots) != 1 or any(
        NodeValue.ClassValue.NameValue not in KImportRootRoles for NodeValue in Roots
    ):
        raise ValueError("import keywords require their actual resolved part roots")
    (CabinetValue,) = (
        NodeValue
        for NodeValue in Roots
        if NodeValue.ClassValue.NameValue == "moDetailCabinet_c"
    )
    (MaterialValue,) = (
        NodeValue
        for NodeValue in Roots
        if NodeValue.ClassValue.NameValue == "moMaterialFolder_c"
    )
    if (
        sum(NodeValue.ClassValue.NameValue == "moBaseBody_c" for NodeValue in Roots)
        != 1
        or MaterialValue.FieldsValue.get("f378") != ""
        or FieldInt(MaterialValue.FieldsValue, "flags380") != 0x80000000
    ):
        raise ValueError("import keywords require one import and unassigned material")
    LightsValue = ReadChildren(EnvValue)
    if any(
        NodeValue.ClassValue.NameValue not in ("moAmbientLight_c", "moDirectionLight_c")
        or NodeValue.FieldsValue.get("owner", EnvValue) is not EnvValue
        for NodeValue in LightsValue
    ):
        raise ValueError("import keyword lights must belong to the actual environment")
    NotesValue = ReadChildren(CabinetValue)
    if NotesValue:
        _ = ReadNotesInput(NotesValue)
    if any(
        NodeValue.FieldsValue.get("owner", CabinetValue) is not CabinetValue
        for NodeValue in NotesValue
    ):
        raise ValueError("import keyword notes must belong to the actual cabinet")
    DirectValue = OwnerValue.FieldsValue["f13f8"]
    HelpersValue = (
        ()
        if DirectValue is None
        else (RequireNative(DirectValue, "moPrtExplViewManager_c"),)
    )
    if any(
        NodeValue.FieldsValue["f18"] is not None
        or NodeValue.FieldsValue.get("owner", OwnerValue) is not OwnerValue
        for NodeValue in HelpersValue
    ):
        raise ValueError(
            "import keyword exploded view requires a nameless config helper"
        )
    NodesValue = (*Roots, *LightsValue, *NotesValue, *HelpersValue)
    RolesValue = sorted(
        (
            (KImportKeyRoles[NodeValue.ClassValue.NameValue], NodeValue)
            for NodeValue in NodesValue
        ),
        key=SortKeyRow,
    )
    RowsValue = tuple(
        KeywordFeature(
            FieldInt(NodeValue.FieldsValue, "f08"),
            "" if NodeValue in HelpersValue else ReadNodeName(NodeValue),
            KindValue,
            TagValue,
            (),
            (),
            None,
            None,
        )
        for (TagValue, KindValue), NodeValue in RolesValue
    )
    return NodesValue, RowsValue, ReadNodeName(MaterialValue)
