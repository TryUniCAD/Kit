from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# fresh notebook storage gives each empty list its own owner and the journal its native schema
def MakeNotebook(JournalName: str) -> dict[str, object]:
    return {
        "f18": ArchiveNode(
            RuntimeClass("uoJournal_c", 0), {"f08": JournalName, "f10": 0, "f18": 0}
        ),
        "f10": {"items": []},
        "f28": 1,
        "f20": {"items": []},
        "f38": 1,
        "f30": {"items": []},
        "pending": {"items": []},
    }
