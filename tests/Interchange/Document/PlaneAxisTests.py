from dataclasses import replace as ReplaceValue

from pytest import raises as Raises

from interchange import CadDocument, PlaneAxis
from interchange.document.Models.DocumentError import DocumentError
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource


# an offset axis exercises real frame geometry and ordered document ownership in the same fixture
def BuildAxisDoc() -> CadDocument:
    OriginPoint = SpaceVector(8.0, 14.0, 22.0)
    LowerPlane = SupportPlane("base", "Offset base", Transform(OriginPoint))
    SidePlane = SupportPlane(
        "side",
        "Offset side",
        Transform(
            OriginPoint,
            SpaceVector(0.0, 0.0, -1.0),
            SpaceVector(0.0, 1.0, 0.0),
            SpaceVector(1.0, 0.0, 0.0),
        ),
    )
    FirstPick = Selection(
        "base-pick", "Base", (SelectPathElem("support_plane", "base"),)
    )
    SecondPick = Selection(
        "side-pick", "Side", (SelectPathElem("support_plane", "side"),)
    )
    Definition = PlaneAxis(
        FirstPick.id,
        SecondPick.id,
        SpaceVector(8.0, 18.0, 22.0),
        SpaceVector(8.0, 6.0, 22.0),
    )
    StepValue = FeatureStep(
        "axis",
        "Finite axis",
        FeatureKind.KReference,
        0,
        definition=Definition,
        selection_ids=(FirstPick.id, SecondPick.id),
    )
    return CadDocument(
        source=CadSource("kit-neutral", "", ""),
        configurations=(Configuration("default", "Default", True),),
        parameters=(),
        support_planes=(LowerPlane, SidePlane),
        sketches=(),
        selections=(FirstPick, SecondPick),
        feature_timeline=(StepValue,),
        bodies=(),
    )


# public document round trips must retain the authored order and explicit finite segment
def CheckAxisWire() -> None:
    Document = BuildAxisDoc()
    for DisplayUnit in UnitSystem:
        Candidate = ReplaceValue(Document, units=DisplayUnit)
        Payload = Candidate.to_json(indent=None)
        Restored = CadDocument.from_json(Payload)
        assert '"$type": "PlaneIntersectionAxis"' in Payload
        assert Restored == CadDocument.from_dict(Candidate.to_dict()) == Candidate
        assert Restored.support_planes == Document.support_planes
        Definition = Restored.feature_timeline[0].definition
        assert type(Definition) is PlaneAxis
        assert Definition.FirstPlaneSelectionId == "base-pick"
        assert Definition.StartMm.y > Definition.EndMm.y


# ordinary decode must refuse contradictory selection ownership and translated support geometry
def CheckAxisOwners() -> None:
    Document = BuildAxisDoc()
    (StepValue,) = Document.feature_timeline
    Swapped = ReplaceValue(StepValue, selection_ids=StepValue.selection_ids[::-1])
    Broken = ReplaceValue(Document, feature_timeline=(Swapped,))
    with Raises(DocumentError, match="inconsistent ordered selection roles"):
        _ = CadDocument.from_json(Broken.to_json())
    LowerPlane, SidePlane = Document.support_planes
    FrameValue = ReplaceValue(SidePlane.transform, origin=SpaceVector(9.0, 14.0, 22.0))
    Broken = ReplaceValue(
        Document,
        support_planes=(LowerPlane, ReplaceValue(SidePlane, transform=FrameValue)),
    )
    with Raises(
        DocumentError, match="endpoints are outside the support plane intersection"
    ):
        _ = CadDocument.from_json(Broken.to_json())


# a malformed support should surface an axis diagnostic through the ordinary document reader
def CheckAxisFrame() -> None:
    Document = BuildAxisDoc()
    LowerPlane, SidePlane = Document.support_planes
    Reflected = ReplaceValue(SidePlane.transform, z_axis=SpaceVector(-1.0, 0.0, 0.0))
    Broken = ReplaceValue(
        Document,
        support_planes=(LowerPlane, ReplaceValue(SidePlane, transform=Reflected)),
    )
    with Raises(
        DocumentError,
        match="plane axis supports require finite orthonormal right handed frames",
    ):
        _ = CadDocument.from_json(Broken.to_json())
