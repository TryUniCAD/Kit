from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# each native source needs an isolated guarded configuration reader process
KSectionProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgSection.py"
)


# verified framing must keep the actual header alias and distinguish incomplete ownership
def ReadSecCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KSectionProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["runtime_external_accesses"] == 0
    assert ReportValue["root_completed"] is False
    assert ReportValue["config_slot"] == 3 and ReportValue["base"] == 4
    return ReportValue


# nested windows must carry native graph identity across the following stream fields
def TestLadderSec() -> None:
    ReportValue = ReadSecCase("ladder")
    assert ReportValue["sections"] == [[18, 3052], [3056, 25390]]
    assert ReportValue["header_slot"] == 69 and ReportValue["lead"] == [0, 19000]
    assert ReportValue["ghost"] == {"f80": 10000, "fe0": 1, "n": 0, "objects": []}
    assert ReportValue["signed_ghost"] == {"f80": 25, "fe0": -1, "n": 0, "objects": []}
    assert ReportValue["authored_graph"] == [20, 42, 5]
    assert ReportValue["refusals"] == [
        "prefix",
        "oversized",
        "unconsumed",
        "nested_crossing",
        "scalar_crossing",
        "tag_crossing",
        "descriptor_crossing",
        "vendor_count_crossing",
        "framework_count_crossing",
        "text_payload_crossing",
        "unicode_length_crossing",
        "wrong_version",
        "skipped_section",
        "inline_header",
        "populated_ghost",
    ]


# the separate imported part has different section ends and zero stored lead words
def TestConcaveSec() -> None:
    ReportValue = ReadSecCase("concave")
    assert ReportValue["sections"] == [[18, 2105], [2109, 22700]]
    assert ReportValue["header_slot"] == 15 and ReportValue["lead"] == [0, 0]
    assert ReportValue["ghost"] == {"f80": 10000, "fe0": 0, "n": 0, "objects": []}
