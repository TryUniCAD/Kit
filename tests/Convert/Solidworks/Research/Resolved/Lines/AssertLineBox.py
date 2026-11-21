from math import isclose as IsClose

from interchange.document.Models.DocumentModel import CadDocument


# extrusion summary bounds must follow independent neutral vertices and depth rather than scanned profile shapes
def AssertLineBox(
    Document: CadDocument,
    VerticesValue: tuple[tuple[float, float], ...],
    DepthValue: float,
) -> None:
    BoxValue = Document.bodies[0].topology.bounding_box
    assert BoxValue is not None
    ActualBox = (
        BoxValue.minimum.x,
        BoxValue.minimum.y,
        BoxValue.minimum.z,
        BoxValue.maximum.x,
        BoxValue.maximum.y,
        BoxValue.maximum.z,
    )
    ExpectedBox = (
        min(Value[0] for Value in VerticesValue),
        min(Value[1] for Value in VerticesValue),
        0.0,
        max(Value[0] for Value in VerticesValue),
        max(Value[1] for Value in VerticesValue),
        DepthValue,
    )
    assert all(
        IsClose(ActualValue, ExpectedValue, rel_tol=0.0, abs_tol=1e-12)
        for ActualValue, ExpectedValue in zip(ActualBox, ExpectedBox, strict=True)
    )
