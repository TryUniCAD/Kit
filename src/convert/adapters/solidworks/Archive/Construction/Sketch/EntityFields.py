from convert.adapters.solidworks.Archive.Construction.Sketch.EntityVisible import (
    EntityVisible,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# ordinary local entities need complete common constructor state before geometry specific insertion changes
def EntityFields(SketchValue: ArchiveNode) -> dict[str, object]:
    return {
        "_sketch": SketchValue,
        "f08": 0,
        "f0c": -1,
        "vis": EntityVisible(),
        "f20": 0,
        "dflt": 0,
        "f30": 5,
        "f34": 1,
        "f38": 1,
        "lw": {"f06": 0, "f00": -1.0},
        "ext": None,
        "f54": 4,
        "f56": 0,
        "f50": 0,
        "group": None,
        "has_name": 0,
        "f68": 1.0,
        "f74": 0,
        "f78": 0,
    }
