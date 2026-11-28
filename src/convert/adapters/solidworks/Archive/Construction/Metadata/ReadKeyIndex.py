from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordIndex import (
    KeywordIndex,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.ReadKeyRow import (
    ReadKeyConfig,
    ReadKeyRow,
)
from convert.adapters.solidworks.Core.Native import ParseXml


# exact typed readback rejects unaccounted markup or ordering before returning model values
def ReadKeyIndex(Payload: bytes) -> KeywordIndex:
    RootValue = ParseXml(Payload)
    if RootValue.tag != "Keywords" or set(RootValue.attrib) != {"id", "Name"}:
        raise ValueError("keyword index lacks its actual document title and event")
    Layouts = {
        tuple(NodeValue.attrib).index("DissectableChildren")
        < tuple(NodeValue.attrib).index("DissectableRoot")
        for NodeValue in RootValue
        if {"DissectableChildren", "DissectableRoot"} <= NodeValue.attrib.keys()
    }
    if len(Layouts) > 1:
        raise ValueError("keyword index mixes incompatible cut attribute orders")
    IndexValue = KeywordIndex(
        RootValue.attrib["Name"],
        int(RootValue.attrib["id"]),
        tuple(
            ReadKeyConfig(NodeValue)
            for NodeValue in RootValue
            if NodeValue.tag == "Configuration"
        ),
        tuple(
            ReadKeyRow(NodeValue)
            for NodeValue in RootValue
            if NodeValue.tag != "Configuration"
        ),
        True,
        False not in Layouts,
    )
    if IndexValue.ToBytes() == Payload:
        return IndexValue
    Spaced = ReplaceValue(IndexValue, CompactTags=False)
    if Spaced.ToBytes() == Payload:
        return Spaced
    raise ValueError("keyword index differs from its classified typed representation")
