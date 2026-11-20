from pathlib import PureWindowsPath
from xml.etree.ElementTree import Element, SubElement
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
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
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# assembly keyword rows derive native roles from actual generated roots and sort their independent lexical identifier namespace before framing computed xml
def MakeAsmKeys(
    StateValue: AssemblyState,
    HeaderValue: ArchiveNode,
    ChildValue: PartCandidate,
    References: tuple[ArchiveNode, ...],
) -> bytes:
    FileValue = ArchiveNode.RequireNode(HeaderValue.FieldsValue["f38"])
    ChildFile = ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"])
    RootValue = Element(
        "Keywords",
        {
            "id": str(ReadFileKey(FileValue)[3]),
            "Name": ReadNodeName(StateValue.RootValue),
        },
    )
    ConfigValue = StateValue.CurrentConfig
    _ = SubElement(
        RootValue,
        "Configuration",
        {
            "id": str(ConfigValue.FieldsValue["f08"]),
            "Name": ReadNodeName(ConfigValue),
            "Type": "ConfigurationManager",
        },
    )
    EntriesValue = [
        (KAsmXmlRoles[NodeValue.ClassValue.NameValue], NodeValue)
        for NodeValue in AsmKeyNodes(StateValue.RootValue, StateValue.FeatureValues)
    ]
    EntriesValue.extend(
        (
            ("Reference", PureWindowsPath(ReadFileKey(ChildFile)[1]).stem + "-"),
            NodeValue,
        )
        for NodeValue in References
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
