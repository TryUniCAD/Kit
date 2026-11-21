from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# the bounded helper must run in a fresh guarded process for each document
KFinishProbe = (
    FilePath(__file__).resolve().parents[5] / "re/tooling/sw2026/CheckCfgFinish.py"
)

# the three roles use the same layout at distinct observed positions
KFinishCases = (
    (
        "ladder",
        69,
        ([16177, 16499], [17306, 17628], [17628, 17950]),
        "f3c69749ed02bd488ab5c2a78a4ae3581f9c0a48a6c57a73df703fc7ed9052fa",
        "140e622af90241ea7d7290dee6f407d2fea7993e025671142bae1065011d4c80",
    ),
    (
        "concave",
        54,
        ([14626, 14972], [15839, 16185], [16185, 16531]),
        "f8f312682227a80904061cf83cdec95fd9403a141ac92a1605ea2c198ba55e65",
        "e6ab28092afb8b1176b3d94ef66908fbbf14ad528fc62f8c30b8154a4e7c8a95",
    ),
)


# process diagnostics must remain visible when a scoped archive replay fails
def RunFinishCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KFinishProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Result = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert Result["case"] == CaseName
    assert Result["runtime_external_accesses"] == 0
    return Result


# real bounded helpers must preserve both fonts and every field at the native positions
def TestFinishParts() -> None:
    for CaseName, CounterValue, Bounds, FieldsHash, WireHash in KFinishCases:
        Result = RunFinishCase(CaseName)
        assert Result["map_anchors"] == [1, 2, 3]
        assert Result["map_base"] == 4
        assert Result["map_counter"] == CounterValue
        Records = CastValue(list[dict[str, object]], Result["exact_intervals"])
        assert [RowValue["layout"] for RowValue in Records] == [
            "moSFDataHelper_c",
            "utCharFormat_c",
            "moAnnotationDataHelper_c",
            "utCharFormat_c",
        ] * 3
        Roots = Records[::4]
        assert [RowValue["role"] for RowValue in Roots] == [
            ["f2e8"],
            ["f730", "f260"],
            ["f730", "f268"],
        ]
        assert tuple(RowValue["interval"] for RowValue in Roots) == Bounds
        assert {RowValue["fields_sha256"] for RowValue in Roots} == {FieldsHash}
        assert {RowValue["wire_sha256"] for RowValue in Roots} == {WireHash}


# the authored helper distinguishes both font owners and rejects alternative boundaries
def TestFinishWire() -> None:
    Result = RunFinishCase("wire")
    assert Result["bytes"] == 372
    assert Result["wire_sha256"] == (
        "8cc8ee465b1e487b83d8644eb9bb0a7ce2da334b1df5e87f82030ca252a82eed"
    )
    assert Result["fields_sha256"] == (
        "8ab421ce98e4ee1475abf2c1eff4bb8e4a83f8bb0027e224d163b7d82895cadf"
    )
    assert Result["outer_font"] == ["A", "Finish É"]
    assert Result["leader_font"] == "Lead λ😀"
    assert Result["maps"] == {
        "base": 4,
        "counter": 69,
        "entries": 68,
        "classes": 18,
        "objects": 50,
    }
    assert Result["refusals"] == [
        "truncated",
        "trailing",
        "wrong_version",
        "unmapped_part",
        "noncanonical_text",
    ]
