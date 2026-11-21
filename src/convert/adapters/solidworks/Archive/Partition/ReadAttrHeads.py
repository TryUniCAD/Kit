from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# native attribute indices must own complete nonbranching chains for each registered definition
def ReadAttrHeads(
    NodesValue: Mapping[int, XmtNode], Definitions: tuple[int, ...]
) -> Mapping[int, int]:
    HeadsValue: dict[int, int] = {}
    DefinitionIds: set[int] = set()
    for NodeValue in NodesValue.values():
        if NodeValue.KindValue != 81:
            continue
        DefinitionIndex = NodeValue.Integer("definition")
        if DefinitionIndex not in Definitions:
            raise ValueError("native attribute is not registered")
        DefinitionIds.add(DefinitionIndex)
        if not NodeValue.Integer("previous_of_type"):
            if DefinitionIndex in HeadsValue:
                raise ValueError("native attribute definition has multiple chain heads")
            HeadsValue[DefinitionIndex] = NodeValue.IndexValue
        for Previous, Following, OwnerField in (
            ("previous", "next", "owner"),
            ("previous_of_type", "next_of_type", "definition"),
        ):
            if NextIndex := NodeValue.Integer(Following):
                NextValue = RequireXmt(NodesValue, NextIndex, 81)
                if NextValue.Integer(
                    Previous
                ) != NodeValue.IndexValue or NextValue.Integer(
                    OwnerField
                ) != NodeValue.Integer(
                    OwnerField
                ):
                    raise ValueError("native attribute chain is not reciprocal")
    if set(HeadsValue) != DefinitionIds:
        raise ValueError("native attribute definition has a headless chain")
    for DefinitionIndex, IndexValue in HeadsValue.items():
        MembersValue = WalkXmtChain(
            NodesValue,
            IndexValue,
            81,
            "next_of_type",
            "previous_of_type",
            "definition",
            DefinitionIndex,
        )
        if set(MembersValue) != {
            NodeValue.IndexValue
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue == 81
            and NodeValue.Integer("definition") == DefinitionIndex
        }:
            raise ValueError("native attribute definition chain is incomplete")
    return HeadsValue
