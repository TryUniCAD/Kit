from hashlib import sha256 as HashData
from pathlib import Path as FilePath
from os import pathsep as PathSeparator

from pytest import mark as TestMark, raises as RaiseError, MonkeyPatch as PatchScope

from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Integration.Fusion.RimFillet.Policy.ReadPolicyCases import (
    ReadPolicyCases,
)
from tests.Convert.Integration.Fusion.RimFillet.Policy.RimPolicyCase import (
    RimPolicyCase,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.MakeNeutralBad import (
    MakeNeutralBad,
)


# selection and profile corruptions must remain refused after complete serialized document restoration
@TestMark.parametrize("Sample", (ReadPolicyCases()[0], ReadPolicyCases()[12]))
@TestMark.parametrize(
    "ModeName",
    (
        "vertex_query",
        "wrong_curve",
        "lower_query",
        "missing_body",
        "foreign_body",
        "self_source",
        "missing_source",
        "missing_dependency",
        "extra_dependency",
        "missing_output",
        "wrong_final",
        "wrong_frame",
        "reverse",
        "symmetric",
        "taper",
        "oversized_radius",
        "missing_profile",
        "line_profile",
        "offset_circle",
    ),
)
def CheckNeutralBad(Sample: RimPolicyCase, ModeName: str) -> None:
    Encoded = MakeNeutralBad(Sample, ModeName)
    with RaiseError(ValueError, match="radius fillet"):
        Restored = CadDocument.from_json(Encoded)
        Restored.AssertValid()
    assert HashData(Sample.Source.read_bytes()).hexdigest() == Sample.Digest


# public cli refusal must precede publication and preserve both the source and existing destination
@TestMark.parametrize("Sample", (ReadPolicyCases()[0], ReadPolicyCases()[12]))
@TestMark.parametrize(
    "ModeName",
    (
        "vertex_query",
        "foreign_body",
        "missing_dependency",
        "wrong_frame",
        "line_profile",
        "oversized_radius",
    ),
)
def CheckNeutralCli(
    Sample: RimPolicyCase, ModeName: str, TmpPath: FilePath, MonkeyPatch: PatchScope
) -> None:
    RootPath = FilePath(__file__).resolve().parents[6]
    MonkeyPatch.setenv(
        "PYTHONPATH", PathSeparator.join((str(RootPath / "src"), str(RootPath / "Cli")))
    )
    Encoded = MakeNeutralBad(Sample, ModeName)
    Source = TmpPath / "Malformed.json"
    Target = TmpPath / "Preserved.f3d"
    _ = Source.write_text(Encoded, encoding="utf-8")
    _ = Target.write_bytes(b"preserved destination")
    Outcome = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--json", "--overwrite"
    )
    assert (
        Outcome.returncode != 0
        and "radius fillet" in Outcome.stderr
        and "Traceback" not in Outcome.stderr
    )
    assert Source.read_text(encoding="utf-8") == Encoded
    assert Target.read_bytes() == b"preserved destination"
    assert set(TmpPath.iterdir()) == {Source, Target}
    assert HashData(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
