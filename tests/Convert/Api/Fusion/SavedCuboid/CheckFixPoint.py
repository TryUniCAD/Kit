from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from interchange.geometry.Models.Sketch import Sketch


# fixed point properties must preserve the separate native corner and construction origin identities
def CheckFixPoint(Graph: NativeGraph, SketchValue: Sketch) -> None:
    FixedPoints = tuple(
        Value
        for Value in Graph.ByClass("Point3D")
        if Value.Fields["isFixed"] and not Value.Fields["isOrigin"]
    )
    assert len(FixedPoints) == 1
    Entities = {Value.id: Value for Value in SketchValue.entities}
    assert Entities[FixedPoints[0].Identity].fixed is True
    assert Entities[FixedPoints[0].Identity].construction is False
    Origins = tuple(
        Value for Value in Graph.ByClass("Point3D") if Value.Fields["isOrigin"]
    )
    assert len(Origins) == 1 and Origins[0].Identity != FixedPoints[0].Identity
    assert Entities[Origins[0].Identity].fixed is True
    assert Entities[Origins[0].Identity].construction is True
