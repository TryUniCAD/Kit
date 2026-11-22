from __future__ import annotations

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactDirs import ReportDir
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.CorpusPaths import KPrimaryStreams
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# complete containers expose framing changes alongside actual archive maps and neighboring fields
def TestStrings(TmpPath: FilePath) -> None:
    OutputRoot = ReportDir(TmpPath, "SourceParser", "Curve", "Strings")
    ScriptPath = KRepoRoot / "re/tooling/sw2026/serial/StringCorpus.py"
    for ModeValue in ("prepare", "verify"):
        Outcome = RunProcess(
            [PythonExec, str(ScriptPath), ModeValue, str(OutputRoot)],
            cwd=KRepoRoot,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        if OutputRoot.is_dir():
            for Suffix, TextValue in (
                ("stdout.log", Outcome.stdout),
                ("stderr.log", Outcome.stderr),
            ):
                Written = ArtifactFile(OutputRoot, f"{ModeValue}.{Suffix}").write_text(
                    TextValue, encoding="utf-8"
                )
                assert Written == len(TextValue)
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Evidence = ReadObject(ArtifactFile(OutputRoot, "Checked.json"))
    assert Evidence["passed"] is Evidence["source_immutable"] is True
    assert Evidence["writer_output"] is Evidence["native_acceptance"] is False
    assert Evidence["heldout_payloads_read"] == 0
    assert Evidence["primary_streams"] == 8 and Evidence["linked_streams"] == 1
    assert Evidence["positive_count"] == 10 and Evidence["negative_count"] == 3
    assert set(CastValue(list[str], Evidence["emitted_modeled_streams"])) == set(
        KPrimaryStreams
    )
    assert (
        Evidence["donor_template_used"]
        is Evidence["saved_stream_passthrough"]
        is Evidence["complete_native_document"]
        is False
    )
    assert (
        Evidence["prepared_sha256"]
        == HashBytes(ArtifactFile(OutputRoot, "Prepared.json").read_bytes()).hexdigest()
    )
