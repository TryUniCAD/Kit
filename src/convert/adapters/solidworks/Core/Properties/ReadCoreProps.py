from convert.adapters.solidworks.Core.Properties.ReadPropRoot import ReadPropRoot
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.CheckPropText import (
    CheckPropText,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PropertyNames import (
    KSummaryNamespaces,
    KSummaryTags,
)


# authored summary fields must remain distinct from native save author and timestamp provenance
def ReadCoreProps(BufferValue: bytes) -> dict[str, str]:
    RootValue = ReadPropRoot(BufferValue)
    if (
        RootValue.tag != "{" + KSummaryNamespaces["xmlns:cp"] + "}coreProperties"
        or RootValue.attrib
    ):
        raise ValueError("part summary has an unsupported root or attributes")
    TagsValue = {
        "{" + KSummaryNamespaces["xmlns:dc"] + "}" + Value: FieldName
        for FieldName, Value in KSummaryTags.items()
    }
    NativeTags = {
        "{" + KSummaryNamespaces["xmlns:dc"] + "}lastModifiedBy",
        "{" + KSummaryNamespaces["xmlns:dcterms"] + "}created",
        "{" + KSummaryNamespaces["xmlns:dcterms"] + "}modified",
    }
    SeenTags: set[str] = set()
    ResultValue: dict[str, str] = {}
    for ItemValue in RootValue:
        if ItemValue.tag in SeenTags or len(ItemValue) or ItemValue.attrib:
            raise ValueError("part summary contains duplicate or structured values")
        SeenTags.add(ItemValue.tag)
        if ItemValue.tag in TagsValue:
            ResultValue[TagsValue[ItemValue.tag]] = CheckPropText(ItemValue.text or "")
        elif ItemValue.tag not in NativeTags:
            raise ValueError("part summary contains an unqualified field")
    return ResultValue
