from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# constructor collections retain the ordered object links and derive their element count
def MakeObList(*ObjectValues: ArchiveNode) -> dict[str, object]:
    return {"n": len(ObjectValues), "items": [{"o": Value} for Value in ObjectValues]}
