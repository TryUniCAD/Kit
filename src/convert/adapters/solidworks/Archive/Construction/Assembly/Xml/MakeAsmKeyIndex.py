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
    Owners = AsmKeyNodes(RootValue, FeatureValues)
    References = tuple(
        MakeAsmKeyRef(Reference, ReadFileKey(ChildFile)[1])
        for Reference, ChildFile in Targets
    )
    return EmitAsmKeyIndex(
        RootValue,
        HeaderValue,
        ConfigValue,
        Owners,
        References,
    )


# the selected file leaf and concrete occurrence supply independent keyword fields
def MakeAsmKeyRef(Reference: ArchiveNode, FileName: str) -> KeywordRef:
    return KeywordRef(
        FieldInt(Reference.FieldsValue, "f08"),
        ReadNodeName(Reference),
        PureWindowsPath(FileName).stem,
    )


# decoded and generated assembly models share row vocabulary and the lexical index order
def EmitAsmKeyIndex(
    RootValue: ArchiveNode,
    HeaderValue: ArchiveNode,
    ConfigValue: ArchiveNode,
    Owners: tuple[ArchiveNode, ...],
    References: tuple[KeywordRef, ...],
) -> bytes:
    RowValues: list[KeywordFeature | KeywordRef] = []
    for NodeValue in Owners:
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
    RowValues.extend(References)
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
