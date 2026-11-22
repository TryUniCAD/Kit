from json import loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Configuration.MaterialVisual.RunVisualCase import (
    KVisualRoot,
)


# the primary texture must retain every authored field through the physical part reader
def TestPartTexture() -> None:
    ProofValue = KVisualRoot / "re/tooling/sw2026/materials/CheckPartTexture.py"
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(ProofValue)),
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0 and not Outcome.stderr, Outcome.stderr
    ReportValue = LoadJson(Outcome.stdout)
    assert ReportValue["prefix_span"] == [18, 891]
    assert ReportValue["visual_span"] == ["moVisualProperties_c", 7, 87, 891]
    assert ReportValue["prefix_map"] == {"entry_counter": 4, "end_counter": 8}
    assert ReportValue["identity"] == "Kit|Texture probe|71"
    assert ReportValue["selector"] == [0, 1, 1, 0, 1]
    assert ReportValue["texture_calls"] == 1
    assert ReportValue["texture_fields"] == {
        "f08": 0.125,
        "f10": -0.25,
        "f18": 0.375,
        "f20": -0.5,
        "f28": 0.625,
        "f30": -0.75,
        "f38": 0.875,
        "f40": -1.0,
        "f48": 1.125,
        "f50": -1.25,
        "f58": 1.375,
        "f60": -1.5,
        "f68": 1.625,
        "f70": "Kit texture Ω",
        "f78": -314,
        "f7c": -271828,
        "f80": 2.75,
        "f88": -4.125,
        "f9c": 913,
    }
    assert (
        ReportValue["prefix_sha256"]
        == "0d1407fc50dddb53db6900d8af862db5442a7622e5d301f45c8250f0bdebb0f8"
    )
    assert ReportValue["exact_typed_replay"] is True
    assert ReportValue["author_external_accesses"] == 0
    assert ReportValue["runtime_input_or_process_accesses"] == 0
