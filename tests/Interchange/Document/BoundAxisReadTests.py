from dataclasses import replace as ReplaceValue
from io import BytesIO

from pytest import raises as Raises

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.json.Adapter import JsonAdapter
from interchange import CadDocument
from interchange.document.Models.DocumentError import DocumentError
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from tests.Interchange.Document.BoundAxisCfgTests import AxisOverride
from tests.Interchange.Document.BoundPlaneAxisTests import BuildBoundAxis, ReadAxisDoc


# reading a requested variant validates its actual axis after choosing its station values
def CheckSelectAxis() -> None:
    Document = BuildBoundAxis()
    (Default,) = Document.configurations
    Saved = ReplaceValue(Default, overrides=(AxisOverride("end", 0.4),))
    Requested = Configuration(
        "requested", "Requested", overrides=(AxisOverride("end", -1.2),)
    )
    Stored = ReplaceValue(Document, configurations=(Saved, Requested))
    Payload = Stored.to_json().encode("utf-8")
    with Raises(DocumentError, match="distinct endpoints with a finite span"):
        _ = JsonAdapter().read(BytesIO(Payload))
    for StrictMode in (True, False):
        Loaded = JsonAdapter().read(
            BytesIO(Payload),
            ReadOptions(configuration=Requested.name, strict=StrictMode),
        )
        assert ReadAxisDoc(Loaded) == (
            SpaceVector(8.0, 18.0, 22.0),
            SpaceVector(8.0, 2.0, 22.0),
        )
        assert Loaded.parameters == Document.parameters
        with Raises(DocumentError, match="distinct endpoints with a finite span"):
            _ = JsonAdapter().read(
                BytesIO(Payload), ReadOptions(configuration=Saved.id, strict=StrictMode)
            )


# selecting a variant keeps unrelated graph ownership under normal structural validation
def CheckCfgLinks() -> None:
    Document = BuildBoundAxis()
    (Default,) = Document.configurations
    Saved = ReplaceValue(Default, overrides=(AxisOverride("missing", 0.4),))
    Requested = Configuration("requested", "Requested")
    Stored = ReplaceValue(Document, configurations=(Saved, Requested))
    with Raises(DocumentError, match="references missing parameter missing"):
        _ = JsonAdapter().read(
            BytesIO(Stored.to_json().encode("utf-8")),
            ReadOptions(configuration=Requested.name, strict=False),
        )


# suppression defers segment construction while keeping rigid support validation active
def CheckSuppFrame() -> None:
    Document = BuildBoundAxis()
    (StepValue,) = Document.feature_timeline
    Suppressed = ReplaceValue(
        Document, feature_timeline=(ReplaceValue(StepValue, suppressed=True),)
    )
    assert ReadAxisDoc(Suppressed) is None
    LowerPlane, SidePlane = Suppressed.support_planes
    FrameValue = ReplaceValue(SidePlane.transform, z_axis=SpaceVector(-1.0, 0.0, 0.0))
    Reflected = ReplaceValue(
        Suppressed,
        support_planes=(LowerPlane, ReplaceValue(SidePlane, transform=FrameValue)),
    )
    with Raises(DocumentError, match="require finite orthonormal right handed frames"):
        _ = CadDocument.from_json(Reflected.to_json())
