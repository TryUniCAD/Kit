from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordRef import (
    KeywordRef,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.ReadKeyDim import (
    ReadKeyDim,
)


# optional dissection words admit only the two classified boolean spellings
def ReadKeyBool(ValueInput: str | None) -> bool | None:
    if ValueInput is None:
        return None
    if ValueInput in ("true", "false"):
        return ValueInput == "true"
    raise ValueError("keyword dissection value must be a native boolean")


# configuration rows have independent identity and an optional material label
def ReadKeyConfig(NodeValue: Element) -> KeywordConfig:
    BaseAttrs = {"id", "Name", "Type"}
    if (
        set(NodeValue.attrib) not in (BaseAttrs, BaseAttrs | {"Material"})
        or NodeValue.get("Type") != "ConfigurationManager"
        or len(NodeValue)
    ):
        raise ValueError("keyword configuration has an unsupported row structure")
    return KeywordConfig(
        int(NodeValue.attrib["id"]), NodeValue.attrib["Name"], NodeValue.get("Material")
    )


# feature and occurrence rows resolve their own grammar before passing typed values to the writer
def ReadKeyRow(NodeValue: Element) -> KeywordFeature | KeywordRef:
    BaseAttrs = {"id", "Name"}
    TypeValue = NodeValue.get("Type")
    if not BaseAttrs <= NodeValue.attrib.keys():
        raise ValueError("keyword row lacks its actual identity or name")
    IdValue = int(NodeValue.attrib["id"])
    NameValue = NodeValue.attrib["Name"]
    if NodeValue.tag == "Reference":
        if (
            set(NodeValue.attrib) != BaseAttrs | {"Type"}
            or TypeValue is None
            or not TypeValue.endswith("-")
            or len(NodeValue)
        ):
            raise ValueError("keyword occurrence has an unsupported row structure")
        return KeywordRef(IdValue, NameValue, TypeValue.removesuffix("-"))
    if (
        set(NodeValue.attrib)
        - BaseAttrs
        - {
            "Type",
            "Dissectable",
            "DissectableRoot",
            "DissectableChildren",
        }
    ):
        raise ValueError("keyword feature carries unclassified attributes")
    ChildText = NodeValue.get("DissectableChildren")
    return KeywordFeature(
        IdValue,
        NameValue,
        TypeValue,
        NodeValue.tag,
        tuple(map(ReadKeyDim, NodeValue)),
        () if ChildText is None else (int(ChildText),),
        ReadKeyBool(NodeValue.get("Dissectable")),
        ReadKeyBool(NodeValue.get("DissectableRoot")),
    )
