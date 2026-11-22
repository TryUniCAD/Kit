from pathlib import PureWindowsPath
from typing import cast as CastValue
from xml.etree.ElementTree import Element, SubElement, tostring as XmlBytes
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.AddTargetFiles import (
    AddTargetFiles,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.AddTargetModels import (
    AddTargetModels,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.VisitXmlMut import (
    VisitXmlMut,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.XmlWalkState import (
    XmlWalkState,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# native nested indexes must enumerate the actual generated definition closure without flattening binary ownership or duplicating shared child models
def MakeNestedTree(TargetValue: TargetDocument) -> bytes:
    StateValue = XmlWalkState({}, [], [], {}, 2)
    ModelId = VisitXmlMut(StateValue, TargetValue)
    RootValue = Element(
        "swSolidWorks",
        {
            "xmlns": "http://www.solidworks.com/sw2003/schema",
            "swObjCount": str(StateValue.NextValue - 1),
            "swVersion": "19000",
        },
    )
    HeaderValue = SubElement(
        RootValue,
        "swHeader",
        {"swObjCount": str(len(StateValue.FileValues)), "swSavedInLDREditMode": "NO"},
    )
    ModelsValue = SubElement(
        RootValue, "swModelList", {"swObjCount": str(len(StateValue.ModelValues))}
    )
    AddTargetFiles(StateValue, HeaderValue)
    FileValue = ArchiveNode.RequireNode(TargetValue.HeaderValue.FieldsValue["f38"])
    AddTargetModels(
        StateValue, ModelsValue, PureWindowsPath(ReadFileKey(FileValue)[1]).stem
    )
    ConfigValue = TargetValue.CurrentConfig
    Configurations = SubElement(RootValue, "swConfigurationList", {"swObjCount": "1"})
    NeedsRebuild = FieldInt(ConfigValue.FieldsValue, "f968") != 1 and bool(
        FieldInt(ConfigValue.FieldsValue, "f0c") & 8
    )
    _ = SubElement(
        Configurations,
        "swConfiguration",
        {
            "id": "1",
            "swName": ReadNodeName(ConfigValue),
            "swID": str(ConfigValue.FieldsValue["f08"]),
            "swReference": ReadNodeName(TargetValue.RootValue),
            "swMostRecentConfiguration": "YES",
            "swConfigurationNeedsUpdate": "YES" if NeedsRebuild else "NO",
            "swDefeatureConfiguration": "NO",
            "swModelRef": str(ModelId),
        },
    )
    _ = SubElement(RootValue, "swExtFeatureList", {"swObjCount": "0"})
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>\r\n'
        + CastValue(bytes, XmlBytes(RootValue, encoding="utf-8")).replace(b" />", b"/>")
        + b"\r\n"
    )
