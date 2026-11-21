from pathlib import PureWindowsPath
from typing import cast as CastValue
from xml.etree.ElementTree import Element, SubElement, tostring as XmlBytes
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.PutViewXmlMut import (
    PutViewXmlMut,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.XmlModelAttrs import (
    XmlModelAttrs,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.XmlNumbers import (
    XmlNumbers,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.XmlRefAttrs import (
    XmlRefAttrs,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# the instance index enumerates actual files models configuration and occurrences in its separately qualified xml namespace without importing binary object slots
def MakeAsmTree(
    StateValue: AssemblyState,
    HeaderValue: ArchiveNode,
    ChildValue: PartCandidate,
    References: tuple[ArchiveNode, ...],
    *,
    DisplayName: str | None = None,
) -> bytes:
    OwnerFile = ArchiveNode.RequireNode(HeaderValue.FieldsValue["f38"])
    ChildFile = ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"])
    RootPath = ReadFileKey(OwnerFile)[1]
    NameValue = PureWindowsPath(RootPath).stem
    RootValue = Element(
        "swSolidWorks",
        {
            "xmlns": "http://www.solidworks.com/sw2003/schema",
            "swObjCount": str(5 + len(References)),
            "swVersion": "19000",
        },
    )
    HeaderNode = SubElement(
        RootValue, "swHeader", {"swObjCount": "2", "swSavedInLDREditMode": "NO"}
    )
    ModelsValue = SubElement(RootValue, "swModelList", {"swObjCount": "2"})
    for FileId, KindValue, FileValue in (
        (3, "ASSEMBLY", OwnerFile),
        (6, "PART", ChildFile),
    ):
        FileKey = ReadFileKey(FileValue)
        _ = SubElement(
            HeaderNode,
            "swFile",
            {
                "id": str(FileId),
                "swDocType": KindValue,
                "swCreationTime": str(FileKey[3]),
                "swPath": FileKey[1],
            },
        )
    _ = SubElement(
        ModelsValue,
        "swModel",
        XmlModelAttrs(
            ChildValue.CurrentConfig,
            5,
            6,
            NameValue,
            FieldInt(References[0].FieldsValue, "f3e0"),
        ),
    )
    ConfigValue = StateValue.CurrentConfig
    OwnerAttrs = XmlModelAttrs(
        ConfigValue, 2, 3, NameValue, FieldInt(ConfigValue.FieldsValue, "f860")
    )
    BoundsValue = FieldRecord(StateValue.RootValue.FieldsValue["f1a18"])
    OwnerAttrs["swBoundingBox"] = XmlNumbers(
        RequireScalar(BoundsValue[f"b{IndexValue}"])
        for IndexValue in (6, 7, 8, 3, 4, 5)
    )
    OwnerAttrs["swAssemblyFeatureEffectedComponents"] = ""
    OwnerNode = SubElement(ModelsValue, "swModel", OwnerAttrs)
    for IndexValue, Reference in enumerate(References):
        _ = SubElement(
            OwnerNode,
            "swReference",
            XmlRefAttrs(Reference, 4 if IndexValue == 0 else IndexValue + 6),
        )
    Configurations = SubElement(RootValue, "swConfigurationList", {"swObjCount": "1"})
    NeedsRebuild = FieldInt(ConfigValue.FieldsValue, "f968") != 1 and bool(
        FieldInt(ConfigValue.FieldsValue, "f0c") & 8
    )
    ConfigNode = SubElement(
        Configurations,
        "swConfiguration",
        {
            "id": "1",
            "swName": ReadNodeName(ConfigValue),
            "swID": str(ConfigValue.FieldsValue["f08"]),
            "swReference": ReadNodeName(StateValue.RootValue),
            "swMostRecentConfiguration": "YES",
            "swConfigurationNeedsUpdate": "YES" if NeedsRebuild else "NO",
            "swDefeatureConfiguration": "NO",
            "swModelRef": "2",
        },
    )
    if DisplayName is not None:
        PutViewXmlMut(RootValue, ConfigNode, References, DisplayName)
    _ = SubElement(RootValue, "swExtFeatureList", {"swObjCount": "0"})
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>\r\n'
        + CastValue(bytes, XmlBytes(RootValue, encoding="utf-8")).replace(b" />", b"/>")
        + b"\r\n"
    )
