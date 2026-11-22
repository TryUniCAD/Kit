from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import (
    EntityFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# authored positions and independent point creation order must retain the ordinary local point constructor semantics
def MakeRingPoint(
    SketchValue: ArchiveNode, PositionValue: tuple[float, float], IndexValue: int
) -> ArchiveNode:
    FieldsValue = EntityFields(SketchValue)
    FieldsValue.update(
        {
            "f0c": IndexValue + 1,
            "pflags": 0x1E,
            "pos": {"x": PositionValue[0], "y": PositionValue[1]},
            "fe4": 0,
            "fe8": 0,
            "h1": None,
            "h2": None,
            "fec": 0,
            "f108": -2,
            "p1": {"x": 0.0, "y": 0.0},
            "p2": {"x": 0.0, "y": 0.0},
            "has_jet": 0,
            "ff0": 0,
        }
    )
    return ArchiveNode(RuntimeClass("sgPoint", 1), FieldsValue)
