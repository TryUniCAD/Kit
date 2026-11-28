from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue
from zlib import ZLIB_RUNTIME_VERSION as DeflateRuntime


# the exact disclosed neutral requests exercise ordinary publication and strict readback in fresh guarded processes
def RunChamfFlow(SlotValue: int) -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    WorkerValue = RootValue / "re/tooling/sw2026/CheckMeasuredChamfer.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(WorkerValue), "--slot", str(SlotValue)),
        cwd=RootValue,
        capture_output=True,
        encoding="utf-8",
        timeout=100,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    if ReportValue["archive_sha256"] == ReportValue["expected_native_sha256"]:
        assert ReportValue["native_acceptance_routes"] == 2
        assert ReportValue["readback_native_acceptance_routes"] == 2
        assert ReportValue["exact_native_transfer_evidence"] is True
        assert ReportValue["codec_refused"] is False
    else:
        assert "zlib-ng" in DeflateRuntime
        assert ReportValue["native_acceptance_routes"] == 0
        assert ReportValue["readback_native_acceptance_routes"] == 0
        assert ReportValue["exact_native_transfer_evidence"] is False
        assert ReportValue["codec_refused"] is True
    assert ReportValue["qualified_logical_streams"] == 10
    assert ReportValue["owned_selection_count"] == 2
    assert ReportValue["altered_readback_refused"] is True
    assert ReportValue["unsupported_history_read_guarded"] is True
    assert ReportValue["discovery_refusals"] == ["class_alias", "keyword_only"]
    assert ReportValue["semantic_read_matches"] is True
    assert ReportValue["runtime_reads"] == 0


# the shared distance retains its one actual editable driver
def TestEqualDist() -> None:
    RunChamfFlow(0)


# the independently set distances retain distinct driver ownership
def TestTwoDist() -> None:
    RunChamfFlow(1)


# ordinary merge queue coverage binds the real saved part to distinct semantic and raw payload results
def TestSavedDist() -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    WorkerValue = RootValue / "re/tooling/sw2026/CheckWarmChmfBoundary.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(WorkerValue), "--fixture"),
        cwd=RootValue,
        capture_output=True,
        encoding="utf-8",
        timeout=75,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    CasesValue = CastValue(dict[str, dict[str, object]], LoadJson(Outcome.stdout))
    assert set(CasesValue) == {"EqualOriginal"}
    ReportValue = CasesValue["EqualOriginal"]
    assert ReportValue["strict_semantic_refusals"] == 2
    assert ReportValue["permissive_warnings"] == 2
    assert ReportValue["permissive_brep_topology"] == [1, 1, 7, 15, 10]
    assert ReportValue["semantic_runtime_reads"] == 0
    Payloads = CastValue(list[str], ReportValue["raw_payload_sha256"])
    assert len(set(Payloads)) == 2
