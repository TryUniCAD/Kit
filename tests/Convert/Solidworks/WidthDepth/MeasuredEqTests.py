from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec, platform as PlatformValue
from typing import cast as CastValue

from tests.Convert.Solidworks.WidthDepth.MakeEqRequest import MakeEqRequest


# an independently authored queue request verifies the real strict reader and gated writer in a fresh process
def TestMeasuredEq() -> None:
    RootValue = FilePath(__file__).resolve().parents[4]
    EvidencePath = RootValue / "re/solidworks/measurements/2026"
    NativeReport = LoadJson(
        (EvidencePath / "SdkWidthDepthPreparationNative01.json").read_bytes()
    )
    WireReport = LoadJson((EvidencePath / "SdkWidthDepthReview01.json").read_bytes())
    Digest = NativeReport["cases"]["Reference"]["generated_sha256"]
    Command = RootValue / "re/tooling/sw2026/equations/ProveMeasuredWidthDepth.py"
    Request = MakeEqRequest() | {
        "receipt": NativeReport,
        "stream_sha256": WireReport["reference"]["stream_sha256"],
    }
    Outcome = RunProcess(
        (
            PythonExec,
            "-I",
            "-B",
            str(Command),
            "--root",
            str(RootValue),
            "--worker",
            "--portable",
        ),
        input=DumpJson(Request),
        capture_output=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Report["guarded_runtime_input_reads"] == 0
    assert Report["unrelated_formula_legacy_inspection"] is True
    AssertEqRead(Report, Digest)


# strict native transport retains all owners and requires complete binary identity before both publication routes
def AssertEqRead(Report: dict[str, object], Digest: str) -> None:
    IsMeasured = Report["sha256"] == Digest
    assert Report["matches_measured_archive"] is IsMeasured
    assert Report["published_routes"] == (
        (4 if PlatformValue == "win32" else 5) if IsMeasured else 0
    )
    assert Report["feature_rows"] == 19
    assert Report["parameter_ids"] == [
        "sldprt:parameter:18:D1",
        "sldprt:parameter:18:D2",
        "sldprt:parameter:21:D1",
    ]
    assert Report["width_inverse"] == {
        "width_mm": 20.01,
        "depth_mm": 10.005,
        "strict_readback_regenerated": True,
        "publication_refused": True,
    }
    Refusals = CastValue(list[str], Report["refusals"])
    assert "unqualified_mode_partial_diagnostic" in Refusals
    assert "unqualified_mode_raw_diagnostic" in Refusals
