from pathlib import Path as FilePath

from pytest import mark as TestMark

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.ScopedExtrude import ScopedExtrude
from tests.Convert.Solidworks.Core.NativeWrites.EndEvidence import EndEvidence
from tests.Convert.Solidworks.Core.NativeWrites.RejectFields import RejectFields


# unknown end modes must fail consistently for both nesting and suppression states
@TestMark.parametrize(
    ("Family", "IsScoped"),
    (
        ("extrude", False),
        ("second", False),
        ("hole", False),
        ("extrude", True),
        ("second", True),
    ),
)
@TestMark.parametrize(
    "EndValue", (ExtrudeEnd.NATIVE, "native:32767", "future:termination")
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("IsSuppressed", (False, True))
def TestEndWrite(
    TmpPath: FilePath,
    Family: str,
    EndValue: ExtrudeEnd | str,
    IsNested: bool,
    IsSuppressed: bool,
    IsScoped: bool,
) -> None:
    RejectFields(
        EndEvidence(Family, EndValue, IsSuppressed, IsScoped), TmpPath, IsNested
    )


# depthless through all is valid neutral history while destination reconstruction still needs qualification
@TestMark.parametrize(("IsNested", "IsSuppressed"), ((False, False), (True, True)))
@TestMark.parametrize("IsScoped", (False, True))
def TestDepthless(
    TmpPath: FilePath, IsNested: bool, IsSuppressed: bool, IsScoped: bool
) -> None:
    Document = EndEvidence("depthless", ExtrudeEnd.THROUGH_ALL, IsSuppressed, IsScoped)
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document
    Definitions = tuple(
        (
            StepValue.definition.Extrusion
            if isinstance(StepValue.definition, ScopedExtrude)
            else StepValue.definition
        )
        for StepValue in Restored.feature_timeline
    )
    assert any(
        isinstance(Definition, ExtrudeFeature) and Definition.length is None
        for Definition in Definitions
    )
    RejectFields(
        Document, TmpPath, IsNested, "depthless extrusion reconstruction is unqualified"
    )
