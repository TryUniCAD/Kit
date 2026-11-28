from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# ordered native object collections derive their actual count from linked graph members
def MakeSweepRows(*NodeValues: ArchiveNode) -> dict[str, object]:
    return {
        "n": len(NodeValues),
        "items": tuple({"o": NodeValue} for NodeValue in NodeValues),
    }
