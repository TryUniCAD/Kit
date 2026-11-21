from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# insertion options are independently initialized native configuration objects with explicit absent display state and default suppression semantics
def MakeAsmOptions() -> ArchiveNode:
    FieldsValue: dict[str, object] = dict.fromkeys(
        (
            "f14",
            "f28",
            "f20",
            "f34",
            "f40",
            "f58",
            "f5c",
            "f60",
            "f68",
            "f6c",
            "f70",
            "f74",
        ),
        0,
    )
    FieldsValue.update(
        {
            "f08": 2,
            "f0c": 1,
            "f10": 1,
            "f18": 2,
            "f38": 6,
            "f3c": 1,
            "f48": "",
            "f50": -1,
            "f64": -1,
        }
    )
    return ArchiveNode(RuntimeClass("moConfig_c", 1), FieldsValue)
