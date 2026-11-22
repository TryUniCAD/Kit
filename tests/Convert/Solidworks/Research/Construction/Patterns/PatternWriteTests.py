from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# ordinary preparation preserves typed pattern geometry while unsupported publication leaves every destination unchanged
def TestPatWrite() -> None:
    Script = (
        KRepoRoot
        / "re/tooling/sw2026/linear_pattern/neutral/ProvePublicPatternWrite.py"
    )
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(Script)),
        capture_output=True,
        text=True,
        check=False,
        timeout=150,
    )
    assert Outcome.returncode == 0 and not Outcome.stderr, Outcome.stderr
    Report: dict[str, object] = LoadJson(Outcome.stdout)
    assert Report["guarded_worker_processes"] == 2
    assert Report["native_processes_started"] == Report["protected_inputs_read"] == 0
    Cases = CastValue(dict[str, dict[str, object]], Report["cases"])
    assert set(Cases) == {"ColdRaisedPatternA", "ColdRaisedPatternB"}
    First = Cases["ColdRaisedPatternA"]
    Second = Cases["ColdRaisedPatternB"]
    assert (First["count"], First["faces"], First["reversed"]) == (3, 21, False)
    assert (Second["count"], Second["faces"], Second["reversed"]) == (4, 26, True)
    for Evidence in Cases.values():
        assert Evidence["prepared_routes"] == Evidence["missing_receipt_refusals"] == 4
        assert Evidence["publication_routes"] == 0 and Evidence["logical_streams"] == 10
        assert Evidence["intended_capabilities"] == [
            "body_structure",
            "configurations",
            "editable_sketches",
            "parameters",
            "parametric_history",
            "selections",
            "support_planes",
        ]
        assert (
            Evidence["runtime_input_file_reads"] == 0
            and Evidence["strict_path_and_stream"] is True
        )
        assert Evidence["refusals"] == [
            "overlapping",
            "overhanging",
            "retained_geometry",
            "configuration",
            "unnamed_stream",
            "unmodeled_option",
            "wrong_locator",
        ]
