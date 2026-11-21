from dataclasses import replace as ReplaceValue

from pytest import raises as Raises

from interchange import CadDocument, PlaneAxis
from interchange.document.Models.DocumentError import DocumentError
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Interchange.Document.PlaneAxisTests import BuildAxisDoc


# nearly parallel frames need an actual line even where independent plane residuals are small
def BuildNearAxis(
    AngleValue: float, StartValue: SpaceVector, EndValue: SpaceVector
) -> CadDocument:
    Document = BuildAxisDoc()
    LowerPlane, SidePlane = Document.support_planes
    FrameValue = Transform(
        origin=SpaceVector(0.0, 2.5, 0.0),
        y_axis=SpaceVector(0.0, 1.0, -AngleValue),
        z_axis=SpaceVector(0.0, AngleValue, 1.0),
    )
    (StepValue,) = Document.feature_timeline
    Definition = PlaneAxis("base-pick", "side-pick", StartValue, EndValue)
    return ReplaceValue(
        Document,
        support_planes=(
            ReplaceValue(LowerPlane, transform=Transform()),
            ReplaceValue(SidePlane, transform=FrameValue),
        ),
        feature_timeline=(ReplaceValue(StepValue, definition=Definition),),
    )


# separated small angle planes must preserve a genuine translated intersection and reject off line segments
def CheckNearLine() -> None:
    StartValue = SpaceVector(5.0, 2.5, 0.0)
    EndValue = SpaceVector(-8.0, 2.5, 0.0)
    ValidAxis = BuildNearAxis(1.5e-9, StartValue, EndValue)
    assert CadDocument.from_json(ValidAxis.to_json()) == ValidAxis
    Perpendicular = BuildNearAxis(
        1.5e-9, SpaceVector(0.0, 2.5, 0.0), SpaceVector(0.0, 12.5, -7.5e-9)
    )
    with Raises(
        DocumentError, match="direction differs from the support plane intersection"
    ):
        _ = CadDocument.from_json(Perpendicular.to_json())
    Displaced = BuildNearAxis(
        1.5e-9, SpaceVector(0.0, 12.5, -7.5e-9), SpaceVector(8.0, 12.5, -7.5e-9)
    )
    with Raises(
        DocumentError, match="endpoints are outside the support plane intersection"
    ):
        _ = CadDocument.from_json(Displaced.to_json())
    NearParallel = BuildNearAxis(0.5e-9, StartValue, EndValue)
    with Raises(DocumentError, match="must define a unique intersection"):
        _ = CadDocument.from_json(NearParallel.to_json())
