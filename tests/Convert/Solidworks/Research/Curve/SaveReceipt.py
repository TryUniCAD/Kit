from __future__ import annotations

from hashlib import sha256 as HashBytes
from json import dumps as DumpJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile
from tests.Convert.Solidworks.Research.Curve.CorpusPaths import KCurveCorpus


# parser evidence must remain distinct from generated candidate files in remote artifacts
def SaveReceipt(
    ReportPath: FilePath, Outcome: CompletedProcess[str], IsLinked: bool
) -> None:
    Evidence = {
        "scope": "curve discovery source parser compatibility only",
        "is_writer_output": False,
        "native_acceptance_inherited": False,
        "manifest_sha256": HashBytes(
            (KCurveCorpus / "Manifest.json").read_bytes()
        ).hexdigest(),
        "require_proven": True,
        "linked_configurations": IsLinked,
        "returncode": Outcome.returncode,
    }
    for Suffix, TextValue in (
        (".stdout.log", Outcome.stdout),
        (".stderr.log", Outcome.stderr),
        (".scope.json", DumpJson(Evidence, indent=2) + "\n"),
    ):
        SaveReport(ReportPath.with_suffix(Suffix), TextValue)


# process logs keep their designated name within the checked artifact directory
def SaveReport(ReportPath: FilePath, TextValue: str) -> None:
    OutputPath = ArtifactFile(ReportPath.parent, ReportPath.name)
    Written = OutputPath.write_text(TextValue, encoding="utf-8")
    assert Written == len(TextValue)
