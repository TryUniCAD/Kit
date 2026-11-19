from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the note reference resolves actual local data without an external component or selection cache
def MakeNoteReference(DataValue: ArchiveNode, VersionValue: int) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moCompNote_c", 1),
        {
            "f18": 0,
            "f1c": 0,
            "f20": 0,
            "f30": 0,
            "f34": 0,
            "f48": 0,
            "f4c": VersionValue,
            "f58": None,
            "f68": 0,
            "f70": 0,
            "f84": 0,
            "f90": -1,
            "f94": -1,
            "f98": -1,
            "f9c": -1,
            "fa0": 0,
            "has_fb0": 0,
            "has_fb8": 0,
            "has_fc0": 0,
            "has_fc8": 0,
            "has_fd0": 0,
            "fe8": DataValue,
            "ff8": None,
            "f100": 0,
        },
    )
