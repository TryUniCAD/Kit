from dataclasses import replace as ReplaceValue
from math import sqrt as SquareRoot

from pytest import raises as Raises

from interchange import CadDocument, PlaneAxis
from interchange.document.Models.DocumentError import DocumentError
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Interchange.Document.PlaneAxisTests import BuildAxisDoc


# large translations must retain the signed offset encoded in the actual stored floats
def CheckShiftLine() -> None:
    Document = BuildAxisDoc()
    Shared = SquareRoot(0.5)
    TiltValue = 1.5e-9
    AxisPoint = float.fromhex("0x1.3fffd13ebbeaep+2")
    LowerPlane, SidePlane = Document.support_planes
    FrameX = SpaceVector(Shared, 0.0, -Shared)
    First = Transform(
        SpaceVector(0.001, 0.0, 0.0),
        FrameX,
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(Shared, 0.0, Shared),
    )
    Second = Transform(
        SpaceVector(1000.001, 5.0, -1000.0),
        FrameX,
        SpaceVector(-Shared * TiltValue, 1.0, -Shared * TiltValue),
        SpaceVector(Shared, TiltValue, Shared),
    )
    Document = ReplaceValue(
        Document,
        support_planes=(
            ReplaceValue(LowerPlane, transform=First),
            ReplaceValue(SidePlane, transform=Second),
        ),
    )
    Correct = ReadShiftAxis(Document, AxisPoint)
    assert CadDocument.from_json(Correct.to_json()) == Correct
    Rounded = ReadShiftAxis(Document, 5.0)
    with Raises(
        DocumentError, match="endpoints are outside the support plane intersection"
    ):
        _ = CadDocument.from_json(Rounded.to_json())


# fixed endpoint snapshots distinguish the stored coordinates from the rounded subtraction locus
def ReadShiftAxis(Document: CadDocument, AxisPoint: float) -> CadDocument:
    (StepValue,) = Document.feature_timeline
    Shared = SquareRoot(0.5)
    Definition = PlaneAxis(
        "base-pick",
        "side-pick",
        SpaceVector(0.001, AxisPoint, 0.0),
        SpaceVector(0.001 - Shared * 12.0, AxisPoint, Shared * 12.0),
    )
    return ReplaceValue(
        Document, feature_timeline=(ReplaceValue(StepValue, definition=Definition),)
    )
