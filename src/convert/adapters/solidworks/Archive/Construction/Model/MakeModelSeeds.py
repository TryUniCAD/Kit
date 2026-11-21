from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# complete constructor bookkeeping must be generated before any saved geometry or active configuration exists
def MakeModelSeeds() -> dict[str, object]:
    return {
        "fdb0": ArchiveNode(
            RuntimeClass("moTransRefPlaneData_c", 1),
            {"f08": 1, "f0c": 1, "f10": 0xFF00, "f14": 0xFF, "f18": 0x5F, "f1c": 0},
        ),
        "ff80": 1000.0,
        "ff88": 1e-8,
        "fa98": {
            "kind": 2,
            "f18": EmptyRootRows(),
            "f110": -0x55555556,
            "f114": -0x44444445,
        },
        "fd50": 1,
        "f784": bytes(16),
        "f7a4": bytes(16),
        "f1300": 101,
        "fd88": {"f260": 100, "n6c": 0, "atoms": (), "fa8": 0},
        "fd90": {"f80": 10000, "fe0": 0, "n": 0, "objects": ()},
        "fce8": 0x32,
        "fcec": 0x6C,
        "fd44": 10,
        "feb0": KNoAnno,
        "feb4": KNoAnno,
        "feb8": 0,
        "f760": "",
        "f768": "",
    }
