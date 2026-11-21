from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# generated component references must survive linking the actual standalone sdk header nodes
def AssertHeadLink(ParentPath: FilePath, ChildPath: FilePath) -> None:
    ReportPath = ParentPath.parent / "HeaderHandoff.json"
    Outcome = RunProcess(
        [
            PythonExec,
            str(KRepoRoot / "re/tooling/sw2026/serial/CheckSdkHeaders.py"),
            str(ParentPath),
            str(ChildPath),
            "--config-handoff",
            "--report",
            str(ReportPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = ReadObject(ReportPath)
    assert Report["passed"] is True and Report["config_handoff_requested"] is True
    assert Report["document_count"] == 2 and Report["writer_output_count"] == 0
    assert Report["native_application_runs"] == 0 and Report["handoff_sources"]
    Cases = CastValue(list[dict[str, object]], Report["cases"])
    assert {Entry["file"] for Entry in Cases} == {ParentPath.name, ChildPath.name}
    for Entry in Cases:
        (Handoff,) = CastValue(list[dict[str, object]], Entry["config_handoffs"])
        assert Handoff["direct_base"] == 3 + CastValue(int, Handoff["direct_count"])
        assert Handoff["direct_identity_preserved"] is True
        assert Handoff["standalone_indices_preserved"] is True
        assert (
            Handoff["config_byte_identity"] is Handoff["resolved_byte_identity"] is True
        )
        assert Handoff["research_model_header_trace_retained"] is True
        if Entry["file"] == ParentPath.name:
            assert (
                Handoff["occurrence_aliases"] == 2
                and Handoff["mate_byte_identity"] is True
            )
