from pathlib import PureWindowsPath
from xml.etree.ElementTree import Element, SubElement
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmKeyNodes import (
    AsmKeyNodes,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmKeywordName import (
    AsmKeywordName,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmXmlRoles import (
    KAsmXmlRoles,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.SortKeyRow import (
    SortKeyRow,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# nested keyword references must derive their native type from each actual target rather than reuse one part label across an assembly closure
def MakeNestedKeys(TargetValue: TargetDocument) -> bytes:
    FileValue = ArchiveNode.RequireNode(TargetValue.HeaderValue.FieldsValue["f38"])
    RootValue = Element(
        "Keywords",
        {
            "id": str(ReadFileKey(FileValue)[3]),
            "Name": ReadNodeName(TargetValue.RootValue),
        },
    )
    _ = SubElement(
        RootValue,
        "Configuration",
        {
            "id": str(TargetValue.CurrentConfig.FieldsValue["f08"]),
            "Name": ReadNodeName(TargetValue.CurrentConfig),
            "Type": "ConfigurationManager",
        },
    )
    EntriesValue = [
        (KAsmXmlRoles[NodeValue.ClassValue.NameValue], NodeValue)
        for NodeValue in AsmKeyNodes(TargetValue.RootValue, TargetValue.FeatureValues)
    ]
    for Reference, ChildValue in zip(
        TargetValue.ReferenceValues, TargetValue.ChildTargets, strict=True
    ):
        ChildFile = ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"])
        EntriesValue.append(
            (
                ("Reference", PureWindowsPath(ReadFileKey(ChildFile)[1]).stem + "-"),
                Reference,
            )
        )
    EntriesValue.sort(key=SortKeyRow)
    for (TagValue, KindValue), NodeValue in EntriesValue:
        _ = SubElement(
            RootValue,
            TagValue,
            {
                "id": str(NodeValue.FieldsValue["f08"]),
                "Name": AsmKeywordName(NodeValue),
                "Type": KindValue,
            },
        )
    return FrameKeywords(RootValue, True)
