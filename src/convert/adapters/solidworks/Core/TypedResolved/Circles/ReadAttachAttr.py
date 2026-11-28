from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# actual body labels and identities must come from uniquely owned native attributes
def ReadAttachAttrs(
    NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode
) -> dict[str, tuple[int, ...]]:
    Chain = WalkXmtChain(
        NodesValue,
        BodyValue.Integer("attributes_features"),
        81,
        OwnerField="owner",
        OwnerValue=BodyValue.IndexValue,
    )
    if set(Chain) != {
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 81
        and NodeValue.Integer("owner") == BodyValue.IndexValue
    }:
        raise ValueError("SOLIDWORKS attached circle has detached body attributes")
    Found: dict[str, tuple[int, ...]] = {}
    for IndexValue in Chain:
        AttrValue = NodesValue[IndexValue]
        Definition = RequireXmt(NodesValue, AttrValue.Integer("definition"), 80)
        AttrName = RequireXmt(NodesValue, Definition.Integer("identifier"), 79).String(
            "string"
        )
        if AttrName in Found:
            raise ValueError("SOLIDWORKS attached circle has duplicate body attributes")
        if AttrName == "SWIMPLICITBODYNAME_ID_U":
            WordIndex, Empty = AttrValue.Indexes("fields")
            if Empty != 0:
                raise ValueError(
                    "SOLIDWORKS attached circle name has alternate storage"
                )
            Found[AttrName] = RequireXmt(NodesValue, WordIndex, 98).Indexes("values")
        elif AttrName in (
            "BODY_MATCH",
            "ENT_TIME_STAMP_2001",
            "ATOM_ID_2001",
            "LAST_BODY_MODIFYING_FEATURE_ID",
        ):
            (WordIndex,) = AttrValue.Indexes("fields")[-1:]
            Found[AttrName] = RequireXmt(NodesValue, WordIndex, 82).Indexes("values")
        else:
            Found[AttrName] = ()
    return Found
