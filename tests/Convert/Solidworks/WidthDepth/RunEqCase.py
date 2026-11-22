from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from typing import cast as CastValue

from tests.Convert.Solidworks.WidthDepth.MakeEqRequest import MakeEqRequest


# both queue cases use the same portable model and independently pinned receipt
def RunEqCase(RuntimePath: str) -> tuple[dict[str, object], str]:
    RootValue = FilePath(__file__).resolve().parents[4]
    EvidencePath = RootValue / "re/solidworks/measurements/2026"
    NativeReport = LoadJson(
        (EvidencePath / "SdkWidthDepthPreparationNative01.json").read_bytes()
    )
    WireReport = LoadJson((EvidencePath / "SdkWidthDepthReview01.json").read_bytes())
    Digest = CastValue(str, NativeReport["cases"]["Reference"]["generated_sha256"])
    Command = RootValue / "re/tooling/sw2026/equations/ProveMeasuredWidthDepth.py"
    Request = MakeEqRequest() | {
        "receipt": NativeReport,
        "stream_sha256": WireReport["reference"]["stream_sha256"],
    }
    Outcome = RunProcess(
        (
            RuntimePath,
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
    return Report, Digest
