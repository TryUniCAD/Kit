from convert.adapters.solidworks.Core.Properties.ReadPropRoot import ReadPropRoot
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PropertyNames import (
    KConfigPropertyNamespace,
    KModelPropertyNamespace,
    KSummaryPropertyFormat,
)
from convert.adapters.solidworks.Core.Properties.ReadPropSection import ReadPropSection
from convert.adapters.solidworks.Drawing.Metadata.Writing.PropertyVocabulary import (
    KUserPropertyFormat,
)


# document and configuration bags use distinct roots while sharing the two measured native sections
def ReadCustomProps(BufferValue: bytes, IsConfig: bool) -> dict[str, str]:
    RootValue = ReadPropRoot(BufferValue)
    NamespaceValue, NameValue = (
        (KConfigPropertyNamespace, "ConfigProperties")
        if IsConfig
        else (KModelPropertyNamespace, "Properties")
    )
    if (
        RootValue.tag != "{" + NamespaceValue + "}" + NameValue
        or RootValue.attrib
        or len(RootValue) != 2
    ):
        raise ValueError("part properties have an unsupported root or section count")
    ExpectedValues = (
        {"name": "DocumentSummaryInformation", "fmtid": KSummaryPropertyFormat},
        {"name": "UserDefinedProperties", "fmtid": KUserPropertyFormat},
    )
    for ItemValue, ExpectedValue in zip(RootValue, ExpectedValues, strict=True):
        if ItemValue.tag != "propertySection" or ItemValue.attrib != ExpectedValue:
            raise ValueError("part property section identity is unqualified")
    _ = ReadPropSection(RootValue[0], IsConfig, False)
    return ReadPropSection(RootValue[1], IsConfig, True)
