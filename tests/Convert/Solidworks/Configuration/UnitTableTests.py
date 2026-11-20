from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# a fresh process must consume the original table records through the shared codec
KUnitProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckUnitTables.py"
)

# both ordinary native tables must refuse the same unsupported framing and role changes
KCommonRefusals = [
    "truncated",
    "trailing",
    "version",
    "density_override",
    "earlier_root",
    "null_row",
]


# the verifier runs inside the same integration boundary as the other archive process cases
def ReadUnitCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KUnitProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))


# the native ladder table retains its inherited length data and distinct override
def TestUnitsLadder() -> None:
    ReportValue = ReadUnitCase("ladder")
    assert ReportValue["archive_version"] == 19000
    assert ReportValue["tables"] == [
        {
            "bytes": 1487,
            "rows": 16,
            "root_index": 9,
            "next_index": 43,
            "shared_classes": 0,
            "schema_count": 19,
            "length": [2, 0.1, 0],
            "length_override_index": 12,
            "angle": 0,
            "density_override": 0,
            "system": 4,
        }
    ]
    assert ReportValue["refusals"] == [
        *KCommonRefusals,
        "wrong_map_base",
        "wrong_length_owner",
    ]


# the second physical table has distinct units and resolves the original class positions
def TestUnitsLink() -> None:
    ReportValue = ReadUnitCase("concave")
    assert ReportValue["archive_version"] == 19000
    assert ReportValue["tables"] == [
        {
            "bytes": 1421,
            "rows": 16,
            "root_index": 9,
            "next_index": 42,
            "shared_classes": 0,
            "schema_count": 19,
            "length": [4, 0.01, 0],
            "length_override_index": None,
            "angle": 0,
            "density_override": 0,
            "system": 4,
        },
        {
            "bytes": 1055,
            "rows": 16,
            "root_index": 60,
            "next_index": 77,
            "shared_classes": 17,
            "schema_count": 19,
            "length": [4, 0.01, 2],
            "length_override_index": None,
            "angle": 3,
            "density_override": 0,
            "system": 1,
        },
    ]
    assert ReportValue["refusals"] == [
        *KCommonRefusals,
        "absent_class_seed",
        "wrong_seed_kind",
    ]
