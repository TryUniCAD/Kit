from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

# each disclosed scene needs a fresh guarded process with its actual native parent
KSceneProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCfgLights.py"
)


# the merge queue needs the isolated process outcome and its precise reader diagnostics
def ReadSceneCase(CaseName: str) -> dict[str, object]:
    Outcome = RunProcess(
        (PythonExec, "-I", "-B", str(KSceneProbe), CaseName),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = CastValue(dict[str, object], LoadJson(Outcome.stdout))
    assert ReportValue["owner"] == "moPart_c.f1e0"
    assert ReportValue["runtime_external_accesses"] == 0
    assert ReportValue["inherited_slots"] == [4, 5]
    return ReportValue


# actual directional class reuse must preserve all three distinct objects and vectors
def TestSceneLadder() -> None:
    ReportValue = ReadSceneCase("ladder")
    MembersValue = CastValue(list[dict[str, object]], ReportValue["members"])
    assert ReportValue["counter"] == [69, 82]
    assert ReportValue["normalization_calls"] == 4
    assert [RowValue["slots"] for RowValue in MembersValue] == [
        [69, 70, 71],
        [72, 73, 74],
        [75, 76, 77],
        [75, 78, 79],
        [75, 80, 81],
    ]
    assert [RowValue["class"] for RowValue in MembersValue] == [
        "moEnvFolder_c",
        "moAmbientLight_c",
        "moDirectionLight_c",
        "moDirectionLight_c",
        "moDirectionLight_c",
    ]
    assert [RowValue["name"] for RowValue in MembersValue] == [
        "Lights and Cameras",
        "Ambient",
        "Directional1",
        "Directional2",
        "Directional3",
    ]
    assert [RowValue["record_bytes"] for RowValue in MembersValue] == [
        1488,
        291,
        343,
        321,
        321,
    ]
    assert [RowValue["direction"] for RowValue in MembersValue[2:]] == [
        [0.5417, 0.7071, -0.4545],
        [-0.3971, 0.342, 0.8517],
        [-0.8067, -0.1736, -0.5649],
    ]
    assert all(RowValue["normalization"] == [0, 0] for RowValue in MembersValue[1:])
    assert ReportValue["refusals"] == ["repeated_light"]


# the separate ambient scene must keep source words even when native runtime values clear
def TestSceneSmall() -> None:
    ReportValue = ReadSceneCase("concave")
    FolderValue, LightValue = CastValue(list[dict[str, object]], ReportValue["members"])
    assert ReportValue["counter"] == [54, 60]
    assert ReportValue["normalization_calls"] == 1
    assert FolderValue["slots"] == [54, 55, 56]
    assert FolderValue["record_bytes"] == 531
    assert LightValue["slots"] == [57, 58, 59]
    assert LightValue["record_bytes"] == 319
    assert LightValue["name"] == "Import ambient"
    assert LightValue["normalization"] == LightValue["state"] == [0, 0]
    assert ReportValue["contrasted_words"] == [-739, 0, 27, -16]
    assert ReportValue["refusals"] == [
        "truncated_word",
        "trailing",
        "wrong_version",
        "null_scene",
        "light_as_root",
        "unknown_nested_role",
        "borrowed_name",
        "populated_property",
        "empty_scene",
        "missing_inherited_name",
    ]
