from dataclasses import replace as ReplaceValue

from pytest import raises as Raises

from interchange import CadDocument, PlaneAxis
from interchange.document.Models.DocumentError import DocumentError
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Interchange.Document.BoundPlaneAxisTests import BuildBoundAxis, ReadAxisDoc


# rounded points at a distant anchor must fit the line without retesting its generated direction
def CheckShortSpan() -> None:
    Document = ShortAxisDoc(1_000_000.0, 0.0, 0.01)
    Points = (
        SpaceVector(1_000_000.0, 0.0, 0.0),
        SpaceVector(1_000_000.006, 0.008, 0.0),
    )
    assert ReadAxisDoc(Document) == Points
    (StepValue,) = Document.feature_timeline
    Snapshot = PlaneAxis("base-pick", "side-pick", *Points)
    SnapshotDoc = ReplaceValue(
        Document,
        parameters=(),
        feature_timeline=(
            ReplaceValue(StepValue, definition=Snapshot, parameter_ids=()),
        ),
    )
    with Raises(
        DocumentError, match="direction differs from the support plane intersection"
    ):
        _ = CadDocument.from_json(SnapshotDoc.to_json())
    Collapsed = ShortAxisDoc(1.0e16, 1.0e16, 0.01)
    with Raises(DocumentError, match="distinct endpoints with a finite span"):
        _ = CadDocument.from_json(Collapsed.to_json())


# translated orthogonal frames give an analytic line across both model coordinates
def ShortAxisDoc(OffsetX: float, OffsetY: float, Length: float) -> CadDocument:
    Document = BuildBoundAxis()
    Origin = SpaceVector(OffsetX, OffsetY, 0.0)
    LowerPlane, SidePlane = Document.support_planes
    SideFrame = Transform(
        Origin,
        SpaceVector(0.0, 0.0, -1.0),
        SpaceVector(0.6, 0.8, 0.0),
        SpaceVector(0.8, -0.6, 0.0),
    )
    StartValue, EndValue = Document.parameters
    return ReplaceValue(
        Document,
        support_planes=(
            ReplaceValue(LowerPlane, transform=Transform(Origin)),
            ReplaceValue(SidePlane, transform=SideFrame),
        ),
        parameters=(
            ReplaceValue(StartValue, value=ReplaceValue(StartValue.value, value=0.0)),
            ReplaceValue(
                EndValue, value=ReplaceValue(EndValue.value, value=Length, unit="mm")
            ),
        ),
    )
