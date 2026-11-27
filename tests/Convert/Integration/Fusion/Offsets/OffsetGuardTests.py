from hashlib import sha256 as HashBytes
import json as JsonLib
from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from tests.Convert.Integration.Fusion.MakeBadLabel import MakeBadLabel
from tests.Convert.Integration.Fusion.MakeOffsetPlane import MakeOffsetPlane
from tests.Convert.Integration.Fusion.Offsets.ChangeOffset import ChangeOffset


# new start support must preserve refusals for unqualified frames and tapered source states
@MarkTests.parametrize("CaseIndex", (0, 1, 2))
def CheckStartScope(CaseIndex: int) -> None:
    FixtureRoot = (
        FilePath(__file__).resolve().parents[5] / "re/Fusion/OffsetAdmission20261127"
    )
    Sample = JsonLib.loads((FixtureRoot / "Manifest.json").read_text())["refusals"][
        CaseIndex
    ]
    Source = FixtureRoot / Sample["file"]
    assert HashBytes(Source.read_bytes()).hexdigest() == Sample["sha256"]
    with RaisesError(ValueError):
        _ = OpenDocument(Source)


# malformed archives must fail before typed offset controls can reach consumers
@MarkTests.parametrize(
    "CaseName",
    (
        "start_kind",
        "entity_start",
        "missing_offset",
        "wrong_role",
        "owner",
        "parent",
        "reciprocal",
        "allocator",
        "units",
        "native_name",
        "value_copy",
        "nonfinite",
        "taper",
    ),
)
def CheckStartGuard(TmpPath: FilePath, CaseName: str) -> None:
    Source = (
        FilePath(__file__).resolve().parents[5]
        / "re/Fusion/OffsetAdmission20261127/Controls/baseline.f3d"
    )
    Target = TmpPath / "Changed.f3d"
    ChangeOffset(Source, Target, CaseName)
    with RaisesError(ValueError):
        _ = OpenDocument(Target)


# geometry and identity proofs must remain mandatory when parameter bindings are valid
@MarkTests.parametrize("CaseName", ("labels", "planes"))
def CheckStartSolid(TmpPath: FilePath, CaseName: str) -> None:
    Source = (
        FilePath(__file__).resolve().parents[5]
        / "re/Fusion/OffsetAdmission20261127/Controls/baseline.f3d"
    )
    Target = TmpPath / "Changed.f3d"
    if CaseName == "labels":
        MakeBadLabel(Source, Target)
    else:
        MakeOffsetPlane(Source, Target)
    with RaisesError(ValueError):
        _ = OpenDocument(Target)


# reader admission must not authorize unqualified native or neutral publication
@MarkTests.parametrize("FormatName", ("interchange.json", "fusion.f3d"))
def CheckStartWrite(TmpPath: FilePath, FormatName: str) -> None:
    Source = (
        FilePath(__file__).resolve().parents[5]
        / "re/Fusion/OffsetAdmission20261127/Controls/baseline.f3d"
    )
    Document = OpenDocument(Source)
    Target = TmpPath / (
        "Guard.json" if FormatName == "interchange.json" else "Guard.f3d"
    )
    _ = Target.write_bytes(b"existing destination")
    with RaisesError((ValueError, AdapterNotFoundError)):
        _ = WriteDocument(
            Document, Target, destination_format=FormatName, overwrite=True
        )
    assert Target.read_bytes() == b"existing destination"
