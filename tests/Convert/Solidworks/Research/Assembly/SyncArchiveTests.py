from __future__ import annotations

from os import getenv as ReadEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# synchronized archives must preserve linked references and their exact named child evidence
def TestSyncArchive(TmpPath: FilePath) -> None:
    OutputRoot = (
        FilePath(ReadEnv("SwResearchOutput") or str(TmpPath)) / "SourceParser/Assembly"
    )
    OutputRoot.mkdir(parents=True, exist_ok=True)
    ReportPath = OutputRoot / "Synchronized.json"
    Outcome = RunProcess(
        [
            PythonExec,
            str(KRepoRoot / "re/tooling/sw2026/serial/SyncedAssemblies.py"),
            "--report",
            str(ReportPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = ReadObject(ReportPath)
    assert Report["passed"] is True and Report["stream_comparisons"] == 40
    assert Report["sdk_header_comparisons"] == 10
    assert Report["sdk_config_handoffs"] == 5
    for Entry in CastValue(list[dict[str, object]], Report["cases"]):
        for Record in CastValue(list[dict[str, object]], Entry["records"]):
            Handoff = CastValue(dict[str, object], Record["sdk_config_handoff"])
            assert (
                Handoff["config_byte_identity"]
                is Handoff["resolved_byte_identity"]
                is True
            )
            assert (
                Handoff["direct_identity_preserved"]
                is Handoff["standalone_indices_preserved"]
                is True
            )
            assert Handoff["research_model_header_trace_retained"] is True
    assert Report["external_file_time_comparisons"] == 8
    assert Report["native_acceptance"] is Report["heldout_payloads_read"] is False
    assert Report["writer_output_count"] == 0
