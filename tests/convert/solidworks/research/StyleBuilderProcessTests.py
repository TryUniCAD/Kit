from __future__ import annotations

from copy import deepcopy as CopyValues
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

KRepoRoot = FilePath(__file__).resolve().parents[4]
KProgram = FilePath(__file__).with_name("StyleBuilderProcess.py")
KStyles: dict[str, object] = {
    "standard": 1,
    "font_name": "authored font α",
    "line_style_name": "authored continuous",
    "language_id": 1033,
    "print_widths_m": [0.0001, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006, 0.0007, 0.0008],
    "exclusion_names": [],
    "task_labels": [
        "description",
        "priority high",
        "priority low",
        "complete",
        "reminder",
    ],
    "cutlist_expressions": ["authored item", "authored description", "authored stock"],
}
KUnits: dict[str, object] = {
    "length_unit": "mm",
    "angle_unit": "degree",
    "unit_system": "mmgs",
    "decimal_places": 4,
}


def MakeInput() -> dict[str, dict[str, object]]:
    return CopyValues({"styles": KStyles, "units": KUnits})


def RunBuilders(Inputs: list[dict[str, dict[str, object]]]) -> list[dict[str, object]]:
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(KProgram), str(KRepoRoot)],
        input=DumpJson(Inputs),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(list[dict[str, object]], LoadJson(Outcome.stdout))


def TestStyleGraph() -> None:
    Changed = MakeInput()
    Changed["styles"]["font_name"] = "authored alternative font 輪郭"
    Changed["styles"]["language_id"] = 1037
    Changed["styles"]["exclusion_names"] = ["α", "longer authored exclusion"]
    Changed["styles"]["task_labels"] = [
        "description α",
        "high",
        "low",
        "finished",
        "reminder α",
    ]
    Small, Large = RunBuilders([MakeInput(), Changed])
    assert Small["read_blocked"] and Large["read_blocked"]
    assert CastValue(int, Small["import_reads"]) > 0
    assert Small["standard"] == Large["standard"] == 1
    assert Small["font"] == Small["linear_font"] == "authored font α"
    assert Large["font"] == Large["linear_font"] == "authored alternative font 輪郭"
    assert Small["annotation_align"] == 0 and Large["annotation_align"] == 2
    assert Small["exclusion_count"] == 0 and Large["exclusion_count"] == 2
    assert Large["exclusions"] == [{"s": "α"}, {"s": "longer authored exclusion"}]
    assert Small["task_count"] == Large["task_count"] == 5
    assert Large["task_labels"] == [
        {"s": Value}
        for Value in ["description α", "high", "low", "finished", "reminder α"]
    ]
    assert Small["cutlist"] == [
        "authored item",
        "authored description",
        "authored stock",
    ]
    assert Small["gtol_frames"] == Large["gtol_frames"] == 2
    assert CastValue(int, Large["style_size"]) > CastValue(int, Small["style_size"])
    assert Large["style_hash"] != Small["style_hash"]
    assert Large["unit_hash"] == Small["unit_hash"]


def TestUnitTables() -> None:
    Custom = MakeInput()
    Custom["units"] = {
        "definitions": [
            {"kind": "length", "unit_code": 2, "decimal_places": 6},
            {"kind": "angle", "unit_code": 3, "decimal_places": 8},
        ]
    }
    Profile, Paired = RunBuilders([MakeInput(), Custom])
    assert Profile["read_blocked"] and Paired["read_blocked"]
    assert Profile["unit_count"] == 16 and Paired["unit_count"] == 2
    assert Paired["unit_classes"] == ["moLengthUserUnits_c", "moAngleUserUnits_c"]
    assert Paired["unit_codes"] == [2, 3] and Paired["unit_precision"] == [6, 8]
    Classes = CastValue(list[str], Profile["unit_classes"])
    Codes = CastValue(list[object], Profile["unit_codes"])
    assert Codes[Classes.index("moLengthUserUnits_c")] == 0
    assert Codes[Classes.index("moAngleUserUnits_c")] == 0
    assert Codes[Classes.index("moUnitSysUnits_c")] == 4
    assert Profile["unit_precision"] == [4] * 16
    assert CastValue(int, Profile["unit_size"]) > CastValue(int, Paired["unit_size"])
    assert Profile["style_hash"] == Paired["style_hash"]


def TestInputScope() -> None:
    Standard = MakeInput()
    Standard["styles"]["standard"] = 0
    UnknownUnit = MakeInput()
    UnknownUnit["units"]["length_unit"] = "unrecovered unit"
    Precision = MakeInput()
    Precision["units"]["decimal_places"] = True
    Labels = MakeInput()
    Labels["styles"]["task_labels"] = ["incomplete"]
    Results = RunBuilders([Standard, UnknownUnit, Precision, Labels])
    assert all(Result["read_blocked"] for Result in Results)
    assert "standard-1" in CastValue(str, Results[0]["error"])
    assert "unsupported semantic length" in CastValue(str, Results[1]["error"])
    assert "decimal places must be an integer" in CastValue(str, Results[2]["error"])
    assert "five authored task-column" in CastValue(str, Results[3]["error"])
