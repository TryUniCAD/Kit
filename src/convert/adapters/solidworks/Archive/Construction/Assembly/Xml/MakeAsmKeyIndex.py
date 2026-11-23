from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmKeyNodes import (
    AsmKeyNodes,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmKeywordName import (
    AsmKeywordName,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.AsmXmlRoles import (
    KAsmXmlRoles,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordRef import (
    KeywordRef,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireRecord,
)


# assembly keywords must link each occurrence to its actual child file while sharing the part index writer
def MakeAsmKeyIndex(
    RootValue: ArchiveNode,
    FeatureValues: tuple[ArchiveNode, ...],
    HeaderValue: ArchiveNode,
    ConfigValue: ArchiveNode,
    Targets: tuple[tuple[ArchiveNode, ArchiveNode], ...],
) -> bytes:
    RowValues: list[KeywordFeature | KeywordRef] = []
    for NodeValue in AsmKeyNodes(RootValue, FeatureValues):
        TagValue, KindValue = KAsmXmlRoles[NodeValue.ClassValue.NameValue]
        RowValues.append(
            KeywordFeature(
                FieldInt(NodeValue.FieldsValue, "f08"),
                AsmKeywordName(NodeValue),
                KindValue,
                TagValue,
                (),
                (),
                None,
                None,
            )
        )
    for Reference, ChildFile in Targets:
        RowValues.append(
            KeywordRef(
                FieldInt(Reference.FieldsValue, "f08"),
                ReadNodeName(Reference),
                PureWindowsPath(ReadFileKey(ChildFile)[1]).stem,
            )
        )
    RowValues.sort(key=KeyIndexOrder)
    FileValue = ArchiveNode.RequireNode(HeaderValue.FieldsValue["f38"])
    EpochValue = FieldInt(RequireRecord(FileValue.FieldsValue.get("shared")), "f28")
    return MakeKeywords(
        ReadNodeName(RootValue),
        EpochValue,
        (
            KeywordConfig(
                FieldInt(ConfigValue.FieldsValue, "f08"),
                ReadNodeName(ConfigValue),
                None,
            ),
        ),
        tuple(RowValues),
        CompactTags=True,
    )


# native grouping orders tags and decimal identities independently of archive traversal
def KeyIndexOrder(RowValue: KeywordFeature | KeywordRef) -> tuple[str, str]:
    TagValue = (
        RowValue.TagValue if isinstance(RowValue, KeywordFeature) else "Reference"
    )
    return TagValue, str(RowValue.IdValue)
