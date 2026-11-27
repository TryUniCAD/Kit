from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# face identity and rank must come from the validated typed owner chains
def ReadFaceAttrs(
    Nodes: Mapping[int, XmtNode], Heads: Mapping[str, int], FaceIds: set[int]
) -> tuple[dict[int, int], dict[str, dict[int, int]]]:
    Unchanged: dict[int, int] = {}
    Orders: dict[str, dict[int, int]] = {}
    for NameValue, RoleName in (
        ("SWEntUnchanged", "unchanged"),
        ("DOWNSTREAM_FACE_ID", "downstream"),
    ):
        HeadValue = RequireXmt(Nodes, Heads[NameValue], 81)
        Definition = HeadValue.Integer("definition")
        Members = WalkXmtChain(
            Nodes,
            HeadValue.IndexValue,
            81,
            "next_of_type",
            "previous_of_type",
            "definition",
            Definition,
        )
        Ranks: dict[int, int] = {}
        for RankValue, IndexValue in enumerate(Members):
            Attribute = Nodes[IndexValue]
            FaceValue = RequireXmt(Nodes, Attribute.Integer("owner"), 14).IndexValue + 1
            if FaceValue in Ranks:
                raise ValueError(
                    "attributed active face annotation has duplicate owners"
                )
            Ranks[FaceValue] = RankValue
            if RoleName == "unchanged":
                (SlotValue,) = Attribute.Indexes("fields")
                (Identity,) = RequireXmt(Nodes, SlotValue, 82).Indexes("values")
                if Identity <= 0:
                    raise ValueError("attributed active face identity must be positive")
                Unchanged[FaceValue] = Identity
        if Ranks.keys() != {IndexValue + 1 for IndexValue in FaceIds}:
            raise ValueError(
                "attributed active face annotations do not cover the typed faces"
            )
        Orders[RoleName] = Ranks
    return Unchanged, Orders
