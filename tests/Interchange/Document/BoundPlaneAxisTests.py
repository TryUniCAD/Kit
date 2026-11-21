from dataclasses import replace as ReplaceValue

from pytest import raises as Raises

from interchange import BoundPlaneAxis, CadDocument
from interchange.document.Models.DocumentError import DocumentError
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.Axes.ResolveAxis import ResolveAxis
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter, ParameterValue
from tests.Interchange.Document.PlaneAxisTests import BuildAxisDoc


# two independently typed stations give the axis portable editable extent without a geometry snapshot
def BuildBoundAxis() -> CadDocument:
    Document = BuildAxisDoc()
    (StepValue,) = Document.feature_timeline
    Definition = BoundPlaneAxis("base-pick", "side-pick", "start", "end")
    StartValue = Parameter(
        "start",
        "Start",
        ParameterValue(4.0, ValueKind.KLength, "mm"),
        owner_id=StepValue.id,
    )
    EndValue = Parameter(
        "end",
        "End",
        ParameterValue(-0.8, ValueKind.KLength, "cm"),
        owner_id=StepValue.id,
    )
    FeatureValue = ReplaceValue(
        StepValue, parameter_ids=(StartValue.id, EndValue.id), definition=Definition
    )
    return ReplaceValue(
        Document, feature_timeline=(FeatureValue,), parameters=(StartValue, EndValue)
    )


# integration checks use the same geometry resolver as the public neutral validator
def ReadAxisDoc(Document: CadDocument) -> tuple[SpaceVector, SpaceVector] | None:
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document == CadDocument.from_dict(Document.to_dict())
    return ResolveAxis(
        Restored.feature_timeline[0],
        {Value.id: Value for Value in Restored.selections},
        {Value.id: Value for Value in Restored.support_planes},
        {Value.id: Value for Value in Restored.parameters},
        Restored.configurations,
    )


# editing selected support geometry and finite stations should rebuild their separate contributions
def CheckBoundMove() -> None:
    Document = BuildBoundAxis()
    assert ReadAxisDoc(Document) == (
        SpaceVector(8.0, 18.0, 22.0),
        SpaceVector(8.0, 6.0, 22.0),
    )
    LowerPlane, SidePlane = Document.support_planes
    NewFrame = ReplaceValue(SidePlane.transform, origin=SpaceVector(12.0, 14.0, 22.0))
    Moved = ReplaceValue(
        Document,
        support_planes=(LowerPlane, ReplaceValue(SidePlane, transform=NewFrame)),
    )
    assert ReadAxisDoc(Moved) == (
        SpaceVector(12.0, 18.0, 22.0),
        SpaceVector(12.0, 6.0, 22.0),
    )
    StartValue, EndValue = Moved.parameters
    Edited = ReplaceValue(EndValue, value=ReplaceValue(EndValue.value, value=-1.2))
    Rebuilt = ReplaceValue(Moved, parameters=(StartValue, Edited))
    assert ReadAxisDoc(Rebuilt) == (
        SpaceVector(12.0, 18.0, 22.0),
        SpaceVector(12.0, 2.0, 22.0),
    )


# document read must reject an axis whose linked lengths lose driving or ownership semantics
def CheckBoundOwner() -> None:
    Document = BuildBoundAxis()
    StartValue, EndValue = Document.parameters
    Foreign = ReplaceValue(StartValue, owner_id="elsewhere")
    Broken = ReplaceValue(Document, parameters=(Foreign, EndValue))
    with Raises(DocumentError, match="requires owned finite length parameters"):
        _ = CadDocument.from_json(Broken.to_json())
    Driven = ReplaceValue(EndValue, role=ParameterRole.KDriven)
    Broken = ReplaceValue(Document, parameters=(StartValue, Driven))
    with Raises(DocumentError, match="requires editable literal length parameters"):
        _ = CadDocument.from_json(Broken.to_json())
